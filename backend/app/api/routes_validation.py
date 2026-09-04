from fastapi import APIRouter, HTTPException, Depends

from ..models.validation import ValidationResult
from ..services.storage import StorageService
from ..pipeline.validation.engine import run_validation
from ..core.exceptions import ProjectNotFoundError

router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/validate", tags=["Validation"])

def get_storage():
    return StorageService()

@router.get("", response_model=ValidationResult)
async def validate_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    storage: StorageService = Depends(get_storage)
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    labels = []
    for label_id in diagram.labels:
        try:
            labels.append(storage.load_label(project_id, label_id))
        except FileNotFoundError:
            pass
            
    result = run_validation(diagram, labels)
    
    return result
