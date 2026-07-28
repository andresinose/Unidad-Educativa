"""Ephemeral per-session working directories.

There is no database: a "session" is just a random id mapped to a folder under
WORK_DIR that holds the uploaded documents, their extracted structure, and any
generated exports for one analyze -> generate -> download cycle. Sessions are
deleted after the caller downloads their export, or after SESSION_TTL_SECONDS
on a best-effort sweep triggered from the health/cleanup endpoint.
"""
from __future__ import annotations

import secrets
import shutil
import time
from pathlib import Path

from app.core.config import SESSION_TTL_SECONDS, WORK_DIR


def new_session_id() -> str:
    return secrets.token_urlsafe(18)


def _is_safe_session_id(session_id: str) -> bool:
    # Defends session_dir() against path traversal from a caller-supplied id.
    return session_id.isalnum() or all(c.isalnum() or c in "-_" for c in session_id)


def session_dir(session_id: str) -> Path:
    if not session_id or not _is_safe_session_id(session_id):
        raise ValueError("invalid session id")
    d = WORK_DIR / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def random_filename(original_name: str) -> str:
    """Never trust the uploaded filename for storage — keep only the extension."""
    suffix = Path(original_name).suffix.lower()
    return f"{secrets.token_hex(16)}{suffix}"


def delete_session(session_id: str) -> None:
    d = WORK_DIR / session_id
    if d.exists() and d.is_dir():
        shutil.rmtree(d, ignore_errors=True)


def sweep_expired_sessions(ttl_seconds: int = SESSION_TTL_SECONDS) -> int:
    """Best-effort cleanup of stale session directories. Returns count removed."""
    if not WORK_DIR.exists():
        return 0
    now = time.time()
    removed = 0
    for child in WORK_DIR.iterdir():
        if not child.is_dir():
            continue
        try:
            age = now - child.stat().st_mtime
        except OSError:
            continue
        if age > ttl_seconds:
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed
