"""Deterministic renderer: converts typed Pydantic blocks into clean, safe HTML fragments.
All user/model strings are explicitly escaped with html.escape.
Includes explicit inline styles for 100% Canvas LMS (Instructure) compatibility.
"""
from __future__ import annotations

import html
from app.services.material_builder.blocks import (
    Bloque,
    BloqueCaja,
    BloqueEjercicioRelleno,
    BloqueFigura,
    BloqueFlujo,
    BloqueLista,
    BloqueParrafo,
    BloquePeriodo,
    BloqueSubtitulo,
    BloqueTablaDatos,
    BloqueTablaGenerica,
    BloqueTituloSeccion,
    BloqueZonaTrabajo,
    PaginaTranscrita,
)


def _render_caja(b: BloqueCaja) -> str:
    color_styles = {
        "azul": "border-left: 5px solid #2563eb; background-color: #eff6ff; color: #1e3a8a;",
        "verde": "border-left: 5px solid #059669; background-color: #ecfdf5; color: #065f46;",
        "naranja": "border-left: 5px solid #d97706; background-color: #fef3c7; color: #78350f;",
        "amarillo": "border-left: 5px solid #d97706; background-color: #fef3c7; color: #78350f;",
        "rosa": "border-left: 5px solid #e11d48; background-color: #fff1f2; color: #881337;",
        "rojo": "border-left: 5px solid #dc2626; background-color: #fef2f2; color: #7f1d1d;",
        "morado": "border-left: 5px solid #9333ea; background-color: #faf5ff; color: #581c87;",
        "purpura": "border-left: 5px solid #9333ea; background-color: #faf5ff; color: #581c87;",
        "gris": "border-left: 5px solid #64748b; background-color: #f1f5f9; color: #0f172a;",
        "destacado": "border: 2px solid #6366f1; background-color: #eef2ff; color: #312e81; border-radius: 0.75rem;",
    }
    color_classes = {
        "azul": "border-l-4 border-blue-600 bg-blue-50/70 text-blue-950",
        "verde": "border-l-4 border-emerald-600 bg-emerald-50/70 text-emerald-950",
        "naranja": "border-l-4 border-amber-600 bg-amber-50/70 text-amber-950",
        "rosa": "border-l-4 border-rose-600 bg-rose-50/70 text-rose-950",
        "gris": "border-l-4 border-slate-500 bg-slate-100/80 text-slate-900",
        "destacado": "border-2 border-indigo-500 bg-indigo-50/80 text-indigo-950 shadow-sm",
        "morado": "border-l-4 border-purple-600 bg-purple-50/70 text-purple-950",
        "purpura": "border-l-4 border-purple-600 bg-purple-50/70 text-purple-950",
        "rojo": "border-l-4 border-red-600 bg-red-50/70 text-red-950",
        "amarillo": "border-l-4 border-amber-500 bg-amber-50/70 text-amber-950",
    }
    style_key = (b.estilo or "azul").lower().strip()
    style_inline = color_styles.get(style_key, color_styles["azul"])
    style_cls = color_classes.get(style_key, color_classes["azul"])

    header_html = (
        f'<div style="font-weight: 700; font-size: 0.875rem; margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em;" class="font-bold text-sm mb-1 uppercase tracking-wide">{html.escape(b.titulo)}</div>'
        if b.titulo
        else ""
    )
    return (
        f'<div style="margin: 1rem 0; padding: 1rem 1.25rem; border-top-right-radius: 0.75rem; border-bottom-right-radius: 0.75rem; {style_inline}" class="caja-info my-4 p-4 rounded-r-xl {style_cls}">'
        f"{header_html}"
        f'<div style="font-size: 0.875rem; line-height: 1.6;" class="text-sm leading-relaxed">{html.escape(b.contenido)}</div>'
        f"</div>"
    )


