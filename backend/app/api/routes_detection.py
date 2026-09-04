from fastapi import APIRouter, HTTPException, Depends
from typing import List, Union
import cv2
from pathlib import Path

from ..models.diagram import DiagramCandidate, Diagram, DiagramStatus
from ..services.storage import StorageService
from ..pipeline.detection import DiagramDetector
from ..core.logging import get_logger

logger = get_logger("api.detection")
router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}", tags=["detection"])

def get_storage() -> StorageService:
    return StorageService()

@router.post("/detect", response_model=List[DiagramCandidate])
async def detect_diagrams(
    project_id: str,
    page_id: str,
    storage: StorageService = Depends(get_storage)
):
    """Detect diagram candidates in a preprocessed page."""
    try:
        page = storage.load_page(project_id, page_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Page {page_id} not found in project {project_id}")
        
    if not page.preprocessed_path or not Path(page.preprocessed_path).exists():
        raise HTTPException(status_code=400, detail="Page has not been preprocessed yet or file is missing")
        
    image = cv2.imread(page.preprocessed_path)
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to load preprocessed image")
        
    detector = DiagramDetector()
    candidates = detector.detect(image)
    
    return candidates

@router.post("/diagrams", response_model=List[Diagram])
async def save_diagrams(
    project_id: str,
    page_id: str,
    diagrams: List[Union[Diagram, DiagramCandidate]],
    storage: StorageService = Depends(get_storage)
):
    """Save user-confirmed diagrams to the storage service."""
    try:
        page = storage.load_page(project_id, page_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Page {page_id} not found in project {project_id}")
        
    saved_diagrams = []
    for item in diagrams:
        if isinstance(item, DiagramCandidate):
            # Create a Diagram from the candidate
            diagram = Diagram(
                id=item.id,
                project_id=project_id,
                page_id=page_id,
                status=DiagramStatus.CANDIDATE,
                source_bbox=item.bbox
            )
        else:
            diagram = item
            if diagram.project_id != project_id or diagram.page_id != page_id:
                raise HTTPException(status_code=400, detail=f"Diagram {diagram.id} project/page mismatch")
        
        storage.save_diagram(diagram)
        saved_diagrams.append(diagram)
        
    return saved_diagrams
