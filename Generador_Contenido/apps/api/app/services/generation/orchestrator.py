"""Generation orchestrator: an LLM (Claude) picks *what* pedagogical content to
produce, grounded in one already-validated sílabo week, but can only render it
through the whitelisted MCP tools (app/mcp_server/tools/*) — never by emitting
HTML/JS directly. This is the same security property described in the plan:
content decisions come from the model, rendering is deterministic and typed.
"""
from __future__ import annotations

from anthropic import Anthropic

from app.core.config import ANTHROPIC_API_KEY, GENERATION_MODEL
from app.mcp_server.tools.activity_builder import InteractiveActivitySchema, build_interactive_activity
from app.mcp_server.tools.diagram import DiagramSchema, render_diagram
from app.schemas.concordance import WeekConcordance
from app.schemas.extraction import SilaboWeek
from app.schemas.generation import GeneratedResource, GenerationRequest, ResourceBlock, ResourceBlockType

_TOOL_SPECS = [
    {
        "name": "build_interactive_activity",
        "description": (
            "Crea una actividad de autoevaluación (opción múltiple con retroalimentación) "
            "autónoma en HTML, útil para practicar, reforzar o comprobar comprensión."
        ),
        "input_schema": InteractiveActivitySchema.model_json_schema(),
    },
    {
        "name": "render_diagram",
        "description": (
            "Crea un diagrama de nodos y flechas (mapa conceptual o proceso) en SVG, útil "
            "para presentar, visualizar o comparar un tema."
        ),
        "input_schema": DiagramSchema.model_json_schema(),
    },
]

_TOOL_IMPLS: dict[str, tuple[type, callable, ResourceBlockType]] = {
    "build_interactive_activity": (InteractiveActivitySchema, build_interactive_activity, ResourceBlockType.interactive_activity),
    "render_diagram": (DiagramSchema, render_diagram, ResourceBlockType.diagram),
}


def _anonymized_adaptations_summary(week: SilaboWeek) -> str:
    """Never pass real student names/identifiers to the LLM — only the anonymized
    pseudonym assigned during parsing (see docx_parser._Anonymizer) and the need."""
    if not week.adaptations:
        return "(sin adaptaciones registradas)"
    return "\n".join(
        f"- {a.student_ref}: {a.need_description or 'necesidad no especificada'}"
        for a in week.adaptations
    )


def _build_prompt(week: SilaboWeek, concordance: WeekConcordance, request: GenerationRequest) -> str:
    return f"""Eres un asistente pedagógico. Genera UN recurso didáctico para la siguiente semana de
planificación curricular, usando EXCLUSIVAMENTE una de las herramientas disponibles — nunca
respondas con HTML/JS directamente, y no expliques tu razonamiento fuera de la llamada a la
herramienta.

Semana {week.week_number}: {week.topic}
Códigos de competencia: {', '.join(week.competency_codes) or '(sin códigos)'}
Contenido central de la clase (fase de construcción): {week.methodology_phases.construccion or '(no especificada)'}
Nivel de logro esperado: {week.achievement_level or '(no especificado)'}
Estado de concordancia con la guía didáctica: {concordance.status.value} — {concordance.observation}

Adaptaciones curriculares registradas para esta semana (identificadores ya anonimizados; ten en
cuenta estas necesidades al diseñar el recurso, pero no las menciones explícitamente en el
contenido generado):
{_anonymized_adaptations_summary(week)}

Intención pedagógica solicitada por el docente: {request.intent.value}
Instrucciones adicionales del docente: {request.extra_instructions or '(ninguna)'}

Elige la herramienta más apropiada para esa intención y llámala con datos completos y
pedagógicamente correctos para el tema de esta semana."""


def generate_resource(
    week: SilaboWeek, concordance: WeekConcordance, request: GenerationRequest
) -> GeneratedResource:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY no está configurada. La generación de recursos requiere una "
            "clave de API de Anthropic (variable de entorno ANTHROPIC_API_KEY)."
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = _build_prompt(week, concordance, request)

    response = client.messages.create(
        model=GENERATION_MODEL,
        max_tokens=4096,
        tools=_TOOL_SPECS,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

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
        except Exception as exc:  # noqa: BLE001 — recorded in the trace, not fatal
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
