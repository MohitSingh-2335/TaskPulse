"""
TaskPulse: One-Time Google Calendar Authentication Script.
Can be executed from any folder in PowerShell or CMD.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Config
from src.core.calendar_sync import get_calendar_service, get_or_create_target_calendar


def main():
    print("=" * 65)
    print("  TaskPulse: Google Calendar Authorization")
    print("=" * 65)
    print(f"Project Folder:      {ROOT}")
    print(f"Target Sub-Calendar: '{Config.GOOGLE_CALENDAR_NAME}' (Primary will NOT be touched)")
    print("\n[INFO] Opening your default web browser for Google Authorization...")
    print("       (Select your Google Account and click 'Continue / Allow')\n")

    try:
        svc = get_calendar_service(allow_interactive=True)
        if not svc:
            print("\n[ERROR] Authorization failed or credentials.json was not found.")
            print("        Ensure credentials.json is saved in: " + str(Config.GOOGLE_CREDENTIALS_FILE))
            return 1

        cal_id = get_or_create_target_calendar(svc)
        print("\n" + "=" * 65)
        print("  [SUCCESS] Google Calendar Linked Successfully!")
        print(f"  Token Saved:        {Config.GOOGLE_TOKEN_FILE}")
        print(f"  Isolated Calendar:  '{Config.GOOGLE_CALENDAR_NAME}'")
        print(f"  Calendar ID:        {cal_id}")
        print("  Status:             Permanent (Never expires)")
        print("=" * 65)
        return 0
    except Exception as exc:
        print(f"\n[ERROR] An unexpected error occurred: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
