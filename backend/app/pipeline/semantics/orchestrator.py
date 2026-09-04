from .base import SemanticDetector
from ...models.diagram import DiagramElement
from ...models.component import Component

class CompositeSemanticDetector(SemanticDetector):
    """
    An orchestrator that runs multiple semantic detectors and aggregates their results.
    """
    
    def __init__(self, detectors: list[SemanticDetector]):
        self.detectors = detectors
        
    def detect(self, elements: list[DiagramElement]) -> list[Component]:
        aggregated_components = []
        for detector in self.detectors:
            components = detector.detect(elements)
            aggregated_components.extend(components)
        return aggregated_components
