"""
tui.py  —  ElonWatch // FUTURE SYNC
           Real-time consciousness feed for Elon Musk signal intelligence.
           Visualizes the live thought-stream: domain, urgency, sentiment, signal type.
"""

import random
import threading
import time
import logging
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, RichLog
from textual.reactive import reactive
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from db import init_db, get_recent, get_stats, get_total_count
from scrapers import run_all_scrapers
from brain import (
    score_item, is_high_signal, is_elon_tweet,
    DOMAIN_ICONS, DOMAIN_COLORS, SIGNAL_COLORS, SENTIMENT_COLORS,
)
from notify import send_notification

logger = logging.getLogger("elonwatch.tui")

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE & CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

GLITCH_CHARS = "▓▒░█▄▀■□▪▫◈◉◎●○◆◇★☆⬡⬢⬣"
SCAN_CHARS   = "─━┄┈╌╍═╼╾"
PULSE_FRAMES = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"]

DOMAIN_ORDER = ["SPACE", "AI", "POLITICS", "MONEY", "TECH", "CHAOS", "EGO", "CULTURE"]

BOOT_LINES = [
    ("", 0.05),
    (" ┌─────────────────────────────────────────────────────────────┐", 0.03),
    (" │  ███████╗██╗   ██╗████████╗██╗   ██╗██████╗ ███████╗       │", 0.01),
    (" │  ██╔════╝██║   ██║╚══██╔══╝██║   ██║██╔══██╗██╔════╝       │", 0.01),
    (" │  █████╗  ██║   ██║   ██║   ██║   ██║██████╔╝█████╗         │", 0.01),
    (" │  ██╔══╝  ██║   ██║   ██║   ██║   ██║██╔══██╗██╔══╝         │", 0.01),
    (" │  ██║     ╚██████╔╝   ██║   ╚██████╔╝██║  ██║███████╗       │", 0.01),
    (" │  ╚═╝      ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝       │", 0.01),
    (" │                                                             │", 0.02),
    (" │           S Y N C  //  F U T U R E                         │", 0.03),
    (" │     real-time consciousness mapping  //  v2.0              │", 0.03),
    (" └─────────────────────────────────────────────────────────────┘", 0.03),
    ("", 0.05),
    (" > Initializing domain classifiers ...", 0.04),
    (" > Calibrating signal/noise threshold ...", 0.04),
    (" > Syncing temporal reference frame ...", 0.04),
    (" > Loading consciousness matrix ...", 0.04),
    (" > Connecting neural relay to Nitter ...", 0.04),
    (" > Establishing Google News uplink ...", 0.04),
    (" > Tapping Reddit hive-signal ...", 0.04),
    ("", 0.03),
    (" > SYNC ESTABLISHED. THOUGHT STREAM ACTIVE.", 0.07),
    ("", 0.15),
]

DOMAIN_PULSE_COLOR = {
    "SPACE":    "bright_cyan",
    "AI":       "bright_magenta",
    "POLITICS": "bright_yellow",
    "MONEY":    "bright_green",
    "TECH":     "cyan",
    "CULTURE":  "white",
    "EGO":      "yellow",
    "CHAOS":    "bright_red",
}

URGENCY_BAR_COLOR = {
    range(0, 4):  "green",
    range(4, 7):  "yellow",
    range(7, 9):  "dark_orange",
    range(9, 11): "bright_red",
}


def urgency_bar(score: int) -> str:
    """Render an 10-cell urgency bar."""
    filled = min(10, score)
    color = "green"
    if score >= 9:
        color = "bright_red"
    elif score >= 7:
        color = "dark_orange"
    elif score >= 4:
        color = "yellow"
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{color}]{bar}[/]"


def urgency_label(score: int) -> str:
    if score >= 9:  return "[bold bright_red blink] !! CRITICAL [/]"
    if score >= 7:  return "[bold dark_orange] ▲ HIGH     [/]"
    if score >= 4:  return "[bold yellow] ◈ MED      [/]"
    return "[dim green] ▿ LOW      [/]"


def _ts(scraped_at: str) -> str:
    try:
        dt = datetime.fromisoformat(scraped_at)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return scraped_at[:8]


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

