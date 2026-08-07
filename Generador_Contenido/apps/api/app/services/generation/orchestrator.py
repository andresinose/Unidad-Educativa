"""Generation orchestrator: an LLM (OpenRouter, Gemini or Claude) picks *what* pedagogical content to
produce, grounded in one already-validated sílabo week, but can only render it
through the whitelisted MCP tools (app/mcp_server/tools/*) — never by emitting
HTML/JS directly. This is the same security property described in the plan:
content decisions come from the model, rendering is deterministic and typed.
"""
from __future__ import annotations

import json
import httpx

from app.core.config import (
    ANTHROPIC_API_KEY,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GENERATION_MODEL,
    LLM_PROVIDER,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)
from app.mcp_server.tools.activity_builder import InteractiveActivitySchema, build_interactive_activity
from app.mcp_server.tools.diagram import DiagramSchema, render_diagram
from app.mcp_server.tools.word_search import WordSearchSchema, build_word_search
from app.mcp_server.tools.flashcards import FlashcardsSchema, build_flashcards
from app.mcp_server.tools.study_guide import StudyGuideSchema, build_study_guide
from app.mcp_server.tools.crossword import CrosswordSchema, build_crossword
from app.mcp_server.tools.logic_puzzle import LogicPuzzleSchema, build_logic_puzzle

from app.schemas.concordance import WeekConcordance
from app.schemas.extraction import SilaboWeek
from app.schemas.generation import GeneratedResource, GenerationRequest, ResourceBlock, ResourceBlockType

_TOOL_SPECS = [
    {
        "name": "build_interactive_activity",
        "description": (
            "Crea una actividad de autoevaluación o cuestionario interactivo (opción múltiple con retroalimentación) "
            "autónoma en HTML, útil para evaluar, practicar, reforzar o comprobar comprensión."
        ),
        "input_schema": InteractiveActivitySchema.model_json_schema(),
    },
    {
        "name": "render_diagram",
        "description": (
            "Crea un diagrama visual de nodos y flechas (mapa conceptual, flujograma o esquema) en SVG, útil "
            "para presentar el tema, visualizar procesos, comparar conceptos o analizar una situación."
        ),
        "input_schema": DiagramSchema.model_json_schema(),
    },
    {
        "name": "build_word_search",
        "description": (
            "Crea una sopa de letras interactiva en HTML/CSS, excelente para actividades lúdicas, "
            "reforzar vocabulario clave, aprendizaje dinámico y motivación lúdica."
        ),
        "input_schema": WordSearchSchema.model_json_schema(),
    },
    {
        "name": "build_flashcards",
        "description": (
            "Crea una colección de tarjetas de estudio 3D (flashcards giratorias) en HTML/CSS, excelente "
            "para repasar conceptos clave, fórmulas, preguntas y definiciones de forma lúdica."
        ),
        "input_schema": FlashcardsSchema.model_json_schema(),
    },
    {
        "name": "build_study_guide",
        "description": (
            "Crea una ficha o guía de estudio sintética infográfica con secciones, viñetas e ideas clave "
            "para sintetizar la materia y entregar material de estudio."
        ),
        "input_schema": StudyGuideSchema.model_json_schema(),
    },
    {
        "name": "build_crossword",
        "description": (
            "Crea un crucigrama interactivo autónomo en HTML/CSS con grilla y pistas horizontales/verticales, "
            "excelente para reforzar conceptos, definiciones y vocabulario mediante razonamiento y pistas."
        ),
        "input_schema": CrosswordSchema.model_json_schema(),
    },
    {
        "name": "build_logic_puzzle",
        "description": (
            "Crea un rompecabezas de lógica (emparejar columnas o clasificar secuencia lógica de pasos) "
            "interactivo en HTML/CSS/JS, ideal para pensamiento crítico y secuenciación."
        ),
        "input_schema": LogicPuzzleSchema.model_json_schema(),
    },
]

_TOOL_IMPLS: dict[str, tuple[type, callable, ResourceBlockType]] = {
    "build_interactive_activity": (InteractiveActivitySchema, build_interactive_activity, ResourceBlockType.interactive_activity),
    "render_diagram": (DiagramSchema, render_diagram, ResourceBlockType.diagram),
    "build_word_search": (WordSearchSchema, build_word_search, ResourceBlockType.word_search),
    "build_flashcards": (FlashcardsSchema, build_flashcards, ResourceBlockType.flashcards),
    "build_study_guide": (StudyGuideSchema, build_study_guide, ResourceBlockType.study_guide),
    "build_crossword": (CrosswordSchema, build_crossword, ResourceBlockType.crossword),
    "build_logic_puzzle": (LogicPuzzleSchema, build_logic_puzzle, ResourceBlockType.logic_puzzle),
}


