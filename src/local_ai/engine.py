from __future__ import annotations

import json
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

from src.local_ai.memory import get_memory_manager
from src.local_ai.parser import INTAKE_SYSTEM_PROMPT, extract_json_payload, parse_brain_dump_heuristically
from src.local_ai.telemetry import TelemetryTracker


def _query_local_ollama(text: str, memory_context: str = "", timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Attempts to query a local Ollama instance if running."""
    url = f"{Config.LOCAL_OLLAMA_URL.rstrip('/')}/api/generate"
    full_prompt = f"{INTAKE_SYSTEM_PROMPT}\n\n{memory_context}\n\nUser Brain Dump:\n{text}" if memory_context else f"{INTAKE_SYSTEM_PROMPT}\n\nUser Brain Dump:\n{text}"
    payload = {
        "model": Config.LOCAL_MODEL_NAME,
        "prompt": full_prompt,
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


def _query_groq(text: str, memory_context: str = "") -> Optional[Dict[str, Any]]:
    """Queries Groq API using the installed Groq SDK."""
    if not Config.GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=Config.GROQ_API_KEY)
        messages = [{"role": "system", "content": INTAKE_SYSTEM_PROMPT}]
        if memory_context:
            messages.append({"role": "system", "content": memory_context})
        messages.append({"role": "user", "content": text})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if content:
            return extract_json_payload(content)
    except Exception:
        return None
    return None


class AIEngine:
    """Unified inference engine with intelligent RAG memory, local-first and cloud fallback."""

    @classmethod
    def process_intake(cls, text: str) -> Dict[str, Any]:
        """Processes unstructured brain dump into a structured plan with RAG telemetry."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        with TelemetryTracker(operation="intake_decomposition") as tracker:
            plan = None
            provider = "heuristic"
            model_name = "offline-rules"

            # 1. Retrieve Semantic Memories from ChromaDB
            memory_mgr = get_memory_manager()
            retrieved_memories = memory_mgr.search_similar_tasks(text, top_k=3)
            memory_context = ""
            if retrieved_memories:
                mem_lines = ["Relevant Historical Memory (Past Experience):"]
                for m in retrieved_memories:
                    mem_lines.append(f"- {m['summary']}")
                mem_lines.append("Use these past patterns to calibrate realistic durations and priorities.")
                memory_context = "\n".join(mem_lines)

            # 2. Try Local Ollama if configured
            if Config.AI_PROVIDER in ("auto", "local"):
                plan = _query_local_ollama(text, memory_context=memory_context)
                if plan:
                    provider = "local_ollama"
                    model_name = Config.LOCAL_MODEL_NAME

            # 3. Try Groq Cloud if local unavailable
            if not plan and Config.AI_PROVIDER in ("auto", "groq"):
                plan = _query_groq(text, memory_context=memory_context)
                if plan:
                    provider = "groq_cloud"
                    model_name = "llama-3.3-70b-versatile"

            # 4. Fallback to smart heuristic offline parser
            if not plan:
                plan = parse_brain_dump_heuristically(text)
                provider = "offline_heuristic"
                model_name = "heuristic-rule-engine"

            tracker.set_model(model_name)
            tokens = len(text.split())
            tracker.set_tokens(prompt_tokens=tokens, completion_tokens=len(str(plan).split()))

            return {
                "plan": plan,
                "provider": provider,
                "model": model_name,
                "latency_ms": tracker.latency_ms,
                "memories_referenced": retrieved_memories,
            }
