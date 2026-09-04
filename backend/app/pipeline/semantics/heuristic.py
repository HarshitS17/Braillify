from .base import SemanticDetector
from ...models.diagram import DiagramElement, ElementType
from ...models.component import Component, ComponentType

class HeuristicSemanticDetector(SemanticDetector):
    """
    Uses simple geometric and type-based rules to deduce semantics.
    """
    
    def detect(self, elements: list[DiagramElement]) -> list[Component]:
        components = []
        
        for el in elements:
            if el.type == ElementType.ARROW:
                components.append(Component(
                    diagram_id="placeholder",  # Replaced later by orchestrator or caller
                    type=ComponentType.CONNECTOR,
                    name="Arrow Connector",
                    confidence=el.confidence,
                    evidence="Detected arrow geometry",
                    element_ids=[el.id]
                ))
            
            elif el.type in (ElementType.FILLED_REGION, ElementType.CIRCLE):
                # Basic heuristic: if it's a big circle or filled shape, it's a structure (e.g. node, cell)
                components.append(Component(
                    diagram_id="placeholder",
                    type=ComponentType.STRUCTURE,
                    name="Geometric Structure",
                    confidence=el.confidence,
                    evidence="Detected closed shape structure",
                    element_ids=[el.id]
                ))
                
            elif el.type == ElementType.TEXT_REGION:
                components.append(Component(
                    diagram_id="placeholder",
                    type=ComponentType.ANNOTATION,
                    name="Text Label",
                    confidence=el.confidence,
                    evidence="Detected text region",
                    element_ids=[el.id]
                ))
                
        return components
