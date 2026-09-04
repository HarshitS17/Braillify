from abc import ABC, abstractmethod
from ...models.diagram import DiagramElement
from ...models.component import Component

class SemanticDetector(ABC):
    """
    Base interface for all semantic detectors.
    A SemanticDetector groups generic geometries into meaningful academic components.
    """
    
    @abstractmethod
    def detect(self, elements: list[DiagramElement]) -> list[Component]:
        """
        Identify components from a list of diagram elements.
        
        Args:
            elements: The structural elements from the diagram analyzer.
            
        Returns:
            A list of detected semantic Components.
        """
        pass
