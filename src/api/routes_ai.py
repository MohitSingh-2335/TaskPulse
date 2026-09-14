from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.core.task_service import TaskService
from src.local_ai.engine import AIEngine
from src.local_ai.telemetry import get_telemetry_summary

ai_bp = Blueprint("ai_bp", __name__)


@ai_bp.route("/api/intake", methods=["POST"])
@ai_bp.route("/api/process-brain-dump", methods=["POST"])
def intake_endpoint():
    """Converts raw unstructured text into structured goals and tasks using Local/Groq AI."""
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "error": {"type": "ValidationError", "message": "text is required"}}), 400

    try:
        # 1. AI Decomposition
        inference_res = AIEngine.process_intake(text)
        plan_data = inference_res.get("plan")

        # 2. Persist to Database via TaskService
        service = TaskService()
        created_plan = service.create_goal_plan(plan_data, source=body.get("source", "intake"))

        return jsonify({
            "ok": True,
            "status": "success",
            "plan": created_plan,
            "telemetry": {
                "provider": inference_res.get("provider"),
                "model": inference_res.get("model"),
                "latency_ms": inference_res.get("latency_ms"),
            },
        }), 201
    except Exception as exc:
        return jsonify({"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), 500


@ai_bp.route("/api/telemetry", methods=["GET"])
def telemetry_endpoint():
    """Returns observability statistics and recent trace logs."""
    try:
        summary = get_telemetry_summary()
        return jsonify({"ok": True, "telemetry": summary}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
