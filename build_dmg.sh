#!/usr/bin/env bash
# build_dmg.sh - Build ElonWatch.app + ElonWatch.dmg
# Creates a self-contained .app bundle and wraps it in a DMG.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

APP_NAME="ElonWatch"
APP_VERSION="2.0"
APP_BUNDLE="$DIR/dist/${APP_NAME}.app"
DMG_PATH="$DIR/dist/${APP_NAME}.dmg"
STAGING="$DIR/dist/dmg_staging"
PYTHON="$DIR/venv/bin/python3"

echo "╔══════════════════════════════════════════════╗"
echo "║   ELONWATCH // FUTURE SYNC  —  DMG BUILDER  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Clean old build ─────────────────────────────────────────────────────
echo ">> Cleaning dist/ ..."
rm -rf "$DIR/dist" "$DIR/build" "$DIR/__pycache__"
mkdir -p "$DIR/dist"

# ── 2. PyInstaller — build the menubar .app ───────────────────────────────
echo ">> Running PyInstaller (menubar.app) ..."
source "$DIR/venv/bin/activate"

pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --distpath "$DIR/dist" \
  --workpath "$DIR/build" \
  --specpath "$DIR/build" \
  --icon "$DIR/ElonWatch.icns" \
  --add-data "$DIR/db.py:." \
  --add-data "$DIR/scrapers.py:." \
  --add-data "$DIR/brain.py:." \
  --add-data "$DIR/notify.py:." \
  --add-data "$DIR/tui.py:." \
  --add-data "$DIR/scrape_worker.py:." \
  --hidden-import rumps \
  --hidden-import feedparser \
  --hidden-import bs4 \
  --hidden-import requests \
  --hidden-import textual \
  --hidden-import rich \
  --osx-bundle-identifier "com.elonwatch.futuresync" \
  "$DIR/menubar.py"

echo ">> PyInstaller done. App bundle: $APP_BUNDLE"

# ── 3. Inject a copy of the venv DB path + elonwatch.db ──────────────────
# The app stores its DB in ~/Library/Application Support/ElonWatch/
# We patch the db.py inside the bundle to use that path.
RESOURCES="$APP_BUNDLE/Contents/Resources"
mkdir -p "$RESOURCES"

# Copy the launchd plist for reference
cp "$DIR/com.elonwatch.scraper.plist" "$RESOURCES/"

# ── 4. Create DMG staging ─────────────────────────────────────────────────
echo ">> Creating DMG staging area ..."
mkdir -p "$STAGING"
cp -r "$APP_BUNDLE" "$STAGING/"

# Add a symlink to /Applications for drag-install
ln -sf /Applications "$STAGING/Applications"

# Add a README
cat > "$STAGING/README.txt" << 'EOF'
ELONWATCH // FUTURE SYNC  v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTALL
  Drag ElonWatch.app to the Applications folder.
  Double-click to launch.

WHAT IT DOES
  ◈ Scrapes Elon's tweets (via nitter.net), Google News,
    and Reddit every hour automatically.
  ◈ Classifies every signal by domain (SPACE / AI / POLITICS /
    MONEY / TECH / CHAOS / EGO / CULTURE), urgency, and
    sentiment in real time.
  ◈ Sends macOS push notifications for new tweets and
    high-urgency signals.
  ◈ Lives in your menubar — click ◈ for stats.
  ◈ Opens a full-screen cyberpunk TUI via "Open TUI Console".

FIRST RUN NOTE
  macOS may show a security warning (unsigned app).
  Right-click ElonWatch.app → Open → Open to bypass.

DATA
  ~/Library/Application Support/ElonWatch/elonwatch.db
  ~/Library/Logs/ElonWatch/elonwatch.log

EOF

# ── 5. Build the DMG ──────────────────────────────────────────────────────
echo ">> Building DMG ..."
hdiutil create \
  -volname "ElonWatch — Future Sync" \
  -srcfolder "$STAGING" \
  -ov \
  -format UDZO \
  -imagekey zlib-level=9 \
  "$DMG_PATH"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   BUILD COMPLETE                             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  DMG:  $DMG_PATH"
echo "  APP:  $APP_BUNDLE"
echo ""
echo "  Install: open $DMG_PATH"
echo ""
