"""
menubar.py - ElonWatch macOS Menubar App
Lives in your menubar. Shows live signal count, domain breakdown,
launches TUI, triggers scrapes, sends notifications.
"""

import os
import sys
import time
import logging
import subprocess
import threading
from datetime import datetime

import rumps

# Make sure we can import sibling modules regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, get_recent, get_stats, get_total_count
from scrapers import run_all_scrapers
from brain import score_item, is_high_signal, is_elon_tweet, DOMAIN_ICONS
from notify import send_notification

logger = logging.getLogger("elonwatch.menubar")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "elonwatch.log")),
    ],
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TUI_SCRIPT = os.path.join(APP_DIR, "tui.py")
VENV_PYTHON = os.path.join(APP_DIR, "venv", "bin", "python3")

ICON_IDLE     = "◈"   # unicode menubar text (no image needed)
ICON_SYNCING  = "◉"
ICON_ALERT    = "!!"


class ElonWatchMenuBar(rumps.App):
    def __init__(self):
        super().__init__(
            name="ElonWatch",
            title=ICON_IDLE,
            quit_button=None,
        )
        init_db()

        self._scrape_thread: threading.Thread | None = None
        self._seen_ids: set[int] = set()
        self._next_scrape_ts: float = time.time() + 10   # first scrape in 10s
        self._is_syncing: bool = False
        self._pulse_idx: int = 0
        self._pulse_chars = ["◈", "◉", "◎", "●", "◉", "◎"]

        # ── Build menu ──────────────────────────────────────────────────────
        self.status_item   = rumps.MenuItem("◈ ELONWATCH // FUTURE SYNC")
        self.stats_item    = rumps.MenuItem("Loading ...")
        self.sync_item     = rumps.MenuItem("Next sync: ...")
        self.domain_item   = rumps.MenuItem("Domain breakdown:")
        self.sep1          = rumps.separator
        self.open_tui      = rumps.MenuItem("Open TUI Console", callback=self.launch_tui)
        self.scrape_now    = rumps.MenuItem("Sync Now", callback=self.manual_scrape)
        self.sep2          = rumps.separator
        self.last_tweet    = rumps.MenuItem("Last Tweet: —")
        self.last_news     = rumps.MenuItem("Last News: —")
        self.sep3          = rumps.separator
        self.quit_item     = rumps.MenuItem("Quit ElonWatch", callback=rumps.quit_application)

        self.menu = [
            self.status_item,
            self.stats_item,
            self.sync_item,
            rumps.separator,
            self.domain_item,
            rumps.separator,
            self.open_tui,
            self.scrape_now,
            rumps.separator,
            self.last_tweet,
            self.last_news,
            rumps.separator,
            self.quit_item,
        ]

        # ── Timers ──────────────────────────────────────────────────────────
        self._stats_timer = rumps.Timer(self._update_stats, 10)
        self._stats_timer.start()

        self._countdown_timer = rumps.Timer(self._tick, 1)
        self._countdown_timer.start()

        # Seed seen IDs from DB so we don't spam notifications on first run
        for row in get_recent(limit=500):
            self._seen_ids.add(row["id"])

        self._update_stats(None)

    # ── Tick (every second) ────────────────────────────────────────────────
    def _tick(self, _sender) -> None:
        # Pulse icon while syncing
        if self._is_syncing:
            self._pulse_idx = (self._pulse_idx + 1) % len(self._pulse_chars)
            self.title = self._pulse_chars[self._pulse_idx]
        else:
            self.title = ICON_IDLE

        # Countdown
        remaining = max(0, int(self._next_scrape_ts - time.time()))
        m, s = divmod(remaining, 60)
        self.sync_item.title = f"Next sync: {m:02d}:{s:02d}"

        # Trigger scheduled scrape
        if time.time() >= self._next_scrape_ts:
            if self._scrape_thread is None or not self._scrape_thread.is_alive():
                self._next_scrape_ts = time.time() + 3600
                self._run_scrape()

    # ── Stats update ────────────────────────────────────────────────────────
    def _update_stats(self, _sender) -> None:
        total = get_total_count()
        stats = get_stats()
        src_parts = []
        for row in stats:
            src_parts.append(f"{row['source']}: {row['cnt']}")
        self.stats_item.title = f"Total signals: {total}  ({', '.join(src_parts)})"

        # Update last tweet / last news
        for row in get_recent(limit=50, source="twitter"):
            self.last_tweet.title = f"Tweet: {row['title'][:60]}"
            break
        for row in get_recent(limit=50, source="google-news"):
            self.last_news.title = f"News: {row['title'][:60]}"
            break

        # Domain breakdown (top 4)
        rows = get_recent(limit=300)
        domain_cnt: dict[str, int] = {}
        for row in rows:
            s = score_item(row)
            domain_cnt[s.domain] = domain_cnt.get(s.domain, 0) + 1
        top = sorted(domain_cnt, key=lambda d: -domain_cnt[d])[:4]
        parts = [f"{DOMAIN_ICONS.get(d, '·')} {d}: {domain_cnt[d]}" for d in top]
        self.domain_item.title = "  ".join(parts)

    # ── Scrape ────────────────────────────────────────────────────────────
    def _run_scrape(self) -> None:
        def worker():
            self._is_syncing = True
            self.scrape_now.title = "Syncing ..."
            try:
                results = run_all_scrapers()
                total = sum(results.values())
                logger.info(f"Scrape done: {results}")
                self._check_new_items()
                self._update_stats(None)
            except Exception as e:
                logger.error(f"Scrape error: {e}")
            finally:
                self._is_syncing = False
                self.scrape_now.title = "Sync Now"
                self.title = ICON_IDLE

        self._scrape_thread = threading.Thread(target=worker, daemon=True)
        self._scrape_thread.start()

    def manual_scrape(self, _sender) -> None:
        self._next_scrape_ts = time.time()

    # ── Notification check ────────────────────────────────────────────────
    def _check_new_items(self) -> None:
        rows = get_recent(limit=100)
        for row in rows:
            if row["id"] in self._seen_ids:
                continue
            self._seen_ids.add(row["id"])
            s = score_item(row)

            if is_elon_tweet(s):
                send_notification(
                    title="ELONWATCH  //  Elon Tweeted",
                    subtitle=f"{s.domain}  ·  {s.signal_type}  ·  urgency {s.urgency}/10",
                    message=s.title[:200],
                    urgency=s.urgency,
                )
            elif is_high_signal(s):
                send_notification(
                    title=f"ELONWATCH  //  High Signal  [{s.domain}]",
                    subtitle=f"{s.signal_type}  ·  urgency {s.urgency}/10  ·  {s.source}",
                    message=s.title[:200],
                    urgency=s.urgency,
                )

    # ── Launch TUI ────────────────────────────────────────────────────────
    def launch_tui(self, _sender) -> None:
        """Open a new Terminal window: plays intro video then launches TUI."""
        launcher = os.path.join(APP_DIR, "elonwatch.sh")
        # Use the shell launcher so the video intro fires before the TUI
        script = f'''
        tell application "Terminal"
            activate
            do script "bash \\"{launcher}\\""
        end tell
        '''
        try:
            subprocess.Popen(["osascript", "-e", script])
        except Exception as e:
            logger.error(f"Failed to launch TUI: {e}")
            rumps.alert(
                title="ElonWatch",
                message=f"Could not open Terminal.\n\nRun manually:\nbash {launcher}",
            )


def main():
    send_notification(
        title="ELONWATCH  //  FUTURE SYNC",
        subtitle="Consciousness feed active",
        message="Monitoring Elon Musk signals. Click the ◈ in your menubar.",
        urgency=4,
        sound=True,
    )
    ElonWatchMenuBar().run()


if __name__ == "__main__":
    main()
