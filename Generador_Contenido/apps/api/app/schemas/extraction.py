"""Structures extracted from the two uploaded documents.

Kept generic on purpose: nothing here is specific to Math/8th grade. The only
"template" assumption is the institution's own sílabo/guía layout (validated
against a real Math Unit 1 pair), not a particular subject.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class MethodologyPhases(BaseModel):
    activacion: str = ""
    anticipacion: str = ""
    construccion: str = ""
    consolidacion: str = ""


class CurricularAdaptation(BaseModel):
    student_ref: str = Field(..., description="Anonymized reference (e.g. 'Estudiante A'), never the real name past ingestion")
    need_description: str = ""
    grade_level: str = ""
    methodology_phases: MethodologyPhases = Field(default_factory=MethodologyPhases)
    achievement_level: str = ""


class SilaboWeek(BaseModel):
    week_number: int
    topic: str = ""
    competency_codes: list[str] = Field(default_factory=list)
    competency_labels: list[str] = Field(default_factory=list)
    methodology_phases: MethodologyPhases = Field(default_factory=MethodologyPhases)
    resources: list[str] = Field(default_factory=list)
    achievement_level: str = ""
    evaluation_technique: str = ""
    adaptations: list[CurricularAdaptation] = Field(default_factory=list)
    confidence: float = 1.0


class SilaboExtraction(BaseModel):
    subject: str = ""
    teacher: str = ""
    grade: str = ""
    parallels: str = ""
    unit_name: str = ""
    trimester: str = ""
    parcial: str = ""
    unit_objective: str = ""
    start_date: str = ""
    end_date: str = ""
    weeks: list[SilaboWeek] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GuiaSection(BaseModel):
    week_number: int | None = None
    lesson_title: str = ""
    section_type: str = Field(..., description="e.g. EXPLORA_Y_CONECTA, IDEA_CLAVE, REFUERZO_GRADUADO — see parsing config")
    page_start: int
    page_end: int
    text_excerpt: str = ""


class GuiaExtraction(BaseModel):
    subject: str = ""
    grade: str = ""
    weeks_detected: list[int] = Field(default_factory=list)
    competency_codes_by_week: dict[int, list[str]] = Field(default_factory=dict)
    sections: list[GuiaSection] = Field(default_factory=list)
    total_pages: int = 0
    warnings: list[str] = Field(default_factory=list)
