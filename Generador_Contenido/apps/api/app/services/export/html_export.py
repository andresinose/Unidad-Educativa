"""Renders a GeneratedResource into a single standalone HTML file.

Block content (`block.rendered_html`) is already safe by construction — it
comes only from our own deterministic renderers (activity_builder.py,
diagram.py), which html.escape() every interpolated value themselves; the
LLM never supplies raw markup. Free-text fields that flow through less
controlled paths (title, topic, summary) are still explicitly sanitized
here with bleach as defense in depth. A restrictive CSP (script/style must
be inline since this needs to be a single portable file; everything else
is blocked, with GeoGebra allow-listed for the one embeddable third party)
means it's safe to drop straight into a Canvas LMS iframe.
"""
from __future__ import annotations

import html

import bleach

from app.schemas.generation import GeneratedResource

_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
    "img-src data:; frame-src https://www.geogebra.org;"
)


def _clean_text(value: str) -> str:
    return bleach.clean(value or "", tags=[], strip=True)


def export_html(resource: GeneratedResource) -> str:
    title = html.escape(_clean_text(resource.title))
    topic = html.escape(_clean_text(resource.topic))
    blocks_html = "\n".join(
        f'<section class="uei-resource-block">{block.rendered_html}</section>' for block in resource.blocks
    )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{_CSP}">
<title>{title}</title>
<style>
  body {{ margin: 0; padding: 24px; background: #fff; color: #111; }}
  .uei-resource-header {{ max-width: 720px; margin: 0 auto 20px; font-family: system-ui, sans-serif; }}
  .uei-resource-block {{ margin-bottom: 32px; }}
  .uei-resource-footer {{ max-width: 720px; margin: 24px auto 0; font-family: system-ui, sans-serif;
    font-size: 0.8em; color: #888; text-align: center; }}
</style>
</head>
<body>
<div class="uei-resource-header">
  <h1>{title}</h1>
  {f'<p>{topic}</p>' if topic else ''}
</div>
{blocks_html}
<div class="uei-resource-footer">Generado por el Motor de análisis curricular y generación de recursos — Unidad Educativa Bilingüe Indoamérica.</div>
</body>
</html>"""