def _get_clean_tool_schema(schema_cls) -> dict:
    """Recursively dereferences Pydantic's $defs to create an inline OpenAPI JSON Schema."""
    schema = schema_cls.model_json_schema()
    defs = schema.pop("$defs", {})

    def _resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                ref_key = node["$ref"].split("/")[-1]
                if ref_key in defs:
                    return _resolve(defs[ref_key])
            return {k: _resolve(v) for k, v in node.items()}
        elif isinstance(node, list):
            return [_resolve(x) for x in node]
        return node

    return _resolve(schema)


def _anonymized_adaptations_summary(week: SilaboWeek) -> str:
    """Never pass real student names/identifiers to the LLM — only the anonymized
    pseudonym assigned during parsing (see docx_parser._Anonymizer) and the need."""
    if not week.adaptations:
        return "(sin adaptaciones registradas)"
    return "\n".join(
        f"- {a.student_ref}: {a.need_description or 'necesidad no especificada'}"
        for a in week.adaptations
    )


def _build_prompt(
    week: SilaboWeek,
    concordance: WeekConcordance | None,
    request: GenerationRequest,
    forced_tool: str | None = None,
) -> str:
    status_obs = f"{getattr(concordance.status, 'value', str(concordance.status))} — {concordance.observation}" if concordance else "(sin concordancia evaluada)"
    intent_str = getattr(request.intent, "value", str(request.intent))
    extra_lower = (request.extra_instructions or "").lower()

    if forced_tool and forced_tool in _TOOL_IMPLS:
        tool_guidance = f"DEBES invocar la herramienta `{forced_tool}`."
    elif any(k in extra_lower for k in ["crucigrama"]):
        tool_guidance = "El docente solicitó un CRUCIGRAMA. DEBES invocar la herramienta `build_crossword`."
    elif any(k in extra_lower for k in ["logica", "rompecabezas", "emparejar", "relacionar", "secuencia", "ordenar"]):
        tool_guidance = "El docente solicitó un ROMPECABEZAS DE LÓGICA Y RELACIÓN. DEBES invocar la herramienta `build_logic_puzzle`."
    elif any(k in extra_lower for k in ["sopa", "letras", "juego", "ludico"]):
        tool_guidance = "El docente solicitó una actividad LÚDICA (sopa de letras). DEBES invocar la herramienta `build_word_search`."
    elif any(k in extra_lower for k in ["tarjetas", "flashcard", "memorizar", "fichas", "memoria"]):
        tool_guidance = "El docente solicitó TARJETAS DE ESTUDIO (flashcards). DEBES invocar la herramienta `build_flashcards`."
    elif any(k in extra_lower for k in ["guia", "ficha de estudio", "resumen", "infografia"]):
        tool_guidance = "El docente solicitó una GUÍA DE ESTUDIO / RESUMEN. DEBES invocar la herramienta `build_study_guide`."
    elif any(k in intent_str.lower() for k in ["presentar", "visualizar", "comparar", "analizar"]) or any(k in extra_lower for k in ["proceso", "mapa", "diagrama", "esquema", "flujo"]):
        tool_guidance = (
            "El docente solicita un RECURSO VISUAL DIDÁCTICO SINTÉTICO (mapa conceptual / esquema de aprendizaje).\n"
            "INSTRUCCIÓN DIDÁCTICA DE SIMPLIFICACIÓN PARA EL APRENDIZAJE:\n"
            "- DEBES invocar la herramienta `render_diagram`.\n"
            "- Para que sea didácticamente efectivo y fácil de aprender por estudiantes, genera entre 4 y 6 NODOS CLAVE MÁXIMO en una secuencia de aprendizaje clara:\n"
            "  (1. Tema Central ➔ 2. Regla / Paso Principal ➔ 3. Ejemplo Práctico ➔ 4. Conclusión / Resultado).\n"
            "- Mantiene labels sintéticos, breves y sin red compleja de líneas cruzadas.\n"
            "- Asigna 'node_type' adecuado ('concept', 'process', 'example', 'outcome') para cada nodo."
        )
    else:
        tool_guidance = "Elige la herramienta MCP más apropiada según la intención pedagógica (`build_interactive_activity`, `render_diagram`, `build_word_search`, `build_flashcards`, `build_study_guide`, `build_crossword`, o `build_logic_puzzle`)."

    return f"""Eres un asistente pedagógico experto en diseño instruccional y gamificación. Genera UN recurso didáctico para la siguiente semana de
planificación curricular, usando EXCLUSIVAMENTE una de las herramientas MCP disponibles — nunca
respondas con HTML/JS directamente, y no expliques tu razonamiento fuera de la llamada a la
herramienta.

Semana {week.week_number}: {week.topic}
Códigos de competencia: {', '.join(week.competency_codes) or '(sin códigos)'}
Contenido central de la clase (fase de construcción): {week.methodology_phases.construccion or '(no especificada)'}
Nivel de logro esperado: {week.achievement_level or '(no especificado)'}
Estado de concordancia con la guía didáctica: {status_obs}

Adaptaciones curriculares registradas para esta semana (identificadores ya anonimizados; ten en
cuenta estas necesidades al diseñar el recurso, pero no las menciones explícitamente en el
contenido generado):
{_anonymized_adaptations_summary(week)}

Intención pedagógica solicitada por el docente: {intent_str}
Instrucciones adicionales del docente: {request.extra_instructions or '(ninguna)'}

INSTRUCCIÓN DE SELECCIÓN DE HERRAMIENTA:
{tool_guidance}"""


