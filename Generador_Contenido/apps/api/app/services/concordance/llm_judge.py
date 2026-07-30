"""Acotado LLM Judge module according to Spec v1.2 (Section 5.6).

Resolves doubtful/uncovered subtopics (MENCIONADO/AUSENTE) in a single batch LLM call.
"""
from __future__ import annotations

import json
import os
from typing import Any


def resolver_dudosos_batch(dudosos: list[dict[str, Any]], api_key: str | None = None) -> dict[tuple[int, str], dict[str, str]]:
    """Resolución semántica en batch de subtemas dudosos.
    
    Cada elemento en `dudosos` tiene:
    - "semana": int
    - "subtema": str
    - "periodos": list[str]
    - "ruta": list[str]
    - "sintesis": list[str]

    Retorna {(semana, subtema_normalizado): {"estado": ..., "evidencia": ..., "justificacion": ...}}
    """
    res: dict[tuple[int, str], dict[str, str]] = {}
    if not dudosos:
        return res

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return res

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        
        system_prompt = (
            "Eres un evaluador pedagógico. Para cada subtema dudoso decide si el material de la semana realmente lo desarrolla. "
            "Ignora ortografía, sinónimos y orden ('valor absoluto' ≡ 'interpreta el valor absoluto' ≡ 'distancia al cero'). "
            "Equivalencias pedagógicas válidas: taller ≈ hoja de trabajo ≈ guía; prueba corta ≈ evaluación escrita ≈ comprueba tu aprendizaje.\n"
            "Responde SOLO JSON estricto: {\"resoluciones\": [{\"semana\": N, \"subtema\": \"...\", \"estado\": \"CUBIERTO|MENCIONADO|AUSENTE\", \"evidencia\": \"...\", \"justificacion\": \"...\"}]}"
        )
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": json.dumps(dudosos, ensure_ascii=False)}]
        )
        
        content_text = response.content[0].text.strip()
        if "```json" in content_text:
            content_text = content_text.split("```json")[1].split("```")[0].strip()
        elif "```" in content_text:
            content_text = content_text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content_text)
        for item in parsed.get("resoluciones", []):
            wn = item.get("semana")
            sub = item.get("subtema")
            estado = item.get("estado")
            if wn is not None and sub and estado in ("CUBIERTO", "MENCIONADO", "AUSENTE"):
                res[(wn, sub.strip().lower())] = {
                    "estado": estado,
                    "evidencia": item.get("evidencia", ""),
                    "justificacion": item.get("justificacion", "")
                }
    except Exception:
        # Fallback conservador silencioso
        pass

    return res
