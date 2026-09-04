from pydantic import BaseModel, Field
from enum import Enum

class PhysicalUnit(str, Enum):
    MM = "mm"
    CM = "cm"
    IN = "in"

class ExportConfig(BaseModel):
    width: float = 210.0  # Default to A4 width in mm
    height: float = 297.0 # Default to A4 height in mm
    unit: PhysicalUnit = PhysicalUnit.MM
    include_metadata: bool = True
    stroke_width_mm: float = 0.5  # Tactile line thickness
