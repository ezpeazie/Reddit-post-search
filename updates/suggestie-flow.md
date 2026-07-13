# suggestie-flow

Subreddit/keyword-suggestie bij het aanmaken of bewerken van een project, en de
self-promo-whitelist vervangen door een toggle per subreddit (standaard uit).

## Details

**Nieuwe flow in het projectformulier**
1. Gebruiker typt de projectinstructie.
2. Knop "Stel subreddits & keywords voor" → Claude Haiku genereert kandidaten
   (`backend/suggest.py`, structured outputs).
3. Elke kandidaat-subreddit wordt automatisch geverifieerd via de Reddit API
   (`verify_subreddits` in `backend/reddit_client.py`): bestaat hij, is hij
   publiek/restricted (niet gequarantained/gebanned). Eén goedkope PRAW-call per
   subreddit, geen Claude-call. Afgevallen namen worden getoond maar zijn geen optie.
4. Geverifieerde voorstellen verschijnen aanvinkbaar (voor-aangevinkt); handmatig
   toevoegen/schrappen kan ook.
5. Self-promo-toggle staat voor elke nieuwe subreddit standaard **uit**; Claude
   zet hem nooit aan. Per subreddit is er een "bekijk regels"-knop
   (`GET /api/subreddits/{name}/rules` via PRAW `subreddit.rules`) om de regels na
   te kijken vóór het handmatig aanzetten.
6. Er wordt pas opgeslagen bij "Bevestigen & opslaan" — nooit direct na het voorstel.

**Datamodel**
- `projects.subreddits` is nu een JSON-lijst van `{name, selfpromo}` in plaats van
  een stringlijst + aparte `selfpromo_whitelist`. Bestaande rijen worden bij het
  opstarten automatisch gemigreerd (`_migrate_subreddit_format` in `backend/db.py`);
  de oude kolom blijft ongebruikt staan.
- Labeling bij een scan gebruikt de toggles: `marketing` alleen voor subreddits
  met `selfpromo: true`.

**Nieuwe endpoints**
- `POST /api/suggest` — instructie in, `{subreddits (geverifieerd), keywords, rejected}` uit.
- `GET /api/subreddits/{name}/rules` — subreddit-regels voor de handmatige check.
