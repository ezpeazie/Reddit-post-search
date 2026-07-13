"""Read-only Reddit-scan via PRAW.

Zoekt per subreddit op de keywords van het project en dedupliceert op reddit_id.
Er wordt nooit iets gepost — de client is read-only (geen username/password).
"""
import os

import praw
import prawcore

SEARCH_LIMIT_PER_KEYWORD = 10
TIME_FILTER = "month"


def get_reddit() -> praw.Reddit:
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "reddit-opportunity-scanner/0.1")
    if not client_id or not client_secret:
        raise RuntimeError(
            "REDDIT_CLIENT_ID en REDDIT_CLIENT_SECRET ontbreken. "
            "Maak een app aan op https://www.reddit.com/prefs/apps en zet ze in .env"
        )
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def verify_subreddits(names: list[str]) -> tuple[list[str], list[str]]:
    """Controleer per subreddit of hij bestaat en publiek toegankelijk is.

    Retourneert (geldig, afgevallen). Quarantained (403), gebanned/onbestaand (404)
    en ongeldige namen vallen af. Eén goedkope PRAW-call per subreddit, geen Claude.
    """
    reddit = get_reddit()
    valid: list[str] = []
    rejected: list[str] = []
    for name in names:
        clean = name.strip().removeprefix("r/")
        if not clean:
            continue
        try:
            sub = reddit.subreddit(clean)
            # Attribuut-toegang triggert de fetch (PRAW is lazy).
            if sub.subreddit_type in ("public", "restricted"):
                valid.append(sub.display_name)
            else:
                rejected.append(clean)
        except (
            prawcore.exceptions.NotFound,
            prawcore.exceptions.Forbidden,
            prawcore.exceptions.Redirect,
            prawcore.exceptions.BadRequest,
        ):
            rejected.append(clean)
    return valid, rejected


def get_subreddit_rules(name: str) -> list[dict]:
    """Haal de regels van een subreddit op, zodat de gebruiker ze kan nakijken
    voordat hij de self-promo-toggle handmatig aanzet."""
    reddit = get_reddit()
    sub = reddit.subreddit(name.strip().removeprefix("r/"))
    return [
        {"short_name": rule.short_name, "description": rule.description or ""}
        for rule in sub.rules
    ]


def scan_subreddits(subreddits: list[str], keywords: list[str]) -> list[dict]:
    """Zoek posts die bij de keywords passen. Retourneert platte dicts."""
    reddit = get_reddit()
    found: dict[str, dict] = {}
    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name.strip().removeprefix("r/"))
        for keyword in keywords:
            try:
                results = subreddit.search(
                    keyword,
                    sort="new",
                    time_filter=TIME_FILTER,
                    limit=SEARCH_LIMIT_PER_KEYWORD,
                )
                for submission in results:
                    if submission.id in found:
                        continue
                    found[submission.id] = {
                        "reddit_id": submission.id,
                        "subreddit": submission.subreddit.display_name,
                        "title": submission.title,
                        "body": submission.selftext or "",
                        "url": f"https://www.reddit.com{submission.permalink}",
                        "author": str(submission.author) if submission.author else "[deleted]",
                        "num_comments": submission.num_comments,
                        "upvotes": submission.score,
                        "created_utc": submission.created_utc,
                    }
            except Exception as exc:  # subreddit kan privé/verwijderd zijn
                print(f"Waarschuwing: zoeken in r/{sub_name} op '{keyword}' mislukt: {exc}")
    return list(found.values())
