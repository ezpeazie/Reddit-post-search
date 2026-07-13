"""Scoring van gevonden posts.

Relevantie komt uit Claude Haiku (gebatcht: meerdere posts per API-call).
De overige factoren (leeftijd, reacties, upvotes) worden deterministisch
berekend. Gewichten conform CLAUDE.md: relevantie zwaarst, leeftijd en
reacties middel, upvotes licht (met plafond).
"""
import json
import math
import time

import anthropic

MODEL = "claude-haiku-4-5-20251001"  # vastgelegd in CLAUDE.md (kostenreden)
BATCH_SIZE = 20

WEIGHTS = {
    "relevance": 0.5,
    "age": 0.2,
    "comments": 0.2,
    "upvotes": 0.1,
}

RELEVANCE_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "reddit_id": {"type": "string"},
                    "relevance": {"type": "integer", "description": "0-100, hoe relevant is deze post om op te reageren gezien de projectinstructie"},
                    "is_pain_point": {"type": "boolean", "description": "true als de post een klacht/pijnpunt over een concurrent of bestaande oplossing signaleert"},
                    "rationale": {"type": "string", "description": "1 korte zin uitleg, in het Nederlands"},
                },
                "required": ["reddit_id", "relevance", "is_pain_point", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "Je beoordeelt Reddit-posts voor iemand die zinvol wil bijdragen aan discussies "
    "rond een specifiek project. Je krijgt de projectinstructie en een batch posts. "
    "Geef per post een relevantiescore 0-100: hoe geschikt is deze post om een "
    "waardevolle reactie op te schrijven, gegeven het project? Markeer daarnaast of "
    "de post een pijnpunt of klacht over een concurrent/bestaande oplossing bevat "
    "(interessant als research). Wees streng: generieke posts zonder raakvlak "
    "scoren laag."
)


def age_score(created_utc: float) -> float:
    """Recenter = beter. Halfwaardetijd van 48 uur."""
    hours = max(0.0, (time.time() - created_utc) / 3600)
    return 100 * math.pow(0.5, hours / 48)


def comments_score(num_comments: int) -> float:
    """Minder reacties = meer ruimte = beter."""
    return max(0.0, 100 - num_comments * 4)


def upvotes_score(upvotes: int) -> float:
    """Hoger = beter, met plafond op 50 upvotes."""
    return min(max(upvotes, 0), 50) / 50 * 100


def score_relevance_batch(instruction: str, posts: list[dict]) -> dict[str, dict]:
    """Vraag Haiku om relevantiescores voor een lijst posts. Keyed op reddit_id."""
    client = anthropic.Anthropic()
    out: dict[str, dict] = {}
    for i in range(0, len(posts), BATCH_SIZE):
        batch = posts[i : i + BATCH_SIZE]
        post_lines = [
            {
                "reddit_id": p["reddit_id"],
                "subreddit": p["subreddit"],
                "title": p["title"],
                "body": p["body"][:1500],
                "num_comments": p["num_comments"],
            }
            for p in batch
        ]
        user_msg = (
            f"Projectinstructie:\n{instruction}\n\n"
            f"Posts (JSON):\n{json.dumps(post_lines, ensure_ascii=False)}"
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            output_config={
                "format": {"type": "json_schema", "schema": RELEVANCE_SCHEMA}
            },
            messages=[{"role": "user", "content": user_msg}],
        )
        text = next(b.text for b in response.content if b.type == "text")
        for item in json.loads(text)["results"]:
            out[item["reddit_id"]] = item
    return out


def compute_scores(instruction: str, posts: list[dict]) -> list[dict]:
    """Combineer Haiku-relevantie met deterministische factoren tot een totaalscore."""
    relevance_map = score_relevance_batch(instruction, posts)
    scored = []
    for p in posts:
        rel = relevance_map.get(p["reddit_id"], {"relevance": 0, "is_pain_point": False, "rationale": "Geen score ontvangen"})
        factors = {
            "relevance": float(rel["relevance"]),
            "age": age_score(p["created_utc"]),
            "comments": comments_score(p["num_comments"]),
            "upvotes": upvotes_score(p["upvotes"]),
        }
        total = sum(WEIGHTS[k] * v for k, v in factors.items())
        scored.append(
            {
                **p,
                "factors": factors,
                "total": round(total, 1),
                "is_pain_point": bool(rel["is_pain_point"]),
                "rationale": rel["rationale"],
            }
        )
    return scored
