from __future__ import annotations

import re
import unicodedata

from fastapi import APIRouter
from fastapi.responses import Response

from app.schemas.generation import GeneratedResource
from app.services.export.html_export import export_html
from app.services.export.pptx_export import export_pptx

router = APIRouter(prefix="/export", tags=["export"])


def _slug(title: str) -> str:
    """ASCII-only slug — Content-Disposition filenames must stay within the
    header's allowed charset, so accents are stripped rather than encoded."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\-]+", "_", ascii_title.strip().lower()).strip("_")
    return slug or "recurso"


@router.post("/html")
async def export_html_endpoint(resource: GeneratedResource) -> Response:
    content = export_html(resource)
    filename = f"{_slug(resource.title)}.html"
    return Response(
        content=content,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/pptx")
async def export_pptx_endpoint(resource: GeneratedResource) -> Response:
    content = export_pptx(resource)
    filename = f"{_slug(resource.title)}.pptx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
