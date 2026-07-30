"""Subtopic decomposition module according to Spec v1.2 (Section 5.2).

Extracts atomic subtopics per week either via a single LLM batch call or via a robust deterministic fallback.
"""
from __future__ import annotations

import json
import re
import os
from typing import Any

from app.schemas.extraction import SilaboWeek
from app.services.concordance.text_utils import normalizar

NO_SEPARAN = [
    "criterios de", "reglas de", "relaciones de",
    "resolucion de", "resolución de", "analisis de", "análisis de", "jerarquia de", "jerarquía de"
]

FRAMING_PREFIXES = [
    r"^diagn[oó]stico y nivelaci[oó]n de aprendizajes requeridos\s*:\s*",
    r"^diagn[oó]stico y nivelaci[oó]n\s*:\s*",
    r"^concepto de\s*",
    r"^concepto y\s*",
    r"^introducci[oó]n a\s*",
    r"^identificaci[oó]n de\s*",
]


def descomponer_fallback(tema: str) -> list[str]:
    """Fallback determinista para extraer subtemas atómicos respetando locuciones compuestas y eliminando frases de encuadre."""
    if not tema:
        return []

    clean_tema = tema
    for prefix in FRAMING_PREFIXES:
        clean_tema = re.sub(prefix, "", clean_tema, flags=re.IGNORECASE).strip()
    
    # Proteger locuciones no-separables reemplazando ' y ' temporalmente dentro de ellas
    temp_tema = clean_tema
    protected_map: dict[str, str] = {}
    for idx, phrase in enumerate(NO_SEPARAN):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = list(pattern.finditer(temp_tema))
        for m in matches:
            matched_str = m.group(0)
            key = f"__PROTECTED_{idx}__"
            protected_map[key] = matched_str
            temp_tema = temp_tema[:m.start()] + key + temp_tema[m.end():]

    # Split por punto, coma, punto y coma, y ' y ' (case insensitive)
    parts = re.split(r"[.,;]|\s+y\s+", temp_tema, flags=re.IGNORECASE)
    
    subtemas: list[str] = []
    for p in parts:
        restored = p.strip()
        for key, orig in protected_map.items():
            restored = restored.replace(key, orig)
        
        restored = restored.strip(" -:;,.")
        if restored and len(restored) >= 2:
            subtemas.append(restored.lower())

    seen: set[str] = set()
    res: list[str] = []
    for s in subtemas:
        if s not in seen:
            seen.add(s)
            res.append(s)

    return res if res else [tema.strip().lower()]


def descomponer_subtemas_batch(weeks: list[SilaboWeek], api_key: str | None = None) -> dict[int, list[str]]:
    """Descompone los temas de todas las semanas en subtemas atómicos."""
    res: dict[int, list[str]] = {}
    
    weeks_to_parse: list[SilaboWeek] = []
    for w in weeks:
        if w.subtemas:
            res[w.week_number] = [s.strip().lower() for s in w.subtemas if s.strip()]
        else:
            weeks_to_parse.append(w)

    if not weeks_to_parse:
        return res

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            prompt_input = [{"numero": w.week_number, "tema": w.topic} for w in weeks_to_parse]
            
            system_prompt = (
                "Eres un experto en planificación curricular. Recibes los temas semanales de un sílabo. "
                "Descompón cada tema en subtemas atómicos (unidades de contenido enseñables por separado).\n"
                "Reglas:\n"
                "- Conserva el contexto: 'propiedades, reglas de signo' dentro de un tema de multiplicación pertenecen a ese tema.\n"
                "- No inventes subtemas que no estén en el texto.\n"
                "- Ignora conectores y frases de encuadre.\n"
                "Responde SOLO JSON estricto con el formato: {\"semanas\": [{\"numero\": N, \"subtemas\": [\"...\", ...]}]}"
            )
            
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": json.dumps(prompt_input, ensure_ascii=False)}]
            )
            
            content_text = response.content[0].text.strip()
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content_text)
            for item in parsed.get("semanas", []):
                wn = item.get("numero")
                subs = item.get("subtemas", [])
                if wn is not None and isinstance(subs, list):
                    res[wn] = [s.strip().lower() for s in subs if s.strip()]
        except Exception:
            pass

    for w in weeks_to_parse:
        if w.week_number not in res or not res[w.week_number]:
            res[w.week_number] = descomponer_fallback(w.topic)

    return res
