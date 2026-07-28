"""Tunables for document parsing.

Nothing here should hardcode a subject or grade. `COMPETENCY_CODE_PATTERN`
matches the Ecuadorian curriculum-code style used across subjects (e.g.
`8.SUP.A.R.L.M.1.1.1`, `10.MED.CN.F.5.2`) — grade number, level tag, one or
more dot-separated uppercase axis letters, then up to four dot-separated
numeric segments. `GUIA_SECTION_HEADERS` lists the section labels observed in
this institution's guía template; `is_probable_section_header` falls back to
a generic ALL-CAPS heuristic so a differently-worded template still gets
*some* section detected instead of silently producing nothing.
"""
from __future__ import annotations

import re

COMPETENCY_CODE_PATTERN = re.compile(
    r"\b\d{1,2}\.\s?[A-Z]{2,5}(?:\.[A-Z]{1,5}){1,6}(?:\.\d{1,3}){0,4}\b"
)

WEEK_HEADER_PATTERN = re.compile(
    r"SEMANA\s*N?[°º]?\s*(\d{1,2})", re.IGNORECASE
)

WEEK_LESSON_PATTERN = re.compile(
    r"Semana\s+y\s+lecci[oó]n\s*Semana\s*(\d{1,2})\s*[–-]\s*Lecci[oó]n\s*(\d{1,2})",
    re.IGNORECASE,
)

ADAPTATION_HEADER_MARKERS = {"adaptación curricular", "adaptacion curricular"}

GUIA_SECTION_HEADERS = [
    "PROPÓSITO DE ESTA SEMANA", "CRITERIOS DE ÉXITO", "EXPLORA Y CONECTA",
    "NECESITAS RECORDAR", "IDEA CLAVE", "EJEMPLO O MODELO PASO A PASO",
    "ERROR FRECUENTE", "REFUERZO GRADUADO", "MI REGISTRO DIAGNÓSTICO",
    "PRÁCTICA PROGRESIVA", "CONEXIÓN CON EL MUNDO", "COMPRUEBA ESTA IDEA",
    "TALLER INTEGRADOR", "TALLER PEDAGÓGICO", "SÍNTESIS",
    "ORGANIZA EL PROCEDIMIENTO", "COMPRUEBA TU APRENDIZAJE",
    "PRUEBA ESCRITA CORTA", "AUTOEVALUACIÓN", "ACTIVACIÓN BREVE",
    "DATOS INFORMATIVOS",
]

_HEADER_LOOKUP = {h.upper(): h for h in GUIA_SECTION_HEADERS}


def normalize_code(raw: str) -> str:
    code = re.sub(r"\.\s+", ".", raw.strip())
    code = re.sub(r"\s+", "", code)
    return code.rstrip(".").upper()


def extract_codes(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for m in COMPETENCY_CODE_PATTERN.finditer(text or ""):
        norm = normalize_code(m.group(0))
        # A bare grade+level fragment like "8.MED" isn't a usable competency
        # code on its own; require at least one numeric segment too.
        if re.search(r"\.\d", norm):
            seen[norm] = None
    return list(seen.keys())


def match_known_header(line: str) -> str | None:
    stripped = line.strip().upper()
    for key, original in _HEADER_LOOKUP.items():
        if stripped.startswith(key):
            return original
    return None


def is_probable_section_header(line: str) -> bool:
    """Generic fallback: a short, mostly-uppercase, multi-word standalone line.

    Requires >=2 words with at least one word of length >=3 to avoid matching
    answer-key fragments like single all-caps words ("ENTEROS") or option
    letter lists ("A B C", "P Q R S").
    """
    stripped = line.strip()
    if not (6 <= len(stripped) <= 60):
        return False
    words = stripped.split()
    if len(words) < 2:
        return False
    if max(len(w.strip(".,;:")) for w in words) < 3:
        return False
    letters = [c for c in stripped if c.isalpha()]
    if len(letters) < 6:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return upper_ratio > 0.9 and not stripped.endswith(".")
