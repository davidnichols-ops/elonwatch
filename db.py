"""
db.py - SQLite storage layer for ElonWatch
"""

import sqlite3
import os
from datetime import datetime

def _resolve_db_path() -> str:
    """
    Use ~/Library/Application Support/ElonWatch/ when running as a .app bundle,
    otherwise use the script directory (development mode).
    """
    # Detect PyInstaller bundle
    if getattr(__import__("sys"), "frozen", False):
        support = os.path.expanduser("~/Library/Application Support/ElonWatch")
        os.makedirs(support, exist_ok=True)
        return os.path.join(support, "elonwatch.db")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "elonwatch.db")


DB_PATH = _resolve_db_path()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL,
            category    TEXT NOT NULL,
            title       TEXT NOT NULL,
            url         TEXT,
            content     TEXT,
            author      TEXT,
            published   TEXT,
            scraped_at  TEXT NOT NULL,
            UNIQUE(url, title)
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_scraped_at ON items(scraped_at DESC)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_source ON items(source)
    """)
    conn.commit()
    conn.close()


def insert_item(source: str, category: str, title: str, url: str = None,
                content: str = None, author: str = None, published: str = None) -> bool:
    """Insert item, returns True if new, False if duplicate."""
    conn = get_conn()
    c = conn.cursor()
    scraped_at = datetime.utcnow().isoformat()
    try:
        c.execute("""
            INSERT INTO items (source, category, title, url, content, author, published, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source, category, title, url, content, author, published, scraped_at))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_recent(limit: int = 100, source: str = None):
    """Fetch most recent items."""
    conn = get_conn()
    c = conn.cursor()
    if source:
        c.execute("""
            SELECT * FROM items WHERE source = ?
            ORDER BY scraped_at DESC LIMIT ?
        """, (source, limit))
    else:
        c.execute("""
            SELECT * FROM items ORDER BY scraped_at DESC LIMIT ?
        """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_stats():
    """Get counts per source."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT source, COUNT(*) as cnt,
               MAX(scraped_at) as last_seen
        FROM items GROUP BY source
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_total_count():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM items")
    count = c.fetchone()[0]
    conn.close()
    return count
