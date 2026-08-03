"""render_diagram — concept-map and flow renderer with rich visual gamified styling.

Renders boxes, nodes, and labeled arrows from a structured node/edge list
directly to a modern, responsive SVG in pure Python.
"""
from __future__ import annotations

import html
from pydantic import BaseModel, Field

BOX_WIDTH = 240
H_GAP = 95  # Generous horizontal spacing so connection labels never overlap cards
V_GAP = 85  # Generous vertical spacing for clean arrow flow
MARGIN = 45


class DiagramNode(BaseModel):
    id: str
    label: str
    node_type: str = "concept"  # 'concept' | 'process' | 'example' | 'outcome'


class DiagramEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class DiagramSchema(BaseModel):
    title: str = ""
    diagram_type: str = "flow"  # 'flow' | 'concept_map'
    nodes: list[DiagramNode] = Field(min_length=1, max_length=15)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=30)


def _wrap_label(text: str, max_chars_per_line: int = 22) -> list[str]:
    words = (text or "").split()
    lines = []
    current_line = []
    current_length = 0

    for w in words:
        if current_length + len(w) + 1 > max_chars_per_line and current_line:
            lines.append(" ".join(current_line))
            current_line = [w]
            current_length = len(w)
        else:
            current_line.append(w)
            current_length += len(w) + 1

    if current_line:
        lines.append(" ".join(current_line))
    return lines or [text or ""]


