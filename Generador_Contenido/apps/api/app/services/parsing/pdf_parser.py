"""Parses the guía didáctica (.pdf) into a GuiaExtraction according to Spec v1.2.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from app.schemas.extraction import GuiaExtraction, GuiaPeriodoDetail, GuiaSection, GuiaWeekDeveloped
from app.services.parsing.config import (
    WEEK_HEADER_PATTERN,
    extract_codes,
    is_probable_section_header,
    match_known_header,
)

DATOS_INFORMATIVOS_MARK = "datos informativos"
_SEMANA_NUM = re.compile(r"Semana\s*(\d{1,2})", re.IGNORECASE)
_PERIODO_PATTERN = re.compile(r"Per[íi]odo\s+(\d+)\s*[—–-]\s*(.+)", re.IGNORECASE)
_FECHAS_PATTERN = re.compile(r"Fechas?\s+(\d{2}/\d{2}/\d{4}\s+al\s+\d{2}/\d{2}/\d{4})", re.IGNORECASE)

KNOWN_ACTIVITIES = [
    "EXPLORA Y CONECTA", "ACTIVIDAD GUIADA", "TALLER", "PRÁCTICA PROGRESIVA",
    "COMPRUEBA TU APRENDIZAJE", "AUTOEVALUACIÓN", "PRUEBA", "SÍNTESIS",
    "REFUERZO", "GUÍA", "HOJA", "IDEA CLAVE"
]


def _normalize_section_key(label: str) -> str:
    key = re.sub(r"[^\w]+", "_", label.strip().upper(), flags=re.UNICODE)
    return key.strip("_")


def _extract_topic(page_text: str) -> str:
    for line in page_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("tema "):
            return stripped[5:].strip()
    return ""


def _extract_cover_and_fechas(first_pages_text: list[str]) -> tuple[str, str, str]:
    subject, grade, fechas = "", "", ""
    combined = "\n".join(first_pages_text[:3])
    
    m_fechas = _FECHAS_PATTERN.search(combined)
    if m_fechas:
        fechas = m_fechas.group(1).strip()
        
    for line in combined.splitlines():
        stripped = line.strip()
        if stripped.upper() == "MATERIAL PEDAGÓGICO":
            pass
        if "EGB" in stripped.upper() or "OCTAVO" in stripped.upper():
            grade = stripped
        if not subject and ("MATEMÁTICA" in stripped.upper() or "MATEMATICA" in stripped.upper()):
            subject = stripped
            
    return subject, grade, fechas


def _find_semanas_mencionadas(pages_text: list[str]) -> list[int]:
    mencionadas: set[int] = set()
    full_text = "\n".join(pages_text[:5])
    if "RUTA DEL PARCIAL" in full_text.upper():
        ruta_text = full_text.upper().split("RUTA DEL PARCIAL")[1]
        if "DATOS INFORMATIVOS" in ruta_text:
            ruta_text = ruta_text.split("DATOS INFORMATIVOS")[0]
        
        matches = re.findall(r"SEMANA\s*(\d{1,2})", ruta_text)
        for m in matches:
            mencionadas.add(int(m))
            
    return sorted(mencionadas)


def _find_week_start_pages(pages_text: list[str]) -> list[tuple[int, int]]:
    starts: list[tuple[int, int]] = []
    for i, text in enumerate(pages_text):
        lines = [l.strip().lower() for l in text.splitlines()]
        if DATOS_INFORMATIVOS_MARK not in lines and "datos informativos" not in text.lower():
            continue
        m = WEEK_HEADER_PATTERN.search(text) or _SEMANA_NUM.search(text)
        if m:
            starts.append((i, int(m.group(1))))
    return starts


def parse_guia_pdf(path: str | Path) -> GuiaExtraction:
    warnings: list[str] = []

    with pdfplumber.open(str(path)) as pdf:
        pages_text = [p.extract_text() or "" for p in pdf.pages]

    total_pages = len(pages_text)
    total_char_count = sum(len(p.strip()) for p in pages_text)

    if total_pages > 0 and total_char_count < 150:
        warnings.append(
            "El documento PDF parece ser un archivo escaneado o de imagen sin texto seleccionable. "
            "Se recomienda utilizar un archivo digital original en PDF o Word para un análisis preciso."
        )

    subject, grade, fechas_globales = _extract_cover_and_fechas(pages_text) if pages_text else ("", "", "")

    semanas_mencionadas = _find_semanas_mencionadas(pages_text)
    week_starts = _find_week_start_pages(pages_text)
    
    if not semanas_mencionadas and week_starts:
        semanas_mencionadas = sorted([w for _, w in week_starts])

    if not week_starts:
        warnings.append('No se detectaron páginas de "Datos informativos" con número de semana.')
        return GuiaExtraction(
            subject=subject,
            grade=grade,
            fechas=fechas_globales,
            semanas_mencionadas=semanas_mencionadas,
            total_pages=total_pages,
            warnings=warnings
        )

    competency_codes_by_week: dict[int, list[str]] = {}
    sections: list[GuiaSection] = []
    weeks_detected: list[int] = []
    semanas_desarrolladas: list[GuiaWeekDeveloped] = []

    for idx, (page_idx, week_num) in enumerate(week_starts):
        page_end_idx = week_starts[idx + 1][0] - 1 if idx + 1 < len(week_starts) else total_pages - 1
        page_text = pages_text[page_idx]
        topic = _extract_topic(page_text)
        weeks_detected.append(week_num)

        # Extraer texto completo de toda la semana para códigos y evidencias
        full_week_text = "\n".join(pages_text[p] for p in range(page_idx, page_end_idx + 1))
        codes = extract_codes(full_week_text)
        competency_codes_by_week[week_num] = codes

        m_f = _FECHAS_PATTERN.search(page_text)
        week_fechas = m_f.group(1).strip() if m_f else fechas_globales

        periodos_detalle: list[GuiaPeriodoDetail] = []
        ruta_aprendizaje: list[str] = []
        sintesis: list[str] = []
        actividades_detectadas: set[str] = set()

        for p in range(page_idx, page_end_idx + 1):
            p_text = pages_text[p]
            for line in p_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue

                m_p = _PERIODO_PATTERN.search(stripped)
                if m_p:
                    p_num = int(m_p.group(1))
                    p_title = m_p.group(2).strip()
                    periodos_detalle.append(GuiaPeriodoDetail(numero=p_num, titulo=p_title, pagina=p + 1))

                stripped_up = stripped.upper()
                for act in KNOWN_ACTIVITIES:
                    if act in stripped_up:
                        actividades_detectadas.add(act)

                header = match_known_header(stripped)
                if not header and is_probable_section_header(stripped):
                    header = stripped
                if header:
                    sections.append(
                        GuiaSection(
                            week_number=week_num,
                            lesson_title=topic,
                            section_type=_normalize_section_key(header),
                            page_start=p + 1,
                            page_end=p + 1,
                        )
                    )

        week_dev = GuiaWeekDeveloped(
            numero=week_num,
            tema=topic,
            fechas=week_fechas,
            periodos=str(len(periodos_detalle)) if periodos_detalle else "6",
            objetivo="",
            competencias=codes,
            pagina_inicio=page_idx + 1,
            pagina_fin=page_end_idx + 1,
            periodos_detalle=periodos_detalle,
            ruta_aprendizaje=ruta_aprendizaje,
            sintesis=sintesis,
            actividades=sorted(actividades_detectadas),
        )
        semanas_desarrolladas.append(week_dev)

    if not semanas_mencionadas:
        semanas_mencionadas = sorted([w.numero for w in semanas_desarrolladas])
    else:
        all_mencionadas = set(semanas_mencionadas) | {w.numero for w in semanas_desarrolladas}
        semanas_mencionadas = sorted(all_mencionadas)

    return GuiaExtraction(
        subject=subject,
        grade=grade,
        fechas=fechas_globales,
        semanas_mencionadas=semanas_mencionadas,
        semanas_desarrolladas=semanas_desarrolladas,
        weeks_detected=sorted(set(weeks_detected)),
        competency_codes_by_week=competency_codes_by_week,
        sections=sections,
        total_pages=total_pages,
        warnings=warnings,
    )
