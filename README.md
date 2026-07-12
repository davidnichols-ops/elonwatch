# ElonWatch // Future Sync

> *Real-time Elon Musk consciousness mapping, signal intelligence, and live thought-stream decoding.*
>
> Yes, someone built this.

---

## What is this

ElonWatch is a fully automated news aggregator that monitors Twitter/X, Google News, and Reddit 24/7 for Elon Musk content, classifies each piece of coverage by domain, urgency, and sentiment using a rule-based ML-adjacent brain engine, and displays everything in a cinematic terminal-aesthetic macOS app.

It was built because someone found the idea of a system that treats "what is Elon Musk thinking right now" as a serious intelligence problem genuinely hilarious. The result is technically sound and works exactly as described. The fact that it works exactly as described is part of the joke.

---

## Features

### macOS (Native SwiftUI App)
- Cinematic intro video on launch (plays `intro.mp4`, transitions to main UI)
- Live feed of all Elon-related signals across Twitter/X, Google News, and Reddit
- **FEED tab**: full classified signal stream with urgency indicators, domain tags, sentiment scoring
- **GLAZE tab**: filters to only positive/praise coverage — a dedicated view for detecting when people are "glazing" him. Shows a real-time GLAZE INTENSITY bar. Yes, this is a real feature.
- Domain pulse bar with animated waveforms: SPACE / AI / POLITICS / MONEY / TECH / CHAOS / EGO / CULTURE
- Right panel: Signal Brain (domain breakdown, signal type distribution, sentiment mix, avg urgency), Source Counts, Sync Engine
- Scrolling amber ticker at the bottom showing high-urgency items
- Embedded Python scraper binary — runs as a subprocess, no Python install required
- Auto-sync every 15 minutes, manual "SYNC NOW" button
- macOS notifications for high-urgency items (urgency ≥ 7)
- Ships as a drag-to-Applications `.dmg` with a cinematic background

### Ubuntu / Linux (TUI)
- Terminal UI using `rich` — tables, panels, live refresh
- Same scraper and classification engine
- `mpv`-based video intro sequence before the TUI loads
- `systemd` service for background scraping

---

## Installation

### macOS (Recommended)

```
# Download ElonWatch.dmg
# Drag ElonWatch.app to Applications
# Launch from Applications or Spotlight
```

The app is self-contained. No Python, no Homebrew, no dependencies.

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
│  Python scraper → Twitter/X · Google News · Reddit     │
│  Writes to SQLite: ~/Library/Application Support/       │
│                    ElonWatch/elonwatch.db               │
└───────────────────────────┬─────────────────────────────┘
                            │ every 15min
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     BRAIN LAYER                         │
│  Domain classifier  → SPACE / AI / POLITICS / etc.     │
│  Signal type scorer → DIRECTIVE / VISION / HUMOR / etc │
│  Urgency scorer     → 0-10 (BREAKING = 10)             │
│  Sentiment scorer   → BULLISH / BEARISH / HOSTILE / ..  │
│  Glaze detector     → bullish + praise keywords        │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      UI LAYER                           │
│  SwiftUI macOS app reads DB, scores on the fly,        │
│  renders live feed + glaze tab + brain stats panel     │
└─────────────────────────────────────────────────────────┘
```

### The Brain

The classifier (`brain.py` / `Database.swift`) uses keyword frequency matching across eight domains. It's not a neural network. It's a pile of if-statements dressed up with the word "brain." It works surprisingly well for this use case because Elon Musk content is highly domain-predictable.

### The Glaze Tab

Filters the full feed to items where:
1. Sentiment is `BULLISH`
2. Title or content contains any of: *genius, visionary, incredible, revolutionary, legend, goat, hero, praised, inspired, outstanding, historic, remarkable,* and ~25 more glaze-positive terms

Each match gets a ✦✦✦✦✦ star rating based on urgency. The GLAZE INTENSITY bar fills as the proportion of glazing content rises. "MAX — ASTRONOMICAL GLAZE" is a real system state.

### Urgency Scoring

| Score | Indicator | Meaning |
|-------|-----------|---------|
| 9-10  | `!!`      | Breaking / emergency |
| 7-8   | `▲▲`     | High signal |
| 4-6   | `▲·`     | Notable |
| 0-3   | `··`     | Background noise |

---

## Project Structure

```
elonwatch/             ← Python backend (scraper, TUI, brain)
  scrape_worker.py     ← main scrape loop
  scrapers.py          ← Twitter/X, Google News, Reddit scrapers
  brain.py             ← classification engine
  tui.py               ← Ubuntu TUI
  db.py                ← SQLite interface
  install-ubuntu.sh    ← Ubuntu installer
  install.sh           ← macOS legacy installer

elonwatch-mac/         ← SwiftUI macOS app
  Sources/ElonWatch/
    ElonWatchApp.swift      ← app entry, intro gate
    IntroPlayerView.swift   ← AVPlayerLayer splash screen
    ContentView.swift       ← full UI: feed, glaze, brain panel
    FeedViewModel.swift     ← data layer, refresh logic
    Database.swift          ← Swift port of brain.py + SQLite reader
    Models.swift            ← SignalItem, Domain, Sentiment, etc.
    ScraperRunner.swift     ← launches embedded scraper subprocess
  Resources/
    intro.mp4               ← the cinematic intro
    elonwatch_scraper       ← compiled Python scraper (PyInstaller)
    AppIcon.icns
  build_dmg.sh             ← dmgbuild-based DMG packaging
  dmg_settings.py          ← DMG window layout, background config
  project.yml              ← XcodeGen project spec
```

---

## Building from Source

### macOS App

Requirements: Xcode 26+, XcodeGen, ffmpeg (optional, for video editing)

```bash
cd elonwatch-mac

# Generate Xcode project
xcodegen generate

# Build
xcodebuild -project ElonWatch.xcodeproj -scheme ElonWatch \
  -configuration Release -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY=""

# Inject resources (scraper binary + video)
cp Sources/ElonWatch/Resources/elonwatch_scraper \
   build/Build/Products/Release/ElonWatch.app/Contents/Resources/
cp Sources/ElonWatch/Resources/intro.mp4 \
   build/Build/Products/Release/ElonWatch.app/Contents/Resources/

# Build DMG
bash build_dmg.sh
```

### Rebuilding the Scraper Binary

```bash
cd elonwatch
pip install pyinstaller
pyinstaller --onefile scrape_worker.py -n elonwatch_scraper
cp dist/elonwatch_scraper ../elonwatch-mac/Sources/ElonWatch/Resources/
```

---

## Repos

- **Backend / Ubuntu**: [github.com/davidnichols-ops/elonwatch](https://github.com/davidnichols-ops/elonwatch)
- **macOS App**: [github.com/davidnichols-ops/elonwatch-mac](https://github.com/davidnichols-ops/elonwatch-mac)

---

## Honest disclaimer

This project does not endorse, oppose, celebrate, or condemn Elon Musk. It monitors him the way a seismologist monitors a volcano — because if you're going to live near it, you might as well have instruments.

The "GLAZE" tab was added because positive coverage of extremely powerful people follows identifiable patterns worth documenting. Also because naming a feature "GLAZE WATCH" with a glaze intensity bar is objectively funny.

The intro video plays every time you open the app. This was a deliberate choice.

---

## License

MIT. Fork it. Add more domains. Build a "RATIO WATCH" tab for people dunking on him. Go nuts.
