"""PDF Exporter for Concordance Analysis Report and Generated Didactic Resources according to UEI standards.
Generates official, publication-quality PDF documents using ReportLab.
"""
from __future__ import annotations

import io
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.concordance import ConcordanceResult
from app.schemas.extraction import GuiaExtraction, SilaboExtraction
from app.schemas.generation import GeneratedResource, ResourceBlockType


def export_concordance_pdf(
    silabo: SilaboExtraction,
    guia: GuiaExtraction,
    concordance: ConcordanceResult,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    
    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0a2f68"),
        alignment=0,
    )
    
    header_subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#059669"),
        alignment=0,
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )

    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0a2f68"),
        spaceBefore=10,
        spaceAfter=6,
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )

    cell_bold_style = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    cell_th_style = ParagraphStyle(
        "TableTH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("UNIDAD EDUCATIVA BILINGÜE INDOAMÉRICA", header_subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("REPORTE OFICIAL DE VALIDACIÓN Y TRAZABILIDAD CURRICULAR", header_title_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#5ecfb1"), spaceAfter=12))

    # 2. Metadata Table
    meta_data = [
        [
            Paragraph("Asignatura:", meta_label_style),
            Paragraph(silabo.subject or guia.subject or "N/A", meta_val_style),
            Paragraph("Docente:", meta_label_style),
            Paragraph(silabo.teacher or "N/A", meta_val_style),
        ],
        [
            Paragraph("Grado / Curso:", meta_label_style),
            Paragraph(silabo.grade or guia.grade or "N/A", meta_val_style),
            Paragraph("Unidad Temática:", meta_label_style),
            Paragraph(silabo.unit_name or guia.unit_name or "N/A", meta_val_style),
        ],
        [
            Paragraph("Fechas Sílabo:", meta_label_style),
            Paragraph(f"{silabo.start_date} – {silabo.end_date}", meta_val_style),
            Paragraph("Páginas Guía:", meta_label_style),
            Paragraph(f"{guia.total_pages} páginas totales", meta_val_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[90, 180, 90, 180])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Veredicto Global Stamp
    veredicto_key = concordance.veredicto_global or "CUMPLE_PARCIAL"
    if veredicto_key == "CUMPLE":
        v_bg = colors.HexColor("#ecfdf5")
        v_border = colors.HexColor("#059669")
        v_txt = "VEREDICTO GLOBAL: CUMPLE (CONCORDANCIA COMPLETA)"
        v_color = colors.HexColor("#065f46")
    elif veredicto_key == "CUMPLE_PARCIAL":
        v_bg = colors.HexColor("#fef3c7")
        v_border = colors.HexColor("#d97706")
        v_txt = "VEREDICTO GLOBAL: CUMPLE PARCIAL"
        v_color = colors.HexColor("#78350f")
    else:
        v_bg = colors.HexColor("#fff1f2")
        v_border = colors.HexColor("#e11d48")
        v_txt = "VEREDICTO GLOBAL: NO CUMPLE"
        v_color = colors.HexColor("#881337")

    stamp_p = Paragraph(f"<b>{v_txt}</b><br/>{concordance.resumen}", ParagraphStyle(
        "StampText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=v_color,
        alignment=1,
    ))
    stamp_table = Table([[stamp_p]], colWidths=[540])
    stamp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), v_bg),
                ("BOX", (0, 0), (-1, -1), 2, v_border),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(stamp_table)
    story.append(Spacer(1, 14))

    # 4. Hallazgos e Incidencias Clave
    findings = concordance.key_findings or (concordance.semanas.observaciones if concordance.semanas else [])
    if findings:
        story.append(Paragraph("Hallazgos e Incidencias Clave", section_heading_style))
        find_items = []
        for f in findings:
            find_items.append([Paragraph("•", cell_bold_style), Paragraph(f, cell_style)])
        find_table = Table(find_items, colWidths=[15, 525])
        find_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(find_table)
        story.append(Spacer(1, 12))

    # 5. Matriz de Trazabilidad Curricular por Semana
    story.append(Paragraph("Matriz de Trazabilidad Curricular por Semana", section_heading_style))

    matrix_rows = [
        [
            Paragraph("Semana", cell_th_style),
            Paragraph("Tema Planificado en Sílabo", cell_th_style),
            Paragraph("Cobertura", cell_th_style),
            Paragraph("Veredicto Semana", cell_th_style),
        ]
    ]

    weeks_list = concordance.detalle_semanal or concordance.weeks or []
    for w in weeks_list:
        wn = w.semana if w.semana is not None else w.week_number
        topic = w.tema_silabo or w.topic
        cobertura_pct = round((w.matriz_subtemas.cobertura or 0) * 100) if w.matriz_subtemas else 0
        v_sem = w.veredicto_semana or w.status or "NO_CUMPLE"
        
        if v_sem in ("CUMPLE", "CONCORDANTE"):
            v_str = "<font color='#059669'><b>CUMPLE</b></font>"
        elif v_sem in ("CUMPLE_PARCIAL", "PARCIAL"):
            v_str = "<font color='#d97706'><b>PARCIAL</b></font>"
        else:
            v_str = "<font color='#e11d48'><b>NO CUMPLE</b></font>"

        matrix_rows.append(
            [
                Paragraph(f"<b>Semana {wn}</b>", cell_bold_style),
                Paragraph(topic, cell_style),
                Paragraph(f"{cobertura_pct}%", cell_style),
                Paragraph(v_str, cell_style),
            ]
        )

    matrix_table = Table(matrix_rows, colWidths=[65, 305, 70, 100])
    matrix_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a2f68")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(matrix_table)
    story.append(Spacer(1, 16))

    footer_p = Paragraph(
        "Documento generado automáticamente por la Plataforma Pedagógica Indoamérica · Validador de Trazabilidad Curricular v1.2",
        ParagraphStyle("FooterP", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7, leading=9, textColor=colors.HexColor("#94a3b8"), alignment=1),
    )
    story.append(footer_p)

    doc.build(story)
    return buffer.getvalue()


