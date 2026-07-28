from __future__ import annotations

import re

PHASE_LABELS = ["Activación", "Anticipación", "Construcción", "Consolidación"]


def clean_line(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def extract_topic(cell_text: str) -> str:
    m = re.match(r"Tema:\s*(.+?)(?:\n\s*\n|$)", cell_text or "", re.DOTALL)
    if m:
        return clean_line(m.group(1))
    return ""


def extract_phases(cell_text: str) -> dict[str, str]:
    """Split a strategy cell into Activación/Anticipación/Construcción/Consolidación.

    The source text uses paragraphs like 'Activación: ...' or a combined
    'Activación y anticipación:' label for the resources column — this
    assigns combined labels to both underlying phase keys.
    """
    text = cell_text or ""
    pattern = re.compile(
        r"(Activaci[oó]n(?:\s+y\s+anticipaci[oó]n)?|Anticipaci[oó]n|Construcci[oó]n|Consolidaci[oó]n)\s*:\s*",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    result = {k: "" for k in ["activacion", "anticipacion", "construccion", "consolidacion"]}
    if not matches:
        return result
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = clean_line(text[start:end])
        label = m.group(1).lower()
        if "activaci" in label:
            result["activacion"] = segment
            if "anticipaci" in label:
                result["anticipacion"] = segment
        elif "anticipaci" in label:
            result["anticipacion"] = segment
        elif "construcci" in label:
            result["construccion"] = segment
        elif "consolidaci" in label:
            result["consolidacion"] = segment
    return result


def extract_resources(cell_text: str) -> list[str]:
    items: list[str] = []
    for raw_line in (cell_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ ]*:$", line):
            continue  # a phase label like "Construcción:", not an actual resource
        items.append(line)
    # de-duplicate while preserving order
    seen: dict[str, None] = {}
    for it in items:
        seen[it] = None
    return list(seen.keys())


def first_line(cell_text: str) -> str:
    for line in (cell_text or "").splitlines():
        if line.strip():
            return clean_line(line)
    return ""


def second_line(cell_text: str) -> str:
    lines = [l for l in (cell_text or "").splitlines() if l.strip()]
    return clean_line(lines[1]) if len(lines) > 1 else ""
