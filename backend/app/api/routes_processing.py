from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path

from ..models.page import PageStatus
from ..models.preprocessing import PreprocessingConfig, PreprocessingResult
from ..services.storage import StorageService
from ..pipeline.preprocessing import preprocess_image
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger("api.processing")
router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}", tags=["processing"])

def get_storage() -> StorageService:
    return StorageService()

@router.post("/preprocess")
async def preprocess_page(
    project_id: str,
    page_id: str,
    config: PreprocessingConfig | None = None,
    storage: StorageService = Depends(get_storage),
) -> dict:
    """Run the preprocessing pipeline on an uploaded page.
    
    Optionally accepts a PreprocessingConfig body to override default parameters.
    """
    settings = get_settings()
    
    # Load the page from the specific project
    try:
        page = storage.load_page(project_id, page_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Page {page_id} not found in project {project_id}")
    
    if not page.original_path or not Path(page.original_path).exists():
        raise HTTPException(status_code=422, detail="Original image file not found")
    
    # Update status
    page.status = PageStatus.PREPROCESSING
    page.processing_log.append("Starting preprocessing")
    storage.save_page(page)
    
    try:
        # Set up output directory
        output_dir = storage.get_page_preprocessed_dir(page.project_id, page.id)
        
        # Run preprocessing
        preprocess_config = config or PreprocessingConfig()
        result = preprocess_image(
            image_path=Path(page.original_path),
            output_dir=output_dir,
            config=preprocess_config,
            page_id=page.id,
            save_debug=settings.debug_artifacts,
            source_dpi=page.metadata.dpi,
        )
        
        # Update page with results
        page.status = PageStatus.PREPROCESSED
        page.preprocessed_path = result.preprocessed_path
        page.grayscale_path = result.grayscale_path
        page.binary_path = result.binary_path
        page.detected_skew_angle = result.detected_skew_angle
        page.processing_log.append(
            f"Preprocessing complete: {len(result.stages)} stages, "
            f"skew={result.detected_skew_angle:.2f}° " if result.detected_skew_angle else "Preprocessing complete"
        )
        storage.save_page(page)
        
        return {
            "page_id": page.id,
            "status": page.status.value,
            "stages_completed": len(result.stages),
            "detected_skew_angle": result.detected_skew_angle,
            "original_size": [result.original_width, result.original_height],
            "preprocessed_path": result.preprocessed_path,
            "grayscale_path": result.grayscale_path,
            "binary_path": result.binary_path,
            "stages": [
                {
                    "stage": s.stage.value,
                    "success": s.success,
                    "metadata": s.metadata,
                }
                for s in result.stages
            ],
        }
        
    except Exception as e:
        page.status = PageStatus.ERROR
        page.processing_log.append(f"Preprocessing failed: {str(e)}")
        storage.save_page(page)
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")