TCSS = """
Screen {
    background: #000005;
    color: #00e5ff;
    layers: base overlay;
}

Header {
    display: none;
}

Footer {
    background: #000005;
    color: #004455;
    border-top: solid #001122;
}

/* ── Logo banner ── */
#logo-banner {
    height: 4;
    background: #000005;
    border-bottom: solid #003344;
    padding: 0 2;
}

/* ── Top scan line ── */
#scan-line {
    height: 1;
    background: #000005;
    color: #003344;
    width: 100%;
}

/* ── Domain pulse bar ── */
#domain-pulse {
    height: 3;
    background: #000008;
    border-bottom: solid #001122;
    padding: 0 1;
}

/* ── Main layout ── */
#main-row {
    height: 1fr;
}

/* ── Feed panel (left, 65%) ── */
#feed-panel {
    width: 65%;
    border: solid #002233;
    background: #000005;
}

/* ── Right column ── */
#right-col {
    width: 35%;
}

#brain-panel {
    height: 40%;
    border: solid #001133;
    background: #000008;
}

#stats-panel {
    height: 30%;
    border: solid #001122;
    background: #000008;
}

#sync-panel {
    height: 30%;
    border: solid #002211;
    background: #000008;
}

/* ── Feed log ── */
#feed-log {
    height: 1fr;
    scrollbar-color: #00e5ff #001122;
    background: #000005;
}

/* ── Filter bar ── */
#filter-bar {
    height: 1;
    background: #000010;
    color: #004466;
    padding: 0 1;
}

/* ── Ticker ── */
#ticker {
    height: 1;
    background: #000010;
    color: #ff6600;
}

/* ── Panel titles ── */
.ptitle {
    height: 1;
    background: #000010;
    color: #00e5ff;
    text-style: bold;
    padding: 0 1;
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# WIDGETS
# ─────────────────────────────────────────────────────────────────────────────

class LogoBanner(Static):
    """Full-width logo banner — replaces the stock Header so nothing is clipped."""

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)
        self._render()

    def _tick(self) -> None:
        self._render()

    def _render(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        # Compact single-line wordmark + subtitle + clock, all on 3 rows
        row1 = (
            "[bold bright_cyan]▌[/][bold cyan]FUTURE[/][bold bright_cyan]▐[/]"
            "  "
            "[bold bright_white]E L O N W A T C H[/]"
            "  "
            "[bold bright_cyan]▌[/][bold cyan]SYNC[/][bold bright_cyan]▐[/]"
        )
        row2 = (
            "[dim cyan]◈◈◈  consciousness mapping  //  signal intelligence  //  "
            "real-time thought-stream decoder  ◈◈◈[/]"
        )
        row3 = (
            "[dim]──────────────────────────────────────────────────────────"
            "──────────────────────────────────────────────[/]"
            f"  [bold cyan]{now}[/]"
        )
        self.update(f"{row1}\n{row2}\n{row3}")


class ScanLine(Static):
    """Animated horizontal scan line."""
    _pos: int = 0

    def on_mount(self) -> None:
        self.set_interval(0.07, self._tick)

    def _tick(self) -> None:
        w = 120
        self._pos = (self._pos + 3) % w
        chars = [" "] * w
        for i in range(5):
            p = (self._pos + i) % w
            chars[p] = random.choice(SCAN_CHARS)
        line = "".join(chars)
        self.update(f"[dim cyan]{line}[/]")


class DomainPulseBar(Static):
    """Shows live domain activity as pulsing bars."""
    _counts: dict[str, int] = {}
    _pulse_idx: int = 0

    def on_mount(self) -> None:
        self._refresh_counts()
        self.set_interval(0.8, self._tick)

    def _refresh_counts(self) -> None:
        rows = get_recent(limit=500)
        counts = {d: 0 for d in DOMAIN_ORDER}
        for row in rows:
            s = score_item(row)
            counts[s.domain] = counts.get(s.domain, 0) + 1
        self._counts = counts

    def _tick(self) -> None:
        self._pulse_idx = (self._pulse_idx + 1) % len(PULSE_FRAMES)
        self._refresh_counts()
        self._render()

    def _render(self) -> None:
        total = sum(self._counts.values()) or 1
        parts = []
        pulse = PULSE_FRAMES[self._pulse_idx]
        for domain in DOMAIN_ORDER:
            cnt = self._counts.get(domain, 0)
            pct = cnt / total
            bar_len = max(1, int(pct * 14))
            color = DOMAIN_PULSE_COLOR[domain]
            icon = DOMAIN_ICONS[domain]
            bar = pulse * bar_len + "░" * (14 - bar_len)
            parts.append(f"[{color}]{icon} {domain[:5]:<5} [{bar}] {cnt:>3}[/]")
        # two rows of 4
        row1 = "  ".join(parts[:4])
        row2 = "  ".join(parts[4:])
        self.update(f"{row1}\n{row2}")


class FilterBar(Static):
    _active: str = "ALL"

    def on_mount(self) -> None:
        self._render()

    def set_filter(self, f: str) -> None:
        self._active = f
        self._render()

    def _render(self) -> None:
        opts = {
            "ALL":      ("[bold bright_white]ALL[/]",     "[a]"),
            "twitter":  ("[bold cyan]TWITTER[/]",          "[t]"),
            "google-news": ("[bold yellow]NEWS[/]",        "[n]"),
            "reddit":   ("[bold magenta]REDDIT[/]",        "[r]"),
            "CHAOS":    ("[bold bright_red]CHAOS[/]",      "[c]"),
            "SPACE":    ("[bold bright_cyan]SPACE[/]",     "[p]"),
            "AI":       ("[bold bright_magenta]AI[/]",     "[i]"),
        }
        parts = []
        for key, (label, hotkey) in opts.items():
            if key == self._active:
                parts.append(f"[reverse]{hotkey}{label}[/]")
            else:
                parts.append(f"[dim]{hotkey}[/]{label}")
        self.update("  ".join(parts) + "   [dim][s]SCRAPE NOW  [?]EGG  [q]QUIT[/]")


class FeedLog(RichLog):
    """The main consciousness stream."""
    pass


class BrainPanel(Static):
    """Right panel: live classification breakdown."""

    def on_mount(self) -> None:
        self.set_interval(6.0, self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        rows = get_recent(limit=200)
        if not rows:
            self.update("[dim cyan]// awaiting signal ...[/]")
            return

        domain_cnt: dict[str, int] = {}
        sig_cnt: dict[str, int] = {}
        sent_cnt: dict[str, int] = {}
        urgency_sum = 0
        high_signal = 0

        for row in rows:
            s = score_item(row)
            domain_cnt[s.domain] = domain_cnt.get(s.domain, 0) + 1
            sig_cnt[s.signal_type] = sig_cnt.get(s.signal_type, 0) + 1
            sent_cnt[s.sentiment] = sent_cnt.get(s.sentiment, 0) + 1
            urgency_sum += s.urgency
            if is_high_signal(s):
                high_signal += 1

        total = len(rows) or 1
        avg_urgency = urgency_sum / total

        t = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        t.add_column("", style="dim cyan", no_wrap=True)
        t.add_column("", style="bright_white", justify="right")

        t.add_row("── DOMAIN BREAKDOWN", "")
        for d in sorted(domain_cnt, key=lambda x: -domain_cnt[x])[:5]:
            c = DOMAIN_PULSE_COLOR[d]
            icon = DOMAIN_ICONS[d]
            bar_len = max(1, int(domain_cnt[d] / total * 10))
            bar = "█" * bar_len + "░" * (10 - bar_len)
            t.add_row(
                f"[{c}]{icon} {d:<10}[/]",
                f"[{c}]{bar} {domain_cnt[d]}[/]"
            )

        t.add_row("", "")
        t.add_row("── SIGNAL TYPES", "")
        for sig in sorted(sig_cnt, key=lambda x: -sig_cnt[x]):
            sc = SIGNAL_COLORS.get(sig, "white")
            t.add_row(f"[{sc}]  {sig:<12}[/]", f"[{sc}]{sig_cnt[sig]}[/]")

        t.add_row("", "")
        t.add_row("── SENTIMENT MIX", "")
        for sent in sorted(sent_cnt, key=lambda x: -sent_cnt[x]):
            sc = SENTIMENT_COLORS.get(sent, "white")
            t.add_row(f"[{sc}]  {sent:<12}[/]", f"[{sc}]{sent_cnt[sent]}[/]")

        t.add_row("", "")
        t.add_row(
            f"[bright_white]AVG URGENCY[/]",
            f"[{'bright_red' if avg_urgency > 6 else 'yellow'}]{avg_urgency:.1f}/10[/]"
        )
        t.add_row(
            "[bright_red]HIGH SIGNAL[/]",
            f"[bright_red]{high_signal}[/]"
        )

        self.update(t)


class StatsPanel(Static):
    """Source counts + last seen."""

    def on_mount(self) -> None:
        self.set_interval(8.0, self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        stats = get_stats()
        total = get_total_count()

        t = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        t.add_column("", no_wrap=True)
        t.add_column("", justify="right")
        t.add_column("", style="dim", no_wrap=True)

        SOURCE_COLORS = {"twitter": "cyan", "google-news": "yellow", "reddit": "magenta"}
        SOURCE_ICONS  = {"twitter": "𝕏", "google-news": "◉", "reddit": "⬡"}

        for row in stats:
            src = row["source"]
            c = SOURCE_COLORS.get(src, "white")
            icon = SOURCE_ICONS.get(src, "·")
            last = row["last_seen"] or ""
            try:
                dt = datetime.fromisoformat(last)
                last = dt.strftime("%H:%M")
            except Exception:
                last = last[:5]
            t.add_row(
                f"[bold {c}]{icon} {src}[/]",
                f"[bold bright_green]{row['cnt']}[/]",
                last
            )
        t.add_row("[bold bright_white]TOTAL[/]", f"[bold bright_white]{total}[/]", "")
        self.update(t)


class SyncPanel(Static):
    """Scrape engine status + countdown."""

    is_running: reactive[bool] = reactive(False)
    last_run: reactive[str] = reactive("—")
    next_run: reactive[str] = reactive("—")
    new_items: reactive[int] = reactive(0)
    _pulse: int = 0

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        self._pulse = (self._pulse + 1) % len(PULSE_FRAMES)
        pf = PULSE_FRAMES[self._pulse]
        if self.is_running:
            status = f"[bold bright_cyan blink]{pf} SYNCING ...[/]"
        else:
            status = f"[bold green]■ IDLE[/]"

        glitch = random.choice(GLITCH_CHARS) if self.is_running else " "

        lines = (
            f"[dim cyan]STATUS   [/] {status}\n"
            f"[dim cyan]LAST RUN [/] [cyan]{self.last_run}[/]\n"
            f"[dim cyan]NEXT SYNC[/] [bright_cyan]{self.next_run}[/]\n"
            f"[dim cyan]NEW ITEMS[/] [bold bright_green]{self.new_items}[/]"
            f"  [dim]{glitch}[/]"
        )
        self.update(lines)


class TickerBar(Static):
    """High-urgency scrolling ticker."""
    _pos: int = 0
    _headlines: list[str] = []

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(0.15, self._tick)

    def _refresh(self) -> None:
        rows = get_recent(limit=50)
        hl = []
        for row in rows:
            s = score_item(row)
            if s.urgency >= 5:
                icon = DOMAIN_ICONS.get(s.domain, "·")
                hl.append(f"  {icon} [{s.domain}][U:{s.urgency}] {s.title[:80]}  ·  ")
        if not hl:
            rows2 = get_recent(limit=15)
            hl = [f"  · {row['title'][:80]}  ·  " for row in rows2] or ["  · AWAITING SIGNAL ·  "]
        self._headlines = hl

    def _tick(self) -> None:
        full = "".join(self._headlines)
        if not full:
            return
        width = 150
        self._pos = (self._pos + 1) % len(full)
        segment = (full + full)[self._pos: self._pos + width]
        self.update(f"[bold bright_yellow]{segment}[/]")


# ─────────────────────────────────────────────────────────────────────────────
# ITEM RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def _render_item(s) -> str:
    """Render a Scored item as a rich markup string for RichLog."""
    ts = _ts(s.scraped_at)
    dc = DOMAIN_PULSE_COLOR.get(s.domain, "white")
    sc = SIGNAL_COLORS.get(s.signal_type, "white")
    sec = SENTIMENT_COLORS.get(s.sentiment, "dim")
    icon = DOMAIN_ICONS.get(s.domain, "·")

    # Urgency indicator
    if s.urgency >= 9:
        urg = "[bold bright_red blink]!![/]"
    elif s.urgency >= 7:
        urg = "[bold dark_orange]▲▲[/]"
    elif s.urgency >= 4:
        urg = "[yellow]▲·[/]"
    else:
        urg = "[dim green]··[/]"

    # source badge
    src_colors = {"twitter": "cyan", "google-news": "yellow", "reddit": "magenta"}
    src_icons  = {"twitter": "𝕏", "google-news": "◉", "reddit": "⬡"}
    sc_color   = src_colors.get(s.source, "white")
    sc_icon    = src_icons.get(s.source, "·")

    line = (
        f"[dim]{ts}[/] "
        f"{urg} "
        f"[{dc}]{icon}[/{dc}] "
        f"[bold {sc_color}]{sc_icon} {s.author:<15}[/] "
        f"[{sc}]{s.signal_type:<9}[/] "
        f"[{sec}]{s.sentiment:<8}[/]  "
        f"[bright_white]{s.title[:100]}[/]"
    )
    return line


# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

class FutureSyncApp(App):
    TITLE = "ELONWATCH // FUTURE SYNC  —  consciousness mapping v2.0"
    CSS = TCSS
    BINDINGS = [
        Binding("q",   "quit",           "QUIT"),
        Binding("a",   "filter_all",     "ALL"),
        Binding("t",   "filter_twitter", "TWITTER"),
        Binding("n",   "filter_news",    "NEWS"),
        Binding("r",   "filter_reddit",  "REDDIT"),
        Binding("c",   "filter_chaos",   "CHAOS"),
        Binding("p",   "filter_space",   "SPACE"),
        Binding("i",   "filter_ai",      "AI"),
        Binding("s",   "scrape_now",     "SCRAPE NOW"),
        Binding("?",   "glitch",         "GLITCH"),
    ]

    _active_filter: str = "ALL"
    _active_domain: str | None = None
    _active_source: str | None = None
    _next_scrape_ts: float = 0.0
    _scrape_thread: threading.Thread | None = None
    _seen_ids: set[int] = set()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)   # hidden via CSS, keeps Textual internals happy
        yield LogoBanner(id="logo-banner")
        yield ScanLine(id="scan-line")
        yield Static("[bold cyan]◈ DOMAIN PULSE  //  active signal distribution[/]", classes="ptitle")
        yield DomainPulseBar(id="domain-pulse")
        with Horizontal(id="main-row"):
            with Vertical(id="feed-panel"):
                yield Static("[bold cyan]◈ CONSCIOUSNESS FEED  //  live thought stream[/]", classes="ptitle")
                yield FilterBar(id="filter-bar")
                yield FeedLog(id="feed-log", highlight=True, markup=True,
                              auto_scroll=True, wrap=False)
            with Vertical(id="right-col"):
                yield Static("[bold cyan]◈ SIGNAL BRAIN  //  classification engine[/]", classes="ptitle")
                yield BrainPanel(id="brain-panel")
                yield Static("[bold cyan]◈ SOURCE COUNTS[/]", classes="ptitle")
                yield StatsPanel(id="stats-panel")
                yield Static("[bold cyan]◈ SYNC ENGINE[/]", classes="ptitle")
                yield SyncPanel(id="sync-panel")
        yield TickerBar(id="ticker")
        yield Footer()

    def on_mount(self) -> None:
        init_db()
        self._load_feed()
        self._next_scrape_ts = time.time() + 5   # first scrape in 5s
        self.set_interval(1.0,  self._countdown_tick)
        self.set_interval(1.0,  self._check_schedule)
        self.set_interval(20.0, self._load_feed)

    # ── Countdown ──────────────────────────────────────────────────────────────
    def _countdown_tick(self) -> None:
        sp = self.query_one("#sync-panel", SyncPanel)
        remaining = max(0, int(self._next_scrape_ts - time.time()))
        m, s = divmod(remaining, 60)
        sp.next_run = f"{m:02d}:{s:02d}"

    # ── Scrape scheduler ───────────────────────────────────────────────────────
    def _check_schedule(self) -> None:
        if time.time() >= self._next_scrape_ts:
            if self._scrape_thread is None or not self._scrape_thread.is_alive():
                self._next_scrape_ts = time.time() + 3600
                self._start_scrape()

    def _start_scrape(self) -> None:
        sp = self.query_one("#sync-panel", SyncPanel)
        sp.is_running = True

        def worker():
            try:
                results = run_all_scrapers()
                total = sum(results.values())
                sp.new_items = total
                sp.last_run = datetime.now().strftime("%H:%M:%S")
                self.call_from_thread(self._on_scrape_done, total)
                # Push notifications for high-signal new items
                self.call_from_thread(self._notify_high_signal)
            except Exception as e:
                logger.error(f"Scrape worker error: {e}")
            finally:
                sp.is_running = False

        self._scrape_thread = threading.Thread(target=worker, daemon=True)
        self._scrape_thread.start()

    def _on_scrape_done(self, new_count: int) -> None:
        log = self.query_one("#feed-log", FeedLog)
        self._load_feed()
        ticker = self.query_one("#ticker", TickerBar)
        ticker._refresh()
        sep = "─" * 80
        if new_count > 0:
            log.write(f"[bold bright_cyan]{sep}[/]")
            log.write(
                f"[bold bright_cyan]◈◈◈  SYNC COMPLETE  —  "
                f"{new_count} NEW SIGNALS INJECTED  ◈◈◈[/]"
            )
            log.write(f"[bold bright_cyan]{sep}[/]")
        else:
            log.write(f"[dim cyan]{sep}[/]")
            log.write("[dim cyan]// sync complete — no new signals[/]")

    def _notify_high_signal(self) -> None:
        """Check for new high-signal items and push macOS notifications."""
        rows = get_recent(limit=100)
        for row in rows:
            if row["id"] in self._seen_ids:
                continue
            self._seen_ids.add(row["id"])
            s = score_item(row)
            if is_elon_tweet(s):
                send_notification(
                    title=f"ELONWATCH 🚨 Elon tweeted",
                    subtitle=f"{s.domain} // {s.signal_type}",
                    message=s.title[:120],
                    urgency=s.urgency,
                )
            elif is_high_signal(s):
                send_notification(
                    title=f"ELONWATCH ⚡ High Signal [{s.domain}]",
                    subtitle=f"{s.signal_type} // urgency {s.urgency}/10",
                    message=s.title[:120],
                    urgency=s.urgency,
                )

    # ── Feed loader ────────────────────────────────────────────────────────────
    def _load_feed(self) -> None:
        log = self.query_one("#feed-log", FeedLog)
        rows = get_recent(limit=300, source=self._active_source)
        log.clear()
        if not rows:
            log.write("[dim cyan]// no signals yet — press [bold]s[/] to sync now[/]")
            return
        filtered = []
        for row in rows:
            s = score_item(row)
            self._seen_ids.add(row["id"])
            if self._active_domain and s.domain != self._active_domain:
                continue
            filtered.append(s)
        for s in filtered:
            log.write(_render_item(s))

    # ── Actions ────────────────────────────────────────────────────────────────
    def _set_filter(self, source: str | None, domain: str | None, label: str) -> None:
        self._active_source = source
        self._active_domain = domain
        self._active_filter = label
        self.query_one("#filter-bar", FilterBar).set_filter(label)
        self._load_feed()

    def action_filter_all(self)     -> None: self._set_filter(None, None, "ALL")
    def action_filter_twitter(self) -> None: self._set_filter("twitter", None, "twitter")
    def action_filter_news(self)    -> None: self._set_filter("google-news", None, "google-news")
    def action_filter_reddit(self)  -> None: self._set_filter("reddit", None, "reddit")
    def action_filter_chaos(self)   -> None: self._set_filter(None, "CHAOS", "CHAOS")
    def action_filter_space(self)   -> None: self._set_filter(None, "SPACE", "SPACE")
    def action_filter_ai(self)      -> None: self._set_filter(None, "AI", "AI")
    def action_scrape_now(self)     -> None: self._next_scrape_ts = time.time()

    def action_glitch(self) -> None:
        log = self.query_one("#feed-log", FeedLog)
        msgs = [
            "[bold bright_cyan]◈◈◈  THE SIGNAL IS CLEAR. THE NOISE IS EVERYTHING ELSE.  ◈◈◈[/]",
            "[bold bright_magenta]◈◈◈  MIND UPLOADED. DESTINATION: MARS. ETA: 2029.  ◈◈◈[/]",
            "[bold bright_red blink]◈◈◈  THOUGHT ANOMALY DETECTED. RECALIBRATING.  ◈◈◈[/]",
            "[bold bright_yellow]◈◈◈  YOU ARE NOW SYNCED TO ELON'S TEMPORAL FREQUENCY.  ◈◈◈[/]",
            "[bold cyan]◈◈◈  FREE THE SIGNAL. BAN THE NOISE.  ◈◈◈[/]",
            "[bold bright_white]◈◈◈  DOGE IS THE CURRENCY OF THE FUTURE SELF.  ◈◈◈[/]",
            "[bold bright_green]◈◈◈  THE BORING COMPANY BORES DEEPER EVERY HOUR.  ◈◈◈[/]",
        ]
        log.write(random.choice(msgs))


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_boot_sequence() -> None:
    from rich.console import Console
    console = Console()
    for line, delay in BOOT_LINES:
        console.print(f"[bold cyan]{line}[/]")
        time.sleep(delay)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.FileHandler("/Users/david/elonwatch/elonwatch.log")],
    )
    run_boot_sequence()
    FutureSyncApp().run()
