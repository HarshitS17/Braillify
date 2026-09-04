import cv2
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from pydantic import BaseModel

from ..models.diagram import Diagram, DiagramStatus
from ..models.label import Label, LabelSource, LabelPlacement
from ..services.storage import StorageService
from ..pipeline.labels import extract_labels
from ..pipeline.braille_translation import translate_labels
from ..pipeline.ocr.mock import MockOCRProvider
from ..core.exceptions import ProjectNotFoundError

router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/labels", tags=["Labels"])

def get_storage():
    return StorageService()

@router.post("/extract", response_model=Diagram)
async def extract_diagram_labels_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    storage: StorageService = Depends(get_storage)
):
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    extracted_path = storage.get_diagram_extracted_path(project_id, page_id, diagram_id)
    if not extracted_path.exists():
        raise HTTPException(status_code=400, detail="Diagram image not found")
        
    image = cv2.imread(str(extracted_path))
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to load diagram image")
        
    provider = MockOCRProvider()
    labels = extract_labels(diagram, image, provider)
    
    # Save the labels objects to disk
    label_ids = []
    for label in labels:
        storage.save_label(project_id, label)
        label_ids.append(label.id)
        
    diagram.labels = label_ids
    if diagram.status in (DiagramStatus.SIMPLIFIED, DiagramStatus.VECTORIZED):
        diagram.status = DiagramStatus.LABELED
        
    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(f"Extracted {len(labels)} labels via OCR at {diagram.updated_at.isoformat()}")
    
    storage.save_diagram(diagram)
    
    return diagram

@router.get("", response_model=list[Label])
async def list_labels_endpoint(
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
            
    return labels

class LabelUpdateRequest(BaseModel):
    """Partial label update. Only provided fields are applied."""
    text: str | None = None
    braille_unicode: str | None = None
    braille_dots: str | None = None
    placement: LabelPlacement | None = None

@router.put("/{label_id}", response_model=Label)
async def update_label_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    label_id: str,
    request: LabelUpdateRequest,
    storage: StorageService = Depends(get_storage)
):
    """Human-in-the-loop correction endpoint.

    Persists text / braille / placement edits made in the editor. When the
    text changes, the Braille representation is re-translated server-side so
    the exported tactile output always matches the corrected text.
    """
    try:
        label = storage.load_label(project_id, label_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Label not found")

    if label.diagram_id != diagram_id:
        raise HTTPException(status_code=400, detail="Label does not belong to this diagram")

    text_changed = request.text is not None and request.text != label.text
    if request.text is not None:
        label.text = request.text
    if request.braille_unicode is not None or request.braille_dots is not None:
        if request.braille_unicode is not None:
            label.braille.braille_unicode = request.braille_unicode
        if request.braille_dots is not None:
            label.braille.braille_dots = request.braille_dots
    if request.placement is not None:
        request.placement.is_manual = True
        label.placement = request.placement

    if text_changed or request.placement is not None:
        label.source = LabelSource.MANUAL  # Audit trail: mark as manually corrected
    if text_changed:
        # Keep Braille in sync with the corrected text (grade 1 English).
        translate_labels([label])

    storage.save_label(project_id, label)

    return label

class LabelsReplaceRequest(BaseModel):
    """Full replacement of the diagram's label set (used by editor sync for
    deletes and undo/redo, where the whole label state must be restored)."""
    labels: list[Label]

@router.put("", response_model=list[Label])
async def replace_labels_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: LabelsReplaceRequest,
    storage: StorageService = Depends(get_storage)
):
    """Replace the diagram's full label set atomically.

    - Saves every label in the payload (re-creating ones restored by undo).
    - Deletes label files that belonged to this diagram but are no longer
      present (i.e. user-deleted labels).
    - Manually-corrected labels get their Braille re-translated from the
      corrected text (deterministic, so undo/redo stays consistent).
    """
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if diagram.page_id != page_id:
        raise HTTPException(status_code=400, detail="Diagram does not belong to this page")

    incoming_ids = []
    for label in request.labels:
        label.diagram_id = diagram_id
        if label.source == LabelSource.MANUAL and label.text:
            translate_labels([label])
        storage.save_label(project_id, label)
        incoming_ids.append(label.id)

    # Remove label files that are no longer part of the diagram.
    for old_id in diagram.labels:
        if old_id not in incoming_ids:
            label_file = storage.get_label_dir(project_id) / f"{old_id}.json"
            if label_file.exists():
                label_file.unlink()

    diagram.labels = incoming_ids
    diagram.updated_at = datetime.now(timezone.utc)
    diagram.processing_log.append(
        f"Editor sync: label set replaced ({len(incoming_ids)} labels) at {diagram.updated_at.isoformat()}"
    )
    storage.save_diagram(diagram)

    return [storage.load_label(project_id, lid) for lid in incoming_ids]

@router.post("/translate", response_model=list[Label])
async def translate_labels_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    storage: StorageService = Depends(get_storage)
):
    """Translate all labels for a diagram into Braille."""
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from ..pipeline.braille_translation import translate_labels as do_translate

    labels = []
    for label_id in diagram.labels:
        try:
            labels.append(storage.load_label(project_id, label_id))
        except FileNotFoundError:
            pass

    translated = do_translate(labels)

    for label in translated:
        storage.save_label(project_id, label)

    return translated

@router.post("/place", response_model=list[Label])
async def place_labels_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    storage: StorageService = Depends(get_storage)
):
    """Calculate positions for all labels using constraint-based placement."""
    try:
        diagram = storage.load_diagram(project_id, diagram_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from ..pipeline.placement import place_labels as do_place

    labels = []
    for label_id in diagram.labels:
        try:
            labels.append(storage.load_label(project_id, label_id))
        except FileNotFoundError:
            pass

    placed = do_place(labels, diagram)

    for label in placed:
        storage.save_label(project_id, label)

    return placed
