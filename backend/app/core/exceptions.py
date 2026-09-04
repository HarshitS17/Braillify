from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("tactile_ed.exceptions")

class TactileEdError(Exception):
    """Base exception for TactileEd."""
    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)

class ValidationError(TactileEdError):
    """Input validation failed."""
    pass

class ProcessingError(TactileEdError):
    """Pipeline processing failed."""
    pass

class FileFormatError(TactileEdError):
    """Unsupported or corrupted file."""
    pass

class DiagramDetectionError(ProcessingError):
    """Diagram detection failed."""
    pass

class VectorizationError(ProcessingError):
    """Vectorization failed."""
    pass

class ExportError(TactileEdError):
    """Export failed."""
    pass

class ProjectNotFoundError(TactileEdError):
    """Project not found."""
    pass

async def tactile_ed_error_handler(request: Request, exc: TactileEdError) -> JSONResponse:
    logger.error(f"{type(exc).__name__}: {exc.message}", exc_info=exc)
    status_map = {
        ValidationError: 422,
        FileFormatError: 422,  # corrupted/undecodable content, not a media-type problem
        ProjectNotFoundError: 404,
        ProcessingError: 500,
        ExportError: 500,
    }
    status = 500
    for exc_type, code in status_map.items():
        if isinstance(exc, exc_type):
            status = code
            break
    return JSONResponse(
        status_code=status,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "detail": exc.detail,
        },
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalError",
            "message": "An unexpected error occurred.",
            "detail": str(exc),
        },
    )
