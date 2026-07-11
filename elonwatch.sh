#!/usr/bin/env bash
# elonwatch.sh — Launch ElonWatch // Future Sync
# Plays intro video (auto-installs mpv via Homebrew if needed), then opens TUI.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# ── Video intro ───────────────────────────────────────────────────────────────
INTRO="$DIR/intro.mp4"

if [[ -f "$INTRO" ]]; then
    # Ensure mpv is available
    if ! command -v mpv &>/dev/null; then
        if [[ "$(uname)" == "Darwin" ]]; then
            echo ">> mpv not found — installing via Homebrew ..."
            if command -v brew &>/dev/null; then
                brew install --quiet mpv
            fi
        else
            echo ">> mpv not found — run install-ubuntu.sh to install it."
        fi
    fi

    if command -v mpv &>/dev/null; then
        # Play fullscreen, no OSD, auto-quit when done, borderless
        mpv "$INTRO" \
            --fs \
            --no-osc \
            --no-osd-bar \
            --osd-level=0 \
            --no-input-default-bindings \
            --input-key-bindings=no \
            --keep-open=no \
            --really-quiet \
            2>/dev/null || true
    fi
fi

# ── Launch TUI ────────────────────────────────────────────────────────────────
source "$DIR/venv/bin/activate"
exec python3 "$DIR/tui.py" "$@"
