import asyncio
import calendar
import html
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urldefrag

import feedparser
import httpx

from .config import FEEDS, FeedSource
from .database import get_db

logger = logging.getLogger(__name__)
USER_AGENT = "AI-Radar/1.0 (+https://github.com/ai-radar)"


def canonicalize(url: str) -> str:
    return urldefrag((url or "").strip())[0]


def clean_description(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def entry_date(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    for key in ("published", "updated", "created"):
        if entry.get(key):
            try:
                return parsedate_to_datetime(entry[key]).astimezone(timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass
    return datetime.now(timezone.utc)


def normalize(entry, source: FeedSource) -> dict | None:
    url = canonicalize(entry.get("link") or entry.get("id"))
    title = clean_description(entry.get("title", ""))
    if not url or not title:
        return None
    return {
        "canonical_url": url,
        "title": title,
        "provider": source.provider,
        "source_name": source.name,
        "published_at": entry_date(entry).isoformat(),
        "description": clean_description(entry.get("summary") or entry.get("description", "")),
    }


async def fetch_source(source: FeedSource) -> int:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        response = await client.get(source.url)
        response.raise_for_status()
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"invalid feed: {parsed.bozo_exception}")
    articles = [item for entry in parsed.entries if (item := normalize(entry, source))]
    fetched_at = datetime.now(timezone.utc).isoformat()
    with get_db() as db:
        for article in articles:
            db.execute(
                """INSERT INTO articles (canonical_url, title, provider, source_name, published_at, description)
                   VALUES (:canonical_url, :title, :provider, :source_name, :published_at, :description)
                   ON CONFLICT(canonical_url) DO NOTHING""",
                article,
            )
        db.execute(
            "INSERT INTO feed_state (source_url, last_successful_fetch) VALUES (?, ?) ON CONFLICT(source_url) DO UPDATE SET last_successful_fetch=excluded.last_successful_fetch",
            (source.url, fetched_at),
        )
    return len(articles)


async def ingest_all() -> dict[str, int]:
    results = {}
    for source in FEEDS:
        try:
            results[source.provider] = await fetch_source(source)
            logger.info("Fetched %s (%s entries)", source.name, results[source.provider])
        except Exception:
            logger.exception("Failed to ingest %s (%s)", source.name, source.url)
            results[source.provider] = -1
    return results


async def scheduled_ingestion(interval_hours: float):
    while True:
        await asyncio.sleep(interval_hours * 3600)
        await ingest_all()

