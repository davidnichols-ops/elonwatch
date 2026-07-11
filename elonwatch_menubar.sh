#!/usr/bin/env bash
# elonwatch_menubar.sh - Launch the ElonWatch menubar app
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

source "$DIR/venv/bin/activate"
exec python3 "$DIR/menubar.py" "$@"