def generate_resource_openrouter(
    week: SilaboWeek,
    concordance: WeekConcordance | None,
    request: GenerationRequest,
    forced_tool: str | None = None,
) -> GeneratedResource:
    api_key = OPENROUTER_API_KEY.strip()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY no está configurada. La generación requiere una clave de OpenRouter."
        )

    prompt = _build_prompt(week, concordance, request, forced_tool=forced_tool)
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    tools_payload = [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": impl[0].__doc__ or name,
                "parameters": _get_clean_tool_schema(impl[0]),
            },
        }
        for name, impl in _TOOL_IMPLS.items()
    ]

    models_to_try = [OPENROUTER_MODEL, "openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat"]
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    response_data = None
    last_error = None

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "max_tokens": 3000,
            "messages": [{"role": "user", "content": prompt}],
            "tools": tools_payload,
            "tool_choice": "required",
        }

        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=35)
            if r.status_code == 200:
                response_data = r.json()
                break
            else:
                last_error = f"{r.status_code}: {r.text}"
        except Exception as exc:
            last_error = exc
            continue

    if not response_data:
        raise RuntimeError(f"Fallo en la llamada a OpenRouter. Último error: {last_error}")

    blocks: list[ResourceBlock] = []
    trace: list[str] = []

    choices = response_data.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        tool_calls = msg.get("tool_calls") or []

        for call in tool_calls:
            func = call.get("function") or {}
            tool_name = func.get("name") or ""
            raw_args_str = func.get("arguments") or "{}"

            impl = _TOOL_IMPLS.get(tool_name)
            if impl is None:
                trace.append(f"{tool_name}: herramienta desconocida, ignorada")
                continue

            schema_cls, fn, block_type = impl
            try:
                raw_args = json.loads(raw_args_str) if isinstance(raw_args_str, str) else raw_args_str
                validated = schema_cls.model_validate(raw_args)
            except Exception as exc:
                trace.append(f"{tool_name}: entrada inválida ({exc})")
                continue

            rendered_html = fn(validated)
            title = getattr(validated, "title", tool_name)
            blocks.append(
                ResourceBlock(type=block_type, title=title, payload=raw_args, rendered_html=rendered_html)
            )
            trace.append(f"{tool_name}: ok")

    if not blocks:
        raise RuntimeError(
            "El modelo en OpenRouter no produjo ningún bloque válido a través de las herramientas disponibles."
        )

    return GeneratedResource(
        title=blocks[0].title or f"Recurso — Semana {week.week_number}",
        week_number=week.week_number,
        topic=week.topic,
        intent=request.intent,
        summary="Generado exitosamente con OpenRouter",
        blocks=blocks,
        mcp_tool_trace=trace,
    )


