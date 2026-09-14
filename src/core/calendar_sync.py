from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from src.config import Config

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_calendar_credentials():
    """Retrieves or refreshes Google OAuth2 Credentials."""
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
        else:
            # Full OAuth flow needed - only if credentials.json is present
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


def get_calendar_service():
    """Builds and returns the Google Calendar API Resource client."""
    creds = get_calendar_credentials()
    if not creds:
        return None
    try:
        from googleapiclient.discovery import build
        return build("calendar", "v3", credentials=creds)
    except Exception:
        return None


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
