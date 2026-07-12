# ElonWatch // Future Sync

> *Real-time Elon Musk consciousness mapping, signal intelligence, and live thought-stream decoding.*
>
> Yes, someone built this.

---

## What is this

ElonWatch is a fully automated news aggregator that monitors Twitter/X, Google News, and Reddit 24/7 for Elon Musk content, classifies each piece of coverage by domain, urgency, and sentiment using a rule-based brain engine, and displays everything in either a cinematic terminal-aesthetic macOS app or a Textual TUI on Ubuntu.

It was built because treating "what is Elon Musk thinking right now" as a serious intelligence problem is genuinely funny. The system is technically solid and works exactly as described. That it works exactly as described is part of the joke.

---

## Features

### macOS (Native SwiftUI App)
- Cinematic intro video on launch, transitions to main UI
- Live feed of all Elon-related signals across Twitter/X, Google News, and Reddit
- **Domain pulse bar** across the top — 9 domains, click any to filter the feed:
  `🚀 SPACE` · `🧠 AI` · `⚡ POLITICS` · `◈ MONEY` · `⬡ TECH` · `!! CHAOS` · `★ EGO` · `◉ CULTURE` · `✦ GLAZE`
- Source filter tabs: ALL / 𝕏 TWITTER / ◉ NEWS / ⬡ REDDIT
- Feed header shows active filter and live signal count
- Right panel: Signal Brain (domain breakdown, signal types, sentiment mix, avg urgency), Source Counts, Sync Engine with SYNC NOW button
- Scrolling amber ticker at the bottom with high-urgency items
- Embedded Python scraper — runs as a subprocess, zero external dependencies
- Auto-sync every 15 minutes, macOS notifications for high-urgency signals
- Ships as a drag-to-Applications `.dmg`

### Ubuntu / Linux (Textual TUI)
- Full-screen terminal UI with live refresh
- Same domain pulse bar and classification engine
- Filter by domain or source: `[a]ALL [t]TWITTER [n]NEWS [r]REDDIT [c]CHAOS [p]SPACE [i]AI [g]GLAZE`
- Boot sequence with ASCII art before TUI loads
- `systemd` service for background scraping

### The GLAZE Domain

GLAZE is a first-class domain alongside SPACE, MONEY, TECH, etc. It captures content that is unambiguously positive, praising, or fawning about Elon Musk — the kind of coverage where someone is clearly glazing. Keyword list includes: *genius, visionary, brilliant, legendary, goat, hero, pioneer, revolutionary, inspires, admire, praise, remarkable, outstanding, historic achievement,* and more.

Click `✦ GLAZE` in the domain bar (macOS) or press `[g]` (TUI) to filter to just this content. GLAZE items render with a warm gold tint in the feed so you can immediately identify the glazers. "GLAZE INTENSITY" as a concept lives in the signal brain stats.

---

## Installation

### macOS

```
# Download ElonWatch.dmg
# Drag ElonWatch.app to Applications
# Launch from Spotlight or Applications
```

Self-contained. No Python, no Homebrew, no setup.

### Ubuntu

```bash
git clone https://github.com/davidnichols-ops/elonwatch.git
cd elonwatch
bash install-ubuntu.sh
```

---

## How it works

```
┌─────────────────────────────────────────────────────────┐
│                    SCRAPER LAYER                        │
│  Python → Twitter/X · Google News · Reddit             │
│  Writes to SQLite: ~/Library/Application Support/       │
│                    ElonWatch/elonwatch.db               │
└───────────────────────────┬─────────────────────────────┘
                            │ every 15 min
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     BRAIN LAYER                         │
│  Domain classifier  → 9 domains incl. GLAZE            │
│  Signal type scorer → DIRECTIVE / VISION / HUMOR / etc │
│  Urgency scorer     → 0–10 (BREAKING = 10)             │
│  Sentiment scorer   → BULLISH / BEARISH / HOSTILE / …  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      UI LAYER                           │
│  macOS SwiftUI app  — click-to-filter domain bar       │
│  Ubuntu Textual TUI — keyboard shortcuts               │
└─────────────────────────────────────────────────────────┘
```

### The Brain

`brain.py` / `Database.swift` classify using keyword frequency across 9 domains. It is not a neural network. It is a carefully curated pile of if-statements dressed up with the word "brain." It works well because Elon Musk content is highly predictable.

