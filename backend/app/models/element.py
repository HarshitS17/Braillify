from pydantic import BaseModel, Field
from enum import Enum
from typing import Any
import uuid

class ElementType(str, Enum):
    LINE = "line"
    CURVE = "curve"
    POLYGON = "polygon"
    CIRCLE = "circle"
    FILLED_REGION = "filled_region"
    TEXT_REGION = "text_region"
    ARROW = "arrow"

class DiagramElement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ElementType
    geometry: dict[str, Any]
    style: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    semantic_role: str | None = None
    simplified_from: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
