import re
import pytest
import numpy as np
from app.models.diagram import Diagram, DiagramElement, ElementType
from app.models.component import Component, ComponentType
from app.pipeline.labels import extract_labels
from app.pipeline.ocr.mock import MockOCRProvider

def test_extract_labels():
    element = DiagramElement(type=ElementType.TEXT_REGION, geometry={"x": 10, "y": 20, "w": 100, "h": 20})
    element_id = element.id
    
    component = Component(
        diagram_id="diag-1",
        type=ComponentType.ANNOTATION,
        element_ids=[element_id]
    )
    
    diagram = Diagram(
        project_id="proj-1",
        page_id="page-1",
        elements=[element],
        components=[component]
    )
    
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    provider = MockOCRProvider()
    
    labels = extract_labels(diagram, image, provider)
    
    assert len(labels) == 1
    # MockOCRProvider is a heuristic placeholder: it returns a deterministic
    # descriptive label (Region/Label/Symbol + counter) with a LOW confidence,
    # which flags the label for human-in-the-loop correction.
    assert re.fullmatch(r"(Region|Label|Symbol) \d+", labels[0].text)
    assert labels[0].target_component_id == component.id
    assert labels[0].target_element_id == element_id
    assert labels[0].ocr_confidence in (0.10, 0.20, 0.40)
