from pathlib import Path

from app.services.concordance.engine import build_concordance
from app.services.parsing.docx_parser import parse_silabo_docx
from app.services.parsing.pdf_parser import parse_guia_pdf

SILABO = Path(__file__).parent / "fixtures" / "silabo_matematica_8vo_u1.docx"
GUIA = Path(__file__).parent / "fixtures" / "guia_matematica_8vo_u1.pdf"


def _real_result():
    return build_concordance(parse_silabo_docx(SILABO), parse_guia_pdf(GUIA))


def test_reproduces_manually_validated_findings():
    """Matches the manual analysis in concordancia_silabo_guia_u1.json: weeks
    0-4 concordant, weeks 5-6 missing from the guía, no adaptations reflected
    in the guía for any week."""
    result = _real_result()
    by_week = {w.week_number: w for w in result.weeks}

    for wn in range(5):
        assert by_week[wn].status == "CONCORDANTE", f"week {wn}"
    for wn in (5, 6):
        assert by_week[wn].status == "FALTANTE_EN_GUIA", f"week {wn}"

    assert result.concordant_count == 5
    assert result.missing_count == 2
    assert result.partial_count == 0

    for week in result.weeks:
        assert week.adaptation_in_silabo is True
        assert week.adaptation_in_guia is False


def test_key_findings_mention_missing_weeks_and_adaptation_gap():
    result = _real_result()
    joined = " ".join(result.key_findings)
    assert "5" in joined and "6" in joined
    assert "adapta" in joined.lower()


def test_concordant_week_has_no_missing_codes():
    result = _real_result()
    week1 = next(w for w in result.weeks if w.week_number == 1)
    assert week1.missing_codes_in_guia == []
    assert set(week1.silabo_codes) == set(week1.guia_codes)


def test_synthetic_partial_week_detected():
    """A unit test independent of the real fixture: a week whose sílabo codes
    are only partially covered by the guía should be PARCIAL, not CONCORDANTE."""
    from app.schemas.extraction import GuiaExtraction, SilaboExtraction, SilaboWeek

    silabo = SilaboExtraction(
        weeks=[SilaboWeek(week_number=1, topic="x", competency_codes=["1.A.1", "1.A.2"])]
    )
    guia = GuiaExtraction(weeks_detected=[1], competency_codes_by_week={1: ["1.A.1"]})

    result = build_concordance(silabo, guia)
    week = result.weeks[0]
    assert week.status == "PARCIAL"
    assert week.missing_codes_in_guia == ["1.A.2"]
