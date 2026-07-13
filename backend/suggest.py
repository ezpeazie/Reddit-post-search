"""Subreddit/keyword-voorstellen op basis van de projectinstructie.

Claude (Haiku) genereert alleen kandidaten. Verificatie van subreddits gebeurt
daarna via de Reddit API (reddit_client.verify_subreddits) — niet-bestaande
subreddits worden nooit als optie getoond. Claude bepaalt nooit de
self-promo-toggle; die staat voor nieuwe subreddits altijd uit.
"""
import json

import anthropic

from .scoring import MODEL

SUGGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "subreddits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Subredditnamen zonder r/-prefix, exact gespeld",
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Zoektermen waarmee relevante posts te vinden zijn",
        },
    },
    "required": ["subreddits", "keywords"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "Je krijgt een projectinstructie (een app of product plus doelgroep). "
    "Stel 8 tot 15 bestaande subreddits voor waar die doelgroep actief is, en "
    "5 tot 12 zoek-keywords waarmee relevante posts te vinden zijn. "
    "Alleen subredditnamen die echt bestaan, exact gespeld, zonder r/-prefix. "
    "Mix grote en kleinere niche-subreddits. Keywords kort en concreet, in de "
    "taal waarin de doelgroep post (meestal Engels)."
)


def suggest_subreddits_keywords(instruction: str) -> dict:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": SUGGEST_SCHEMA}},
        messages=[{"role": "user", "content": f"Projectinstructie:\n{instruction}"}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
