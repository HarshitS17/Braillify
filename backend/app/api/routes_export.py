from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel

from ..models.export import ExportConfig
from ..services.storage import StorageService
from ..pipeline.export.svg import generate_svg
from ..core.exceptions import ProjectNotFoundError

router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/export", tags=["Export"])

def get_storage():
    return StorageService()

class ExportRequest(BaseModel):
    config: ExportConfig = ExportConfig()

@router.post("/svg")
async def export_svg_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: ExportRequest,
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
            
    svg_data = generate_svg(diagram, labels, request.config)
    
    return Response(
        content=svg_data,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f"attachment; filename=diagram_{diagram_id}.svg"}
    )

@router.post("/pdf")
async def export_pdf_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: ExportRequest,
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
            
    from ..pipeline.export.pdf import generate_pdf
    pdf_data = generate_pdf(diagram, labels, request.config)
    
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=diagram_{diagram_id}.pdf"}
    )
