from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app.core.session import new_session_id, session_dir
from app.schemas.extraction import SilaboExtraction, SilaboWeek
from app.schemas.generation import GeneratedResource, GenerationRequest, PedagogicalIntent
from app.services.export.pdf_export import export_resource_pdf
from app.services.generation.orchestrator import generate_resource
from app.services.parsing.docx_parser import parse_silabo_docx
from app.services.parsing.generic_fallback import extract_raw_text, fallback_silabo_extraction
from app.services.parsing.upload_utils import save_upload, validate_upload

router = APIRouter(prefix="/activities", tags=["activities"])


class ActivitiesUploadResponse(BaseModel):
    session_id: str
    silabo: SilaboExtraction


class ActivitiesGenerateRequest(BaseModel):
    session_id: str
    week_number: int
    resource_type: Literal["crossword", "logic_puzzle", "word_search", "flashcards"]
    extra_instructions: str = ""


@router.post("/upload", response_model=ActivitiesUploadResponse)
async def upload_activities_silabo(silabo: UploadFile = File(...)) -> ActivitiesUploadResponse:
    """Sube y parsea el documento de planificación/sílabo (.docx) para el módulo de actividades lúdicas."""
    silabo_ext = validate_upload(silabo)
    if silabo_ext != ".docx":
        raise HTTPException(
            status_code=400,
            detail="Para el generador de actividades lúdicas, debe subir un archivo .docx de planificación."
        )

    session_id = new_session_id()
    work_dir = session_dir(session_id)

    silabo_path = await save_upload(silabo, work_dir, silabo_ext)

    try:
        silabo_data = parse_silabo_docx(silabo_path)
    except Exception as exc:
        try:
            silabo_data = fallback_silabo_extraction(extract_raw_text(silabo_path, silabo_ext))
        except Exception as exc2:
            raise HTTPException(status_code=422, detail=f"No se pudo procesar el sílabo: {exc2}") from exc2

    (work_dir / "silabo.json").write_text(silabo_data.model_dump_json(), encoding="utf-8")

    return ActivitiesUploadResponse(session_id=session_id, silabo=silabo_data)


@router.get("/{session_id}/weeks")
async def get_activities_weeks(session_id: str) -> dict[str, Any]:
    """Obtiene la lista de semanas parseadas para una sesión dada."""
    work_dir = session_dir(session_id)
    silabo_json_path = work_dir / "silabo.json"
    if not silabo_json_path.exists():
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada.")

    silabo_data = SilaboExtraction.model_validate_json(silabo_json_path.read_text(encoding="utf-8"))
    return {"session_id": session_id, "weeks": [w.model_dump() for w in silabo_data.weeks]}


@router.post("/generate", response_model=GeneratedResource)
async def generate_activity(req: ActivitiesGenerateRequest) -> GeneratedResource:
    """Genera una actividad lúdica específica (crucigrama, rompecabezas de lógica, etc.) para la semana elegida."""
    work_dir = session_dir(req.session_id)
    silabo_json_path = work_dir / "silabo.json"
    if not silabo_json_path.exists():
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada.")

    silabo_data = SilaboExtraction.model_validate_json(silabo_json_path.read_text(encoding="utf-8"))
    
    target_week: SilaboWeek | None = None
    for w in silabo_data.weeks:
        if w.week_number == req.week_number:
            target_week = w
            break

    if not target_week:
        raise HTTPException(status_code=404, detail=f"No se encontró la Semana {req.week_number} en el sílabo.")

    tool_mapping = {
        "crossword": "build_crossword",
        "logic_puzzle": "build_logic_puzzle",
        "word_search": "build_word_search",
        "flashcards": "build_flashcards",
    }

    forced_tool = tool_mapping.get(req.resource_type, "build_crossword")

    gen_req = GenerationRequest(
        session_id=req.session_id,
        week_number=req.week_number,
        intent=PedagogicalIntent.reforzar,
        extra_instructions=req.extra_instructions,
    )

    try:
        resource = generate_resource(
            week=target_week,
            concordance=None,
            request=gen_req,
            forced_tool=forced_tool,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en la generación del recurso: {exc}") from exc

    (work_dir / "generated_resource.json").write_text(resource.model_dump_json(), encoding="utf-8")

    return resource


@router.get("/{session_id}/download/pdf")
async def download_activity_pdf(session_id: str) -> Response:
    """Descarga el recurso generado para la sesión en formato PDF oficial."""
    work_dir = session_dir(session_id)
    res_path = work_dir / "generated_resource.json"
    if not res_path.exists():
        raise HTTPException(status_code=404, detail="No hay ningún recurso generado en esta sesión.")

    resource = GeneratedResource.model_validate_json(res_path.read_text(encoding="utf-8"))
    pdf_bytes = export_resource_pdf(resource)

    import re, unicodedata
    raw_title = unicodedata.normalize('NFKD', resource.title).encode('ascii', 'ignore').decode('ascii')
    safe_title = re.sub(r'[^\w\s-]', '', raw_title).strip().replace(' ', '_')
    filename = f"Actividad_Semana_{resource.week_number}_{safe_title}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
