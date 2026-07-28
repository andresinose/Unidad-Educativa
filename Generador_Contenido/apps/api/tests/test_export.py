from app.mcp_server.tools.activity_builder import InteractiveActivitySchema, build_interactive_activity
from app.schemas.generation import GeneratedResource, ResourceBlock, ResourceBlockType
from app.services.export.html_export import export_html
from app.services.export.pptx_export import export_pptx


def _sample_resource() -> GeneratedResource:
    schema = InteractiveActivitySchema(
        title="Práctica: números enteros",
        items=[{"question": "¿2+2?", "options": ["3", "4"], "correct_index": 1}],
    )
    block = ResourceBlock(
        type=ResourceBlockType.interactive_activity,
        title=schema.title,
        payload=schema.model_dump(),
        rendered_html=build_interactive_activity(schema),
    )
    return GeneratedResource(
        title="Práctica: números enteros",
        week_number=1,
        topic="Representación y orden de enteros",
        intent="practicar",
        blocks=[block],
    )


def test_export_html_is_standalone_and_sanitized():
    html = export_html(_sample_resource())
    assert html.startswith("<!doctype html>")
    assert "Content-Security-Policy" in html
    assert "Práctica: números enteros" in html
    assert "<script>" in html  # the interactive activity's own script survives


def test_export_html_sanitizes_title_field():
    resource = _sample_resource()
    resource.title = "<img src=x onerror=alert(1)>Título"
    html = export_html(resource)
    assert "onerror" not in html


def test_export_pptx_produces_valid_openxml_bytes():
    data = export_pptx(_sample_resource())
    assert data[:2] == b"PK"  # pptx is a zip container
    assert len(data) > 1000
