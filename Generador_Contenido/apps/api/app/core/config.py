"""Application configuration and paths. No database — everything is session-scoped on disk."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

# Root for ephemeral per-session working directories (uploads + generated exports).
WORK_DIR = Path(os.environ.get("WORK_DIR", BASE_DIR / "var" / "sessions"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

# Uploaded file constraints
ALLOWED_UPLOAD_EXTENSIONS = {".docx", ".pdf"}
ALLOWED_UPLOAD_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB, matches the UX copy already validated with the user

# How long a session's working directory is kept before cleanup, in seconds.
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", 60 * 60 * 6))  # 6h

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "claude-sonnet-5")

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
