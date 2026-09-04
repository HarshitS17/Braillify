import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from pydantic import BaseModel

from ..models.diagram import Diagram, DiagramStatus, DiagramElement
from ..models.extraction import ExtractionConfig, AnalysisConfig
from ..models.simplification import SimplificationConfig
from ..services.storage import StorageService
from ..pipeline.extraction import extract_diagram
from ..pipeline.analysis import analyze_structure
from ..pipeline.simplification import simplify_diagram
from ..core.exceptions import ProjectNotFoundError

router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}", tags=["Extraction"])

def get_storage():
    return StorageService()

class ExtractRequest(BaseModel):
    config: ExtractionConfig = ExtractionConfig()

class AnalyzeRequest(BaseModel):
    config: AnalysisConfig = AnalysisConfig()

@router.get("", response_model=Diagram)
async def get_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    storage: StorageService = Depends(get_storage),
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")
    
    return diagram


class DiagramUpdateRequest(BaseModel):
    """Partial diagram update from the editor (element-level corrections)."""
    elements: list[DiagramElement] | None = None

@router.put("", response_model=Diagram)
async def update_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: DiagramUpdateRequest,
    storage: StorageService = Depends(get_storage),
):
    """Persist editor corrections to the structured diagram (e.g. deleted
    elements). This is what makes frontend edits survive export and reload."""
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")

    if request.elements is not None:
        diagram.elements = request.elements

    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(
        f"Editor sync: diagram updated ({len(diagram.elements)} elements) at {diagram.updated_at.isoformat()}"
    )
    storage.save_diagram(diagram)
    return diagram


@router.post("/extract", response_model=Diagram)
async def extract_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: ExtractRequest,
    storage: StorageService = Depends(get_storage)
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")
        
    if diagram.source_bbox is None:
        raise HTTPException(status_code=400, detail="Diagram does not have a source_bbox")

    page = storage.load_page(project_id, page_id)
    if not page.preprocessed_path or not Path(page.preprocessed_path).exists():
        raise HTTPException(status_code=404, detail="Page preprocessed image not found")
        
    image_path = Path(page.preprocessed_path)
        
    image = cv2.imread(str(image_path))
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to load page image")
        
    cropped, metadata = extract_diagram(image, diagram.source_bbox, request.config)
    
    extracted_path = storage.get_diagram_extracted_path(project_id, page_id, diagram_id)
    cv2.imwrite(str(extracted_path), cropped)
    
    diagram.status = DiagramStatus.EXTRACTED
    diagram.page_offset_x = metadata["offset_x"]
    diagram.page_offset_y = metadata["offset_y"]
    diagram.scale_factor = metadata["scale_factor"]
    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(f"Extracted diagram at {diagram.updated_at.isoformat()}")
    
    storage.save_diagram(diagram)
    
    return diagram

@router.post("/analyze", response_model=Diagram)
async def analyze_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: AnalyzeRequest,
    storage: StorageService = Depends(get_storage)
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")
        
    extracted_path = storage.get_diagram_extracted_path(project_id, page_id, diagram_id)
    if not extracted_path.exists():
        raise HTTPException(status_code=400, detail="Diagram has not been extracted yet")
        
    image = cv2.imread(str(extracted_path))
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to load extracted diagram image")
        
    elements = analyze_structure(image, request.config)
    
    diagram.elements = elements
    diagram.status = DiagramStatus.VECTORIZED
    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(f"Analyzed structure ({len(elements)} elements found) at {diagram.updated_at.isoformat()}")
    
    storage.save_diagram(diagram)
    
    return diagram

class SimplifyRequest(BaseModel):
    config: SimplificationConfig = SimplificationConfig()

@router.post("/simplify", response_model=Diagram)
async def simplify_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: SimplifyRequest,
    storage: StorageService = Depends(get_storage)
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")
        
    diagram.elements = simplify_diagram(diagram.elements, request.config)
    
    diagram.status = DiagramStatus.SIMPLIFIED
    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(f"Simplified diagram at {diagram.updated_at.isoformat()}")
    
    storage.save_diagram(diagram)
    
    return diagram

@router.post("/semantics", response_model=Diagram)
async def semantics_diagram_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    storage: StorageService = Depends(get_storage)
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")
        
    from ..pipeline.semantics.orchestrator import CompositeSemanticDetector
    from ..pipeline.semantics.heuristic import HeuristicSemanticDetector
    from ..pipeline.semantics.ocr import OCRSemanticDetector
    
    orchestrator = CompositeSemanticDetector([
        HeuristicSemanticDetector(),
        OCRSemanticDetector()
    ])
    
    components = orchestrator.detect(diagram.elements)
    
    # We assign placeholder diagram_id in heuristic, let's fix it here
    for comp in components:
        comp.diagram_id = diagram.id
        
    diagram.components = components
    # If the user is doing this step, status normally goes to LABELED, but we use an enum so let's check
    if diagram.status == DiagramStatus.SIMPLIFIED or diagram.status == DiagramStatus.VECTORIZED:
        diagram.status = DiagramStatus.LABELED
        
    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(f"Semantic identification ({len(components)} components) at {diagram.updated_at.isoformat()}")
    
    storage.save_diagram(diagram)
    
    return diagram

