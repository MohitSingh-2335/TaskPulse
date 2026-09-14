from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from src.local_ai.telemetry import TelemetryTracker


def transcribe_audio_file(audio_path: Path) -> Dict[str, Any]:
    """Transcribes an audio file using local Whisper if installed."""
    with TelemetryTracker(operation="voice_transcription") as tracker:
        try:
            import whisper
            tracker.set_model("whisper-local")
            model = whisper.load_model(os.environ.get("WHISPER_MODEL", "base"))
            result = model.transcribe(str(audio_path), fp16=False)
            text = result.get("text", "").strip()
            return {"text": text, "status": "success", "engine": "whisper"}
        except ImportError:
            tracker.status = "error"
            tracker.error_message = "Whisper package is not installed."
            return {
                "text": "",
                "status": "error",
                "message": "Local Whisper is not installed. Use web browser voice dictation or install openai-whisper.",
            }
        except Exception as exc:
            tracker.status = "error"
            tracker.error_message = str(exc)
            return {"text": "", "status": "error", "message": str(exc)}
