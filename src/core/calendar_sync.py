from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from src.config import Config

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

_cached_calendar_id: Optional[str] = None


def get_calendar_credentials(allow_interactive: bool = False):
    """Retrieves or refreshes Google OAuth2 Credentials without blocking unless requested."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return None

    creds = None

    # 1. Environment Variable JSON token (for cloud/serverless)
    token_json_str = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_json_str:
        try:
            token_data = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception:
            creds = None

    # 2. Local token.json file fallback
    if not creds and Config.GOOGLE_TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(Config.GOOGLE_TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    # 3. Refresh or Run Flow if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                if not token_json_str:
                    with open(Config.GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
            except Exception:
                creds = None
        elif allow_interactive:
            # Full OAuth flow needed - only if explicitly allowed interactively
            credentials_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if credentials_json_str:
                try:
                    credentials_data = json.loads(credentials_json_str)
                    flow = InstalledAppFlow.from_client_config(credentials_data, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception:
                    creds = None
            elif Config.GOOGLE_CREDENTIALS_FILE.exists():
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(Config.GOOGLE_CREDENTIALS_FILE), SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(Config.GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                except Exception:
                    creds = None

    return creds


def get_calendar_service(allow_interactive: bool = False):
    """Builds and returns the Google Calendar API Resource client."""
    creds = get_calendar_credentials(allow_interactive=allow_interactive)
    if not creds:
        return None
    try:
        from googleapiclient.discovery import build
        return build("calendar", "v3", credentials=creds)
    except Exception:
        return None


def get_or_create_target_calendar(service) -> str:
    """
    Returns the target Google Calendar ID.
    Guarantees isolation to a dedicated sub-calendar (e.g. 'TaskPulse')
    so the user's primary calendar is NEVER touched or modified.
    """
    global _cached_calendar_id
    if _cached_calendar_id:
        return _cached_calendar_id

    # 1. Explicit ID in Config
    if Config.GOOGLE_CALENDAR_ID:
        _cached_calendar_id = Config.GOOGLE_CALENDAR_ID
        return _cached_calendar_id

    target_name = (Config.GOOGLE_CALENDAR_NAME or "TaskPulse").strip()

    try:
        # 2. Search existing calendars
        calendar_list = service.calendarList().list().execute()
        for item in calendar_list.get("items", []):
            if item.get("summary", "").strip().lower() == target_name.lower():
                _cached_calendar_id = item["id"]
                return _cached_calendar_id

        # 3. If not found, automatically create the dedicated sub-calendar
        new_calendar = service.calendars().insert(body={
            "summary": target_name,
            "description": "Dynamic task schedule managed by TaskPulse",
            "timeZone": Config.DEFAULT_TIME_ZONE,
        }).execute()
        _cached_calendar_id = new_calendar.get("id")
        return _cached_calendar_id
    except Exception as exc:
        raise RuntimeError(f"Could not locate or create dedicated sub-calendar '{target_name}': {exc}")


def is_calendar_connected() -> bool:
    """Checks whether valid Google Calendar credentials exist."""
    return get_calendar_service() is not None


def format_calendar_event(
    task: Dict[str, Any],
    checklist: str,
    start_at: datetime,
    end_at: datetime,
    timezone_name: str,
) -> Dict[str, Any]:
    """Formats event body according to TaskPulse rules."""
    is_deep_work = task.get("priority_rank") == 1 or str(task.get("priority")).lower() == "high"
    summary = f"[Deep Work] {task.get('content')}" if is_deep_work else task.get("content", "Untitled Task")

    parts = [
        f"Goal: {task.get('goal_id', 'General')}",
        f"Task: {task.get('content')}",
        f"Duration: {task.get('remaining_minutes') or task.get('estimated_minutes')} mins",
    ]
    if checklist:
        parts.append("Sub-tasks:\n" + checklist)

    return {
        "summary": summary,
        "description": "\n\n".join(parts),
        "start": {"dateTime": start_at.isoformat(), "timeZone": timezone_name},
        "end": {"dateTime": end_at.isoformat(), "timeZone": timezone_name},
        "colorId": "11" if is_deep_work else "9",  # Red for Deep Work, Blue for Standard
    }


if __name__ == "__main__":
    print("Initiating Google Calendar OAuth Authentication...")
    svc = get_calendar_service(allow_interactive=True)
    if svc:
        cal_id = get_or_create_target_calendar(svc)
        print(f"Successfully authenticated! Dedicated sub-calendar: '{Config.GOOGLE_CALENDAR_NAME}' (ID: {cal_id})")
    else:
        print("Authentication failed or cancelled.")

