"""Standalone MCP server exposing the resource-rendering tools.

Runs independently of the FastAPI backend (stdio transport) so it can be
attached to Claude Desktop or any other MCP client — the same tool
implementations also back the in-process generation orchestrator
(app/services/generation/orchestrator.py), so there is one source of truth
for what the LLM is allowed to render.

Run directly: `python -m app.mcp_server.server`
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from app.mcp_server.tools.activity_builder import InteractiveActivitySchema, build_interactive_activity
from app.mcp_server.tools.diagram import DiagramSchema, render_diagram

server = MCPServer(
    name="uei-recursos",
    title="Generador de recursos didácticos — Unidad Educativa Indoamérica",
    instructions=(
        "Herramientas para renderizar recursos didácticos interactivos a partir de datos "
        "estructurados. No aceptan HTML/JS arbitrario, solo esquemas tipados: el modelo decide "
        "el contenido pedagógico, estas herramientas deciden cómo se ve."
    ),
)


@server.tool(
    name="build_interactive_activity",
    description="Renderiza una actividad de autoevaluación (opción múltiple con retroalimentación) como HTML autónomo.",
)
def _build_interactive_activity(schema: InteractiveActivitySchema) -> str:
    return build_interactive_activity(schema)


@server.tool(
    name="render_diagram",
    description="Renderiza un diagrama de nodos y flechas (mapa conceptual o proceso) como SVG.",
)
def _render_diagram(schema: DiagramSchema) -> str:
    return render_diagram(schema)


if __name__ == "__main__":
    server.run()
