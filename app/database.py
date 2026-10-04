import os
import sqlite3
from contextlib import contextmanager

from .config import DATABASE_PATH


def init_db() -> None:
    directory = os.path.dirname(DATABASE_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                provider TEXT NOT NULL,
                source_name TEXT NOT NULL,
                published_at TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
            CREATE TABLE IF NOT EXISTS feed_state (
                source_url TEXT PRIMARY KEY,
                last_successful_fetch TEXT
            );
            """
        )


@contextmanager
def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()

