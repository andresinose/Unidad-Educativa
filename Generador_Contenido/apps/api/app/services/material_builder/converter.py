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


def _clean_raw_input_dict(raw_input: Any, page_num: int = 1) -> dict:
    """Safely dereferences stringified JSON arrays/dicts emitted by LLM tool calls
    and normalizes block schemas so Pydantic validation never fails on missing, null (None), or stringified fields."""
    if not isinstance(raw_input, dict):
        if isinstance(raw_input, list):
            raw_input = {"bloques": raw_input}
        else:
            raw_input = {}

    raw_input["numero_pagina"] = int(raw_input.get("numero_pagina") or page_num)
    enc = raw_input.get("encabezado")
    raw_input["encabezado"] = str(enc) if enc is not None else f"Página {page_num}"

    raw_bloques = raw_input.get("bloques")
    if isinstance(raw_bloques, str):
        try:
            raw_bloques = json.loads(raw_bloques)
        except Exception:
            raw_bloques = []

    if not isinstance(raw_bloques, list):
        raw_bloques = []

    cleaned_bloques = []
    for b in raw_bloques:
        if isinstance(b, str):
            try:
                b = json.loads(b)
            except Exception:
                b = {"tipo": "parrafo", "texto": b}

        if not isinstance(b, dict):
            if b is not None:
                cleaned_bloques.append({"tipo": "parrafo", "texto": str(b)})
            continue

        # Normalización de alias de tipo
        raw_tipo = str(b.get("tipo") or "").lower().strip()
        if raw_tipo in ["titulo_seccion", "titulo", "header", "encabezado", "title", "seccion"]:
            tipo = "titulo_seccion"
        elif raw_tipo in ["periodo", "period"]:
            tipo = "periodo"
        elif raw_tipo in ["subtitulo", "subtitle"]:
            tipo = "subtitulo"
        elif raw_tipo in ["parrafo", "paragraph", "text", "texto"]:
            tipo = "parrafo"
        elif raw_tipo in ["caja", "box", "callout", "nota"]:
            tipo = "caja"
        elif raw_tipo in ["lista", "list", "bullets"]:
            tipo = "lista"
        elif raw_tipo in ["tabla_datos", "tabla", "table", "tabla_informacion"]:
            tipo = "tabla_datos" if (b.get("columnas") or b.get("headers")) else "tabla_generica"
        elif raw_tipo in ["tabla_generica", "grid"]:
            tipo = "tabla_generica"
        elif raw_tipo in ["figura", "figure", "image", "imagen"]:
            tipo = "figura"
        elif raw_tipo in ["flujo", "flow", "pasos", "steps"]:
            tipo = "flujo"
        elif raw_tipo in ["ejercicio_relleno", "ejercicio", "quiz", "pregunta", "preguntas"]:
            tipo = "ejercicio_relleno"
        elif raw_tipo in ["zona_trabajo", "work_zone", "espacio"]:
            tipo = "zona_trabajo"
        else:
            if b.get("columnas") or b.get("headers"):
                tipo = "tabla_datos"
            elif b.get("filas") or b.get("rows"):
                tipo = "tabla_generica"
            elif b.get("pasos") or b.get("steps"):
                tipo = "flujo"
            elif b.get("items") or b.get("opciones"):
                tipo = "lista"
            elif b.get("contenido"):
                tipo = "caja"
            else:
                tipo = "parrafo"

        b["tipo"] = tipo

        # Limpieza específica por tipo
        if tipo in ["titulo_seccion", "periodo", "subtitulo", "parrafo"]:
            b["texto"] = str(b.get("texto") or b.get("content") or b.get("contenido") or b.get("titulo") or b.get("subtitulo") or "Sección")
            if tipo == "titulo_seccion":
                b["subtitulo"] = str(b.get("subtitulo") or "")
            cleaned_bloques.append(b)

        elif tipo == "caja":
            b["estilo"] = str(b.get("estilo") or "azul")
            b["titulo"] = str(b.get("titulo") or "")
            b["contenido"] = str(b.get("contenido") or b.get("texto") or b.get("descripcion") or "Nota")
            cleaned_bloques.append(b)

        elif tipo == "lista":
            b["ordenada"] = bool(b.get("ordenada", False))
            items_raw = b.get("items") or b.get("bullets") or []
            if isinstance(items_raw, str):
                try: items_raw = json.loads(items_raw)
                except Exception: items_raw = [items_raw]
            if not isinstance(items_raw, list):
                items_raw = [str(items_raw)]
            b["items"] = [str(it if it is not None else "") for it in items_raw if it is not None]
            if not b["items"]:
                b["items"] = ["Elemento"]
            cleaned_bloques.append(b)

        elif tipo in ["tabla_datos", "tabla_generica"]:
            filas_raw = b.get("filas") or b.get("rows") or b.get("data") or []
            if isinstance(filas_raw, str):
                try: filas_raw = json.loads(filas_raw)
                except Exception: filas_raw = []
            if not isinstance(filas_raw, list):
                filas_raw = []

            cleaned_filas = []
            for r in filas_raw:
                if isinstance(r, dict):
                    row_vals = [str(v if v is not None else "") for v in r.values()]
                    cleaned_filas.append(row_vals if row_vals else ["Dato"])
                elif isinstance(r, list):
                    cleaned_filas.append([str(col if col is not None else "") for col in r])
                elif r is not None:
                    cleaned_filas.append([str(r)])
            
            b["filas"] = cleaned_filas if cleaned_filas else [["Dato"]]

            if tipo == "tabla_datos":
                cols_raw = b.get("columnas") or b.get("headers") or []
                if isinstance(cols_raw, str):
                    try: cols_raw = json.loads(cols_raw)
                    except Exception: cols_raw = []
                if not isinstance(cols_raw, list):
                    cols_raw = []
                b["columnas"] = [str(c if c is not None else "") for c in cols_raw] if cols_raw else ["Columna 1"]
            cleaned_bloques.append(b)

        elif tipo == "figura":
            b["imagen_base64"] = str(b.get("imagen_base64") or "")
            b["pie"] = str(b.get("pie") or b.get("caption") or "")
            b["ancho_pct"] = int(b.get("ancho_pct") or 80)
            cleaned_bloques.append(b)

        elif tipo == "flujo":
            pasos_raw = b.get("pasos") or b.get("steps") or []
            if isinstance(pasos_raw, str):
                try: pasos_raw = json.loads(pasos_raw)
                except Exception: pasos_raw = []
            if not isinstance(pasos_raw, list):
                pasos_raw = []
            b["pasos"] = [str(p if p is not None else "") for p in pasos_raw if p is not None] or ["Paso 1"]
            cleaned_bloques.append(b)

        elif tipo == "ejercicio_relleno":
            b["instrucciones"] = str(b.get("instrucciones") or "Responde las siguientes preguntas:")
            items_raw = b.get("items") or b.get("preguntas") or []
            if isinstance(items_raw, str):
                try: items_raw = json.loads(items_raw)
                except Exception: items_raw = []
            if not isinstance(items_raw, list):
                items_raw = []
            
            cleaned_items = []
            for it in items_raw:
                if isinstance(it, dict):
                    opts_raw = it.get("opciones") or it.get("options") or []
                    if isinstance(opts_raw, str):
                        try: opts_raw = json.loads(opts_raw)
                        except Exception: opts_raw = []
                    if not isinstance(opts_raw, list):
                        opts_raw = []
                    cleaned_items.append({
                        "id": str(it.get("id") or ""),
                        "pregunta": str(it.get("pregunta") or it.get("question") or "Pregunta"),
                        "tipo": str(it.get("tipo") or "cerrada"),
                        "opciones": [str(o if o is not None else "") for o in opts_raw],
                        "respuesta": str(it.get("respuesta") or it.get("correct") or ""),
                        "explicacion": str(it.get("explicacion") or ""),
                        "puntos": int(it.get("puntos") or 1),
                    })
            b["items"] = cleaned_items
            cleaned_bloques.append(b)

        elif tipo == "zona_trabajo":
            b["instrucciones"] = str(b.get("instrucciones") or "Zona de trabajo para resolver ejercicios:")
            b["modo"] = str(b.get("modo") or "escritura_y_dibujo")
            b["lineas_guia"] = bool(b.get("lineas_guia", True))
            cleaned_bloques.append(b)

    raw_input["bloques"] = cleaned_bloques
    return raw_input


