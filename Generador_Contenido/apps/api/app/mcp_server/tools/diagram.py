"""render_diagram — concept-map and flow renderer with rich visual styling.

Renders boxes, nodes, and labeled arrows from a structured node/edge list
directly to a modern, responsive SVG in pure Python.
"""
from __future__ import annotations

import html
from pydantic import BaseModel, Field

BOX_HEIGHT = 65
BOX_MIN_WIDTH = 140
CHAR_WIDTH = 8
H_GAP = 60
V_GAP = 70
MARGIN = 40


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
    nodes: list[DiagramNode] = Field(min_length=1, max_length=12)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=30)


def _box_width(label: str) -> int:
    return max(BOX_MIN_WIDTH, len(label) * CHAR_WIDTH + 32)


def render_diagram(schema: DiagramSchema) -> str:
    """Returns a standalone, styled <svg>...</svg> string, safe to inline in HTML."""
    n_nodes = len(schema.nodes)
    cols = min(n_nodes, 4 if n_nodes > 4 else n_nodes)
    
    positions: dict[str, tuple[int, int, int]] = {}  # id -> (x, y, width)
    
    row_widths: list[int] = []
    current_x = MARGIN
    current_row = 0
    col_count = 0
    
    # Calculate grid layout
    for idx, node in enumerate(schema.nodes):
        w = _box_width(node.label)
        if col_count >= 4:
            current_row += 1
            current_x = MARGIN
            col_count = 0
        
        y = MARGIN + (60 if schema.title else 20) + current_row * (BOX_HEIGHT + V_GAP)
        positions[node.id] = (current_x, y, w)
        current_x += w + H_GAP
        col_count += 1

    # Total dimensions
    max_x = max((pos[0] + pos[2] for pos in positions.values()), default=400)
    max_y = max((pos[1] + BOX_HEIGHT for pos in positions.values()), default=300)
    total_width = max_x + MARGIN
    total_height = max_y + MARGIN

    # Color palette
    colors = {
        "concept": {"fill": "#EEF6FF", "stroke": "#2563EB", "text": "#1E40AF", "badge": "#3B82F6"},
        "process": {"fill": "#F0FDF4", "stroke": "#16A34A", "text": "#166534", "badge": "#22C55E"},
        "example": {"fill": "#FEF3C7", "stroke": "#D97706", "text": "#92400E", "badge": "#F59E0B"},
        "outcome": {"fill": "#F3E8FF", "stroke": "#9333EA", "text": "#6B21A8", "badge": "#A855F7"},
    }

    parts: list[str] = [
        f'<svg viewBox="0 0 {total_width} {total_height}" width="100%" height="auto" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="system-ui, -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" '
        f'role="img" aria-label="{html.escape(schema.title or "Diagrama Explicativo Visual")}">',
        '<style>',
        '  .node-box { transition: transform 0.2s ease, filter 0.2s ease; cursor: pointer; }',
        '  .node-box:hover { transform: translateY(-3px); filter: drop-shadow(0 8px 16px rgba(0,0,0,0.12)); }',
        '  .edge-line { stroke-dasharray: 800; animation: drawLine 1s ease-in-out forwards; }',
        '  .title-text { font-size: 18px; font-weight: 700; fill: #1E293B; }',
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

    # Render Connections (Edges)
    for edge in schema.edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        sx, sy, sw = positions[edge.source]
        tx, ty, tw = positions[edge.target]
        
        # Determine connector line coordinates
        if abs(sy - ty) < 10:  # Same row
            x1, y1 = sx + sw, sy + BOX_HEIGHT / 2
            x2, y2 = tx, ty + BOX_HEIGHT / 2
            path_d = f"M {x1} {y1} L {x2 - 4} {y2}"
            label_x, label_y = (x1 + x2) / 2, y1 - 8
        else:  # Different rows
            x1, y1 = sx + sw / 2, sy + BOX_HEIGHT
            x2, y2 = tx + tw / 2, ty
            mid_y = (y1 + y2) / 2
            path_d = f"M {x1} {y1} C {x1} {mid_y}, {x2} {mid_y}, {x2} {y2 - 4}"
            label_x, label_y = (x1 + x2) / 2, mid_y

        parts.append(
            f'<path d="{path_d}" fill="none" stroke="#94A3B8" stroke-width="2.5" '
            f'marker-end="url(#uei-arrow)" class="edge-line"/>'
        )
        
        if edge.label:
            bg_w = max(40, len(edge.label) * 7 + 12)
            parts.append(
                f'<rect x="{label_x - bg_w / 2}" y="{label_y - 12}" width="{bg_w}" height="18" '
                f'rx="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-size="11" '
                f'font-weight="500" fill="#475569">{html.escape(edge.label)}</text>'
            )

    # Render Nodes
    for node in schema.nodes:
        nx, ny, nw = positions[node.id]
        ntype = getattr(node, "node_type", "concept")
        theme = colors.get(ntype, colors["concept"])

        parts.append(f'<g class="node-box" filter="url(#shadow)">')
        # Main Box
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{nw}" height="{BOX_HEIGHT}" rx="12" '
            f'fill="{theme["fill"]}" stroke="{theme["stroke"]}" stroke-width="2"/>'
        )
        # Top color accent bar
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{nw}" height="5" rx="2" fill="{theme["badge"]}"/>'
        )
        # Text Label
        parts.append(
            f'<text x="{nx + nw / 2}" y="{ny + BOX_HEIGHT / 2 + 5}" text-anchor="middle" '
            f'font-size="13" font-weight="600" fill="{theme["text"]}">{html.escape(node.label)}</text>'
        )
        parts.append('</g>')

    parts.append("</svg>")
    return "".join(parts)
