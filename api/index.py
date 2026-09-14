"""Vercel entrypoint and backward-compatibility bridge."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app import app

# Expose app for Vercel WSGI
if __name__ == "__main__":
    app.run(debug=True)