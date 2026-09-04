from abc import ABC, abstractmethod
import numpy as np
from typing import Any

class OCRProvider(ABC):
    """
    Interface for extracting text from diagram regions.
    """
    
    @abstractmethod
    def extract_text(self, image: np.ndarray, bbox: dict[str, Any]) -> tuple[str, float]:
        """
        Extract text from a specific region of an image.
        
        Args:
            image: The full image (numpy array).
            bbox: Bounding box dictionary (x, y, w, h).
            
        Returns:
            Tuple of (extracted_text, confidence_score).
        """
        pass
