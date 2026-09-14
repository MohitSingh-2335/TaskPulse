from __future__ import annotations

from pathlib import Path
from flask import Flask, jsonify, render_template
from flask_cors import CORS

from src.config import Config
from src.core.calendar_sync import is_calendar_connected
from src.core.database import get_database
from src.api.routes_tasks import tasks_bp
from src.api.routes_ai import ai_bp

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    """Application factory for TaskPulse."""
    Config.ensure_directories()

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "web" / "templates"),
        static_folder=str(BASE_DIR / "web" / "static"),
    )
    CORS(app)

    # Register API Blueprints
    app.register_blueprint(tasks_bp)
    app.register_blueprint(ai_bp)

    # Root Web Dashboard
    @app.route("/")
    def index():
        return render_template("index.html")

    # Health & Readiness Checks
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "ok": True,
            "status": "online",
            "service": "TaskPulse Engine",
            "version": "1.0.0",
        }), 200

    @app.route("/api/readiness", methods=["GET"])
    def readiness():
        try:
            db = get_database()
            db_report = db.get_readiness()
            cal_connected = is_calendar_connected()

            return jsonify({
                "ok": db_report.get("ready", True),
                "mode": db_report.get("mode", "sqlite"),
                "database": db_report,
                "calendar_connected": cal_connected,
            }), 200
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 503

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"ok": False, "error": "Route not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"ok": False, "error": "Internal server error"}), 500

    return app


# Default app instance
app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
