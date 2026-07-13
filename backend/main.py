"""Reddit Opportunity Scanner — FastAPI-backend.

Start lokaal met:  .venv\\Scripts\\python -m uvicorn backend.main:app --port 8000
Serveert de gebouwde React-frontend uit frontend/dist op /.
"""
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from . import db  # noqa: E402
from .drafts import generate_draft  # noqa: E402
from .reddit_client import (  # noqa: E402
    get_subreddit_rules,
    scan_subreddits,
    verify_subreddits,
)
from .scoring import compute_scores  # noqa: E402
from .suggest import suggest_subreddits_keywords  # noqa: E402

app = FastAPI(title="Reddit Opportunity Scanner")
db.init_db()


class SubredditIn(BaseModel):
    name: str
    selfpromo: bool = False  # standaard uit; alleen handmatig aan te zetten


class ProjectIn(BaseModel):
    name: str
    instruction: str = ""
    subreddits: list[SubredditIn] = []
    keywords: list[str] = []


class DraftIn(BaseModel):
    mode: str  # karma | marketing


class SuggestIn(BaseModel):
    instruction: str


# ---------- Projecten ----------

@app.get("/api/projects")
def list_projects():
    with db.get_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id").fetchall()
    return [db.row_to_project(r) for r in rows]


@app.post("/api/projects")
def create_project(p: ProjectIn):
    subs = json.dumps([s.model_dump() for s in p.subreddits])
    with db.get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO projects (name, instruction, subreddits, keywords)"
            " VALUES (?, ?, ?, ?)",
            (p.name, p.instruction, subs, json.dumps(p.keywords)),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
    return db.row_to_project(row)


@app.put("/api/projects/{project_id}")
def update_project(project_id: int, p: ProjectIn):
    subs = json.dumps([s.model_dump() for s in p.subreddits])
    with db.get_conn() as conn:
        cur = conn.execute(
            "UPDATE projects SET name=?, instruction=?, subreddits=?, keywords=? WHERE id=?",
            (p.name, p.instruction, subs, json.dumps(p.keywords), project_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Project niet gevonden")
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return db.row_to_project(row)


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int):
    with db.get_conn() as conn:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Project niet gevonden")
    return {"ok": True}


# ---------- Scannen & scoren ----------

def _get_project(project_id: int) -> dict:
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Project niet gevonden")
    return db.row_to_project(row)


@app.post("/api/projects/{project_id}/scan")
def scan_project(project_id: int):
    project = _get_project(project_id)
    if not project["subreddits"] or not project["keywords"]:
        raise HTTPException(400, "Project heeft subreddits én keywords nodig om te scannen")

    sub_names = [s["name"] for s in project["subreddits"]]
    try:
        posts = scan_subreddits(sub_names, project["keywords"])
    except RuntimeError as exc:
        raise HTTPException(400, str(exc))

    # Alleen posts scoren die we nog niet kennen (geschiedenis blijft staan).
    with db.get_conn() as conn:
        known = {
            r["reddit_id"]
            for r in conn.execute(
                "SELECT reddit_id FROM posts WHERE project_id = ?", (project_id,)
            ).fetchall()
        }
    new_posts = [p for p in posts if p["reddit_id"] not in known]
    if not new_posts:
        return {"found": len(posts), "new": 0}

    whitelist = {s["name"].lower() for s in project["subreddits"] if s.get("selfpromo")}
    try:
        scored = compute_scores(project["instruction"], new_posts)
    except (anthropic.AnthropicError, TypeError) as exc:
        raise HTTPException(400, f"Scoren via Claude mislukt: {exc}")

    with db.get_conn() as conn:
        for s in scored:
            if s["is_pain_point"]:
                label = "research"
            elif s["subreddit"].lower() in whitelist:
                label = "marketing"
            else:
                label = "karma"
            cur = conn.execute(
                "INSERT INTO posts (project_id, reddit_id, subreddit, title, body, url,"
                " author, num_comments, upvotes, created_utc, label)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, s["reddit_id"], s["subreddit"], s["title"], s["body"],
                 s["url"], s["author"], s["num_comments"], s["upvotes"],
                 s["created_utc"], label),
            )
            conn.execute(
                "INSERT INTO scores (post_id, total, relevance, age, comments, upvotes, rationale)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cur.lastrowid, s["total"], s["factors"]["relevance"], s["factors"]["age"],
                 s["factors"]["comments"], s["factors"]["upvotes"], s["rationale"]),
            )
    return {"found": len(posts), "new": len(new_posts)}


