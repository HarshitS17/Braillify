import pytest
import numpy as np
import cv2
from pathlib import Path
from app.pipeline.detection import DiagramDetector
from app.models.diagram import DiagramCandidate, BoundingBox

FIXTURE_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"

class TestDiagramDetector:
    def test_detector_initialization(self):
        detector = DiagramDetector(min_area_ratio=0.1, max_aspect_ratio=2.0)
        assert detector.min_area_ratio == 0.1
        assert detector.max_aspect_ratio == 2.0
        
    def test_detection_on_empty_image(self):
        detector = DiagramDetector()
        img = np.zeros((500, 500), dtype=np.uint8)
        candidates = detector.detect(img)
        # Should not find any diagrams on a completely black image
        assert len(candidates) == 0
        
    def test_detection_on_simple_shapes(self):
        detector = DiagramDetector(min_area_ratio=0.01)
        img = cv2.imread(str(FIXTURE_DIR / "simple_shapes.png"), cv2.IMREAD_GRAYSCALE)
        if img is None:
            pytest.skip("Fixture image simple_shapes.png not found")
            
        candidates = detector.detect(img)
        assert isinstance(candidates, list)
        if len(candidates) > 0:
            assert isinstance(candidates[0], DiagramCandidate)
            assert isinstance(candidates[0].bbox, BoundingBox)
        
    def test_detection_on_text_with_diagram(self):
        detector = DiagramDetector(min_area_ratio=0.01)
        img_path = FIXTURE_DIR / "text_with_diagram.png"
        img = cv2.imread(str(img_path))
        if img is None:
            pytest.skip("Fixture image text_with_diagram.png not found")
        
        candidates = detector.detect(img)
        assert isinstance(candidates, list)
        # It should detect at least one candidate
        assert len(candidates) >= 1
        
        cand = candidates[0]
        assert isinstance(cand, DiagramCandidate)
        assert isinstance(cand.bbox, BoundingBox)
        assert 0.0 <= cand.confidence <= 1.0
        assert hasattr(cand, "features")
            
    def test_geometric_filters(self):
        detector = DiagramDetector(min_area_ratio=0.99) # Requires almost full image area
        img = cv2.imread(str(FIXTURE_DIR / "simple_shapes.png"), cv2.IMREAD_GRAYSCALE)
        if img is None:
            pytest.skip("Fixture image simple_shapes.png not found")
        candidates = detector.detect(img)
        # None should be 99% of the image
        assert len(candidates) == 0
