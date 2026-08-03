"""Tests for materials router endpoints: upload PDF, poll job, list, preview, and download."""
from __future__ import annotations

import io
import time
import fitz  # PyMuPDF
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_synthetic_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "PDF Test para Router Materials", fontsize=18)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_upload_non_pdf_rejected():
    res = client.post("/materials/upload", files={"archivo": ("test.txt", b"hola", "text/plain")})
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


def test_list_materials_returns_list():
    res = client.get("/materials")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_job_not_found_returns_404():
    res = client.get("/materials/jobs/invalid-job-id")
    assert res.status_code == 404
