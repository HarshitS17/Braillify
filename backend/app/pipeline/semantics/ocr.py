import logging
from .base import SemanticDetector
from ...models.diagram import DiagramElement
from ...models.component import Component

logger = logging.getLogger(__name__)

class OCRSemanticDetector(SemanticDetector):
    """
    Stub for an OCR or ML-based semantic detector.
    Currently acts as a placeholder to demonstrate the pluggable architecture.
    """
    
    def detect(self, elements: list[DiagramElement]) -> list[Component]:
        logger.warning("OCRSemanticDetector is a stub and currently returns no components. ML model not yet plugged in.")
        # Future implementation would run Tesseract or a Vision API on the text regions.
        return []
