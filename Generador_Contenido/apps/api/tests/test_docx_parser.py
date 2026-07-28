from pathlib import Path

from app.services.parsing.docx_parser import parse_silabo_docx

FIXTURE = Path(__file__).parent / "fixtures" / "silabo_matematica_8vo_u1.docx"


def test_parses_informational_fields():
    result = parse_silabo_docx(FIXTURE)
    assert result.subject == "Matemática"
    assert result.grade == "Octavo"
    assert result.parallels == "A-B-C"
    assert result.unit_name == "Números enteros"
    assert result.trimester == "1"
    assert result.parcial == "1"
    assert result.start_date == "01/09/2026"
    assert result.end_date == "16/10/2026"
    assert not result.warnings


def test_detects_all_seven_weeks():
    result = parse_silabo_docx(FIXTURE)
    assert [w.week_number for w in result.weeks] == [0, 1, 2, 3, 4, 5, 6]


def test_extracts_competency_codes_per_week():
    result = parse_silabo_docx(FIXTURE)
    week1 = next(w for w in result.weeks if w.week_number == 1)
    assert "8.SUP.A.R.L.M.1.1.1" in week1.competency_codes


def test_extracts_methodology_phases():
    result = parse_silabo_docx(FIXTURE)
    week0 = next(w for w in result.weeks if w.week_number == 0)
    assert week0.methodology_phases.activacion
    assert week0.methodology_phases.construccion
    assert week0.methodology_phases.consolidacion


def test_every_week_has_three_anonymized_adaptations():
    result = parse_silabo_docx(FIXTURE)
    for week in result.weeks:
        assert len(week.adaptations) == 3
        refs = {a.student_ref for a in week.adaptations}
        assert refs == {"Estudiante A", "Estudiante B", "Estudiante C"}
        for adaptation in week.adaptations:
            assert "Ayala" not in adaptation.student_ref
            assert "García" not in adaptation.student_ref
            assert "Quiroga" not in adaptation.student_ref


def test_same_student_gets_same_pseudonym_across_weeks():
    result = parse_silabo_docx(FIXTURE)
    week0_dyslexia = next(a for a in result.weeks[0].adaptations if "dislexia" in a.need_description.lower())
    week1_dyslexia = next(a for a in result.weeks[1].adaptations if "dislexia" in a.need_description.lower())
    assert week0_dyslexia.student_ref == week1_dyslexia.student_ref == "Estudiante A"
