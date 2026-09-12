from pydantic import BaseModel, Field
from typing import Any
from .diagram import CoordinateUnit, Point
from enum import Enum
import uuid

class LabelSource(str, Enum):
    OCR = "ocr"
    MANUAL = "manual"
    GENERATED = "generated"

class BrailleRepresentation(BaseModel):
    braille_unicode: str = ""  # Unicode Braille characters
    braille_dots: str = ""    # Dot notation (e.g., "1-245-13")
    grade: int = 1             # Braille grade (1 = uncontracted)
    language: str = "en"

class LeaderLine(BaseModel):
    start: Point
    end: Point
    unit: CoordinateUnit = CoordinateUnit.PX

class LabelPlacement(BaseModel):
    position: Point
    unit: CoordinateUnit = CoordinateUnit.PX
    width: float = 0.0
    height: float = 0.0
    rotation: float = 0.0
    leader_line: LeaderLine | None = None
    placement_score: float = 0.0  # Quality of this placement (lower = better)
    is_manual: bool = False

class Label(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    diagram_id: str
    target_component_id: str | None = None  # Component this label refers to
    target_element_id: str | None = None    # Element this label refers to
    text: str
    braille: BrailleRepresentation = Field(default_factory=BrailleRepresentation)
    source: LabelSource = LabelSource.GENERATED
    ocr_confidence: float | None = None
    needs_review: bool = False  # Auto-set when OCR confidence < threshold
    placement: LabelPlacement | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
