"""Converter pipeline: rasterizes PDF pages with PyMuPDF, extracts WebP base64 illustrations,
and calls Claude vision with forced Pydantic tool calling schema to transcribe pages to blocks.
"""
from __future__ import annotations

import base64
import io
import os
from typing import Callable, Optional
import fitz  # PyMuPDF
from PIL import Image

from app.core.config import ANTHROPIC_API_KEY, GEMINI_API_KEY, GEMINI_MODEL, GENERATION_MODEL, OPENROUTER_API_KEY
from app.services.material_builder.blocks import MetadatosMaterial, PaginaTranscrita
from app.services.material_builder.renderer import render_pagina
from app.services.material_builder.shell import build_material_shell


def rasterize_page_to_png_bytes(page: fitz.Page, dpi: int = 150) -> bytes:
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def extract_page_images_as_webp_base64(page: fitz.Page, max_width: int = 1100, quality: int = 78) -> list[str]:
    webp_list = []
    doc = page.parent
    img_list = page.get_images()
    for img_info in img_list[:4]:  # max 4 illustrations per page
        xref = img_info[0]
        try:
            base_img = doc.extract_image(xref)
            image_bytes = base_img["image"]
            img = Image.open(io.BytesIO(image_bytes))
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_h = int(float(img.height) * ratio)
                img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            img.save(out_buf, format="WEBP", quality=quality)
            b64_str = base64.b64encode(out_buf.getvalue()).decode("utf-8")
            webp_list.append(b64_str)
        except Exception:
            continue
    return webp_list


import json


def _clean_raw_input_dict(raw_input: dict) -> dict:
    """Safely dereferences stringified JSON arrays/dicts emitted by Claude tool calls
    and normalizes block schemas so Pydantic validation never fails on missing or stringified fields."""
    if isinstance(raw_input.get("bloques"), str):
        try:
            raw_input["bloques"] = json.loads(raw_input["bloques"])
        except Exception:
            raw_input["bloques"] = []

    if isinstance(raw_input.get("bloques"), list):
        cleaned_bloques = []
        for b in raw_input["bloques"]:
            if isinstance(b, str):
                try:
                    b = json.loads(b)
                except Exception:
                    continue
            if isinstance(b, dict):
                # Clean nested fields if serialized as strings
                for k in ["items", "opciones", "columnas", "filas", "pasos"]:
                    if k in b and isinstance(b[k], str):
                        try:
                            b[k] = json.loads(b[k])
                        except Exception:
                            pass

                tipo = b.get("tipo", "")
                if tipo == "caja":
                    if not b.get("contenido"):
                        b["contenido"] = b.get("texto") or b.get("descripcion") or b.get("titulo") or "Nota"
                elif tipo in ["titulo_seccion", "subtitulo", "parrafo", "periodo"]:
                    if not b.get("texto"):
                        b["texto"] = b.get("contenido") or b.get("titulo") or b.get("subtitulo") or "Sección"
                elif tipo == "lista":
                    if not b.get("items") or not isinstance(b["items"], list):
                        b["items"] = [str(b.get("items"))] if b.get("items") else ["Item"]
                elif tipo in ["tabla_datos", "tabla_generica"]:
                    if not b.get("filas") or not isinstance(b["filas"], list):
                        b["filas"] = [["Dato"]]
                    if tipo == "tabla_datos" and not b.get("columnas"):
                        b["columnas"] = ["Columna 1"]
                elif tipo == "flujo":
                    if not b.get("pasos") or not isinstance(b["pasos"], list):
                        b["pasos"] = ["Paso 1"]

                cleaned_bloques.append(b)
        raw_input["bloques"] = cleaned_bloques

    return raw_input


def _transcribe_page_gemini(png_bytes: bytes, page_num: int) -> PaginaTranscrita | None:
    """Calls Gemini Vision API to transcribe page PNG bytes into structured PaginaTranscrita."""
    if not GEMINI_API_KEY.strip():
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY.strip())
        prompt = (
            f"Transcribe con alta precisión pedagógica la página {page_num} del PDF adjunto a bloques didácticos en formato JSON estricto.\n"
            "Esquema JSON esperado: {\"numero_pagina\": N, \"encabezado\": \"...\", \"bloques\": [{\"tipo\": \"parrafo|titulo_seccion|subtitulo|caja|lista|tabla_datos|ejercicio_relleno|zona_trabajo\", ...}]}\n"
            "Convierte cualquier ejercicio o pregunta en un bloque 'ejercicio_relleno' con opciones u opción de respuesta correcta.\n"
            "Si hay zonas de trabajo o espacio libre para resolver, incluye un bloque 'zona_trabajo'."
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL or "gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        if response and response.text:
            clean_text = response.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()

            raw_dict = json.loads(clean_text)
            raw_dict["numero_pagina"] = page_num
            raw_dict = _clean_raw_input_dict(raw_dict)
            return PaginaTranscrita.model_validate(raw_dict)
    except Exception:
        pass
    return None


def _default_claude_transcribe_page(page_png_bytes: bytes, page_num: int, model_name: str = "claude-sonnet-4-6") -> PaginaTranscrita:
    """Calls Gemini or Claude Vision to transcribe one PDF page into structured Pydantic blocks."""
    # 1. Try Gemini Vision first if GEMINI_API_KEY is configured
    gemini_res = _transcribe_page_gemini(page_png_bytes, page_num)
    if gemini_res:
        return gemini_res

    api_key = ANTHROPIC_API_KEY.strip()
    if not api_key:
        raise RuntimeError(
            "No se ha configurado ninguna API Key de Visión (GEMINI_API_KEY o ANTHROPIC_API_KEY) para la digitalización de PDFs."
        )

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    png_b64 = base64.b64encode(page_png_bytes).decode("utf-8")
    tool_spec = {
        "name": "save_page_blocks",
        "description": "Guarda la transcripción estructurada de la página pedagógica en bloques didácticos.",
        "input_schema": PaginaTranscrita.model_json_schema(),
    }

    prompt = (
        f"Transcribe con alta precisión pedagógica la página {page_num} del PDF adjunto a bloques didácticos.\n"
        "Convierte cualquier ejercicio o pregunta en un bloque 'ejercicio_relleno' con opciones u opción de respuesta correcta.\n"
        "Si hay zonas de trabajo o espacio libre para resolver, incluye un bloque 'zona_trabajo'."
    )

    models_to_try = [model_name, "claude-sonnet-4-6", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    response = None
    last_error = None
    for m in models_to_try:
        try:
            response = client.messages.create(
                model=m,
                max_tokens=4000,
                tools=[tool_spec],
                tool_choice={"type": "tool", "name": "save_page_blocks"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": png_b64,
                                },
                            },
                        ],
                    }
                ],
            )
            if response:
                break
        except Exception as exc:
            last_error = exc
            continue

    if not response:
        raise RuntimeError(f"Fallo en la transcripción de la página {page_num}: {last_error}")

    for content in response.content:
        if getattr(content, "type", None) == "tool_use" and content.name == "save_page_blocks":
            raw_input = dict(content.input)
            raw_input["numero_pagina"] = page_num
            raw_input = _clean_raw_input_dict(raw_input)
            return PaginaTranscrita.model_validate(raw_input)

    return PaginaTranscrita(numero_pagina=page_num, encabezado=f"Página {page_num}")



