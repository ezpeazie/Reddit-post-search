# Reddit Opportunity Scanner

## Doel
Persoonlijke webapp die per "project" (= app, bijv. Codex) relevante Reddit-posts
vindt om op te reageren (karma/marketing) en bijhoudt waar nieuwe content geplaatst
kan worden. Geen automatisch posten. Geen auto-gegenereerde content die zonder
menselijke review de deur uitgaat.

## Scope — WEL bouwen
- Meerdere projecten (apps), elk met eigen instructie/beschrijving, subreddit- en
  keywordlijst, en self-promo-toggle per subreddit.
- **Subreddit/keyword-suggestie flow** (bij aanmaken of bewerken van een project):
  1. Gebruiker typt project-instructie (bijv. "focus timer voor developers, studenten, ADHD").
  2. Claude (Haiku of Sonnet, geen los "agent"-proces) genereert een voorstel: lijst
     kandidaat-subreddits + keywords passend bij de instructie.
  3. **Elke voorgestelde subreddit wordt automatisch geverifieerd via de Reddit API**
     (bestaat de subreddit, is hij niet gequarantained/gebanned) — dit is een losse,
     goedkope PRAW-call, geen Claude-call. Subreddits die niet bestaan worden NIET
     getoond als optie.
  4. Geverifieerde voorstellen verschijnen als aanvinkbare lijst (voor-aangevinkt),
     gebruiker schrapt/voegt toe en bevestigt.
  5. Self-promo-toggle staat voor elke NIEUWE subreddit standaard op **uit**
     (karma-only). Nooit door Claude automatisch op "aan" laten zetten — dit vereist
     altijd een expliciete, handmatige bevestiging door de gebruiker, eventueel
     nadat de subreddit-rules (op te halen via Reddit API) zijn nagekeken.
  6. Definitieve subreddit/keyword-lijst + toggle-status wordt pas opgeslagen na
     bevestiging door de gebruiker — nooit direct na Claude's voorstel.
- Eén "Generate" knop per project → scant Reddit (read-only, via PRAW) en scoort
  gevonden posts met Claude Haiku.
- Score = weging van meerdere factoren (zie hieronder), getoond als kleurcode +
  bargrafiek per post (per-factor breakdown, niet alleen totaalscore).
- Filter met 3 opties per post:
  1. **Karma** — subreddit staat geen zelfpromotie toe, reactie mag geen productvermelding bevatten
  2. **Marketing** — subreddit staat zelfpromotie toe, reactie mag project noemen (met disclosure)
  3. **Research** — post signaleert een pijnpunt/klacht over concurrenten, geen actie, puur bewaren als inspiratie
- Per post: link naar origineel, "genereer reactie"-knop → concept, mens reviewt en
  post zelf handmatig. Nooit automatisch posten.
- Alle scans, scores en concept-reacties blijven opgeslagen per project (geschiedenis
  blijft staan na sluiten, ook na projectwissel).
- Aparte `updates/` map: bij elke feature-update een bestand met als naam een korte
  1-2-woorden beschrijving (bijv. `scoring-weging.md`), inhoud: bovenaan 1-2 zinnen
  samenvatting, daaronder de detail-uitleg van wat er is veranderd en waarom.
- Apart `DECISIONS.md` bestand: vastgelegde keuzes en de reden erachter (bijv.
  "Haiku i.p.v. Sonnet voor scoring — kostenreden", "geen auto-posten — ToS-risico").
  Nieuwe sessies checken dit bestand voor ze eerdere besluiten terugdraaien.

## Scope — NIET bouwen (tenzij expliciet gevraagd)
- Geen auto-posten naar Reddit of enig ander platform.
- Geen browser-extensie/sidebar.
- Geen SEO-artikel-generatie, geen backlink-outreach-agent, geen concurrent-tracking-agent.
- Geen realtime scanning — periodieke batch-scan (op knop-klik) volstaat.
- Geen scope-uitbreiding naar andere platforms (Quora, Stack Overflow, Twitter) zonder
  dat dit expliciet gevraagd wordt.

## Scoringsfactoren (aanpasbaar, huidige startversie)
| Factor | Richting | Gewicht |
|---|---|---|
| Subreddit-relevantie t.o.v. project-instructie | hoger = beter | zwaarst |
| Postleeftijd | recenter = beter | middel |
| Aantal bestaande reacties | minder = meer ruimte = beter | middel |
| Upvotes op de post | hoger = beter, met plafond | licht |

Self-promo-toestemming is GEEN scorefactor maar een apart label/filter (karma vs.
marketing), zodat de twee doelen niet in één getal vermengd worden.

## Tech
- Backend: Python — PRAW (Reddit, read-only) + Anthropic SDK (Claude Haiku 4.5,
  model-ID: `claude-haiku-4-5-20251001`) voor scoring en reactie-concepten.
- Opslag: SQLite. Tabellen minimaal: `projects`, `posts`, `scores`, `draft_replies`.
- Frontend: lichte webapp (Flask/FastAPI + simpele HTML of React), lokaal draaiend,
  geen aparte hosting-infra nodig voor persoonlijk gebruik.
- Batch de Haiku-calls (meerdere posts per API-call) i.p.v. 1 call per post, om
  kosten en herhaalde system-prompt-overhead te beperken.

## Werkregels voor Claude Code
- Check dit bestand en `DECISIONS.md` bij de start van elke sessie.
- Bij twijfel over een externe API (Reddit API, Anthropic SDK) — verifiëren, niet
  raden. Geen aannames over parameternamen of endpoints die niet expliciet in dit
  bestand of de officiële docs staan.
- Eén feature per keer bouwen, diff tonen voor verder te gaan.
- Na elke afgeronde feature: schrijf een bestand in `updates/` (zie naamgeving
  hierboven) én update `DECISIONS.md` als er een keuze is gemaakt.
- Voeg nooit ongevraagd features toe uit de "NIET bouwen"-lijst, ook niet als het
  "logisch aanvoelt" als aanvulling.