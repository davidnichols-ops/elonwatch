"""
scrape_worker.py - Standalone scraper for launchd invocation.
Called by the LaunchAgent every hour. Writes a log.
"""
import logging
import os
import sys

LOG_PATH = os.path.join(os.path.dirname(__file__), "elonwatch.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)

from db import init_db
from scrapers import run_all_scrapers

if __name__ == "__main__":
    init_db()
    results = run_all_scrapers()
    total = sum(results.values())
    print(f"Done. New items: {total} | {results}")
