from pydantic import BaseModel, Field
from enum import Enum
from typing import Any
import uuid

class ComponentType(str, Enum):
    STRUCTURE = "structure"
    REGION = "region"
    CONNECTOR = "connector"
    ANNOTATION = "annotation"
    UNKNOWN = "unknown"

class Component(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    diagram_id: str
    type: ComponentType = ComponentType.UNKNOWN
    name: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: str = ""  # Explanation of why this was identified
    element_ids: list[str] = Field(default_factory=list)  # associated DiagramElement IDs
    centroid_x: float = 0.0
    centroid_y: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