@app.get("/api/projects/{project_id}/posts")
def list_posts(project_id: int):
    _get_project(project_id)
    with db.get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.*, s.total, s.relevance, s.age AS age_score,
                   s.comments AS comments_score, s.upvotes AS upvotes_score, s.rationale
            FROM posts p JOIN scores s ON s.post_id = p.id
            WHERE p.project_id = ?
            ORDER BY s.total DESC
            """,
            (project_id,),
        ).fetchall()
        drafts = conn.execute(
            """
            SELECT d.* FROM draft_replies d
            JOIN posts p ON p.id = d.post_id
            WHERE p.project_id = ?
            ORDER BY d.id
            """,
            (project_id,),
        ).fetchall()
    drafts_by_post: dict[int, list[dict]] = {}
    for d in drafts:
        drafts_by_post.setdefault(d["post_id"], []).append(dict(d))
    out = []
    for r in rows:
        item = dict(r)
        item["drafts"] = drafts_by_post.get(r["id"], [])
        out.append(item)
    return out


# ---------- Suggestie-flow ----------

@app.post("/api/suggest")
def suggest(body: SuggestIn):
    """Claude stelt subreddits + keywords voor; elke subreddit wordt daarna via de
    Reddit API geverifieerd. Alleen geverifieerde subreddits worden teruggegeven.
    Er wordt hier niets opgeslagen — dat gebeurt pas als de gebruiker bevestigt."""
    if not body.instruction.strip():
        raise HTTPException(400, "Vul eerst een projectinstructie in")
    try:
        proposal = suggest_subreddits_keywords(body.instruction)
    except (anthropic.AnthropicError, TypeError) as exc:
        raise HTTPException(400, f"Voorstel via Claude mislukt: {exc}")
    try:
        verified, rejected = verify_subreddits(proposal["subreddits"])
    except RuntimeError as exc:
        raise HTTPException(400, str(exc))
    return {
        "subreddits": verified,
        "keywords": proposal["keywords"],
        "rejected": rejected,
    }


@app.get("/api/subreddits/{name}/rules")
def subreddit_rules(name: str):
    try:
        return {"rules": get_subreddit_rules(name)}
    except RuntimeError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(404, f"Regels van r/{name} niet op te halen: {exc}")


# ---------- Concept-reacties ----------

@app.post("/api/posts/{post_id}/draft")
def create_draft(post_id: int, body: DraftIn):
    if body.mode not in ("karma", "marketing"):
        raise HTTPException(400, "mode moet 'karma' of 'marketing' zijn")
    with db.get_conn() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        raise HTTPException(404, "Post niet gevonden")
    if body.mode == "marketing" and post["label"] == "karma":
        raise HTTPException(
            400, "Deze subreddit staat geen zelfpromotie toe (niet in whitelist)"
        )
    project = _get_project(post["project_id"])
    try:
        content = generate_draft(project["instruction"], dict(post), body.mode)
    except (anthropic.AnthropicError, TypeError) as exc:
        raise HTTPException(400, f"Genereren via Claude mislukt: {exc}")
    with db.get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO draft_replies (post_id, mode, content) VALUES (?, ?, ?)",
            (post_id, body.mode, content),
        )
        row = conn.execute("SELECT * FROM draft_replies WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


# ---------- Frontend ----------

DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
