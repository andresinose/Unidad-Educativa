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

    deepseek_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "").strip()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    system_prompt = (
        "Eres un evaluador pedagógico. Para cada subtema dudoso decide si el material de la semana realmente lo desarrolla. "
        "Ignora ortografía, sinónimos y orden ('valor absoluto' ≡ 'interpreta el valor absoluto' ≡ 'distancia al cero'). "
        "Equivalencias pedagógicas válidas: taller ≈ hoja de trabajo ≈ guía; prueba corta ≈ evaluación escrita ≈ comprueba tu aprendizaje.\n"
        "Responde SOLO JSON estricto: {\"resoluciones\": [{\"semana\": N, \"subtema\": \"...\", \"estado\": \"CUBIERTO|MENCIONADO|AUSENTE\", \"evidencia\": \"...\", \"justificacion\": \"...\"}]}"
    )

    content_text = None
    if deepseek_key:
        try:
            import httpx
            base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
            payload = {
                "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(dudosos, ensure_ascii=False)},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
            }
            resp = httpx.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                content_text = data["choices"][0]["message"]["content"]
                try:
                    from app.core.usage_tracker import record_llm_usage
                    usage_info = data.get("usage") or {}
                    record_llm_usage(
                        provider="deepseek",
                        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                        feature="juez_concordancia",
                        prompt_tokens=usage_info.get("prompt_tokens", 0),
                        completion_tokens=usage_info.get("completion_tokens", 0),
                        cache_hit_tokens=usage_info.get("prompt_cache_hit_tokens", 0),
                        metadata={"dudosos_count": len(dudosos)},
                    )
                except Exception:
                    pass
        except Exception:
            pass

    if not content_text and openrouter_key:
        try:
            import httpx
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(dudosos, ensure_ascii=False)},
                ],
                "temperature": 0.0,
            }
            resp = httpx.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                content_text = data["choices"][0]["message"]["content"]
        except Exception:
            pass

    if not content_text and anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": json.dumps(dudosos, ensure_ascii=False)}]
            )
            content_text = response.content[0].text.strip()
        except Exception:
            pass

    if content_text:
        try:
            clean_text = content_text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(clean_text)
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
            pass

    return res

