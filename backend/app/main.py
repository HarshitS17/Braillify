from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from .core.config import Settings, get_settings
from .core.logging import setup_logging, get_logger
from .core.exceptions import TactileEdError, tactile_ed_error_handler, generic_error_handler
from .api import routes_projects, routes_upload, routes_processing, routes_export, routes_detection, routes_extraction, routes_labels, routes_validation, routes_workflow

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    # Ensure workspace directory exists
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)
    app.state.settings = settings
    yield
    logger.info("Shutting down TactileEd")

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="TactileEd API",
        description="Textbook Diagram-to-Embossable Tactile Graphic Converter",
        version=settings.app_version,
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    app.add_exception_handler(TactileEdError, tactile_ed_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
    
    # Routes
    app.include_router(routes_projects.router)
    app.include_router(routes_upload.router)
    app.include_router(routes_processing.router)
    app.include_router(routes_detection.router)
    app.include_router(routes_extraction.router)
    app.include_router(routes_labels.router)
    app.include_router(routes_validation.router)
    app.include_router(routes_workflow.router)
    app.include_router(routes_export.router)
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    return app

app = create_app()
