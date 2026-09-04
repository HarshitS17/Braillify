import pytest
from app.models.diagram import DiagramElement, ElementType, SemanticRole
from app.models.component import ComponentType
from app.pipeline.semantics.heuristic import HeuristicSemanticDetector
from app.pipeline.semantics.orchestrator import CompositeSemanticDetector

def test_heuristic_detector():
    elements = [
        DiagramElement(type=ElementType.ARROW, geometry={}),
        DiagramElement(type=ElementType.FILLED_REGION, geometry={}),
        DiagramElement(type=ElementType.LINE, geometry={}),  # Should be ignored by heuristic
        DiagramElement(type=ElementType.TEXT_REGION, geometry={})
    ]
    
    detector = HeuristicSemanticDetector()
    components = detector.detect(elements)
    
    assert len(components) == 3
    types = [c.type for c in components]
    assert ComponentType.CONNECTOR in types
    assert ComponentType.STRUCTURE in types
    assert ComponentType.ANNOTATION in types
    
    # Check that element_ids are linked
    for comp in components:
        assert len(comp.element_ids) == 1

def test_orchestrator():
    class DummyDetector:
        def detect(self, elements):
            return []
            
    detector = CompositeSemanticDetector([
        DummyDetector(),
        HeuristicSemanticDetector()
    ])
    
    elements = [
        DiagramElement(type=ElementType.ARROW, geometry={})
    ]
    
    components = detector.detect(elements)
    assert len(components) == 1
    assert components[0].type == ComponentType.CONNECTOR
