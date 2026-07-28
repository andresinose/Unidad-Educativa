"""Parses the guía didáctica (.pdf) into a GuiaExtraction.

Generic across subjects: the only structural assumption is that each week
starts on a "Datos informativos" page containing a "Semana <n>" marker
(verified against a real Math Unit 1 guía, in two slightly different
formats: "Semana y lección Semana 2 – Lección 2" and plain "Semana 1") and
that every week runs until the next such page. Section headers are matched
against a configured list first, falling back to a generic ALL-CAPS-line
heuristic so an unfamiliar template still yields *some* section structure
instead of nothing.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from app.schemas.extraction import GuiaExtraction, GuiaSection
from app.services.parsing.config import (
    WEEK_HEADER_PATTERN,
    extract_codes,
    is_probable_section_header,
    match_known_header,
)

DATOS_INFORMATIVOS_MARK = "datos informativos"
_SEMANA_NUM = re.compile(r"Semana\s*(\d{1,2})", re.IGNORECASE)


def _normalize_section_key(label: str) -> str:
    key = re.sub(r"[^\w]+", "_", label.strip().upper(), flags=re.UNICODE)
    return key.strip("_")


def _extract_topic(page_text: str) -> str:
    for line in page_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("tema "):
            return stripped[5:].strip()
    return ""


def _extract_cover(first_page_text: str) -> tuple[str, str]:
    lines = [l.strip() for l in first_page_text.splitlines() if l.strip()]
    subject, grade = "", ""
    for i, line in enumerate(lines):
        if line.upper() == "MATERIAL PEDAGÓGICO" and i + 1 < len(lines):
            subject = lines[i + 1]
        if "EGB" in line.upper():
            grade = line
    return subject, grade


def _find_week_start_pages(pages_text: list[str]) -> list[tuple[int, int]]:
    """Returns (0-based page index, week number) for each 'Datos informativos' page."""
    starts: list[tuple[int, int]] = []
    for i, text in enumerate(pages_text):
        lines = [l.strip().lower() for l in text.splitlines()]
        if DATOS_INFORMATIVOS_MARK not in lines:
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
    subject, grade = _extract_cover(pages_text[0]) if pages_text else ("", "")

    week_starts = _find_week_start_pages(pages_text)
    if not week_starts:
        warnings.append('No se detectaron páginas de "Datos informativos" con número de semana.')
        return GuiaExtraction(subject=subject, grade=grade, total_pages=total_pages, warnings=warnings)

    competency_codes_by_week: dict[int, list[str]] = {}
    sections: list[GuiaSection] = []
    weeks_detected: list[int] = []

    for idx, (page_idx, week_num) in enumerate(week_starts):
        page_end_idx = week_starts[idx + 1][0] - 1 if idx + 1 < len(week_starts) else total_pages - 1
        page_text = pages_text[page_idx]
        topic = _extract_topic(page_text)
        weeks_detected.append(week_num)
        competency_codes_by_week[week_num] = extract_codes(page_text)

        for p in range(page_idx, page_end_idx + 1):
            for line in pages_text[p].splitlines():
                header = match_known_header(line)
                if not header and is_probable_section_header(line):
                    header = line.strip()
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

    return GuiaExtraction(
        subject=subject,
        grade=grade,
        weeks_detected=sorted(set(weeks_detected)),
        competency_codes_by_week=competency_codes_by_week,
        sections=sections,
        total_pages=total_pages,
        warnings=warnings,
    )
