from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES
from app.core.session import new_session_id, random_filename, session_dir
from app.schemas.concordance import ConcordanceResult
from app.schemas.extraction import GuiaExtraction, SilaboExtraction
from app.services.concordance.engine import build_concordance
from app.services.parsing.docx_parser import parse_silabo_docx
from app.services.parsing.generic_fallback import (
    extract_raw_text,
    fallback_guia_extraction,
    fallback_silabo_extraction,
)
from app.services.parsing.pdf_parser import parse_guia_pdf

router = APIRouter(tags=["documents"])


class AnalyzeResponse(BaseModel):
    session_id: str
    silabo: SilaboExtraction
    guia: GuiaExtraction
    concordance: ConcordanceResult


def _validate_upload(f: UploadFile) -> str:
    ext = Path(f.filename or "").suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida: '{ext or 'sin extensión'}'. Use .docx o .pdf.",
        )
    return ext


async def _save_upload(f: UploadFile, dest_dir: Path, ext: str) -> Path:
    dest = dest_dir / random_filename(f"upload{ext}")
    size = 0
    with dest.open("wb") as out:
        while True:
            chunk = await f.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo permitido (50 MB).")
            out.write(chunk)
    return dest


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(silabo: UploadFile = File(...), guia: UploadFile = File(...)) -> AnalyzeResponse:
    """Uploads + parses both documents and returns their structure plus concordance.

    Nothing is persisted beyond the ephemeral session working directory — there
    is no database. `session_id` lets the caller reference the same uploaded
    files for a later /generate call in this iteration's scope.
    """
    silabo_ext = _validate_upload(silabo)
    guia_ext = _validate_upload(guia)

    session_id = new_session_id()
    work_dir = session_dir(session_id)

    silabo_path = await _save_upload(silabo, work_dir, silabo_ext)
    guia_path = await _save_upload(guia, work_dir, guia_ext)

    try:
        if silabo_ext == ".docx":
            silabo_data = parse_silabo_docx(silabo_path)
        else:
            silabo_data = fallback_silabo_extraction(extract_raw_text(silabo_path, silabo_ext))
    except Exception as exc:  # noqa: BLE001 — surfaced to the teacher, not a crash
        raise HTTPException(status_code=422, detail=f"No se pudo procesar el sílabo: {exc}") from exc

    try:
        if guia_ext == ".pdf":
            guia_data = parse_guia_pdf(guia_path)
        else:
            guia_data = fallback_guia_extraction(extract_raw_text(guia_path, guia_ext))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"No se pudo procesar la guía: {exc}") from exc

    concordance = build_concordance(silabo_data, guia_data)

    # Persisted only inside this session's ephemeral working directory (no DB) so
    # a later /generate call in the same session can ground itself on the same
    # validated data without re-uploading or re-parsing.
    (work_dir / "silabo.json").write_text(silabo_data.model_dump_json(), encoding="utf-8")
    (work_dir / "concordance.json").write_text(concordance.model_dump_json(), encoding="utf-8")

    return AnalyzeResponse(session_id=session_id, silabo=silabo_data, guia=guia_data, concordance=concordance)