### Domains

| Domain | Icon | What it catches |
|--------|------|----------------|
| SPACE | 🚀 | SpaceX, Starship, Mars, Starlink |
| AI | 🧠 | xAI, Grok, LLMs, AGI, Colossus |
| POLITICS | ⚡ | DOGE, Trump, Congress, lawsuits |
| MONEY | ◈ | Tesla stock, crypto, revenue, deals |
| TECH | ⬡ | FSD, Neuralink, X.com, engineering |
| CHAOS | !! | Fired, crash, scandal, meltdown |
| EGO | ★ | Richest, genius, CEO, visionary |
| CULTURE | ◉ | Memes, podcasts, philosophy, shitposts |
| GLAZE | ✦ | Praise, admiration, "he saved us" energy |

### Urgency Scoring

| Score | Indicator | Meaning |
|-------|-----------|---------|
| 9–10 | `!!` | Breaking / emergency |
| 7–8 | `▲▲` | High signal |
| 4–6 | `▲·` | Notable |
| 0–3 | `··` | Background noise |

---

## Project Structure

```
elonwatch/                ← Python backend (shared by both platforms)
  scrape_worker.py        ← main scrape loop
  scrapers.py             ← Twitter/X, Google News, Reddit scrapers
  brain.py                ← classification engine (9 domains)
  tui.py                  ← Ubuntu Textual TUI
  db.py                   ← SQLite interface
  notify.py               ← macOS / Ubuntu notifications
  install-ubuntu.sh       ← Ubuntu installer
  install.sh              ← macOS legacy installer

elonwatch-mac/            ← SwiftUI macOS app
  Sources/ElonWatch/
    ElonWatchApp.swift         ← app entry, intro gate
    IntroPlayerView.swift      ← AVPlayerLayer splash (AVKit-free, crash-safe)
    ContentView.swift          ← full UI: domain bar, feed, brain panel
    FeedViewModel.swift        ← data layer, refresh logic
    Database.swift             ← Swift brain scorer + SQLite reader
    Models.swift               ← SignalItem, Domain (9), Sentiment, etc.
    ScraperRunner.swift        ← embedded scraper subprocess manager
  Resources/
    intro.mp4                  ← cinematic intro
    elonwatch_scraper          ← PyInstaller-compiled scraper binary
    AppIcon.icns
  build_dmg.sh                ← dmgbuild DMG packaging
  dmg_settings.py             ← DMG window layout + background config
  project.yml                 ← XcodeGen project spec
```

---

## Building from Source

### macOS App

Requirements: Xcode 26+, XcodeGen, ffmpeg (optional)

```bash
cd elonwatch-mac

# Generate Xcode project
xcodegen generate

# Build Release
xcodebuild -project ElonWatch.xcodeproj -scheme ElonWatch \
  -configuration Release -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY=""

# Inject resources
APP=build/Build/Products/Release/ElonWatch.app
cp Sources/ElonWatch/Resources/elonwatch_scraper "$APP/Contents/Resources/"
cp Sources/ElonWatch/Resources/intro.mp4         "$APP/Contents/Resources/"

# Package DMG
bash build_dmg.sh
```

### Rebuild Scraper Binary

```bash
cd elonwatch
pip install pyinstaller
pyinstaller --onefile scrape_worker.py -n elonwatch_scraper
cp dist/elonwatch_scraper ../elonwatch-mac/Sources/ElonWatch/Resources/
```

---

## Repos

- **Backend + Ubuntu TUI**: [github.com/davidnichols-ops/elonwatch](https://github.com/davidnichols-ops/elonwatch)
- **macOS App**: [github.com/davidnichols-ops/elonwatch-mac](https://github.com/davidnichols-ops/elonwatch-mac)

---

## Honest disclaimer

This project does not endorse, oppose, celebrate, or condemn Elon Musk. It monitors him the way a seismologist monitors a volcano — because if you're going to live near it, you might as well have instruments.

The GLAZE domain was added because positive coverage of extremely powerful people follows identifiable and documentable patterns. It is also objectively funny to have a domain called GLAZE sitting right next to SPACE and AI in a real-time intelligence dashboard.

The intro video plays every time. This was deliberate.

---

## License

MIT. Fork it. Add a RATIO domain for people dunking on him. Build a COPE domain. Go nuts.
