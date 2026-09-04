from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from .component import Component

class CoordinateUnit(str, Enum):
    PX = "px"
    MM = "mm"
    CM = "cm"

class DiagramStatus(str, Enum):
    CANDIDATE = "candidate"
    SELECTED = "selected"
    EXTRACTED = "extracted"
    VECTORIZED = "vectorized"
    SIMPLIFIED = "simplified"
    LABELED = "labeled"
    VALIDATED = "validated"
    EXPORTED = "exported"
    ERROR = "error"

class Canvas(BaseModel):
    width: float
    height: float
    unit: CoordinateUnit = CoordinateUnit.PX

class PhysicalOutput(BaseModel):
    width_mm: float = 210.0
    height_mm: float = 148.0
    px_per_mm: float = 5.71

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    unit: CoordinateUnit = CoordinateUnit.PX

class Point(BaseModel):
    x: float
    y: float

class ElementType(str, Enum):
    LINE = "line"
    POLYLINE = "polyline"
    POLYGON = "polygon"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    ARC = "arc"
    CURVE = "curve"
    ARROW = "arrow"
    TEXT_REGION = "text_region"
    BOUNDARY = "boundary"
    FILLED_REGION = "filled_region"

class SemanticRole(str, Enum):
    BOUNDARY = "boundary"
    LABEL = "label"
    ARROW = "arrow"
    CONNECTOR = "connector"
    STRUCTURE = "structure"
    DECORATION = "decoration"
    UNKNOWN = "unknown"

class DiagramElement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ElementType
    geometry: dict[str, Any]  # type-specific geometry data
    unit: CoordinateUnit = CoordinateUnit.PX
    semantic_role: SemanticRole = SemanticRole.UNKNOWN
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_region: BoundingBox | None = None
    simplified_from: str | None = None  # ID of original element before simplification
    metadata: dict[str, Any] = Field(default_factory=dict)

class DetectionFeatures(BaseModel):
    edge_density: float = 0.0
    text_density: float = 0.0
    component_density: float = 0.0
    contour_count: int = 0
    has_enclosed_regions: bool = False

class DiagramCandidate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbox: BoundingBox
    confidence: float = Field(ge=0.0, le=1.0)
    features: DetectionFeatures = Field(default_factory=DetectionFeatures)
    classification_reason: str = ""
    accepted: bool = False
    rejected: bool = False

class Diagram(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page_id: str
    project_id: str
    status: DiagramStatus = DiagramStatus.CANDIDATE
    canvas: Canvas | None = None
    physical_output: PhysicalOutput = Field(default_factory=PhysicalOutput)
    source_bbox: BoundingBox | None = None
    elements: list[DiagramElement] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)  # label IDs, actual Label objects stored separately
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_log: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Coordinate mapping: page coords <-> diagram coords
    page_offset_x: float = 0.0
    page_offset_y: float = 0.0
    scale_factor: float = 1.0
