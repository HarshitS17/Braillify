from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import os


def _default_workspace_dir() -> Path:
    """Resolve the workspace directory.

    Priority:
    1. TACTILE_ED_WORKSPACE_DIR env var (explicit override).
    2. ./workspace (local dev, Docker with a volume).
    """
    env_dir = os.environ.get("TACTILE_ED_WORKSPACE_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("./workspace")


class Settings(BaseSettings):
    # Application
    app_name: str = "TactileEd"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS (same-origin deploys need no CORS; extra origins listed defensively)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://braillify.vercel.app",
        "https://braillify-harshits17s-projects.vercel.app",
    ]

    # Storage
    workspace_dir: Path = Field(default_factory=_default_workspace_dir)
    max_upload_size_mb: int = 50
    allowed_extensions: set[str] = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".pdf"}

    # Vercel Blob — when set, StorageService uses Blob instead of filesystem.
    # The token is auto-injected by Vercel when a Blob store is linked.
    blob_read_write_token: str = ""

    # Processing
    default_dpi: int = 300
    debug_artifacts: bool = True

    model_config = {"env_prefix": "TACTILE_ED_", "env_file": ".env"}


def get_settings() -> Settings:
    return Settings()
