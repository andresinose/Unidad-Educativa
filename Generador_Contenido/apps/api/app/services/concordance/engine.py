"""Generic concordance engine: compares a SilaboExtraction against a GuiaExtraction
week by week, purely by competency-code and week-presence matching — no
subject-specific rules. This is the same logic validated manually against a
real Math Unit 1 pair (see concordancia_silabo_guia_u1.json at the project
root), generalized to run on any subject/grade.
"""
from __future__ import annotations

from app.schemas.concordance import ConcordanceResult, ConcordanceStatus, WeekConcordance
from app.schemas.extraction import GuiaExtraction, SilaboExtraction

ADAPTATION_KEYWORD = "ADAPTA"


def _guia_topic_for_week(guia: GuiaExtraction, week_number: int) -> str:
    for section in guia.sections:
        if section.week_number == week_number and section.lesson_title:
            return section.lesson_title
    return ""


def _guia_page_range(guia: GuiaExtraction, week_number: int) -> str | None:
    pages = [s.page_start for s in guia.sections if s.week_number == week_number]
    if not pages:
        return None
    return f"{min(pages)}-{max(pages)}"


def _guia_has_adaptation_content(guia: GuiaExtraction, week_number: int) -> bool:
    return any(
        ADAPTATION_KEYWORD in s.section_type
        for s in guia.sections
        if s.week_number == week_number
    )


def build_concordance(silabo: SilaboExtraction, guia: GuiaExtraction) -> ConcordanceResult:
    silabo_by_week = {w.week_number: w for w in silabo.weeks}
    all_weeks = sorted(set(silabo_by_week) | set(guia.weeks_detected))

    weeks: list[WeekConcordance] = []
    for wn in all_weeks:
        s = silabo_by_week.get(wn)
        guia_codes = guia.competency_codes_by_week.get(wn, [])
        in_guia = wn in guia.weeks_detected
        adaptation_in_silabo = bool(s.adaptations) if s else False
        adaptation_in_guia = _guia_has_adaptation_content(guia, wn)

        if s is None:
            status = ConcordanceStatus.FALTANTE_EN_SILABO
            observation = f"La semana {wn} tiene contenido en la guía pero no está definida en el sílabo."
            missing_codes: list[str] = []
        elif not in_guia:
            status = ConcordanceStatus.FALTANTE_EN_GUIA
            observation = (
                f"La semana {wn} está definida en el sílabo ('{s.topic}') pero no tiene "
                "ninguna lección desarrollada en la guía didáctica."
            )
            missing_codes = list(s.competency_codes)
        else:
            missing_codes = [c for c in s.competency_codes if c not in guia_codes]
            if not missing_codes:
                status = ConcordanceStatus.CONCORDANTE
                observation = "Los códigos de competencia del sílabo están cubiertos en la guía."
            else:
                status = ConcordanceStatus.PARCIAL
                observation = (
                    "Algunos códigos de competencia del sílabo no aparecen en la guía: "
                    + ", ".join(missing_codes) + "."
                )

        weeks.append(
            WeekConcordance(
                week_number=wn,
                topic=(s.topic if s else _guia_topic_for_week(guia, wn)),
                silabo_codes=s.competency_codes if s else [],
                guia_codes=guia_codes,
                missing_codes_in_guia=missing_codes,
                page_range_guia=_guia_page_range(guia, wn),
                adaptation_in_silabo=adaptation_in_silabo,
                adaptation_in_guia=adaptation_in_guia,
                status=status,
                observation=observation,
            )
        )

    key_findings: list[str] = []
    missing_weeks = [w for w in weeks if w.status == ConcordanceStatus.FALTANTE_EN_GUIA]
    if missing_weeks:
        nums = ", ".join(str(w.week_number) for w in missing_weeks)
        key_findings.append(
            f"Las semanas {nums} están definidas en el sílabo pero no tienen desarrollo en la guía didáctica."
        )
    partial_weeks = [w for w in weeks if w.status == ConcordanceStatus.PARCIAL]
    if partial_weeks:
        nums = ", ".join(str(w.week_number) for w in partial_weeks)
        key_findings.append(f"Las semanas {nums} tienen cobertura parcial: algunos códigos del sílabo faltan en la guía.")
    adaptation_gap_weeks = [
        w for w in weeks if w.adaptation_in_silabo and not w.adaptation_in_guia
    ]
    if adaptation_gap_weeks:
        key_findings.append(
            "Ninguna de las semanas con adaptación curricular individual en el sílabo tiene "
            "contenido adaptado equivalente detectado en la guía "
            f"({len(adaptation_gap_weeks)} semana(s))."
        )
    if not key_findings:
        key_findings.append("No se detectaron brechas estructurales entre el sílabo y la guía.")

    return ConcordanceResult(
        weeks=weeks,
        key_findings=key_findings,
        concordant_count=sum(1 for w in weeks if w.status == ConcordanceStatus.CONCORDANTE),
        partial_count=sum(1 for w in weeks if w.status == ConcordanceStatus.PARCIAL),
        missing_count=sum(
            1 for w in weeks
            if w.status in (ConcordanceStatus.FALTANTE_EN_GUIA, ConcordanceStatus.FALTANTE_EN_SILABO)
        ),
    )
