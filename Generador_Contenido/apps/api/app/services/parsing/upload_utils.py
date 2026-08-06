from __future__ import annotations

from pathlib import Path
from fastapi import HTTPException, UploadFile

from app.core.config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES
from app.core.session import random_filename


def validate_upload_bytes(file_path: Path, ext: str) -> None:
    """Valida los Magic Bytes del archivo según la especificación v1.2 (Sección 3.1)."""
    with file_path.open("rb") as f:
        header = f.read(8)

    if ext == ".docx":
        if not header.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=415,
                detail="El archivo .docx no tiene una firma ZIP/Word válida (Magic Bytes PK\x03\x04)."
            )
    elif ext == ".pdf":
        if not header.startswith(b"%PDF"):
            raise HTTPException(
                status_code=415,
                detail="El archivo .pdf no tiene una firma PDF válida (Magic Bytes %PDF)."
            )
        # Chequeo de PDF escaneado (sin capa de texto)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                if pdf.pages:
                    txt = pdf.pages[0].extract_text() or ""
                    if len(txt.strip()) < 50:
                        raise HTTPException(
                            status_code=422,
                            detail="El PDF no contiene texto seleccionable; suba la versión digital."
                        )
                else:
                    raise HTTPException(
                        status_code=422,
                        detail="El PDF no contiene texto seleccionable; suba la versión digital."
                    )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="El PDF no contiene texto seleccionable; suba la versión digital."
            )


def validate_upload(f: UploadFile) -> str:
    ext = Path(f.filename or "").suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida: '{ext or 'sin extensión'}'. Use .docx o .pdf.",
        )
    return ext


async def save_upload(f: UploadFile, dest_dir: Path, ext: str) -> Path:
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

    validate_upload_bytes(dest, ext)
    return dest
