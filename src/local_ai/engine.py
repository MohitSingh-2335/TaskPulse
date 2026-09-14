from __future__ import annotations

import json
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

from src.config import Config
from src.local_ai.parser import INTAKE_SYSTEM_PROMPT, extract_json_payload, parse_brain_dump_heuristically
from src.local_ai.telemetry import TelemetryTracker


def _query_local_ollama(text: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Attempts to query a local Ollama instance if running."""
    url = f"{Config.LOCAL_OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {
        "model": Config.LOCAL_MODEL_NAME,
        "prompt": f"{INTAKE_SYSTEM_PROMPT}\n\nUser Brain Dump:\n{text}",
        "stream": False,
        "format": "json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                result = json.loads(resp.read().decode("utf-8"))
                response_text = result.get("response", "")
                return extract_json_payload(response_text)
    except Exception:
        return None
    return None


def _query_groq(text: str) -> Optional[Dict[str, Any]]:
    """Queries Groq API using the installed Groq SDK."""
    if not Config.GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=Config.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if content:
            return extract_json_payload(content)
    except Exception:
        return None
    return None


class AIEngine:
    """Unified inference engine with intelligent local-first and cloud fallback."""

    @classmethod
    def process_intake(cls, text: str) -> Dict[str, Any]:
        """Processes unstructured brain dump into a structured plan with telemetry."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        with TelemetryTracker(operation="intake_decomposition") as tracker:
            plan = None
            provider = "heuristic"
            model_name = "offline-rules"

            # 1. Try Local Ollama if configured
            if Config.AI_PROVIDER in ("auto", "local"):
                plan = _query_local_ollama(text)
                if plan:
                    provider = "local_ollama"
                    model_name = Config.LOCAL_MODEL_NAME

            # 2. Try Groq Cloud if local unavailable
            if not plan and Config.AI_PROVIDER in ("auto", "groq"):
                plan = _query_groq(text)
                if plan:
                    provider = "groq_cloud"
                    model_name = "llama-3.3-70b-versatile"

            # 3. Fallback to smart heuristic offline parser
            if not plan:
                plan = parse_brain_dump_heuristically(text)
                provider = "offline_heuristic"
                model_name = "heuristic-rule-engine"

            tracker.set_model(model_name)
            # Estimate word count
            tokens = len(text.split())
            tracker.set_tokens(prompt_tokens=tokens, completion_tokens=len(str(plan).split()))

            return {
                "plan": plan,
                "provider": provider,
                "model": model_name,
                "latency_ms": tracker.latency_ms,
            }
