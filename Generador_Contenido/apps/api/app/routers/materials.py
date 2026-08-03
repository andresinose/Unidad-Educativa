"""Materials router: endpoints for uploading PDFs, polling conversion jobs, listing materials,
and viewing or downloading generated interactive HTML documents.
"""
from __future__ import annotations

import os
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.core.config import MAX_UPLOAD_BYTES
from app.services.material_builder.jobs import (
    iniciar_conversion_async,
    listar_convertidos,
    obtener_job,
    ruta_convertido_html,
    ruta_convertido_zip,
)

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/upload")
async def upload_material_pdf(archivo: UploadFile = File(...)):
    if not archivo.filename or not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos en formato PDF (.pdf).",
        )

    content = await archivo.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el tamaño máximo permitido (50 MB).",
        )

    job_id = iniciar_conversion_async(content, archivo.filename)
    job = obtener_job(job_id)
    return job


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = obtener_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    return job


@router.get("")
async def list_materials():
    return listar_convertidos()


@router.get("/{material_id}/preview")
async def preview_material(material_id: str):
    html_path = ruta_convertido_html(material_id)
    if not html_path or not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Material no encontrado.")
    
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@router.get("/{material_id}/download")
async def download_material(material_id: str):
    html_path = ruta_convertido_html(material_id)
    if not html_path or not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Material no encontrado.")

    return FileResponse(
        path=html_path,
        filename=f"material_{material_id}.html",
        media_type="text/html",
    )


@router.get("/{material_id}/download-zip")
async def download_material_zip(material_id: str):
    zip_path = ruta_convertido_zip(material_id)
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Paquete ZIP no encontrado.")

    return FileResponse(
        path=zip_path,
        filename=f"material_{material_id}.zip",
        media_type="application/zip",
    )
