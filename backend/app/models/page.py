from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid

class PageStatus(str, Enum):
    UPLOADED = "uploaded"
    PREPROCESSING = "preprocessing"
    PREPROCESSED = "preprocessed"
    DETECTING = "detecting"
    DETECTED = "detected"
    ERROR = "error"

class PageMetadata(BaseModel):
    original_filename: str
    file_format: str
    file_size_bytes: int
    width_px: int = 0
    height_px: int = 0
    dpi: int | None = None
    source_pdf_page: int | None = None  # if extracted from PDF

class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    status: PageStatus = PageStatus.UPLOADED
    metadata: PageMetadata
    original_path: str = ""
    preprocessed_path: str | None = None
    grayscale_path: str | None = None
    binary_path: str | None = None
    detected_skew_angle: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_log: list[str] = Field(default_factory=list)
