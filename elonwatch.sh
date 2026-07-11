#!/usr/bin/env bash
# elonwatch.sh - Launch the ElonWatch Future Sync TUI
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

source "$DIR/venv/bin/activate"
exec python3 "$DIR/tui.py" "$@"
