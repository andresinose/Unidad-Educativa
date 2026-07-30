"""Parses the sílabo (.docx) into a SilaboExtraction according to Spec v1.2.
"""
from __future__ import annotations

import re
import string
from pathlib import Path

import docx

from app.schemas.extraction import CurricularAdaptation, MethodologyPhases, SilaboExtraction, SilaboWeek
from app.services.parsing.config import ADAPTATION_HEADER_MARKERS, WEEK_HEADER_PATTERN, extract_codes
from app.services.parsing.text_utils import (
    extract_phases,
    extract_resources,
    extract_topic,
    first_line,
    second_line,
)
from app.services.concordance.subtopic_decomposer import descomponer_fallback

INFO_FIELD_MAP = {
    "asignatura": "subject",
    "nombre del docente": "teacher",
    "grado/curso": "grade",
    "paralelo": "parallels",
    "paralelo/s": "parallels",
    "nombre de la unidad": "unit_name",
    "trimestre": "trimester",
    "parcial": "parcial",
    "objetivo de la unidad": "unit_objective",
    "fecha de inicio": "start_date",
    "fecha de finalización": "end_date",
    "fecha de finalizacion": "end_date",
    "n° de periodos semanales": "periodos_semanales",
    "n° de períodos semanales": "periodos_semanales",
    "n° periodos semanales": "periodos_semanales",
}


def _dedup(cells: list[str]) -> list[str]:
    out: list[str] = []
    for c in cells:
        if not out or out[-1] != c:
            out.append(c)
    return out


def _find_info_table(document: docx.document.Document):
    for table in document.tables:
        first_cell = table.rows[0].cells[0].text.strip().lower()
        if "datos informativos" in first_cell:
            return table
    return None


def _find_weekly_table(document: docx.document.Document):
    for table in document.tables:
        first_cell = table.rows[0].cells[0].text.strip()
        if WEEK_HEADER_PATTERN.search(first_cell):
            return table
    return None


def _parse_info_table(table) -> dict[str, str]:
    info: dict[str, str] = {}
    for row in table.rows:
        raw_cells = [c.text.replace("\xa0", " ").strip() for c in row.cells]
        dedup: list[str] = []
        for c in raw_cells:
            if not dedup or dedup[-1] != c:
                dedup.append(c)

        i = 0
        while i + 1 < len(dedup):
            label_raw = dedup[i].strip().rstrip(":").strip()
            label_norm = re.sub(r"\s+\d+$", "", label_raw).strip().lower()
            value = dedup[i + 1].strip()
            key = INFO_FIELD_MAP.get(label_norm)
            if key and value:
                info[key] = value
                i += 2
            else:
                i += 1
    return info


class _Anonymizer:
    def __init__(self) -> None:
        self._map: dict[str, str] = {}

    def pseudonym(self, real_name: str) -> str:
        if real_name not in self._map:
            idx = len(self._map)
            letters = string.ascii_uppercase
            label = letters[idx] if idx < len(letters) else f"#{idx + 1}"
            self._map[real_name] = f"Estudiante {label}"
        return self._map[real_name]


def _parse_general_row(week_number: int, cells: list[str]) -> SilaboWeek:
    codes_col0 = extract_codes(cells[0])
    codes_col1 = extract_codes(cells[1])
    all_codes = sorted(set(codes_col0 + codes_col1))
    
    # Clasificar generales vs específicas (específicas tienen >= 6 segmentos en código)
    comp_generales = [cells[0].strip()] if cells[0].strip() else []
    comp_especificas = [cells[1].strip()] if cells[1].strip() else []
    
    topic = extract_topic(cells[1])
    if not topic and len(cells) > 1:
        # Fallback si no tiene prefijo 'Tema:'
        topic = cells[1].split("\n")[0].strip()
        
    phases = extract_phases(cells[2])
    subtemas = descomponer_fallback(topic)
    
    return SilaboWeek(
        week_number=week_number,
        topic=topic,
        subtemas=subtemas,
        competency_codes=all_codes,
        competencias_generales=comp_generales,
        competencias_especificas=comp_especificas,
        methodology_phases=MethodologyPhases(**phases),
        resources=extract_resources(cells[3]),
        achievement_level=cells[4].strip(),
        evaluation_technique=cells[5].strip(),
    )


def _parse_adaptation_row(cells: list[str], anonymizer: _Anonymizer) -> CurricularAdaptation:
    real_name = first_line(cells[0])
    need = second_line(cells[0])
    phases = extract_phases(cells[2])
    return CurricularAdaptation(
        student_ref=anonymizer.pseudonym(real_name) if real_name else "Estudiante (sin nombre)",
        need_description=need,
        grade_level=need.split(" - ")[0] if " - " in need else "",
        methodology_phases=MethodologyPhases(**phases),
        achievement_level=cells[4].strip(),
    )


def parse_silabo_docx(path: str | Path) -> SilaboExtraction:
    document = docx.Document(str(path))
    warnings: list[str] = []

    info_table = _find_info_table(document)
    info = _parse_info_table(info_table) if info_table is not None else {}
    if info_table is None:
        warnings.append("No se encontró la tabla de 'Datos informativos'.")

    weekly_table = _find_weekly_table(document)
    if weekly_table is None:
        warnings.append("No se encontró la tabla semanal (fila con 'SEMANA N°X').")
        return SilaboExtraction(**info, warnings=warnings)

    anonymizer = _Anonymizer()
    weeks: dict[int, SilaboWeek] = {}
    mode = "seek"
    current_week: int | None = None

    for row in weekly_table.rows:
        raw_cells = [c.text for c in row.cells]
        dedup = _dedup([c.strip() for c in raw_cells])

        if len(dedup) == 1 or (len(raw_cells) < 6 and any("SEMANA" in c.upper() for c in dedup)):
            text = dedup[0] if dedup else ""
            m = WEEK_HEADER_PATTERN.search(text) or re.search(r"SEMANA\s*N\s*[°ºo]?\s*(\d+)", text, re.IGNORECASE)
            if m and len(text) < 60:
                current_week = int(m.group(1))
                mode = "general"
                continue
            if text.strip().lower() in ADAPTATION_HEADER_MARKERS or "ADAPTACIÓN CURRICULAR" in text.upper():
                mode = "adaptation"
                continue
            continue  # fila separadora

        if dedup[0].lower().startswith("competencia general"):
            continue  # encabezado de columnas

        if current_week is None or len(raw_cells) < 6:
            continue

        cells = [c.strip() for c in raw_cells]
        if mode == "general":
            w_parsed = _parse_general_row(current_week, cells)
            weeks[current_week] = w_parsed
        elif mode == "adaptation" and current_week in weeks:
            adapt = _parse_adaptation_row(cells, anonymizer)
            weeks[current_week].adaptations.append(adapt)
            weeks[current_week].adaptaciones_count += 1

    parsed_weeks = [weeks[k] for k in sorted(weeks.keys())]

    return SilaboExtraction(
        **info,
        weeks=parsed_weeks,
        warnings=warnings,
    )
