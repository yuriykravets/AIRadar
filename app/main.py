import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import FEEDS, INGEST_INTERVAL_HOURS, INGEST_ON_STARTUP
from .database import get_db, init_db
from .ingestion import ingest_all, scheduled_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if INGEST_ON_STARTUP:
        await ingest_all()
    task = asyncio.create_task(scheduled_ingestion(INGEST_INTERVAL_HOURS))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="AI Radar", description="AI updates for developers", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/api/articles")
def articles(provider: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=200)):
    query = "SELECT canonical_url, title, provider, source_name, published_at, description FROM articles"
    params = []
    if provider and provider != "All":
        query += " WHERE provider = ?"
        params.append(provider)
    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)
    with get_db() as db:
        return {"articles": [dict(row) for row in db.execute(query, params)]}


@app.get("/api/health")
def health():
    with get_db() as db:
        states = [dict(row) for row in db.execute("SELECT source_url, last_successful_fetch FROM feed_state")]
    return {"status": "ok", "feeds": states}


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")