def generate_resource_gemini(
    week: SilaboWeek,
    concordance: WeekConcordance | None,
    request: GenerationRequest,
    forced_tool: str | None = None,
) -> GeneratedResource:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY (o GOOGLE_API_KEY) no está configurada. La generación de recursos requiere una "
            "clave de API de Gemini."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = _build_prompt(week, concordance, request, forced_tool=forced_tool)

    def build_interactive_activity(title: str, items: list[dict], instructions: str = "") -> str:
        """Crea una actividad de autoevaluación (opción múltiple con retroalimentación) autónoma en HTML."""
        return ""

    def render_diagram(title: str, nodes: list[dict], edges: list[dict]) -> str:
        """Crea un diagrama de nodos y flechas (mapa conceptual o proceso) en SVG."""
        return ""

    def build_word_search(title: str, words: list[str], instructions: str = "") -> str:
        """Crea una sopa de letras interactiva para reforzar vocabulario clave."""
        return ""

    def build_flashcards(title: str, cards: list[dict], instructions: str = "") -> str:
        """Crea una colección de tarjetas de estudio 3D (flashcards giratorias)."""
        return ""

    def build_study_guide(title: str, summary: str, sections: list[dict]) -> str:
        """Crea una ficha o guía de estudio sintética infográfica con secciones e ideas clave."""
        return ""

    def build_crossword(title: str, items: list[dict], instructions: str = "") -> str:
        """Crea un crucigrama interactivo autónomo en HTML/CSS."""
        return ""

    def build_logic_puzzle(title: str, mode: str, pairs: list[dict] = [], sequence: list[str] = [], instructions: str = "") -> str:
        """Crea un rompecabezas de lógica y relación (emparejar columnas o secuencia ordenada)."""
        return ""

    models_to_try = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    response = None
    last_error = None
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[
                            build_interactive_activity,
                            render_diagram,
                            build_word_search,
                            build_flashcards,
                            build_study_guide,
                            build_crossword,
                            build_logic_puzzle,
                        ],
                        temperature=0.7,
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(
                                mode=types.FunctionCallingConfigMode.ANY
                            )
                        ),
                    ),
                )
                if response:
                    break
            except Exception as exc:
                last_error = exc
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    import time
                    time.sleep(2)
                    continue
                break
        if response:
            break

    if response is None:
        raise RuntimeError(f"Fallo en la llamada a Gemini. Último error: {last_error}")

    blocks: list[ResourceBlock] = []
    trace: list[str] = []

    function_calls = getattr(response, "function_calls", None) or []
    if not function_calls and hasattr(response, "candidates") and response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        function_calls.append(part.function_call)

    for call in function_calls:
        tool_name = call.name
        for known_name in _TOOL_IMPLS:
            if known_name in tool_name:
                tool_name = known_name
                break

        impl = _TOOL_IMPLS.get(tool_name)
        if impl is None:
            trace.append(f"{tool_name}: herramienta desconocida, ignorada")
            continue

        schema_cls, fn, block_type = impl
        raw_args = dict(call.args) if hasattr(call, "args") and call.args else {}

        try:
            validated = schema_cls.model_validate(raw_args)
        except Exception as exc:
            trace.append(f"{tool_name}: entrada inválida ({exc})")
            continue

        rendered_html = fn(validated)
        title = getattr(validated, "title", tool_name)
        blocks.append(
            ResourceBlock(type=block_type, title=title, payload=raw_args, rendered_html=rendered_html)
        )
        trace.append(f"{tool_name}: ok")

    if not blocks:
        raise RuntimeError(
            "El modelo Gemini no produjo ningún bloque válido a través de las herramientas disponibles."
        )

    return GeneratedResource(
        title=blocks[0].title or f"Recurso — Semana {week.week_number}",
        week_number=week.week_number,
        topic=week.topic,
        intent=request.intent,
        summary="Generado exitosamente con Gemini",
        blocks=blocks,
        mcp_tool_trace=trace,
    )


def generate_resource_anthropic(
    week: SilaboWeek,
    concordance: WeekConcordance | None,
    request: GenerationRequest,
    forced_tool: str | None = None,
) -> GeneratedResource:
    api_key = ANTHROPIC_API_KEY.strip()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY no está configurada. La generación de recursos requiere una "
            "clave de API de Anthropic."
        )

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    prompt = _build_prompt(week, concordance, request, forced_tool=forced_tool)

    models_to_try = [GENERATION_MODEL, "claude-sonnet-4-6", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    response = None
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                tools=_TOOL_SPECS,
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": prompt}],
            )
            if response:
                break
        except Exception as exc:
            last_error = exc
            continue

    if response is None:
        raise RuntimeError(f"Fallo en la llamada a Anthropic Claude. Último error: {last_error}")

    blocks: list[ResourceBlock] = []
    trace: list[str] = []
    for content in response.content:
        if getattr(content, "type", None) != "tool_use":
            continue
        tool_name = content.name
        impl = _TOOL_IMPLS.get(tool_name)
        if impl is None:
            trace.append(f"{tool_name}: herramienta desconocida, ignorada")
            continue
        schema_cls, fn, block_type = impl
        try:
            validated = schema_cls.model_validate(content.input)
        except Exception as exc:
            trace.append(f"{tool_name}: entrada inválida ({exc})")
            continue
        rendered_html = fn(validated)
        title = getattr(validated, "title", tool_name)
        blocks.append(
            ResourceBlock(type=block_type, title=title, payload=content.input, rendered_html=rendered_html)
        )
        trace.append(f"{tool_name}: ok")

    if not blocks:
        raise RuntimeError(
            "El modelo no produjo ningún bloque válido a través de las herramientas disponibles."
        )

    return GeneratedResource(
        title=blocks[0].title or f"Recurso — Semana {week.week_number}",
        week_number=week.week_number,
        topic=week.topic,
        intent=request.intent,
        summary=response.stop_reason or "",
        blocks=blocks,
        mcp_tool_trace=trace,
    )