def _default_claude_detect_metadata(cover_png_bytes: bytes, filename: str) -> MetadatosMaterial:
    """Calls Gemini or Claude Vision to extract material metadata (title, subject, grade, teacher) from cover."""
    if GEMINI_API_KEY.strip():
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=GEMINI_API_KEY.strip())
            res = client.models.generate_content(
                model=GEMINI_MODEL or "gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=cover_png_bytes, mime_type="image/png"),
                    "Extrae título, materia, grado, unidad y docente de esta portada educativa en JSON estricto con campos: titulo, materia, grado, unidad, docente.",
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            if res and res.text:
                clean_text = res.text.strip()
                if "```json" in clean_text:
                    clean_text = clean_text.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_text:
                    clean_text = clean_text.split("```")[1].split("```")[0].strip()
                return MetadatosMaterial.model_validate(json.loads(clean_text))
        except Exception:
            pass

    api_key = ANTHROPIC_API_KEY.strip()
    if not api_key:
        return MetadatosMaterial(titulo=os.path.splitext(filename)[0])

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    png_b64 = base64.b64encode(cover_png_bytes).decode("utf-8")
    tool_spec = {
        "name": "save_metadata",
        "description": "Extrae los metadatos institucionales del libro/folleto educativo.",
        "input_schema": MetadatosMaterial.model_json_schema(),
    }

    try:
        res = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            tools=[tool_spec],
            tool_choice={"type": "tool", "name": "save_metadata"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extrae título, materia, grado, unidad y docente del archivo:"},
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": png_b64},
                        },
                    ],
                }
            ],
        )
        for content in res.content:
            if getattr(content, "type", None) == "tool_use" and content.name == "save_metadata":
                return MetadatosMaterial.model_validate(content.input)
    except Exception:
        pass

    return MetadatosMaterial(titulo=os.path.splitext(filename)[0])


from app.services.material_builder.shell import build_material_shell, build_material_zip_bytes


def convert_pdf_to_interactive_html(
    pdf_bytes: bytes,
    original_filename: str = "documento.pdf",
    progress_callback: Optional[Callable[[int, int], None]] = None,
    transcriptor: Optional[Callable[[bytes, int], PaginaTranscrita]] = None,
    metadatos_fn: Optional[Callable[[bytes, str], MetadatosMaterial]] = None,
) -> tuple[str, bytes, MetadatosMaterial]:
    """Converts a PDF into an interactive HTML string and ZIP package bytes, returning (html_content, zip_bytes, metadata)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    if total_pages == 0:
        raise ValueError("El archivo PDF no contiene páginas.")

    # 1. Extract cover metadata
    cover_png = rasterize_page_to_png_bytes(doc[0], dpi=150)
    meta_func = metadatos_fn or (lambda p, fn: _default_claude_detect_metadata(p, fn))
    metadatos = meta_func(cover_png, original_filename)
    metadatos.total_paginas = total_pages

    # 2. Transcribe pages
    trans_func = transcriptor or (lambda png, pnum: _default_claude_transcribe_page(png, pnum, GENERATION_MODEL))

    rendered_pages = []
    for p_idx in range(total_pages):
        page_num = p_idx + 1
        page_obj = doc[p_idx]
        png_bytes = rasterize_page_to_png_bytes(page_obj, dpi=150)

        if progress_callback:
            progress_callback(page_num, total_pages)

        pagina_struct = trans_func(png_bytes, page_num)
        page_html = render_pagina(pagina_struct)
        rendered_pages.append(page_html)

    doc.close()

    # 3. Assemble shell and ZIP package
    final_html = build_material_shell(metadatos, rendered_pages)
    zip_bytes = build_material_zip_bytes(metadatos, rendered_pages)
    return final_html, zip_bytes, metadatos
