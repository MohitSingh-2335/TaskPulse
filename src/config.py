from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Base project directory (1 level up from src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_env_file(env_path: Optional[Path] = None) -> None:
    """Safely loads key-value pairs from .env into os.environ."""
    target_path = env_path or (PROJECT_ROOT / ".env")
    if not target_path.exists():
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(target_path)
    except ImportError:
        # Fallback zero-dependency .env parser
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val

# Auto-load on module import
load_env_file()


class Config:
    """Central configuration parameters with intelligent local defaults."""

    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # Storage Paths
    DATABASE_MODE: str = os.environ.get("DATABASE_MODE", "sqlite").lower()
    SQLITE_PATH: Path = PROJECT_ROOT / os.environ.get("SQLITE_DB_PATH", "data/task_engine.db")
    CHROMA_PERSIST_DIR: Path = PROJECT_ROOT / os.environ.get("CHROMA_PERSIST_DIR", "data/chroma")

    # Supabase (optional cloud store)
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

    # AI Configuration: 'auto', 'local', or 'groq'
    AI_PROVIDER: str = os.environ.get("AI_PROVIDER", "auto").lower()
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    LOCAL_OLLAMA_URL: str = os.environ.get("LOCAL_OLLAMA_URL", "http://localhost:11434")
    LOCAL_MODEL_NAME: str = os.environ.get("LOCAL_MODEL_NAME", "llama3:8b")

    # Calendar & Scheduling Defaults
    DEFAULT_TIME_ZONE: str = os.environ.get("DEFAULT_TIME_ZONE", "Asia/Kolkata")
    SCHEDULE_START_HOUR: int = int(os.environ.get("SCHEDULE_START_HOUR", "7"))
    SCHEDULE_BUFFER_MINUTES: int = int(os.environ.get("SCHEDULE_BUFFER_MINUTES", "15"))
    GOOGLE_CREDENTIALS_FILE: Path = PROJECT_ROOT / os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE: Path = PROJECT_ROOT / os.environ.get("GOOGLE_TOKEN_FILE", "token.json")

    # Server Settings
    PORT: int = int(os.environ.get("PORT", "5000"))
    HOST: str = os.environ.get("HOST", "127.0.0.1")
    DEBUG: bool = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes")

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensures that required directories (like data/) exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
