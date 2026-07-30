"""Comprehensive test suite for Spec v1.2 requirements.
"""
from pathlib import Path
import pytest
from fastapi import HTTPException

from app.schemas.concordance import ConcordanceStatus
from app.schemas.extraction import GuiaExtraction, GuiaPeriodoDetail, GuiaWeekDeveloped, SilaboExtraction, SilaboWeek
from app.services.concordance.engine import build_concordance
from app.services.concordance.subtopic_decomposer import descomponer_fallback
from app.services.concordance.text_utils import normalizar, similitud, tokens
from app.routers.documents import _validate_upload_bytes


def test_text_normalization_and_similarity():
    # Accent stripping & lowercasing
    assert normalizar("Fracciones Equivalentes") == "fracciones equivalentes"
    assert normalizar("Adición y sustracción de números enteros") == "adicion y sustraccion de numeros enteros"

    # Tokenizer
    t = tokens("Adición y sustracción de enteros")
    assert "adicio" in t

    # Similarity overlap over smaller set
    sim = similitud("interpreta el valor absoluto", "Valor absoluto")
    assert sim >= 0.5


def test_subtopic_decomposition_fallback():
    topic = "Diagnóstico y nivelación de aprendizajes requeridos: operaciones combinadas con números naturales. Criterios de divisibilidad. Resolución de problemas."
    subs = descomponer_fallback(topic)
    norm_subs = [normalizar(s) for s in subs]
    assert any("operaciones combinadas" in s for s in norm_subs)
    assert any("criterios de divisibilidad" in s for s in norm_subs)
    assert any("resolucion de problemas" in s for s in norm_subs)


def test_exact_verdict_threshold_boundaries():
    # 5 subtopics: 4 covered (80%) -> CUMPLE; 3 covered (60%) -> CUMPLE_PARCIAL; 2 covered (40%) -> NO_CUMPLE
    subtopics = ["sub1", "sub2", "sub3", "sub4", "sub5"]
    silabo = SilaboExtraction(
        weeks=[SilaboWeek(week_number=1, topic="Tema Test", subtemas=subtopics, competency_codes=["8.1"])]
    )

    # 4 covered (80%) -> CUMPLE
    guia_80 = GuiaExtraction(
        weeks_detected=[1],
        competency_codes_by_week={1: ["8.1"]},
        semanas_desarrolladas=[
            GuiaWeekDeveloped(
                numero=1,
                competencias=["8.1"],
                periodos_detalle=[
                    GuiaPeriodoDetail(numero=1, titulo="sub1", pagina=10),
                    GuiaPeriodoDetail(numero=2, titulo="sub2", pagina=12),
                    GuiaPeriodoDetail(numero=3, titulo="sub3", pagina=14),
                    GuiaPeriodoDetail(numero=4, titulo="sub4", pagina=16),
                ]
            )
        ]
    )
    res_80 = build_concordance(silabo, guia_80)
    w_80 = res_80.detalle_semanal[0]
    assert w_80.veredicto_semana == ConcordanceStatus.CUMPLE
    assert w_80.habilita_generacion is True

    # 3 covered (60%) -> CUMPLE_PARCIAL
    guia_60 = GuiaExtraction(
        weeks_detected=[1],
        competency_codes_by_week={1: ["8.1"]},
        semanas_desarrolladas=[
            GuiaWeekDeveloped(
                numero=1,
                competencias=["8.1"],
                periodos_detalle=[
                    GuiaPeriodoDetail(numero=1, titulo="sub1", pagina=10),
                    GuiaPeriodoDetail(numero=2, titulo="sub2", pagina=12),
                    GuiaPeriodoDetail(numero=3, titulo="sub3", pagina=14),
                ]
            )
        ]
    )
    res_60 = build_concordance(silabo, guia_60)
    w_60 = res_60.detalle_semanal[0]
    assert w_60.veredicto_semana == ConcordanceStatus.CUMPLE_PARCIAL
    assert w_60.habilita_generacion is False

    # 2 covered (40%) -> NO_CUMPLE
    guia_40 = GuiaExtraction(
        weeks_detected=[1],
        competency_codes_by_week={1: ["8.1"]},
        semanas_desarrolladas=[
            GuiaWeekDeveloped(
                numero=1,
                competencias=["8.1"],
                periodos_detalle=[
                    GuiaPeriodoDetail(numero=1, titulo="sub1", pagina=10),
                    GuiaPeriodoDetail(numero=2, titulo="sub2", pagina=12),
                ]
            )
        ]
    )
    res_40 = build_concordance(silabo, guia_40)
    w_40 = res_40.detalle_semanal[0]
    assert w_40.veredicto_semana == ConcordanceStatus.NO_CUMPLE
    assert w_40.habilita_generacion is False


def test_magic_bytes_validation(tmp_path):
    # Valid docx (PK\x03\x04)
    valid_docx = tmp_path / "valid.docx"
    valid_docx.write_bytes(b"PK\x03\x04_content_data")
    _validate_upload_bytes(valid_docx, ".docx")

    # Invalid docx (fake extension)
    invalid_docx = tmp_path / "fake.docx"
    invalid_docx.write_bytes(b"NOT_A_ZIP_HEADER")
    with pytest.raises(HTTPException) as exc_info:
        _validate_upload_bytes(invalid_docx, ".docx")
    assert exc_info.value.status_code == 415

    # Mock PDF (invalid/scanned PDF without selectable text)
    valid_pdf = tmp_path / "valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>\nendobj\ntrailer<<>>\n%%EOF")
    with pytest.raises(HTTPException) as exc_info_pdf:
        _validate_upload_bytes(valid_pdf, ".pdf")
    assert exc_info_pdf.value.status_code == 422
