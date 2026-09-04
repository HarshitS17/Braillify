from abc import ABC, abstractmethod
from ...models.diagram import Diagram
from ...models.label import Label
from ...models.validation import ValidationMessage

class Validator(ABC):
    """
    Abstract interface for diagram validation checks.
    """
    
    @abstractmethod
    def validate(self, diagram: Diagram, labels: list[Label]) -> list[ValidationMessage]:
        """
        Run the validation check on the diagram and its placed labels.
        
        Args:
            diagram: The parsed diagram containing elements and components.
            labels: The generated and placed Braille labels.
            
        Returns:
            A list of ValidationMessage objects (errors, warnings, suggestions).
        """
        pass
