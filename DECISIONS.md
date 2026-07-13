# Beslissingen

Vastgelegde keuzes en de reden erachter. Nieuwe sessies: check dit bestand voordat
je eerdere besluiten terugdraait.

## 2026-07-13 — Suggestie-flow

- **Haiku (niet Sonnet) voor subreddit/keyword-voorstellen** — CLAUDE.md laat
  "Haiku of Sonnet" open; Haiku gekozen voor consistentie met de scoring en omdat
  de taak (namen opsommen) geen zwaarder model vraagt. Hallucinerende namen zijn
  geen risico: elke kandidaat wordt via de Reddit API geverifieerd voordat hij als
  optie verschijnt.
- **Subreddit-verificatie via attribuut-fetch** — PRAW is lazy; het opvragen van
  `subreddit_type` triggert de fetch. 404 (bestaat niet/gebanned), 403
  (gequarantained) en redirect (ongeldige naam) vallen af; alleen `public` en
  `restricted` worden geaccepteerd.
- **Toggle per subreddit i.p.v. aparte whitelist** — datamodel gewijzigd naar
  `{name, selfpromo}`-objecten in `projects.subreddits`, met automatische migratie
  van het oude formaat. De oude kolom `selfpromo_whitelist` blijft ongebruikt staan
  zodat oude databases blijven werken.
- **Self-promo nooit automatisch aan** — nieuwe subreddits (ook uit het voorstel)
  starten altijd met `selfpromo: false`; alleen de gebruiker zet de toggle om,
  desgewenst na het bekijken van de subreddit-regels via de regels-knop.

## 2026-07-13 — Basis-app

- **Haiku i.p.v. Sonnet/Opus voor scoring en concepten** — kostenreden; scoring is
  een hoog-volume, laag-complexiteitstaak. Model-ID vastgepind:
  `claude-haiku-4-5-20251001` (in `backend/scoring.py`).
- **Geen auto-posten** — ToS-risico bij Reddit; alle concepten worden door een mens
  gereviewd en handmatig geplaatst. De PRAW-client is read-only (geen
  username/password geconfigureerd).
- **FastAPI + React (Vite)** — gekozen door gebruiker boven Flask + HTML.
  FastAPI serveert de gebouwde frontend uit `frontend/dist`, dus in productie is
  er maar één proces nodig.
- **Structured outputs voor scoring** — Haiku 4.5 ondersteunt
  `output_config.format` met JSON-schema; dit garandeert parseerbare batchscores
  zonder retry-logica.
- **Relevantie via Haiku, overige factoren deterministisch** — leeftijd, aantal
  reacties en upvotes zijn uit Reddit-metadata te berekenen; alleen relevantie
  vereist een model. Scheelt tokens en maakt scores reproduceerbaar.
- **Gewichten**: relevantie 0.5, leeftijd 0.2, reacties 0.2, upvotes 0.1
  (plafond op 50 upvotes). Leeftijd met halfwaardetijd van 48 uur.
- **Label is geen scorefactor** — karma/marketing/research wordt apart bepaald:
  `research` als Haiku een concurrent-pijnpunt signaleert, anders `marketing` als
  de subreddit in de self-promo-whitelist staat, anders `karma`. Conform CLAUDE.md.
- **Alleen nieuwe posts worden gescoord bij een scan** — bestaande posts en scores
  blijven staan (geschiedenis), en het voorkomt dubbele Haiku-kosten.
- **Marketing-concept geblokkeerd op karma-posts** — de backend weigert een
  marketing-draft voor een subreddit buiten de whitelist (HTTP 400), zodat de
  regel niet per ongeluk in de UI omzeild kan worden.
