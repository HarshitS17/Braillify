import numpy as np
from ..models.diagram import Diagram
from ..models.component import ComponentType
from ..models.label import Label, LabelSource, LabelPlacement
from .ocr.base import OCRProvider

def extract_labels(diagram: Diagram, image: np.ndarray, provider: OCRProvider) -> list[Label]:
    """
    Find ANNOTATION components in the diagram and extract text using the OCR provider.
    """
    labels = []
    
    # We need to map components back to their elements to get bounding boxes
    # Create a quick lookup map of element_id -> element
    element_map = {el.id: el for el in diagram.elements}
    
    for comp in diagram.components:
        if comp.type == ComponentType.ANNOTATION:
            # Get the associated text region element
            if not comp.element_ids:
                continue
                
            element_id = comp.element_ids[0]
            element = element_map.get(element_id)
            if not element or "w" not in element.geometry:
                continue
                
            # Extract text
            text, confidence = provider.extract_text(image, element.geometry)
            
            # Flag for human review when OCR confidence is low
            needs_review = confidence < 0.6
            
            # Create a label
            label = Label(
                diagram_id=diagram.id,
                target_component_id=comp.id,
                target_element_id=element.id,
                text=text,
                source=LabelSource.OCR,
                ocr_confidence=confidence,
                needs_review=needs_review,
                metadata={"auto_extracted": True, "review_reason": "low_ocr_confidence" if needs_review else None}
            )
            labels.append(label)
            
    return labels