def render_diagram(schema: DiagramSchema) -> str:
    """Returns a standalone, styled <svg>...</svg> string, safe to inline in HTML."""
    # Didactic simplification: Limit to max 6 key nodes to keep diagram clean and learning-functional
    nodes = schema.nodes[:6]
    valid_ids = {n.id for n in nodes}
    edges = [e for e in schema.edges if e.source in valid_ids and e.target in valid_ids][:8]

    n_nodes = len(nodes)
    cols = 3 if n_nodes >= 3 else n_nodes
    
    positions: dict[str, tuple[int, int, int, int]] = {}  # id -> (x, y, width, height)
    
    # Node heights based on wrapped lines
    node_data: list[tuple[DiagramNode, list[str], int]] = []
    for node in nodes:
        lines = _wrap_label(node.label, max_chars_per_line=22)
        h = max(95, len(lines) * 18 + 44)
        node_data.append((node, lines, h))

    current_row = 0
    row_nodes: list[list[tuple[DiagramNode, list[str], int]]] = [[]]

    for item in node_data:
        if len(row_nodes[current_row]) >= cols:
            current_row += 1
            row_nodes.append([])
        row_nodes[current_row].append(item)

    current_y = MARGIN + (50 if schema.title else 20)

    for row in row_nodes:
        if not row:
            continue
        max_h_in_row = max(item[2] for item in row)
        start_x = MARGIN

        for i, (node, lines, h) in enumerate(row):
            x = start_x + i * (BOX_WIDTH + H_GAP)
            positions[node.id] = (x, current_y, BOX_WIDTH, h)

        current_y += max_h_in_row + V_GAP

    # Total dimensions
    max_x = max((pos[0] + pos[2] for pos in positions.values()), default=400)
    max_y = max((pos[1] + pos[3] for pos in positions.values()), default=300)
    total_width = max_x + MARGIN
    total_height = max_y + MARGIN

    # Color themes & icons
    themes = {
        "concept": {
            "bg": "#EEF6FF", "border": "#3B82F6", "text": "#1E40AF", "badge_bg": "#3B82F6",
            "badge_text": "#FFFFFF", "icon": "💡", "label": "Concepto"
        },
        "process": {
            "bg": "#F0FDF4", "border": "#22C55E", "text": "#166534", "badge_bg": "#22C55E",
            "badge_text": "#FFFFFF", "icon": "⚡", "label": "Paso / Acción"
        },
        "example": {
            "bg": "#FEF3C7", "border": "#F59E0B", "text": "#92400E", "badge_bg": "#F59E0B",
            "badge_text": "#FFFFFF", "icon": "🔍", "label": "Ejemplo Práctico"
        },
        "outcome": {
            "bg": "#F3E8FF", "border": "#A855F7", "text": "#6B21A8", "badge_bg": "#A855F7",
            "badge_text": "#FFFFFF", "icon": "🎯", "label": "Resultado / Regla"
        },
    }

    parts: list[str] = [
        f'<svg viewBox="0 0 {total_width} {total_height}" width="100%" height="auto" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="system-ui, -apple-system, sans-serif" '
        f'role="img" aria-label="{html.escape(schema.title or "Diagrama Explicativo Visual")}">',
        '<style>',
        '  .node-box { transition: transform 0.2s ease, filter 0.2s ease; cursor: pointer; }',
        '  .node-box:hover { transform: translateY(-4px); filter: drop-shadow(0 10px 20px rgba(0,0,0,0.12)); }',
        '  .edge-path { stroke-dasharray: 1000; animation: drawLine 1s ease-in-out forwards; }',
        '  .title-text { font-size: 20px; font-weight: 800; fill: #0F172A; letter-spacing: -0.5px; }',
        '</style>',
        '<defs>',
        '  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">',
        '    <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.08"/>',
        '  </filter>',
        '  <marker id="uei-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">',
        '    <path d="M0,0 L0,6 L9,3 z" fill="#64748B"/>',
        '  </marker>',
        '</defs>',
    ]

    # Render Header Title
    if schema.title:
        parts.append(
            f'<text x="{total_width / 2}" y="32" text-anchor="middle" class="title-text">'
            f'{html.escape(schema.title)}</text>'
        )

    # Render Connections (Paths first, then Labels on top so lines never cross over text)
    label_elements: list[str] = []

    for edge in edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        sx, sy, sw, sh = positions[edge.source]
        tx, ty, tw, th = positions[edge.target]
        
        # Smart connector math with clearance
        if abs(sy - ty) < 30:  # Horizontal connection in same row
            if sx < tx:
                x1, y1 = sx + sw, sy + sh / 2
                x2, y2 = tx - 4, ty + th / 2
            else:
                x1, y1 = sx, sy + sh / 2
                x2, y2 = tx + tw + 4, ty + th / 2
            path_d = f"M {x1} {y1} L {x2} {y2}"
            label_x, label_y = (x1 + x2) / 2, y1
        else:  # Vertical/Diagonal flow across rows
            x1, y1 = sx + sw / 2, sy + sh
            x2, y2 = tx + tw / 2, ty - 4
            mid_y = (y1 + y2) / 2
            path_d = f"M {x1} {y1} C {x1} {mid_y}, {x2} {mid_y}, {x2} {y2}"
            label_x, label_y = (x1 + x2) / 2, mid_y

        parts.append(
            f'<path d="{path_d}" fill="none" stroke="#94A3B8" stroke-width="2.5" '
            f'marker-end="url(#uei-arrow)" class="edge-path"/>'
        )
        
        if edge.label:
            edge_text = edge.label[:22] + "..." if len(edge.label) > 24 else edge.label
            bg_w = max(45, len(edge_text) * 7.5 + 16)
            label_elements.append(
                f'<g class="edge-label-group">'
                f'<rect x="{label_x - bg_w / 2}" y="{label_y - 11}" width="{bg_w}" height="22" '
                f'rx="11" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5"/>'
                f'<text x="{label_x}" y="{label_y + 4}" text-anchor="middle" font-size="11" '
                f'font-weight="600" fill="#334155">{html.escape(edge_text)}</text>'
                f'</g>'
            )

    # Append all connection label pills on top of lines
    parts.extend(label_elements)

    # Render Nodes on top
    for node, lines, h in node_data:
        nx, ny, nw, nh = positions[node.id]
        ntype = getattr(node, "node_type", "concept")
        theme = themes.get(ntype, themes["concept"])

        parts.append(f'<g class="node-box" filter="url(#shadow)">')
        # Main Card Body
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="14" '
            f'fill="{theme["bg"]}" stroke="{theme["border"]}" stroke-width="2"/>'
        )
        # Top Color Accent Bar
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{nw}" height="6" rx="2" fill="{theme["badge_bg"]}"/>'
        )
        # Badge Pill
        badge_text = f'{theme["icon"]} {theme["label"]}'
        parts.append(
            f'<rect x="{nx + 12}" y="{ny + 14}" width="110" height="20" rx="10" fill="{theme["badge_bg"]}"/>'
        )
        parts.append(
            f'<text x="{nx + 67}" y="{ny + 28}" text-anchor="middle" font-size="10.5" '
            f'font-weight="700" fill="{theme["badge_text"]}">{badge_text}</text>'
        )

        # Multi-line Text Label
        start_text_y = ny + 54
        parts.append(f'<text x="{nx + nw / 2}" y="{start_text_y}" text-anchor="middle" font-size="12" font-weight="700" fill="{theme["text"]}">')
        for i, ltext in enumerate(lines):
            dy_val = "18" if i > 0 else "0"
            parts.append(f'<tspan x="{nx + nw / 2}" dy="{dy_val}">{html.escape(ltext)}</tspan>')
        parts.append('</text>')
        parts.append('</g>')

    parts.append("</svg>")
    return "".join(parts)
