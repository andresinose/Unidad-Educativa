"""Background jobs manager: handles asynchronous PDF conversion jobs in daemon threads.
Stores resulting HTML files, ZIP packages, and metadata JSON in var/materials_convertidos/ with 6-hour TTL sweeping.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import threading
import time
import uuid
import zipfile
from typing import Optional, TypedDict

from app.core.config import BASE_DIR, SESSION_TTL_SECONDS
from app.services.material_builder.converter import convert_pdf_to_interactive_html
from app.services.material_builder.shell import (
    DEFAULT_CSS,
    DEFAULT_JS,
    build_canvas_simple_html,
)

CONVERTED_DIR = os.path.join(BASE_DIR, "var", "materials_convertidos")
os.makedirs(CONVERTED_DIR, exist_ok=True)


class JobState(TypedDict):
    id: str
    estado: str  # 'procesando' | 'completado' | 'error'
    pagina_actual: int
    total_paginas: int
    material_id: Optional[str]
    error: Optional[str]
    created_at: float


_JOBS: dict[str, JobState] = {}
_JOBS_LOCK = threading.Lock()


def crear_job() -> str:
    job_id = str(uuid.uuid4())
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "id": job_id,
            "estado": "procesando",
            "pagina_actual": 0,
            "total_paginas": 0,
            "material_id": None,
            "error": None,
            "created_at": time.time(),
        }
    return job_id


def obtener_job(job_id: str) -> Optional[JobState]:
    with _JOBS_LOCK:
        return _JOBS.get(job_id)


def _ejecutar_conversion(job_id: str, pdf_bytes: bytes, original_filename: str) -> None:
    try:
        def on_progress(page_num: int, total_pages: int):
            with _JOBS_LOCK:
                if job_id in _JOBS:
                    _JOBS[job_id]["pagina_actual"] = page_num
                    _JOBS[job_id]["total_paginas"] = total_pages

        final_html, zip_bytes, metadatos = convert_pdf_to_interactive_html(
            pdf_bytes=pdf_bytes,
            original_filename=original_filename,
            progress_callback=on_progress,
        )

        material_id = str(uuid.uuid4())[:8]
        html_path = os.path.join(CONVERTED_DIR, f"{material_id}.html")
        zip_path = os.path.join(CONVERTED_DIR, f"{material_id}.zip")
        json_path = os.path.join(CONVERTED_DIR, f"{material_id}.json")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        meta_dict = {
            "id": material_id,
            "title": metadatos.titulo,
            "subject": metadatos.materia,
            "grade": metadatos.grado,
            "unit": metadatos.unidad,
            "teacher": metadatos.docente,
            "term": metadatos.periodo,
            "pages": metadatos.total_paginas,
            "filename": f"{material_id}.html",
            "source": "convertido",
            "created_at": time.time(),
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, ensure_ascii=False, indent=2)

        with _JOBS_LOCK:
            if job_id in _JOBS:
                _JOBS[job_id]["estado"] = "completado"
                _JOBS[job_id]["material_id"] = material_id

    except Exception as exc:
        with _JOBS_LOCK:
            if job_id in _JOBS:
                _JOBS[job_id]["estado"] = "error"
                _JOBS[job_id]["error"] = str(exc)


def iniciar_conversion_async(pdf_bytes: bytes, original_filename: str) -> str:
    job_id = crear_job()
    t = threading.Thread(
        target=_ejecutar_conversion,
        args=(job_id, pdf_bytes, original_filename),
        daemon=True,
    )
    t.start()
    return job_id


def listar_convertidos() -> list[dict]:
    """Sweeps expired materials (TTL) and returns active converted materials."""
    limpiar_expirados()
    result = []
    if not os.path.exists(CONVERTED_DIR):
        return result

    for f in os.listdir(CONVERTED_DIR):
        if f.endswith(".json"):
            json_path = os.path.join(CONVERTED_DIR, f)
            try:
                with open(json_path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    result.append(data)
            except Exception:
                continue

    result.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return result


def ruta_convertido_html(material_id: str) -> Optional[str]:
    """Returns absolute path to converted HTML file if valid and exists."""
    clean_id = os.path.basename(material_id).replace(".html", "").replace(".zip", "").replace(".json", "")
    html_path = os.path.join(CONVERTED_DIR, f"{clean_id}.html")
    if os.path.exists(html_path):
        return html_path
    return None


def ruta_convertido_zip(material_id: str) -> Optional[str]:
    """Returns absolute path to converted ZIP file matching UEI Canvas LMS standards.
    Generates/re-generates zip if missing or incomplete."""
    clean_id = os.path.basename(material_id).replace(".html", "").replace(".zip", "").replace(".json", "")
    zip_path = os.path.join(CONVERTED_DIR, f"{clean_id}.zip")
    html_path = os.path.join(CONVERTED_DIR, f"{clean_id}.html")

    # Re-generate zip if it doesn't exist or is missing assets/ structure
    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                if "assets/css/styles.css" in names and "canvas-simple.html" in names:
                    return zip_path
        except Exception:
            pass

    if not os.path.exists(html_path):
        return None

    try:
        with open(html_path, "r", encoding="utf-8") as fp:
            html_content = fp.read()

        # Update stylesheet/script paths to assets/ subfolder if missing
        if "assets/css/styles.css" not in html_content:
            html_content = html_content.replace(
                'href="css/styles.css"', 'href="assets/css/styles.css"'
            )
            if "assets/css/styles.css" not in html_content:
                html_content = html_content.replace(
                    "<head>", '<head>\n  <link rel="stylesheet" href="assets/css/styles.css">'
                )

        if "assets/js/app.js" not in html_content:
            html_content = html_content.replace(
                'src="js/app.js"', 'src="assets/js/app.js"'
            )
            if "assets/js/app.js" not in html_content:
                html_content = html_content.replace(
                    "</body>", '  <script src="assets/js/app.js"></script>\n</body>'
                )

        title = "Material Educativo"
        subject = "General"
        grade = "UEI"
        json_path = os.path.join(CONVERTED_DIR, f"{clean_id}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jfp:
                    jdata = json.load(jfp)
                    title = jdata.get("title", title)
                    subject = jdata.get("subject", subject)
                    grade = jdata.get("grade", grade)
            except Exception:
                pass

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", html_content)
            zf.writestr(
                "canvas-simple.html",
                f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'><title>{title}</title>"
                f"<style>body{{font-family:Arial,sans-serif;margin:0;background:#f8fafc}}header{{padding:16px;background:#0a2f68;color:#fff;text-align:center}}main{{max-width:900px;margin:20px auto;padding:16px}}</style></head>"
                f"<body><header><strong>UEB Indoamérica · {title}</strong><br><small>Versión estática sin JS ({subject} - {grade})</small></header><main>{html_content}</main></body></html>",
            )
            zf.writestr("assets/css/styles.css", DEFAULT_CSS)
            zf.writestr("assets/js/app.js", DEFAULT_JS)
            zf.writestr(
                "INSTRUCCIONES_CANVAS.txt",
                f"PAQUETE HTML PARA CANVAS LMS — UNIDAD EDUCATIVA BILINGÜE INDOAMÉRICA\n"
                f"========================================================================\n"
                f"Material Educativo: {title}\n\n"
                f"Estructura del paquete:\n"
                f"- index.html: Versión completa interactiva con ejercicios y autoguardado.\n"
                f"- canvas-simple.html: Versión estática sin JavaScript para Canvas LMS.\n"
                f"- assets/css/styles.css: Hoja de estilos institucional.\n"
                f"- assets/js/app.js: Motor interactivo.\n\n"
                f"Pasos en Canvas LMS:\n"
                f"1. Sube este ZIP al área Archivos de tu curso en Canvas.\n"
                f"2. Descomprímelo manteniendo exactamente la carpeta assets/.\n"
                f"3. Agrega el enlace a index.html (o canvas-simple.html) en tu módulo.\n"
                f"========================================================================\n",
            )

        with open(zip_path, "wb") as f:
            f.write(buf.getvalue())

        return zip_path
    except Exception:
        return None


def limpiar_expirados(ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
    now = time.time()
    if not os.path.exists(CONVERTED_DIR):
        return

    for f in os.listdir(CONVERTED_DIR):
        file_path = os.path.join(CONVERTED_DIR, f)
        try:
            mtime = os.path.getmtime(file_path)
            if now - mtime > ttl_seconds:
                os.remove(file_path)
        except Exception:
            continue