def generate_resource_deepseek(
    week: SilaboWeek,
    concordance: WeekConcordance | None,
    request: GenerationRequest,
    forced_tool: str | None = None,
) -> GeneratedResource:
    api_key = DEEPSEEK_API_KEY.strip() or os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY no está configurada. La generación de recursos requiere una clave de DeepSeek API."
        )

    prompt = _build_prompt(week, concordance, request, forced_tool=forced_tool)
    base_url = DEEPSEEK_BASE_URL.rstrip("/")
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    tools_payload = [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": impl[0].__doc__ or name,
                "parameters": _get_clean_tool_schema(impl[0]),
            },
        }
        for name, impl in _TOOL_IMPLS.items()
    ]

    payload = {
        "model": DEEPSEEK_MODEL or "deepseek-chat",
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}],
        "tools": tools_payload,
        "tool_choice": "required",
    }

    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=35)
        if r.status_code != 200:
            raise RuntimeError(f"DeepSeek API error {r.status_code}: {r.text}")
        response_data = r.json()
    except Exception as exc:
        raise RuntimeError(f"Fallo en la llamada a DeepSeek API: {exc}")

    blocks: list[ResourceBlock] = []
    trace: list[str] = []

    choices = response_data.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        tool_calls = msg.get("tool_calls") or []

        for call in tool_calls:
            func = call.get("function") or {}
            tool_name = func.get("name") or ""
            raw_args_str = func.get("arguments") or "{}"

            impl = _TOOL_IMPLS.get(tool_name)
            if impl is None:
                trace.append(f"{tool_name}: herramienta desconocida, ignorada")
                continue

            schema_cls, fn, block_type = impl
            try:
                raw_args = json.loads(raw_args_str) if isinstance(raw_args_str, str) else raw_args_str
                validated = schema_cls.model_validate(raw_args)
            except Exception as exc:
                trace.append(f"{tool_name}: entrada inválida ({exc})")
                continue

            rendered_html = fn(validated)
            title = getattr(validated, "title", tool_name)
            blocks.append(
                ResourceBlock(type=block_type, title=title, payload=raw_args, rendered_html=rendered_html)
            )
            trace.append(f"{tool_name}: ok")

    if not blocks:
        raise RuntimeError(
            "El modelo DeepSeek no produjo ningún bloque válido a través de las herramientas disponibles."
        )

    return GeneratedResource(
        title=blocks[0].title or f"Recurso — Semana {week.week_number}",
        week_number=week.week_number,
        topic=week.topic,
        intent=request.intent,
        summary="Generado exitosamente con DeepSeek V4 Flash",
        blocks=blocks,
        mcp_tool_trace=trace,
    )


def generate_resource(
    week: SilaboWeek,
    concordance: WeekConcordance | None = None,
    request: GenerationRequest = None,
    forced_tool: str | None = None,
) -> GeneratedResource:
    provider = LLM_PROVIDER.lower().strip()
    if provider == "deepseek" or DEEPSEEK_API_KEY:
        return generate_resource_deepseek(week, concordance, request, forced_tool=forced_tool)
    elif provider == "openrouter" or (not provider and OPENROUTER_API_KEY):
        return generate_resource_openrouter(week, concordance, request, forced_tool=forced_tool)
    elif provider == "gemini" or (not provider and GEMINI_API_KEY):
        return generate_resource_gemini(week, concordance, request, forced_tool=forced_tool)
    elif provider == "anthropic" or ANTHROPIC_API_KEY:
        return generate_resource_anthropic(week, concordance, request, forced_tool=forced_tool)
    else:
        raise RuntimeError(
            "No se ha configurado ninguna API Key válida (DEEPSEEK_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY o ANTHROPIC_API_KEY)."
        )

