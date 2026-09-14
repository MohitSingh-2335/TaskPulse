from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.core.calendar_sync import get_calendar_service
from src.core.task_service import TaskService

tasks_bp = Blueprint("tasks_bp", __name__)


def _service() -> TaskService:
    return TaskService()


@tasks_bp.route("/api/status", methods=["GET"])
@tasks_bp.route("/api/review", methods=["GET"])
def get_review_status():
    """Fetches full snapshot of scheduled, pending, and completed tasks."""
    try:
        snapshot = _service().review_snapshot()
        return jsonify({"ok": True, "status": "success", "review": snapshot}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), 500


@tasks_bp.route("/api/review", methods=["POST"])
def apply_review():
    """Applies bulk review updates (mark completed or roll over)."""
    body = request.get_json(silent=True) or {}
    updates = body.get("updates") or []
    try:
        result = _service().apply_review_updates(updates)
        return jsonify({"ok": True, "status": "success", "review": result}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), 400


@tasks_bp.route("/api/plan", methods=["POST"])
def create_direct_plan():
    """Creates a structured goal and task plan directly."""
    body = request.get_json(silent=True) or {}
    try:
        result = _service().create_goal_plan(body, source=body.get("source", "api"))
        return jsonify({"ok": True, "status": "success", "plan": result}), 201
    except Exception as exc:
        return jsonify({"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), 400


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task_endpoint(task_id: int):
    """Mutates specific fields of an existing task."""
    body = request.get_json(silent=True) or {}
    try:
        updated = _service().db.update_task(task_id, body)
        if not updated:
            return jsonify({"ok": False, "error": "Task not found"}), 404
        return jsonify({"ok": True, "status": "success", "task": updated}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), 400


@tasks_bp.route("/api/calendar/connect", methods=["POST", "GET"])
def calendar_connect():
    """Initiates interactive Google Calendar OAuth flow."""
    try:
        svc = get_calendar_service(allow_interactive=True)
        if svc:
            from src.core.calendar_sync import get_or_create_target_calendar
            cal_id = get_or_create_target_calendar(svc)
            return jsonify({"ok": True, "connected": True, "calendar_id": cal_id}), 200
        return jsonify({"ok": False, "error": "Calendar authentication could not be completed"}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@tasks_bp.route("/api/schedule", methods=["POST"])
def schedule_endpoint():
    """Calculates schedule for tomorrow, syncing to Google Calendar if available."""
    body = request.get_json(silent=True) or {}
    start_hour = int(body.get("start_hour", 7))
    buffer_minutes = int(body.get("buffer_minutes", 15))
    time_zone = body.get("time_zone")

    try:
        cal_service = get_calendar_service(allow_interactive=True)
        result = _service().schedule_pending_tasks(
            calendar_service=cal_service,
            start_hour=start_hour,
            buffer_minutes=buffer_minutes,
            timezone_name=time_zone,
        )
        return jsonify({
            "ok": True,
            "status": "success",
            "calendar_linked": cal_service is not None,
            "schedule": result,
        }), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), 500


@tasks_bp.route("/api/ideas", methods=["GET", "POST"])
def ideas_endpoint():
    """Quick capture idea inbox endpoint."""
    service = _service()
    if request.method == "GET":
        status = request.args.get("status", "Unread")
        ideas = service.db.list_ideas(status=status)
        return jsonify({"ok": True, "ideas": ideas}), 200

    body = request.get_json(silent=True) or {}
    content = body.get("content", "").strip()
    if not content:
        return jsonify({"ok": False, "error": "Idea content is required"}), 400

    created = service.log_idea(content, source=body.get("source", "web_quick_capture"))
    return jsonify({"ok": True, "idea": created}), 201
