from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import os
import tempfile


def _default_workspace_dir() -> Path:
    """Resolve the workspace directory at import time.

    Priority:
    1. TACTILE_ED_WORKSPACE_DIR env var (explicit override, e.g. on Vercel).
    2. ./workspace if it is writable (local dev, Docker with a volume).
    3. /tmp fallback - serverless filesystems (Vercel Functions) are read-only
       outside /tmp, so writing ./workspace would crash the app there.
    """
    env_dir = os.environ.get("TACTILE_ED_WORKSPACE_DIR")
    if env_dir:
        return Path(env_dir)
    local = Path("./workspace")
    try:
        local.mkdir(parents=True, exist_ok=True)
        probe = local / ".write_probe"
        probe.touch()
        probe.unlink()
        return local
    except OSError:
        return Path(tempfile.gettempdir()) / "tactile_ed_workspace"


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

    # Processing
    default_dpi: int = 300
    debug_artifacts: bool = True

    model_config = {"env_prefix": "TACTILE_ED_", "env_file": ".env"}


def get_settings() -> Settings:
    return Settings()
