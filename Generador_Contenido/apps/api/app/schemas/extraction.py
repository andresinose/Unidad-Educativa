"""Structures extracted from the two uploaded documents, fully updated to Spec v1.2.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class MethodologyPhases(BaseModel):
    activacion: str = ""
    anticipacion: str = ""
    construccion: str = ""
    consolidacion: str = ""


class CurricularAdaptation(BaseModel):
    student_ref: str = Field(..., description="Anonymized reference e.g. 'Estudiante A'")
    need_description: str = ""
    grade_level: str = ""
    methodology_phases: MethodologyPhases = Field(default_factory=MethodologyPhases)
    achievement_level: str = ""


class SilaboWeek(BaseModel):
    week_number: int
    topic: str = ""
    subtemas: list[str] = Field(default_factory=list)
    competency_codes: list[str] = Field(default_factory=list)
    competencias_generales: list[str] = Field(default_factory=list)
    competencias_especificas: list[str] = Field(default_factory=list)
    methodology_phases: MethodologyPhases = Field(default_factory=MethodologyPhases)
    resources: list[str] = Field(default_factory=list)
    achievement_level: str = ""
    evaluation_technique: str = ""
    adaptations: list[CurricularAdaptation] = Field(default_factory=list)
    adaptaciones_count: int = 0
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
    periodos_semanales: str = "6"
    weeks: list[SilaboWeek] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GuiaPeriodoDetail(BaseModel):
    numero: int
    titulo: str
    pagina: int


class GuiaWeekDeveloped(BaseModel):
    numero: int
    tema: str = ""
    fechas: str = ""
    periodos: str = "6"
    objetivo: str = ""
    competencias: list[str] = Field(default_factory=list)
    pagina_inicio: int = 0
    pagina_fin: int = 0
    periodos_detalle: list[GuiaPeriodoDetail] = Field(default_factory=list)
    ruta_aprendizaje: list[str] = Field(default_factory=list)
    sintesis: list[str] = Field(default_factory=list)
    actividades: list[str] = Field(default_factory=list)


class GuiaSection(BaseModel):
    week_number: int | None = None
    lesson_title: str = ""
    section_type: str = Field(..., description="e.g. EXPLORA_Y_CONECTA, TALLER, SINTESIS")
    page_start: int
    page_end: int
    text_excerpt: str = ""


class GuiaExtraction(BaseModel):
    titulo: str = "MATERIAL PEDAGÓGICO"
    subject: str = ""
    grade: str = ""
    unit_name: str = ""
    fechas: str = ""
    semanas_mencionadas: list[int] = Field(default_factory=list)
    semanas_desarrolladas: list[GuiaWeekDeveloped] = Field(default_factory=list)
    weeks_detected: list[int] = Field(default_factory=list)
    competency_codes_by_week: dict[int, list[str]] = Field(default_factory=dict)
    sections: list[GuiaSection] = Field(default_factory=list)
    total_pages: int = 0
    warnings: list[str] = Field(default_factory=list)
