from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.generation import GeneratedResource, PedagogicalIntent, ResourceBlock, ResourceBlockType

client = TestClient(app)
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_activities_upload_and_weeks():
    docx_path = FIXTURES_DIR / "silabo_matematica_8vo_u1.docx"
    assert docx_path.exists()

    with docx_path.open("rb") as f:
        resp = client.post("/activities/upload", files={"silabo": ("silabo.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    session_id = data["session_id"]
    assert "silabo" in data
    assert len(data["silabo"]["weeks"]) > 0

    weeks_resp = client.get(f"/activities/{session_id}/weeks")
    assert weeks_resp.status_code == 200
    w_data = weeks_resp.json()
    assert len(w_data["weeks"]) > 0


@patch("app.routers.activities.generate_resource")
def test_activities_generate_and_pdf(mock_gen):
    mock_resource = GeneratedResource(
        title="Crucigrama de Matemática",
        week_number=1,
        topic="Operaciones enteras",
        intent=PedagogicalIntent.reforzar,
        summary="Mock ok",
        blocks=[
            ResourceBlock(
                type=ResourceBlockType.crossword,
                title="Crucigrama 1",
                payload={"instructions": "Resuelve", "items": [{"word": "SUMA", "clue": "Adición"}]},
                rendered_html="<div>Mock HTML</div>",
            )
        ],
    )
    mock_gen.return_value = mock_resource

    docx_path = FIXTURES_DIR / "silabo_matematica_8vo_u1.docx"
    with docx_path.open("rb") as f:
        upload_resp = client.post("/activities/upload", files={"silabo": ("silabo.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    session_id = upload_resp.json()["session_id"]

    gen_resp = client.post("/activities/generate", json={
        "session_id": session_id,
        "week_number": 1,
        "resource_type": "crossword",
        "extra_instructions": "Hacer énfasis en adición",
    })

    assert gen_resp.status_code == 200
    res_data = gen_resp.json()
    assert res_data["title"] == "Crucigrama de Matemática"
    assert len(res_data["blocks"]) == 1

    pdf_resp = client.get(f"/activities/{session_id}/download/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")