def _render_ejercicio(b: BloqueEjercicioRelleno, page_num: int) -> str:
    items_html = []
    for idx, item in enumerate(b.items):
        item_id = f"pg{page_num}-e{idx+1}"
        q_text = html.escape(item.pregunta)
        ans_text = html.escape(item.respuesta.strip())
        
        if item.tipo == "cerrada" and item.opciones:
            opts_html = []
            for opt_idx, opt in enumerate(item.opciones):
                opt_esc = html.escape(opt)
                opts_html.append(
                    f'<label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; background-color: #ffffff; margin-bottom: 0.375rem; cursor: pointer; font-size: 0.875rem; color: #0f172a;" class="flex items-center gap-2 p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer text-sm mb-1.5 transition-colors">'
                    f'<input type="radio" name="{item_id}" value="{opt_esc}" class="accent-blue-700" data-answer="{ans_text}">'
                    f'<span>{opt_esc}</span>'
                    f'</label>'
                )
            input_section = f'<div style="margin: 0.5rem 0;" class="options-group my-2">{"".join(opts_html)}</div>'
        else:
            input_section = (
                f'<div style="margin: 0.5rem 0;" class="my-2">'
                f'<input type="text" id="{item_id}-input" data-answer="{ans_text}" '
                f'placeholder="Escribe tu respuesta aquí..." '
                f'style="width: 100%; max-width: 28rem; padding: 0.5rem 0.75rem; font-size: 0.875rem; border: 1px solid #cbd5e1; border-radius: 0.5rem; outline: none; background-color: #ffffff; color: #0f172a;" '
                f'class="w-full max-w-md px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-all" />'
                f'</div>'
            )

        feedback_html = (
            f'<div id="{item_id}-feedback" style="display: none; margin-top: 0.5rem; font-size: 0.75rem; font-weight: 600; padding: 0.5rem; border-radius: 0.5rem;" class="feedback-msg hidden mt-2 text-xs font-semibold p-2 rounded-lg"></div>'
        )

        items_html.append(
            f'<div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 0.75rem; margin-bottom: 0.75rem;" class="ejercicio-item bg-slate-50 border border-slate-200 p-4 rounded-xl mb-3 shadow-2xs" data-item-id="{item_id}">'
            f'<div style="font-weight: 600; color: #1e293b; font-size: 0.875rem; margin-bottom: 0.5rem;" class="font-semibold text-slate-800 text-sm mb-2">{idx+1}. {q_text}</div>'
            f'{input_section}'
            f'{feedback_html}'
            f'</div>'
        )

    check_btn = (
        f'<button type="button" onclick="checkExercisePage({page_num})" '
        f'style="margin-top: 0.75rem; padding: 0.5rem 1rem; background-color: #1d4ed8; color: #ffffff; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; border-radius: 0.5rem; border: none; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;" '
        f'class="mt-3 px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs uppercase tracking-wider rounded-lg shadow-sm transition-all cursor-pointer flex items-center gap-2">'
        f'<span>✔ Comprobar respuestas</span>'
        f'</button>'
    ) if b.items else ""

    return (
        f'<div style="background-color: #ffffff; border: 2px solid #bfdbfe; border-radius: 1rem; padding: 1.25rem; margin: 1.5rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);" class="ejercicio-block bg-white border border-blue-200 rounded-2xl p-5 my-6 shadow-sm">'
        f'<h4 style="font-weight: 700; color: #1e3a8a; font-size: 0.875rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;" class="font-bold text-blue-900 text-sm mb-3 flex items-center gap-2">'
        f'<span style="padding: 0.125rem 0.5rem; background-color: #dbeafe; color: #1e40af; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 800;" class="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md text-xs font-extrabold">EJERCICIO</span>'
        f'<span>{html.escape(b.instrucciones)}</span>'
        f'</h4>'
        f'{"".join(items_html)}'
        f'{check_btn}'
        f'</div>'
    )


