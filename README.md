# Reddit Opportunity Scanner

Persoonlijke webapp die per project relevante Reddit-posts vindt om op te reageren
(karma/marketing) en concurrent-pijnpunten bewaart als research. Zie `CLAUDE.md`
voor de volledige scope en `DECISIONS.md` voor vastgelegde keuzes.

## Eenmalige setup

1. Kopieer `.env.example` naar `.env` en vul in:
   - Reddit: maak een **script**-app aan op https://www.reddit.com/prefs/apps
     → `REDDIT_CLIENT_ID` (onder de appnaam) en `REDDIT_CLIENT_SECRET`.
   - Anthropic: `ANTHROPIC_API_KEY` van https://platform.claude.com/
2. Dependencies (al gedaan bij eerste build):
   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   cd frontend; npm install; npm run build
   ```

## Starten

```powershell
.venv\Scripts\python -m uvicorn backend.main:app --port 8000
```

Open http://localhost:8000 — de gebouwde frontend wordt door FastAPI geserveerd.

## Frontend ontwikkelen

```powershell
cd frontend
npm run dev   # dev-server op :5173, proxyt /api naar :8000
```

Na wijzigingen: `npm run build` zodat FastAPI de nieuwe versie serveert.