def _transcribe_page_gemini(png_bytes: bytes, page_num: int) -> PaginaTranscrita | None:
    """Calls Gemini Vision API to transcribe page PNG bytes into structured PaginaTranscrita."""
    api_key = (GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")).strip()
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            f"Transcribe con alta precisión pedagógica la página {page_num} del PDF adjunto a bloques didácticos en formato JSON estricto.\n"
            "Esquema JSON esperado: {\"numero_pagina\": N, \"encabezado\": \"...\", \"bloques\": [{\"tipo\": \"parrafo|titulo_seccion|subtitulo|caja|lista|tabla_datos|ejercicio_relleno|zona_trabajo\", ...}]}\n"
            "Convierte cualquier ejercicio o pregunta en un bloque 'ejercicio_relleno' con opciones u opción de respuesta correcta.\n"
            "Si hay zonas de trabajo o espacio libre para resolver, incluye un bloque 'zona_trabajo'."
        )

        models_to_try = [GEMINI_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
        seen = set()
        models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

        response = None
        last_err = None
        for m in models_to_try:
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=[
                            types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                            prompt,
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1,
                        ),
                    )
                    if response:
                        break
                except Exception as e:
                    last_err = e
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                        import time
                        wait_sec = 10 * (attempt + 1)
                        print(f"Reintento {attempt + 1}/3 por límite de peticiones (429) en Gemini (página {page_num}). Esperando {wait_sec}s...")
                        time.sleep(wait_sec)
                        continue
                    break
            if response:
                break

        if response:
            try:
                from app.core.usage_tracker import record_llm_usage
                um = getattr(response, "usage_metadata", None)
                if um:
                    record_llm_usage(
                        provider="gemini",
                        model=m,
                        feature="transcripcion_pdf_ocr",
                        prompt_tokens=getattr(um, "prompt_token_count", 0) or 0,
                        completion_tokens=getattr(um, "candidates_token_count", 0) or 0,
                        metadata={"page_num": page_num},
                    )
            except Exception:
                pass

        if response and response.text:
            clean_text = response.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()

            try:
                raw_dict = json.loads(clean_text)
            except Exception:
                raw_dict = {"bloques": [{"tipo": "parrafo", "texto": clean_text}]}

            raw_dict = _clean_raw_input_dict(raw_dict, page_num=page_num)

            try:
                return PaginaTranscrita.model_validate(raw_dict)
            except Exception as val_err:
                print(f"Advertencia de validación Pydantic en Gemini (página {page_num}): {val_err}")
                return PaginaTranscrita(
                    numero_pagina=page_num,
                    encabezado=str(raw_dict.get("encabezado") or f"Página {page_num}"),
                    bloques=[{"tipo": "parrafo", "texto": str(raw_dict)}]
                )
        elif last_err:
            print(f"Error en Gemini Visión (página {page_num}): {last_err}")
    except Exception as exc:
        print(f"Error general en Gemini Visión (página {page_num}): {exc}")
        pass
    return None



