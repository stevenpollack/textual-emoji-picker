#!/usr/bin/env bash
# Record an asciinema demo of the emoji picker.
#
# Prerequisites:
#   pip install asciinema
#
# Usage:
#   ./demo/record.sh
#
# Outputs demo/demo.cast — a self-contained recording playable by the
# asciinema-player JS widget on GitHub Pages.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$SCRIPT_DIR/demo.cast"

if ! command -v asciinema &>/dev/null; then
    echo "Error: asciinema not found. Install with: pip install asciinema" >&2
    exit 1
fi

echo "Recording to $OUT"
echo "Run the demo app, interact with it, then exit (Ctrl+C or q)."
echo "---"

asciinema rec "$OUT" \
    --cols 60 \
    --rows 36 \
    --title "textual-emoji-picker demo" \
    --command "uv run python $SCRIPT_DIR/app.py"

echo "---"
echo "Recording saved to: $OUT"
echo "To preview: asciinema play $OUT"
