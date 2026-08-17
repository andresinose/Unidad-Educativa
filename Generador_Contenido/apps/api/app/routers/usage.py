from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query

from app.core.usage_tracker import clear_usage_history, get_usage_history, get_usage_summary

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary")
async def summary() -> dict[str, Any]:
    """Retorna un resumen global de peticiones, tokens y costo estimado en USD."""
    return get_usage_summary()


@router.get("/history")
async def history(
    limit: int = Query(default=100, ge=1, le=1000),
    feature: str | None = Query(default=None),
    provider: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Retorna el historial detallado de llamadas a los modelos LLM."""
    return get_usage_history(limit=limit, feature=feature, provider=provider)


@router.delete("/history")
async def reset_history() -> dict[str, str]:
    """Reinicia el historial de consumo."""
    clear_usage_history()
    return {"status": "ok", "message": "Historial de consumo reiniciado exitosamente."}
