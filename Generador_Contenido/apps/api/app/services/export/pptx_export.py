"""Renders a GeneratedResource into a .pptx, from the same structured
`block.payload` used to render HTML — not by parsing rendered_html — so
interactive elements degrade to readable static slides (e.g. a quiz becomes
one slide per question with the correct option marked) instead of being lost.
"""
from __future__ import annotations

import io

from pptx import Presentation
from pptx.util import Pt

from app.schemas.generation import GeneratedResource, ResourceBlockType


def _title_slide(prs: Presentation, resource: GeneratedResource) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = resource.title
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = resource.topic


def _bullet_slide(prs: Presentation, title: str, bullets: list[str]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title or "Recurso"
    body = slide.placeholders[1].text_frame
    body.clear()
    for i, bullet in enumerate(bullets or [""]):
        p = body.paragraphs[0] if i == 0 else body.add_paragraph()
        p.text = bullet
        p.font.size = Pt(18)


def _quiz_bullets(item: dict) -> list[str]:
    options = item.get("options", [])
    correct = item.get("correct_index")
    return [f"{'✓ ' if i == correct else '• '}{opt}" for i, opt in enumerate(options)]


def export_pptx(resource: GeneratedResource) -> bytes:
    prs = Presentation()
    _title_slide(prs, resource)

    for block in resource.blocks:
        if block.type == ResourceBlockType.interactive_activity:
            for item in block.payload.get("items", []):
                _bullet_slide(prs, item.get("question", block.title), _quiz_bullets(item))
        elif block.type == ResourceBlockType.diagram:
            nodes = block.payload.get("nodes", [])
            edges = block.payload.get("edges", [])
            bullets = [n.get("label", "") for n in nodes]
            bullets += [
                f"{e.get('source')} → {e.get('target')}" + (f" ({e.get('label')})" if e.get("label") else "")
                for e in edges
            ]
            _bullet_slide(prs, block.title or "Diagrama", bullets)
        else:
            _bullet_slide(prs, block.title or "Recurso", [block.title or ""])

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
