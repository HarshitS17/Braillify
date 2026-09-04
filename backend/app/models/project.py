from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid

class ProjectStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    REVIEW = "review"
    COMPLETED = "completed"
    ERROR = "error"

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)

class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    page_count: int = 0

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    page_count: int = 0
    workspace_path: str = ""