def _render_zona_trabajo(b: BloqueZonaTrabajo, page_num: int) -> str:
    zone_id = f"pg{page_num}-z1"
    bg_grid_cls = "bg-grid-pattern" if b.lineas_guia else "bg-white"
    bg_style = "background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 16px 16px; background-color: #ffffff;" if b.lineas_guia else "background-color: #ffffff;"

    return (
        f'<div style="border: 1px solid #cbd5e1; border-radius: 1rem; background-color: #ffffff; margin: 1.5rem 0; overflow: hidden;" class="zona-trabajo my-6 border border-slate-300 rounded-2xl bg-white overflow-hidden shadow-xs" id="{zone_id}">'
        f'<div style="background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0; padding: 0.625rem 1rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;" class="bg-slate-100 border-b border-slate-200 px-4 py-2.5 flex items-center justify-between flex-wrap gap-2">'
        f'  <span style="font-weight: 700; font-size: 0.75rem; text-transform: uppercase; color: #334155; display: flex; align-items: center; gap: 0.5rem;" class="font-bold text-xs uppercase tracking-wide text-slate-700 flex items-center gap-2">'
        f'    ✏️ {html.escape(b.instrucciones)}'
        f'  </span>'
        f'  <div style="display: flex; align-items: center; gap: 0.375rem;" class="flex items-center gap-1.5 tab-controls">'
        f'    <button type="button" style="padding: 0.25rem 0.625rem; font-size: 0.75rem; font-weight: 600; border-radius: 0.375rem; background-color: #ffffff; border: 1px solid #cbd5e1; color: #334155; cursor: pointer;" class="tab-btn active px-2.5 py-1 text-xs font-semibold rounded-md bg-white border border-slate-300 text-slate-700 shadow-2xs cursor-pointer" onclick="switchZoneTab(\'{zone_id}\', \'write\')">⌨ Escribir</button>'
        f'    <button type="button" style="padding: 0.25rem 0.625rem; font-size: 0.75rem; font-weight: 600; border-radius: 0.375rem; background-color: #e2e8f0; border: 1px solid transparent; color: #475569; cursor: pointer;" class="tab-btn px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-200 text-slate-600 hover:bg-white cursor-pointer" onclick="switchZoneTab(\'{zone_id}\', \'draw\')">🎨 Dibujar</button>'
        f'    <button type="button" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 600; color: #e11d48; border: none; background: none; cursor: pointer; margin-left: 0.5rem;" class="px-2 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-md cursor-pointer ml-2" onclick="clearZone(\'{zone_id}\')">🗑️ Limpiar</button>'
        f'  </div>'
        f'</div>'
        f'<div style="padding: 1rem; min-height: 160px; position: relative;" class="zone-body relative p-4 min-h-[160px]">'
        f'  <textarea id="{zone_id}-text" style="width: 100%; height: 9rem; padding: 0.75rem; font-size: 0.875rem; border: 1px solid #cbd5e1; border-radius: 0.75rem; outline: none; {bg_style} color: #0f172a;" class="write-mode w-full h-36 p-3 text-sm border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-600 resize-y {bg_grid_cls}" placeholder="Escribe tu razonamiento o respuesta aquí..."></textarea>'
        f'  <div style="width: 100%; height: 11rem; border: 1px solid #cbd5e1; border-radius: 0.75rem; overflow: hidden; position: relative; display: none; {bg_style}" class="draw-mode hidden relative w-full h-44 border border-slate-200 rounded-xl overflow-hidden {bg_grid_cls}">'
        f'    <canvas id="{zone_id}-canvas" style="width: 100%; height: 100%; cursor: crosshair;" class="w-full h-full cursor-crosshair"></canvas>'
        f'  </div>'
        f'</div>'
        f'</div>'
    )


