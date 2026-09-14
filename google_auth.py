from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.calendar_sync import get_calendar_credentials, get_calendar_service, is_calendar_connected

authenticate_google = get_calendar_service

if __name__ == "__main__":
    print("🔐 Checking Google Calendar Authentication...")
    service = get_calendar_service()
    if service:
        print("✅ Google Calendar successfully authenticated!")
    else:
        print("⚠️ Google Calendar not authenticated. Make sure credentials.json exists or is configured in .env.")