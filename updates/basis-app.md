# basis-app

Eerste werkende versie van de Reddit Opportunity Scanner: projectbeheer, Reddit-scan
met Haiku-scoring, karma/marketing/research-labels en concept-reacties met menselijke review.

## Details

**Backend (FastAPI + SQLite)**
- `backend/db.py` — schema: `projects`, `posts`, `scores`, `draft_replies`.
  Geschiedenis blijft staan na sluiten en projectwissel (alles in `data.db`).
- `backend/reddit_client.py` — read-only PRAW-scan: per subreddit wordt op elk
  keyword gezocht (sort=new, afgelopen maand, 10 per keyword), gededupliceerd op
  reddit-id.
- `backend/scoring.py` — relevantie via Claude Haiku (`claude-haiku-4-5-20251001`),
  gebatcht (20 posts per API-call) met structured outputs. Leeftijd, reacties en
  upvotes deterministisch berekend. Gewichten: 0.5/0.2/0.2/0.1.
- `backend/drafts.py` — concept-reacties in karma-modus (geen productvermelding)
  of marketing-modus (project noemen mag, met disclosure). Nooit auto-posten.
- `backend/main.py` — REST-API + serveert de gebouwde frontend.

**Frontend (React + Vite)**
- Sidebar met projecten, formulier voor naam/instructie/subreddits/keywords/whitelist.
- Generate-knop per project; filtertabs Alle/Karma/Marketing/Research.
- Per post: kleurgecodeerde totaalscore, bargrafiek per factor, link naar origineel,
  Haiku-rationale, en genereer-knoppen voor concepten (marketing alleen op
  whitelist-subreddits). Concepten met kopieerknop.

**Waarom zo**
- Batching van Haiku-calls beperkt kosten en system-prompt-overhead (CLAUDE.md).
- Labels apart van de score houden karma- en marketingdoelen uit elkaar (CLAUDE.md).
- Alleen nieuwe posts scoren voorkomt dubbele kosten en bewaart geschiedenis.
