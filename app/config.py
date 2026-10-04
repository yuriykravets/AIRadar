import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSource:
    provider: str
    name: str
    url: str


# Add or remove sources here. The provider value is used by the UI filter.
FEEDS = [
    FeedSource("OpenAI", "OpenAI News", "https://openai.com/news/rss.xml"),
    FeedSource("Gemini", "Google AI Blog", "https://blog.google/technology/ai/rss/"),
    # Anthropic does not currently publish an official RSS endpoint; this maintained
    # feed mirrors the public Anthropic newsroom and keeps the source configurable.
    FeedSource("Anthropic", "Anthropic News", "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"),
]

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/ai_radar.db")
INGEST_INTERVAL_HOURS = float(os.getenv("INGEST_INTERVAL_HOURS", "6"))
INGEST_ON_STARTUP = os.getenv("INGEST_ON_STARTUP", "true").lower() not in {"0", "false", "no"}
