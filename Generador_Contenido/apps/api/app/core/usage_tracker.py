from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Ruta del archivo de datos
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
USAGE_FILE = DATA_DIR / "usage_history.json"

_lock = threading.Lock()

# Precios por 1,000,000 tokens en USD
MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-chat": {
        "input": 0.14,
        "input_cache_hit": 0.014,
        "output": 0.28,
    },
    "deepseek/deepseek-chat": {
        "input": 0.14,
        "input_cache_hit": 0.014,
        "output": 0.28,
    },
    "deepseek-reasoner": {
        "input": 0.55,
        "input_cache_hit": 0.14,
        "output": 2.19,
    },
    "gemini-2.5-flash": {
        "input": 0.075,
        "input_cache_hit": 0.01875,
        "output": 0.30,
    },
    "openai/gpt-4o-mini": {
        "input": 0.15,
        "input_cache_hit": 0.075,
        "output": 0.60,
    },
    "default": {
        "input": 0.14,
        "input_cache_hit": 0.014,
        "output": 0.28,
    },
}


def _ensure_data_dir() -> None:
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USAGE_FILE.exists():
        USAGE_FILE.write_text("[]", encoding="utf-8")


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cache_hit_tokens: int = 0,
) -> float:
    pricing = MODEL_PRICING.get(model.lower(), MODEL_PRICING["default"])
    
    uncached_tokens = max(0, prompt_tokens - cache_hit_tokens)
    cost_uncached_input = (uncached_tokens / 1_000_000.0) * pricing["input"]
    cost_cached_input = (cache_hit_tokens / 1_000_000.0) * pricing.get("input_cache_hit", pricing["input"])
    cost_output = (completion_tokens / 1_000_000.0) * pricing["output"]
    
    return round(cost_uncached_input + cost_cached_input + cost_output, 7)


def record_llm_usage(
    provider: str,
    model: str,
    feature: str,
    prompt_tokens: int,
    completion_tokens: int,
    cache_hit_tokens: int = 0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Registra una llamada a LLM en el historial de costos."""
    _ensure_data_dir()
    
    total_tokens = prompt_tokens + completion_tokens
    cost_usd = calculate_cost(model, prompt_tokens, completion_tokens, cache_hit_tokens)
    
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "feature": feature,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cache_hit_tokens": cache_hit_tokens,
        "cost_usd": cost_usd,
        "metadata": metadata or {},
    }
    
    with _lock:
        try:
            content = USAGE_FILE.read_text(encoding="utf-8")
            data = json.loads(content) if content.strip() else []
        except Exception:
            data = []
            
        data.append(record)
        USAGE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        
    return record


def get_usage_history(
    limit: int = 100,
    feature: str | None = None,
    provider: str | None = None,
) -> list[dict[str, Any]]:
    """Obtiene el historial de consumo filtrado."""
    _ensure_data_dir()
    with _lock:
        try:
            content = USAGE_FILE.read_text(encoding="utf-8")
            data = json.loads(content) if content.strip() else []
        except Exception:
            return []
            
    filtered = data
    if feature:
        filtered = [r for r in filtered if r.get("feature") == feature]
    if provider:
        filtered = [r for r in filtered if r.get("provider") == provider]
        
    return sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]


def get_usage_summary() -> dict[str, Any]:
    """Obtiene el resumen consolidado de consumo y costos."""
    _ensure_data_dir()
    with _lock:
        try:
            content = USAGE_FILE.read_text(encoding="utf-8")
            data = json.loads(content) if content.strip() else []
        except Exception:
            data = []

    total_requests = len(data)
    total_prompt_tokens = sum(r.get("prompt_tokens", 0) for r in data)
    total_completion_tokens = sum(r.get("completion_tokens", 0) for r in data)
    total_tokens = sum(r.get("total_tokens", 0) for r in data)
    total_cost_usd = round(sum(r.get("cost_usd", 0.0) for r in data), 6)
    
    # Agrupado por feature
    by_feature: dict[str, dict[str, Any]] = {}
    for r in data:
        feat = r.get("feature", "desconocido")
        if feat not in by_feature:
            by_feature[feat] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
        by_feature[feat]["requests"] += 1
        by_feature[feat]["tokens"] += r.get("total_tokens", 0)
        by_feature[feat]["cost_usd"] = round(by_feature[feat]["cost_usd"] + r.get("cost_usd", 0.0), 6)

    # Agrupado por proveedor y modelo
    by_model: dict[str, dict[str, Any]] = {}
    for r in data:
        mod = r.get("model", "desconocido")
        if mod not in by_model:
            by_model[mod] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
        by_model[mod]["requests"] += 1
        by_model[mod]["tokens"] += r.get("total_tokens", 0)
        by_model[mod]["cost_usd"] = round(by_model[mod]["cost_usd"] + r.get("cost_usd", 0.0), 6)

    return {
        "total_requests": total_requests,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "average_cost_per_request": round(total_cost_usd / total_requests, 6) if total_requests > 0 else 0.0,
        "by_feature": by_feature,
        "by_model": by_model,
        "pricing_reference": MODEL_PRICING,
    }


def clear_usage_history() -> None:
    """Limpia el historial de consumo."""
    _ensure_data_dir()
    with _lock:
        USAGE_FILE.write_text("[]", encoding="utf-8")
