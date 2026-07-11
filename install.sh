#!/usr/bin/env bash
# install.sh - Install ElonWatch LaunchAgent for hourly background scraping
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_SRC="$DIR/com.elonwatch.scraper.plist"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_DIR/com.elonwatch.scraper.plist"

echo "╔══════════════════════════════════════╗"
echo "║   ELONWATCH INSTALLER v2.0           ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Make launcher executable
chmod +x "$DIR/elonwatch.sh"

# Create LaunchAgents dir if needed
mkdir -p "$LAUNCH_DIR"

# Unload if already loaded
if launchctl list | grep -q "com.elonwatch.scraper" 2>/dev/null; then
    echo ">> Unloading existing LaunchAgent ..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Copy plist
cp "$PLIST_SRC" "$PLIST_DEST"

# Load
echo ">> Loading LaunchAgent (runs every hour, starts now) ..."
launchctl load "$PLIST_DEST"

echo ""
echo ">> LaunchAgent installed! Scraper will run every hour."
echo ">> To run the TUI now:"
echo "     ./elonwatch.sh"
echo ""
echo ">> To stop the background scraper:"
echo "     launchctl unload ~/Library/LaunchAgents/com.elonwatch.scraper.plist"
echo ""
echo ">> Logs: $DIR/elonwatch.log"
echo ">> DB:   $DIR/elonwatch.db"
