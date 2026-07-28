"""Parses the sílabo (.docx) into a SilaboExtraction.

Generic across subjects/grades: nothing here hardcodes a topic. The only
assumption is the institution's own template shape (a "Datos informativos"
key/value table, then one big weekly table alternating full-width "SEMANA
N°x" / "ADAPTACIÓN CURRICULAR" separator rows with 6-column data rows) —
that shape was verified against a real Math Unit 1 sílabo.

Student names are never kept: `_anonymize` assigns a stable pseudonym
("Estudiante A", "Estudiante B", ...) the first time each name is seen, so
the same student maps to the same pseudonym across every week in one
document, without the real name ever entering the extraction result.
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
    """Rows can hold one or two label/value pairs (e.g. 'Grado/Curso' + 'Paralelo/s'
    side by side), so cells are dedup'd then walked two at a time."""
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
    codes = extract_codes(cells[0] + "\n" + cells[1])
    topic = extract_topic(cells[1])
    phases = extract_phases(cells[2])
    return SilaboWeek(
        week_number=week_number,
        topic=topic,
        competency_codes=codes,
        methodology_phases=MethodologyPhases(**phases),
        resources=extract_resources(cells[3]),
        achievement_level=cells[4].strip(),
        evaluation_technique=cells[5].strip(),
    )


def _parse_adaptation_row(cells: list[str], anonymizer: _Anonymizer) -> CurricularAdaptation:
    real_name = first_line(cells[0])
    need = second_line(cells[0])
    codes = extract_codes(cells[0])  # kept for completeness even if unused downstream
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

        if len(dedup) == 1:
            text = dedup[0]
            m = WEEK_HEADER_PATTERN.search(text)
            if m:
                current_week = int(m.group(1))
                mode = "general"
                continue
            if text.strip().lower() in ADAPTATION_HEADER_MARKERS:
                mode = "adaptation"
                continue
            continue  # unrecognized full-width separator row

        if dedup[0].lower().startswith("competencia general"):
            continue  # column-header row, not data

        if current_week is None or len(raw_cells) < 6:
            continue

        cells = [c.strip() for c in raw_cells]
        if mode == "general":
            weeks[current_week] = _parse_general_row(current_week, cells)
        elif mode == "adaptation" and current_week in weeks:
            weeks[current_week].adaptations.append(_parse_adaptation_row(cells, anonymizer))

    return SilaboExtraction(
        **info,
        weeks=[weeks[k] for k in sorted(weeks.keys())],
        warnings=warnings,
    )
