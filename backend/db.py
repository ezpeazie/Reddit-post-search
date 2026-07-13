"""SQLite-opslag voor projecten, posts, scores en concept-reacties."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    instruction TEXT NOT NULL DEFAULT '',
    subreddits TEXT NOT NULL DEFAULT '[]',          -- JSON-lijst van {name, selfpromo}
    keywords TEXT NOT NULL DEFAULT '[]',            -- JSON-lijst
    selfpromo_whitelist TEXT NOT NULL DEFAULT '[]', -- verouderd; vervangen door selfpromo-toggle per subreddit
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    reddit_id TEXT NOT NULL,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    num_comments INTEGER NOT NULL DEFAULT 0,
    upvotes INTEGER NOT NULL DEFAULT 0,
    created_utc REAL NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    label TEXT NOT NULL DEFAULT 'karma',            -- karma | marketing | research
    UNIQUE(project_id, reddit_id)
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL UNIQUE REFERENCES posts(id) ON DELETE CASCADE,
    total REAL NOT NULL,
    relevance REAL NOT NULL,
    age REAL NOT NULL,
    comments REAL NOT NULL,
    upvotes REAL NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS draft_replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    mode TEXT NOT NULL,                             -- karma | marketing
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate_subreddit_format(conn)


def _migrate_subreddit_format(conn: sqlite3.Connection) -> None:
    """Oud formaat (lijst van strings + aparte whitelist) omzetten naar
    lijst van {name, selfpromo}-objecten."""
    rows = conn.execute("SELECT id, subreddits, selfpromo_whitelist FROM projects").fetchall()
    for r in rows:
        subs = json.loads(r["subreddits"])
        if subs and isinstance(subs[0], str):
            whitelist = {s.lower() for s in json.loads(r["selfpromo_whitelist"])}
            new = [{"name": s, "selfpromo": s.lower() in whitelist} for s in subs]
            conn.execute(
                "UPDATE projects SET subreddits = ? WHERE id = ?",
                (json.dumps(new), r["id"]),
            )


def row_to_project(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["subreddits"] = json.loads(d["subreddits"])
    d["keywords"] = json.loads(d["keywords"])
    d.pop("selfpromo_whitelist", None)
    return d
