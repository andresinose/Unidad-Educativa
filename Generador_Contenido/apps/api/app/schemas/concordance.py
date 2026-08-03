"""Concordance schemas according to Spec v1.2.
"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ConcordanceStatus(str, Enum):
    CUMPLE = "CUMPLE"
    CUMPLE_PARCIAL = "CUMPLE_PARCIAL"
    NO_CUMPLE = "NO_CUMPLE"
    # Legacy fallbacks for compatibility
    CONCORDANTE = "CONCORDANTE"
    PARCIAL = "PARCIAL"
    FALTANTE_EN_GUIA = "FALTANTE_EN_GUIA"
    FALTANTE_EN_SILABO = "FALTANTE_EN_SILABO"


class EstadoSubtema(str, Enum):
    CUBIERTO = "CUBIERTO"
    MENCIONADO = "MENCIONADO"
    AUSENTE = "AUSENTE"


class SubtemaEvidencia(BaseModel):
    texto: str
    estado: EstadoSubtema
    evidencia: str = ""
    fuentes: list[str] = Field(default_factory=list)


class MatrizSubtemas(BaseModel):
    cobertura: float = 0.0
    cubiertos: int = 0
    total: int = 0
    subtemas: list[SubtemaEvidencia] = Field(default_factory=list)
    enriquecimiento: list[str] = Field(default_factory=list)


class CoherenciaDetalle(BaseModel):
    ok: bool
    detalle: str
    confianza: str = "normal"


class CoherenciaTransversal(BaseModel):
    fechas: CoherenciaDetalle
    periodos: CoherenciaDetalle
    codigos_competencia: CoherenciaDetalle


class DimensionInformativa(BaseModel):
    informativa: bool = True
    veredicto: str = "CUMPLE"
    observaciones: list[str] = Field(default_factory=list)
    evidencia: str = ""


class DetalleSemanal(BaseModel):
    semana: int
    tema_silabo: str = ""
    tema_material: str | None = None
    desarrollada_en_material: bool = False
    veredicto_semana: ConcordanceStatus
    habilita_generacion: bool = False
    matriz_subtemas: MatrizSubtemas = Field(default_factory=MatrizSubtemas)
    notas_informativas: list[str] = Field(default_factory=list)
    coherencia: CoherenciaTransversal
    observaciones: list[str] = Field(default_factory=list)
    recomendaciones: list[str] = Field(default_factory=list)
    resultados_aprendizaje: DimensionInformativa | None = None
    estrategias: DimensionInformativa | None = None
    
    # Explicit fields for backwards compatibility with tests
    silabo_codes: list[str] = Field(default_factory=list)
    guia_codes: list[str] = Field(default_factory=list)
    missing_codes_in_guia: list[str] = Field(default_factory=list)
    page_range_guia: str | None = None
    adaptation_in_silabo: bool = False
    adaptation_in_guia: bool = False

    @property
    def week_number(self) -> int:
        return self.semana

    @property
    def topic(self) -> str:
        return self.tema_silabo

    @property
    def status(self) -> str:
        if self.veredicto_semana in (ConcordanceStatus.CUMPLE, ConcordanceStatus.CONCORDANTE):
            return "CONCORDANTE"
        if not self.desarrollada_en_material:
            return "FALTANTE_EN_GUIA"
        elif self.veredicto_semana in (ConcordanceStatus.CUMPLE_PARCIAL, ConcordanceStatus.PARCIAL):
            return "PARCIAL"
        return "NO_CUMPLE"

    @property
    def observation(self) -> str:
        return "; ".join(self.observaciones) if self.observaciones else (self.notas_informativas[0] if self.notas_informativas else "")


class ResumenSemanasDura(BaseModel):
    silabo: int = 0
    material_desarrolladas: int = 0
    material_solo_mencionadas: list[int] = Field(default_factory=list)
    veredicto: ConcordanceStatus = ConcordanceStatus.NO_CUMPLE
    observaciones: list[str] = Field(default_factory=list)
    recomendaciones: list[str] = Field(default_factory=list)


class TemaValidado(BaseModel):
    semana: int
    tema: str
    subtemas: list[str] = Field(default_factory=list)
    competencias: list[str] = Field(default_factory=list)
    estrategias: dict[str, str] = Field(default_factory=dict)
    tecnica_instrumento: str = ""


class ConcordanceResult(BaseModel):
    veredicto_global: ConcordanceStatus = ConcordanceStatus.CUMPLE_PARCIAL
    resumen: str = ""
    semanas: ResumenSemanasDura = Field(default_factory=ResumenSemanasDura)
    detalle_semanal: list[DetalleSemanal] = Field(default_factory=list)
    temas_validados: list[TemaValidado] = Field(default_factory=list)
    metadatos: dict = Field(default_factory=dict)

    @property
    def weeks(self) -> list[DetalleSemanal]:
        return self.detalle_semanal

    @property
    def key_findings(self) -> list[str]:
        findings = list(self.semanas.observaciones)
        missing_weeks = [w for w in self.detalle_semanal if not w.desarrollada_en_material]
        if missing_weeks:
            nums = ", ".join(str(w.semana) for w in missing_weeks)
            findings.append(f"Las semanas {nums} están definidas en el sílabo pero no tienen desarrollo en la guía didáctica.")
        adaptation_gap_weeks = [w for w in self.detalle_semanal if w.adaptation_in_silabo and not w.adaptation_in_guia]
        if adaptation_gap_weeks:
            findings.append(
                f"Ninguna de las semanas con adaptación curricular individual en el sílabo tiene contenido adaptado equivalente detectado en la guía ({len(adaptation_gap_weeks)} semana(s))."
            )
        return findings

    @property
    def concordant_count(self) -> int:
        return sum(1 for w in self.detalle_semanal if w.status == "CONCORDANTE")

    @property
    def partial_count(self) -> int:
        return sum(1 for w in self.detalle_semanal if w.status == "PARCIAL")

    @property
    def missing_count(self) -> int:
        return sum(1 for w in self.detalle_semanal if w.status in ("FALTANTE_EN_GUIA", "FALTANTE_EN_SILABO", "NO_CUMPLE"))


# Alias WeekConcordance for backward compatibility
WeekConcordance = DetalleSemanal
