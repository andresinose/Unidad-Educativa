from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.session import session_dir
from app.schemas.concordance import ConcordanceResult
from app.schemas.extraction import SilaboExtraction
from app.schemas.generation import GeneratedResource, GenerationRequest
from app.services.generation.orchestrator import generate_resource

router = APIRouter(tags=["generation"])


def _load_session_data(session_id: str) -> tuple[SilaboExtraction, ConcordanceResult]:
    work_dir = session_dir(session_id)
    silabo_file = work_dir / "silabo.json"
    concordance_file = work_dir / "concordance.json"
    if not silabo_file.exists() or not concordance_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada o expirada. Vuelva a analizar los documentos.",
        )
    silabo = SilaboExtraction.model_validate_json(silabo_file.read_text(encoding="utf-8"))
    concordance = ConcordanceResult.model_validate_json(concordance_file.read_text(encoding="utf-8"))
    return silabo, concordance


@router.post("/generate", response_model=GeneratedResource)
async def generate(request: GenerationRequest) -> GeneratedResource:
    silabo, concordance = _load_session_data(request.session_id)

    week = next((w for w in silabo.weeks if w.week_number == request.week_number), None)
    if week is None:
        raise HTTPException(status_code=404, detail=f"La semana {request.week_number} no existe en el sílabo analizado.")

    week_concordance = next((w for w in concordance.weeks if w.week_number == request.week_number), None)
    if week_concordance is None:
        raise HTTPException(status_code=404, detail=f"No hay resultado de concordancia para la semana {request.week_number}.")

    try:
        return generate_resource(week, week_concordance, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al generar el recurso con la IA: {exc}") from exc
