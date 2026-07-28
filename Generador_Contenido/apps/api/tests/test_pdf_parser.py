from pathlib import Path

from app.services.parsing.pdf_parser import parse_guia_pdf

FIXTURE = Path(__file__).parent / "fixtures" / "guia_matematica_8vo_u1.pdf"


def test_detects_cover_subject_and_grade():
    result = parse_guia_pdf(FIXTURE)
    assert result.subject == "Matemática"
    assert "EGB" in result.grade
    assert result.total_pages == 95


def test_only_weeks_0_to_4_have_content():
    """The real guía only develops Weeks 0-4 even though the sílabo defines
    Weeks 0-6 — this is the structural gap the whole project is built to catch."""
    result = parse_guia_pdf(FIXTURE)
    assert result.weeks_detected == [0, 1, 2, 3, 4]
    assert 5 not in result.weeks_detected
    assert 6 not in result.weeks_detected


def test_competency_codes_match_expected_per_week():
    result = parse_guia_pdf(FIXTURE)
    assert "8.SUP.A.R.L.M.1.1.1" in result.competency_codes_by_week[1]
    assert "8.SUP.G.F.E.4.1.1" in result.competency_codes_by_week[2]


def test_known_sections_detected_for_every_week():
    result = parse_guia_pdf(FIXTURE)
    for week in result.weeks_detected:
        section_types = {s.section_type for s in result.sections if s.week_number == week}
        assert "EXPLORA_Y_CONECTA" in section_types
        assert "IDEA_CLAVE" in section_types