def export_resource_pdf(resource: GeneratedResource) -> bytes:
    """Exports a GeneratedResource (Sopa de Letras, Flashcards, Guía, Cuestionario) into a clean printable PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "ResTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0a2f68"),
        alignment=0,
    )

    subtitle_style = ParagraphStyle(
        "ResSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#059669"),
        alignment=0,
    )

    h2_style = ParagraphStyle(
        "ResH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0a2f68"),
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "ResBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    bold_cell = ParagraphStyle(
        "BoldCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=0,
    )

    grid_cell_style = ParagraphStyle(
        "GridCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#0a2f68"),
        alignment=1,
    )

    story = []
    story.append(Paragraph("UNIDAD EDUCATIVA BILINGÜE INDOAMÉRICA", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"Recurso Pedagógico: {resource.title}", title_style))
    story.append(Paragraph(f"Semana {resource.week_number} · Módulo 3 Herramientas Didácticas", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#5ecfb1"), spaceAfter=12))

    for block in resource.blocks:
        payload = block.payload or {}
        b_title = block.title or payload.get("title") or "Actividad Didáctica"
        story.append(Paragraph(f"📌 {b_title}", h2_style))

        if block.type == ResourceBlockType.word_search:
            instructions = payload.get("instructions") or "¡Encuentra las palabras clave en la cuadrícula!"
            story.append(Paragraph(instructions, body_style))
            story.append(Spacer(1, 6))

            words = payload.get("words") or []
            if words:
                words_str = "  ·  ".join(f"<b>{w}</b>" for w in words)
                story.append(Paragraph(f"<b>Palabras a buscar:</b> {words_str}", body_style))
                story.append(Spacer(1, 8))

            grid = payload.get("grid") or []
            if not grid and words:
                from app.mcp_server.tools.word_search import _generate_grid
                grid_size = payload.get("grid_size", 12)
                grid, _ = _generate_grid(words, size=grid_size)

            if grid:
                grid_table_data = []
                for row in grid:
                    row_cells = [Paragraph(f"<b>{ch}</b>", grid_cell_style) for ch in row]
                    grid_table_data.append(row_cells)
                
                num_cols = len(grid[0]) if grid else 1
                col_w = min(22, 500 // max(num_cols, 1))
                g_table = Table(grid_table_data, colWidths=[col_w] * num_cols)
                g_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#cbd5e1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ])
                )
                story.append(g_table)
                story.append(Spacer(1, 10))

        elif block.type == ResourceBlockType.flashcards:
            cards = payload.get("cards") or []
            if cards:
                card_rows = [[Paragraph("Término / Concepto", bold_cell), Paragraph("Definición / Explicación", bold_cell)]]
                for c in cards:
                    front = c.get("front") or c.get("term") or ""
                    back = c.get("back") or c.get("definition") or ""
                    card_rows.append([
                        Paragraph(f"<b>{front}</b>", body_style),
                        Paragraph(back, body_style)
                    ])
                c_table = Table(card_rows, colWidths=[180, 340])
                c_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a2f68")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ])
                )
                story.append(c_table)
                story.append(Spacer(1, 10))

        elif block.type == ResourceBlockType.interactive_activity:
            questions = payload.get("questions") or []
            for idx, q in enumerate(questions, 1):
                q_text = q.get("question_text") or q.get("pregunta") or ""
                story.append(Paragraph(f"<b>Pregunta {idx}:</b> {q_text}", body_style))
                opts = q.get("options") or q.get("opciones") or []
                for o_idx, opt in enumerate(opts):
                    letter_opt = chr(65 + o_idx)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>{letter_opt})</b> {opt}", body_style))
                story.append(Spacer(1, 4))
            story.append(Spacer(1, 6))

        elif block.type == ResourceBlockType.study_guide:
            sections = payload.get("sections") or []
            for sec in sections:
                sec_t = sec.get("section_title") or sec.get("titulo") or ""
                if sec_t:
                    story.append(Paragraph(f"<b>{sec_t}</b>", h2_style))
                bullets = sec.get("bullets") or sec.get("puntos") or []
                for b in bullets:
                    story.append(Paragraph(f"• {b}", body_style))
                takeaway = sec.get("key_takeaway") or sec.get("idea_clave")
                if takeaway:
                    story.append(Paragraph(f"<b>Idea Clave:</b> {takeaway}", body_style))
                story.append(Spacer(1, 4))

        else:
            clean_html = re.sub(r"<style[^>]*>.*?</style>", "", block.rendered_html, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub(r"<script[^>]*>.*?</script>", "", clean_html, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<[^>]+>", " ", clean_html)
            clean_text = " ".join(clean_text.split())
            if clean_text:
                story.append(Paragraph(clean_text, body_style))
                story.append(Spacer(1, 6))

    doc.build(story)
    return buffer.getvalue()
