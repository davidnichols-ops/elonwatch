#!/usr/bin/env bash
# build_dmg.sh - Build ElonWatch.app + ElonWatch.dmg
# Creates a self-contained .app bundle and wraps it in a styled DMG.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

APP_NAME="ElonWatch"
APP_VERSION="2.0"
APP_BUNDLE="$DIR/dist/${APP_NAME}.app"
DMG_FINAL="$DIR/dist/${APP_NAME}.dmg"
DMG_TEMP="$DIR/dist/${APP_NAME}_tmp.dmg"
STAGING="$DIR/dist/dmg_staging"
PYTHON="$DIR/venv/bin/python3"

echo "╔══════════════════════════════════════════════╗"
echo "║   ELONWATCH // FUTURE SYNC  —  DMG BUILDER  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Clean old build ────────────────────────────────────────────────────────
echo ">> Cleaning dist/ ..."
rm -rf "$DIR/dist" "$DIR/build" "$DIR/__pycache__"
mkdir -p "$DIR/dist"

# ── 2. PyInstaller ────────────────────────────────────────────────────────────
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
  --add-data "$DIR/intro.mp4:." \
  --add-data "$DIR/elonwatch.sh:." \
  --hidden-import rumps \
  --hidden-import feedparser \
  --hidden-import bs4 \
  --hidden-import requests \
  --hidden-import textual \
  --hidden-import rich \
  --osx-bundle-identifier "com.elonwatch.futuresync" \
  "$DIR/menubar.py"

echo ">> PyInstaller done."

# Copy launchd plist into bundle Resources
RESOURCES="$APP_BUNDLE/Contents/Resources"
mkdir -p "$RESOURCES"
cp "$DIR/com.elonwatch.scraper.plist" "$RESOURCES/"

# ── 3. Build a read-write DMG for styling ─────────────────────────────────────
echo ">> Creating styled DMG staging ..."
mkdir -p "$STAGING"
cp -r "$APP_BUNDLE" "$STAGING/"
ln -sf /Applications "$STAGING/Applications"

# Hide a .background folder with our cinematic still
mkdir -p "$STAGING/.background"
cp "$DIR/dmg_background.png" "$STAGING/.background/background.png"

# Add README
cat > "$STAGING/README.txt" << 'EOF'
ELONWATCH // FUTURE SYNC  v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTALL
  Drag ElonWatch.app to the Applications folder.
  Double-click to launch.

ON FIRST LAUNCH
  Video intro plays fullscreen (mpv auto-installs via Homebrew
  if not present), then the cyberpunk TUI opens.

  macOS may show a security warning (unsigned app).
  Right-click ElonWatch.app → Open → Open to bypass.

DATA
  ~/Library/Application Support/ElonWatch/elonwatch.db
  ~/Library/Logs/ElonWatch/elonwatch.log

EOF

# ── 4. Create temp RW DMG, set background + icon layout via AppleScript ───────
echo ">> Building temp RW DMG for styling ..."
hdiutil create \
  -volname "ElonWatch — Future Sync" \
  -srcfolder "$STAGING" \
  -ov \
  -format UDRW \
  -size 200m \
  "$DMG_TEMP"

# Mount it
MOUNT_DIR="$(mktemp -d)"
hdiutil attach "$DMG_TEMP" -mountpoint "$MOUNT_DIR" -noautoopen -quiet

echo ">> Applying DMG background + icon layout ..."
osascript << APPLESCRIPT || true
tell application "Finder"
  tell disk "ElonWatch \u2014 Future Sync"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set the bounds of container window to {100, 100, 760, 500}
    set theViewOptions to the icon view options of container window
    set arrangement of theViewOptions to not arranged
    set icon size of theViewOptions to 100
    set background picture of theViewOptions to file ".background:background.png"
    set position of item "ElonWatch.app" of container window to {170, 200}
    set position of item "Applications" of container window to {490, 200}
    close
    open
    update without registering applications
    delay 2
  end tell
end tell
APPLESCRIPT

# Copy icon for DMG volume (SetFile is optional — only present with Xcode CLT extra pkg)
cp "$DIR/ElonWatch.icns" "$MOUNT_DIR/.VolumeIcon.icns" 2>/dev/null || true
SetFile -c icnC "$MOUNT_DIR/.VolumeIcon.icns" 2>/dev/null || true
SetFile -a C "$MOUNT_DIR" 2>/dev/null || true

sync
hdiutil detach "$MOUNT_DIR" -quiet || hdiutil detach "$MOUNT_DIR" -force || true

# ── 5. Convert to final compressed read-only DMG ─────────────────────────────
echo ">> Compressing to final DMG ..."
hdiutil convert "$DMG_TEMP" \
  -format UDZO \
  -imagekey zlib-level=9 \
  -o "$DMG_FINAL"

rm -f "$DMG_TEMP"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   BUILD COMPLETE                             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  DMG: $DMG_FINAL"
echo "  APP: $APP_BUNDLE"
echo ""
echo "  Install: open $DMG_FINAL"
echo ""
