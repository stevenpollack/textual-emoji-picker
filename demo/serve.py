"""Run the demo app via textual-serve for browser access.

Usage (local):
    uv run python demo/serve.py

Usage (deployed):
    python demo/serve.py
    # Listens on 0.0.0.0:$PORT (defaults to 8000)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from textual_serve.server import Server

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

app_path = Path(__file__).parent / "app.py"

server = Server(
    f"{sys.executable} {app_path}",
    host=HOST,
    port=PORT,
    title="textual-emoji-picker demo",
)

if __name__ == "__main__":
    server.serve()