def render_bloque(b: Bloque, page_num: int = 1) -> str:
    if b.tipo == "titulo_seccion":
        sub = f'<p style="color: #475569; font-size: 0.875rem; margin-top: 0.25rem;" class="text-slate-600 text-sm mt-1">{html.escape(b.subtitulo)}</p>' if b.subtitulo else ""
        return f'<header style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid #e2e8f0;" class="mb-6 pb-4 border-b border-slate-200"><h2 style="font-size: 1.5rem; font-weight: 800; color: #0a2f68; margin: 0; tracking: -0.025em;" class="text-2xl font-extrabold text-blue-950 tracking-tight">{html.escape(b.texto)}</h2>{sub}</header>'
    elif b.tipo == "periodo":
        return f'<div style="display: inline-block; padding: 0.25rem 0.75rem; margin: 0.5rem 0; background-color: #dbeafe; color: #1e40af; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; border-radius: 9999px;" class="inline-block px-3 py-1 my-2 bg-blue-100 text-blue-900 font-bold text-xs uppercase tracking-wider rounded-full">{html.escape(b.texto)}</div>'
    elif b.tipo == "subtitulo":
        return f'<h3 style="font-size: 1.125rem; font-weight: 700; color: #1e293b; margin: 1rem 0 0.5rem 0;" class="text-lg font-bold text-slate-800 my-4 tracking-tight">{html.escape(b.texto)}</h3>'
    elif b.tipo == "parrafo":
        return f'<p style="color: #334155; font-size: 0.875rem; line-height: 1.6; margin: 0.75rem 0;" class="text-slate-700 text-sm leading-relaxed my-3">{html.escape(b.texto)}</p>'
    elif b.tipo == "caja":
        return _render_caja(b)
    elif b.tipo == "lista":
        tag = "ol" if b.ordenada else "ul"
        cls = "list-decimal" if b.ordenada else "list-disc"
        list_style = "list-style-type: decimal;" if b.ordenada else "list-style-type: disc;"
        items = "".join(f'<li style="margin-bottom: 0.25rem; font-size: 0.875rem; color: #334155;" class="mb-1 text-sm text-slate-700">{html.escape(it)}</li>' for it in b.items)
        return f'<{tag} style="padding-left: 1.5rem; margin: 0.75rem 0; {list_style}" class="{cls} pl-6 my-3 space-y-1">{items}</{tag}>'
    elif b.tipo == "tabla_datos":
        ths = "".join(f'<th style="padding: 0.625rem 1rem; background-color: #0a2f68; color: #ffffff !important; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; text-align: left; border: 1px solid #0d3a80;" class="px-4 py-2.5 bg-blue-900 text-white font-semibold text-xs uppercase text-left">{html.escape(c)}</th>' for c in b.columnas)
        trs = []
        for r in b.filas:
            tds = "".join(f'<td style="padding: 0.5rem 1rem; border: 1px solid #e2e8f0; font-size: 0.75rem; color: #334155;" class="px-4 py-2 border-t border-slate-200 text-xs text-slate-700">{html.escape(cell)}</td>' for cell in r)
            trs.append(f'<tr>{tds}</tr>')
        return f'<div style="margin: 1rem 0; overflow-x: auto; border-radius: 0.75rem; border: 1px solid #e2e8f0;" class="my-4 overflow-x-auto rounded-xl border border-slate-200 shadow-2xs"><table style="width: 100%; border-collapse: collapse;" class="w-full border-collapse"><thead><tr>{ths}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
    elif b.tipo == "tabla_generica":
        trs = []
        for r in b.filas:
            tds = "".join(f'<td style="padding: 0.5rem 0.75rem; border: 1px solid #e2e8f0; font-size: 0.75rem; color: #334155;" class="px-3 py-2 border border-slate-200 text-xs text-slate-700">{html.escape(cell)}</td>' for cell in r)
            trs.append(f'<tr>{tds}</tr>')
        return f'<div style="margin: 1rem 0; overflow-x: auto;" class="my-4 overflow-x-auto"><table style="width: 100%; border-collapse: collapse;" class="w-full border-collapse"><tbody>{"".join(trs)}</tbody></table></div>'
    elif b.tipo == "figura":
        img_src = b.imagen_base64 if b.imagen_base64.startswith("data:") else f"data:image/webp;base64,{b.imagen_base64}" if b.imagen_base64 else ""
        img_tag = f'<img src="{img_src}" style="max-width: 100%; height: auto; border-radius: 0.75rem; border: 1px solid #e2e8f0; display: block; margin: 0 auto;" class="max-w-full h-auto rounded-xl shadow-sm border border-slate-200 mx-auto" alt="{html.escape(b.pie or "Ilustración")}" />' if img_src else ""
        caption = f'<figcaption style="text-align: center; font-size: 0.75rem; font-weight: 600; color: #64748b; margin-top: 0.5rem;" class="text-center text-xs font-semibold text-slate-500 mt-2">{html.escape(b.pie)}</figcaption>' if b.pie else ""
        return f'<figure style="margin: 1.25rem auto; text-align: center; width: {min(100, max(20, b.ancho_pct))}%;" class="my-5 text-center">{img_tag}{caption}</figure>'
    elif b.tipo == "flujo":
        steps = []
        for idx, p in enumerate(b.pasos):
            steps.append(
                f'<div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem; background-color: #ffffff; border: 1px solid #bfdbfe; border-radius: 0.75rem; flex: 1; min-width: 140px;" class="flex items-center gap-3 p-3 bg-white border border-blue-200 rounded-xl shadow-2xs flex-1 min-w-[140px]">'
                f'<span style="width: 1.5rem; height: 1.5rem; border-radius: 9999px; background-color: #1d4ed8; color: #ffffff; font-weight: 700; font-size: 0.75rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;" class="w-6 h-6 rounded-full bg-blue-700 text-white font-bold text-xs flex items-center justify-center shrink-0">{idx+1}</span>'
                f'<span style="font-size: 0.75rem; font-weight: 500; color: #1e293b;" class="text-xs font-medium text-slate-800">{html.escape(p)}</span>'
                f'</div>'
            )
        return f'<div style="margin: 1.25rem 0; display: flex; align-items: center; gap: 0.5rem; overflow-x: auto; padding: 0.5rem 0;" class="my-5 flex items-center gap-2 overflow-x-auto py-2">{"".join(steps)}</div>'
    elif b.tipo == "ejercicio_relleno":
        return _render_ejercicio(b, page_num)
    elif b.tipo == "zona_trabajo":
        return _render_zona_trabajo(b, page_num)
    return ""


def render_pagina(pagina: PaginaTranscrita) -> str:
    p_num = pagina.numero_pagina
    header_html = (
        f'<div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #f1f5f9; display: flex; items-center: center; justify-content: space-between;" class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center justify-between border-b border-slate-100 pb-2">'
        f'<span>{html.escape(pagina.encabezado or f"Página {p_num}")}</span>'
        f'<span style="padding: 0.125rem 0.5rem; background-color: #f1f5f9; color: #475569; border-radius: 0.25rem;" class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded">Pág. {p_num}</span>'
        f'</div>'
    )
    blocks_html = "".join(render_bloque(b, p_num) for b in pagina.bloques)
    
    return (
        f'<section style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 1.5rem; padding: 2rem; margin: 2rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); position: relative; overflow: hidden;" class="pagina bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 my-8 shadow-sm relative overflow-hidden" id="pagina-{p_num}" data-page="{p_num}">'
        f'{header_html}'
        f'{blocks_html}'
        f'<footer style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #f1f5f9; text-align: right; font-size: 0.75rem; font-weight: 600; color: #94a3b8;" class="mt-8 pt-4 border-t border-slate-100 text-right text-xs font-semibold text-slate-400">Página {p_num}</footer>'
        f'</section>'
    )
