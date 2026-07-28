"""render_diagram — a small, dependency-free concept-map / flow renderer.

The original plan referenced a `render_mermaid` tool. Real Mermaid.js
rendering needs a headless-browser toolchain (mermaid-cli + Puppeteer/
Chromium), which works against this project's "keep self-hosting simple"
goal. This renders the same *kind* of artifact — boxes and labeled arrows
from a structured node/edge list — directly to static SVG in pure Python,
so the LLM only ever supplies data, never markup or script.
"""
from __future__ import annotations

import html

from pydantic import BaseModel, Field

BOX_HEIGHT = 56
BOX_MIN_WIDTH = 120
CHAR_WIDTH = 8
H_GAP = 70
MARGIN = 30


class DiagramNode(BaseModel):
    id: str
    label: str


class DiagramEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class DiagramSchema(BaseModel):
    title: str = ""
    diagram_type: str = "flow"  # 'flow' | 'concept_map' — both use the same left-to-right layout
    nodes: list[DiagramNode] = Field(min_length=1, max_length=12)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=30)


def _box_width(label: str) -> int:
    return max(BOX_MIN_WIDTH, len(label) * CHAR_WIDTH + 24)


def render_diagram(schema: DiagramSchema) -> str:
    """Returns a standalone <svg>...</svg> string, safe to inline in HTML."""
    positions: dict[str, tuple[int, int, int]] = {}  # id -> (x, y, width)
    x = MARGIN
    y_center = MARGIN + BOX_HEIGHT // 2 + (20 if schema.title else 0)
    for node in schema.nodes:
        w = _box_width(node.label)
        positions[node.id] = (x, y_center - BOX_HEIGHT // 2, w)
        x += w + H_GAP

    total_width = x - H_GAP + MARGIN
    total_height = y_center + BOX_HEIGHT // 2 + MARGIN

    parts: list[str] = [
        f'<svg viewBox="0 0 {total_width} {total_height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="system-ui, sans-serif" role="img" aria-label="{html.escape(schema.title or "Diagrama")}">',
        "<defs><marker id='uei-arrow' markerWidth='10' markerHeight='10' refX='8' refY='3' "
        "orient='auto'><path d='M0,0 L0,6 L9,3 z' fill='#333'/></marker></defs>",
    ]
    if schema.title:
        parts.append(
            f'<text x="{total_width / 2}" y="20" text-anchor="middle" font-size="15" '
            f'font-weight="600" fill="#111">{html.escape(schema.title)}</text>'
        )

    for edge in schema.edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        sx, sy, sw = positions[edge.source]
        tx, ty, tw = positions[edge.target]
        x1, y1 = sx + sw, sy + BOX_HEIGHT / 2
        x2, y2 = tx, ty + BOX_HEIGHT / 2
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2 - 4}" y2="{y2}" stroke="#333" stroke-width="1.5" marker-end="url(#uei-arrow)"/>')
        if edge.label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 6
            parts.append(
                f'<text x="{mx}" y="{my}" text-anchor="middle" font-size="11" fill="#555">{html.escape(edge.label)}</text>'
            )

    for node in schema.nodes:
        nx, ny, nw = positions[node.id]
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{nw}" height="{BOX_HEIGHT}" rx="10" '
            f'fill="#eaf2fb" stroke="#1a73c1" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{nx + nw / 2}" y="{ny + BOX_HEIGHT / 2 + 5}" text-anchor="middle" '
            f'font-size="13" fill="#0d3a63">{html.escape(node.label)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
