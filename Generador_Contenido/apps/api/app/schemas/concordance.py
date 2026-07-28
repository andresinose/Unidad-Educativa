from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ConcordanceStatus(str, Enum):
    CONCORDANTE = "CONCORDANTE"
    PARCIAL = "PARCIAL"
    FALTANTE_EN_GUIA = "FALTANTE_EN_GUIA"
    FALTANTE_EN_SILABO = "FALTANTE_EN_SILABO"


class WeekConcordance(BaseModel):
    week_number: int
    topic: str = ""
    silabo_codes: list[str] = Field(default_factory=list)
    guia_codes: list[str] = Field(default_factory=list)
    missing_codes_in_guia: list[str] = Field(default_factory=list)
    page_range_guia: str | None = None
    adaptation_in_silabo: bool = False
    adaptation_in_guia: bool = False
    status: ConcordanceStatus
    observation: str = ""


class ConcordanceResult(BaseModel):
    weeks: list[WeekConcordance] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    concordant_count: int = 0
    partial_count: int = 0
    missing_count: int = 0
