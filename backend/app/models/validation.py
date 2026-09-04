from pydantic import BaseModel, Field
from enum import Enum
from typing import Any
import uuid

class ValidationLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"

class ValidationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: ValidationLevel
    message: str
    element_ids: list[str] = Field(default_factory=list)
    label_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ValidationResult(BaseModel):
    errors: list[ValidationMessage] = Field(default_factory=list)
    warnings: list[ValidationMessage] = Field(default_factory=list)
    suggestions: list[ValidationMessage] = Field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Returns True if there are no ERROR level messages."""
        return len(self.errors) == 0
