from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Application
    app_name: str = "TactileEd"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Storage
    workspace_dir: Path = Path("./workspace")
    max_upload_size_mb: int = 50
    allowed_extensions: set[str] = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".pdf"}
    
    # Processing
    default_dpi: int = 300
    debug_artifacts: bool = True
    
    model_config = {"env_prefix": "TACTILE_ED_", "env_file": ".env"}

def get_settings() -> Settings:
    return Settings()
