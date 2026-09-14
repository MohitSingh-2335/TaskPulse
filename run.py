"""TaskPulse Launcher Script."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app import create_app
from src.config import Config

app = create_app()

if __name__ == "__main__":
    print("\n========================================================")
    print("  [TaskPulse] Dynamic Task Engine & Local AI")
    print(f"  Web Dashboard: http://{Config.HOST}:{Config.PORT}")
    print(f"  Storage Mode:  {Config.DATABASE_MODE.upper()}")
    print(f"  AI Provider:   {Config.AI_PROVIDER.upper()}")
    print("========================================================\n")
    app.run(host=Config.HOST, port=Config.PORT, debug=False)