def _default_claude_transcribe_page(page_png_bytes: bytes, page_num: int, model_name: str = "claude-sonnet-4-6") -> PaginaTranscrita:
    """Calls Gemini or Claude Vision to transcribe one PDF page into structured Pydantic blocks."""
    # 1. Try Gemini Vision first if GEMINI_API_KEY is configured
    gemini_res = _transcribe_page_gemini(page_png_bytes, page_num)
    if gemini_res:
        return gemini_res

    gemini_key = (GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")).strip()
    anthropic_key = (ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")).strip()

    if gemini_key and not anthropic_key:
        print(f"Aviso: Página {page_num} procesada con texto simplificado por límite temporal de cuota en Gemini Free Tier.")
        return PaginaTranscrita(
            numero_pagina=page_num,
            encabezado=f"Página {page_num}",
            bloques=[
                {
                    "tipo": "caja",
                    "estilo": "naranja",
                    "titulo": f"Página {page_num}",
                    "contenido": "Esta página superó la velocidad máxima de la cuota gratuita de Gemini (15 peticiones/minuto). Por favor espera un minuto para procesar más páginas.",
                }
            ],
        )

    if not gemini_key and not anthropic_key:
        raise RuntimeError(
            "No se ha configurado ninguna API Key de Visión (GEMINI_API_KEY o ANTHROPIC_API_KEY) para la digitalización de PDFs. Por favor reinicia el servidor para cargar las variables del archivo .env."
        )

    api_key = anthropic_key

    if not api_key:
        raise RuntimeError(
            "Se alcanzó el límite de peticiones de la API gratuita de Gemini (429 Rate Limit - 15 solicitudes por minuto). Espera 1 minuto antes de convertir otro PDF o usa una API Key con cuota extendida."
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

        if p_idx < total_pages - 1:
            import time
            time.sleep(4.2)  # Pacing de 4.2s para mantenerse por debajo del límite de 15 RPM de Gemini Free Tier

    doc.close()

    # 3. Assemble shell and ZIP package
    final_html = build_material_shell(metadatos, rendered_pages)
    zip_bytes = build_material_zip_bytes(metadatos, rendered_pages)
    return final_html, zip_bytes, metadatos
