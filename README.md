# AI Radar

AI Radar is a small, free-to-host news aggregator for developers. It collects recent RSS/Atom updates from OpenAI, Google/Gemini, and Anthropic, stores them in SQLite, and presents a responsive provider-filtered feed. It does not need an LLM API, authentication, or user accounts.

## Local setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## Environment variables

Copy `.env.example` or export values in your hosting platform:

- `DATABASE_PATH` — SQLite file location; defaults to `./data/ai_radar.db`.
- `INGEST_INTERVAL_HOURS` — scheduled fetch interval; defaults to `6`.
- `INGEST_ON_STARTUP` — fetch feeds when the server starts; defaults to `true`.

No API keys are required or read by the application.

## How ingestion works

On startup (configurable), and then every six hours, the app fetches each configured RSS/Atom feed. Entries are normalized into a shared article model, canonicalized by URL, and inserted with a unique constraint so the same article is never stored twice. Articles are sorted newest first. A failed feed is logged and does not affect other feeds or remove existing articles. The last successful fetch time for each feed is exposed at `/api/health`.

Anthropic does not currently expose an official RSS endpoint, so the default Anthropic source uses a maintained public mirror of its newsroom feed. Replace that URL in `app/config.py` if you prefer another feed or a future official endpoint.

The ingestion boundary is `app/ingestion.py`; a future summarizer can be inserted after `normalize()` and before the database insert without changing the UI or storage model. The MVP currently uses the feed title and description directly.

## Add another source

Edit `FEEDS` in `app/config.py`:

```python
FeedSource("Provider label", "Source name", "https://example.com/feed.xml"),
```

The provider label becomes the article filter value. Restart the app after changing it.

## Deployment

This is a single FastAPI service, so it can run on free Python web hosting such as Render, Railway, or Fly.io (subject to their current free-tier terms). Use the start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For a persistent SQLite database, attach a persistent disk/volume and set `DATABASE_PATH` to a path on it. Ephemeral free instances may lose SQLite data on redeploy; the app will safely rebuild its database and re-ingest feeds. For multi-instance production hosting, use a shared database and a single scheduled worker to avoid duplicate scheduled fetches.
