"""
scrapers.py - Data scrapers for ElonWatch
Sources: Nitter (Twitter), Google News RSS, Reddit RSS
"""

import re
import time
import random
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from db import insert_item

logger = logging.getLogger("elonwatch.scrapers")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.cz",
]

REDDIT_FEEDS = [
    ("https://www.reddit.com/r/elonmusk/.rss?limit=50", "reddit", "r/elonmusk"),
    ("https://www.reddit.com/r/spacex/.rss?limit=50", "reddit", "r/spacex"),
    ("https://www.reddit.com/r/teslamotors/.rss?limit=50", "reddit", "r/teslamotors"),
    ("https://www.reddit.com/r/neuralink/.rss?limit=50", "reddit", "r/neuralink"),
    ("https://www.reddit.com/search/.rss?q=elon+musk&sort=new&limit=50", "reddit", "reddit-search"),
]

GOOGLE_NEWS_QUERIES = [
    ("Elon Musk", "news", "google-news"),
    ("@elonmusk", "tweets", "google-news"),
    ("Tesla Elon Musk", "news", "google-news"),
    ("SpaceX Elon Musk", "news", "google-news"),
    ("Elon Musk statement", "news", "google-news"),
    ("DOGE Elon Musk", "news", "google-news"),
    ("xAI Grok Elon Musk", "news", "google-news"),
]

NITTER_ACCOUNTS = [
    ("elonmusk", "tweets", "twitter"),
    ("SpaceX", "tweets", "twitter"),
    ("Tesla", "tweets", "twitter"),
    ("xai", "tweets", "twitter"),
    ("boring_company", "tweets", "twitter"),
]


def _get(url: str, timeout: int = 12) -> requests.Response | None:
    """GET with retries and random backoff."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r
            logger.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
        time.sleep(random.uniform(1.5, 3.5))
    return None


def _strip_html(html: str) -> str:
    """Strip HTML tags and clean whitespace."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


# ── Nitter (Twitter) ──────────────────────────────────────────────────────────

def scrape_nitter() -> int:
    """Scrape Elon + related accounts from Nitter RSS. Returns new item count."""
    new_count = 0
    for account, category, source in NITTER_ACCOUNTS:
        scraped = False
        for instance in NITTER_INSTANCES:
            url = f"{instance}/{account}/rss"
            r = _get(url)
            if not r:
                continue
            try:
                feed = feedparser.parse(r.text)
                for entry in feed.entries:
                    title = _strip_html(entry.get("title", ""))
                    link = entry.get("link", "").replace(instance, "https://x.com")
                    link = re.sub(r"#m$", "", link)
                    content = _strip_html(entry.get("summary", ""))
                    published = entry.get("published", "")
                    author = f"@{account}"
                    if not title:
                        continue
                    is_new = insert_item(
                        source=source,
                        category=category,
                        title=title[:500],
                        url=link,
                        content=content[:2000],
                        author=author,
                        published=published,
                    )
                    if is_new:
                        new_count += 1
                scraped = True
                logger.info(f"[nitter] @{account}: {len(feed.entries)} entries from {instance}")
                break
            except Exception as e:
                logger.error(f"[nitter] parse error for @{account} @ {instance}: {e}")
        if not scraped:
            logger.error(f"[nitter] all instances failed for @{account}")
        time.sleep(random.uniform(1, 2))
    return new_count


# ── Google News RSS ───────────────────────────────────────────────────────────

def scrape_google_news() -> int:
    """Scrape Google News RSS for Elon-related queries. Returns new item count."""
    new_count = 0
    base = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    for query, category, source in GOOGLE_NEWS_QUERIES:
        encoded = requests.utils.quote(query)
        url = base.format(query=encoded)
        r = _get(url)
        if not r:
            logger.warning(f"[google-news] failed for query: {query}")
            continue
        try:
            feed = feedparser.parse(r.text)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                published = entry.get("published", "")
                content = _strip_html(entry.get("summary", ""))
                # publisher often in title as "Title - Publisher"
                parts = title.rsplit(" - ", 1)
                author = parts[1] if len(parts) == 2 else "Google News"
                if not title:
                    continue
                is_new = insert_item(
                    source=source,
                    category=category,
                    title=title[:500],
                    url=link,
                    content=content[:2000],
                    author=author,
                    published=published,
                )
                if is_new:
                    new_count += 1
            logger.info(f"[google-news] '{query}': {len(feed.entries)} entries")
        except Exception as e:
            logger.error(f"[google-news] parse error for '{query}': {e}")
        time.sleep(random.uniform(0.8, 1.8))
    return new_count


# ── Reddit RSS ────────────────────────────────────────────────────────────────

def scrape_reddit() -> int:
    """Scrape Reddit RSS feeds. Returns new item count."""
    new_count = 0
    # Reddit needs a descriptive User-Agent and longer gaps to avoid 429
    reddit_headers = {
        "User-Agent": "ElonWatch/2.0 (macOS; personal research aggregator; contact@localhost)"
    }
    for url, source, subreddit in REDDIT_FEEDS:
        # Longer cooldown between Reddit requests to avoid rate-limits
        time.sleep(random.uniform(3.0, 6.0))
        try:
            r = requests.get(url, headers=reddit_headers, timeout=12)
            if r.status_code == 429:
                logger.warning(f"[reddit] rate limited on {subreddit}, skipping")
                time.sleep(10)
                continue
            if r.status_code != 200:
                logger.warning(f"[reddit] HTTP {r.status_code} for {subreddit}")
                continue
        except Exception as e:
            logger.warning(f"[reddit] request error for {subreddit}: {e}")
            continue
        try:
            feed = feedparser.parse(r.text)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                published = entry.get("published", "")
                content = _strip_html(entry.get("summary", ""))
                author = entry.get("author", subreddit)
                if not title:
                    continue
                is_new = insert_item(
                    source=source,
                    category="community",
                    title=title[:500],
                    url=link,
                    content=content[:2000],
                    author=author,
                    published=published,
                )
                if is_new:
                    new_count += 1
            logger.info(f"[reddit] {subreddit}: {len(feed.entries)} entries")
        except Exception as e:
            logger.error(f"[reddit] parse error for {subreddit}: {e}")
    return new_count


# ── Master scrape ─────────────────────────────────────────────────────────────

def run_all_scrapers() -> dict:
    """Run all scrapers and return counts."""
    results = {}
    logger.info("=== Starting scrape cycle ===")

    try:
        results["twitter"] = scrape_nitter()
    except Exception as e:
        logger.error(f"Nitter scraper crashed: {e}")
        results["twitter"] = 0

    try:
        results["google_news"] = scrape_google_news()
    except Exception as e:
        logger.error(f"Google News scraper crashed: {e}")
        results["google_news"] = 0

    try:
        results["reddit"] = scrape_reddit()
    except Exception as e:
        logger.error(f"Reddit scraper crashed: {e}")
        results["reddit"] = 0

    total = sum(results.values())
    logger.info(f"=== Scrape complete. {total} new items: {results} ===")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from db import init_db
    init_db()
    print(run_all_scrapers())
