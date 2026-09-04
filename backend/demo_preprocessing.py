import asyncio
import os
import shutil
from pathlib import Path

# Setup fake environment for the script
os.environ["TACTILE_ED_WORKSPACE_DIR"] = str(Path("../workspace").resolve())

from app.pipeline.preprocessing import preprocess_image
from app.models.preprocessing import PreprocessingConfig
import cv2

def run_demo():
    input_path = Path("../data/fixtures/noisy_diagram.png")
    
    config = PreprocessingConfig(deskew_enabled=True)
    
    # We need a dummy page_id and project_dir for it to save debug artifacts
    from app.services.storage import StorageService
    from app.models.project import Project, ProjectCreate
    from app.models.page import Page, PageMetadata
    
    storage = StorageService()
    
    # Create dummy project and page
    project = Project(name="Demo Project", description="Demo")
    storage.save_project(project)
    
    page = Page(
        project_id=project.id,
        filename="noisy_diagram.png",
        content_type="image/png",
        size_bytes=1024,
        metadata=PageMetadata(original_filename="noisy_diagram.png", file_format="image/png", file_size_bytes=1024)
    )
    
    # Setup page directory
    page_dir = storage.get_project_dir(project.id) / "pages" / page.id
    preprocessed_dir = page_dir / "preprocessed"
    preprocessed_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy original so pipeline can load it
    work_path = page_dir / "original.png"
    shutil.copy(str(input_path), str(work_path))
    
    print("Running pipeline...")
    result = preprocess_image(work_path, preprocessed_dir, config, page.id, save_debug=True)
    print(f"Success: {result.success}")
    
    # Copy results to the artifact directory for the user to see
    artifact_dir = Path("/Users/saini/.gemini/antigravity/brain/bb75f285-e0d6-4fac-b7d5-0a2d352b2a29")
    
    shutil.copy(str(input_path), str(artifact_dir / "demo_original.png"))
    for stage in result.stages:
        if stage.image_path:
            shutil.copy(stage.image_path, str(artifact_dir / f"demo_{stage.stage.value}.png"))
    print("Images copied to artifact dir.")

if __name__ == "__main__":
    run_demo()
