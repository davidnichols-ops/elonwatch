#!/usr/bin/env bash
# install-ubuntu.sh — ElonWatch // Future Sync  (Ubuntu / Linux)
# TUI-only install. No menubar, no macOS-specific deps.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════╗"
echo "║  ELONWATCH // FUTURE SYNC  —  Ubuntu Setup  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Python check ──────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo ">> Installing python3 ..."
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip python3-venv
fi

# ── Virtualenv ────────────────────────────────────────────────────────────
echo ">> Creating virtualenv ..."
python3 -m venv "$DIR/venv"
source "$DIR/venv/bin/activate"

echo ">> Installing dependencies ..."
pip install -q --upgrade pip
pip install -q -r "$DIR/requirements-ubuntu.txt"

# ── Make scripts executable ────────────────────────────────────────────────
chmod +x "$DIR/elonwatch.sh"

# ── systemd unit (optional, hourly background scrape) ─────────────────────
SYSTEMD_USER="$HOME/.config/systemd/user"
SERVICE="elonwatch-scraper.service"
TIMER="elonwatch-scraper.timer"

if command -v systemctl &>/dev/null; then
    mkdir -p "$SYSTEMD_USER"

    cat > "$SYSTEMD_USER/$SERVICE" << EOF
[Unit]
Description=ElonWatch // Future Sync — hourly scraper
After=network-online.target

[Service]
Type=oneshot
ExecStart=$DIR/venv/bin/python3 $DIR/scrape_worker.py
WorkingDirectory=$DIR
StandardOutput=append:$DIR/elonwatch.log
StandardError=append:$DIR/elonwatch.log
EOF

    cat > "$SYSTEMD_USER/$TIMER" << EOF
[Unit]
Description=Run ElonWatch scraper every hour

[Timer]
OnBootSec=30s
OnUnitActiveSec=1h
Unit=$SERVICE

[Install]
WantedBy=timers.target
EOF

    systemctl --user daemon-reload
    systemctl --user enable --now "$TIMER"
    echo ">> systemd timer installed — scraper runs every hour."
    echo ">> Check status: systemctl --user status $TIMER"
else
    echo ">> systemd not found — add a cron job manually:"
    echo "   0 * * * * $DIR/venv/bin/python3 $DIR/scrape_worker.py"
fi

echo ""
echo ">> Done. Run the TUI with:"
echo "     $DIR/elonwatch.sh"
echo ""
echo ">> Logs: $DIR/elonwatch.log"
echo ">> DB:   $DIR/elonwatch.db"
