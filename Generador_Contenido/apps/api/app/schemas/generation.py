from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

INTENTS = [
    "presentar", "comprender", "visualizar", "practicar", "aplicar",
    "resolver", "analizar", "comparar", "experimentar", "reforzar",
    "comprobar", "evaluar",
]


class PedagogicalIntent(str, Enum):
    presentar = "presentar"
    comprender = "comprender"
    visualizar = "visualizar"
    practicar = "practicar"
    aplicar = "aplicar"
    resolver = "resolver"
    analizar = "analizar"
    comparar = "comparar"
    experimentar = "experimentar"
    reforzar = "reforzar"
    comprobar = "comprobar"
    evaluar = "evaluar"


class GenerationRequest(BaseModel):
    session_id: str
    week_number: int
    intent: PedagogicalIntent
    extra_instructions: str = ""


class ResourceBlockType(str, Enum):
    diagram = "diagram"
    interactive_activity = "interactive_activity"
    word_search = "word_search"
    flashcards = "flashcards"
    study_guide = "study_guide"
    crossword = "crossword"
    logic_puzzle = "logic_puzzle"
    geogebra = "geogebra"
    text = "text"


class ResourceBlock(BaseModel):
    type: ResourceBlockType
    title: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    rendered_html: str = ""


class GeneratedResource(BaseModel):
    title: str
    week_number: int
    topic: str = ""
    intent: PedagogicalIntent
    summary: str = ""
    blocks: list[ResourceBlock] = Field(default_factory=list)
    mcp_tool_trace: list[str] = Field(default_factory=list)
