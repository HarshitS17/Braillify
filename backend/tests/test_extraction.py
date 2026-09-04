import pytest
import numpy as np
from app.models.diagram import BoundingBox
from app.models.extraction import ExtractionConfig
from app.pipeline.extraction import extract_diagram

def test_extract_diagram_basic():
    # Create a dummy image
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[20:80, 20:80] = 255  # White square
    
    bbox = BoundingBox(x=20, y=20, width=60, height=60)
    config = ExtractionConfig(padding=5, remove_text=False)
    
    cropped, metadata = extract_diagram(image, bbox, config)
    
    assert cropped.shape == (70, 70, 3) # 60 + 5 + 5
    assert metadata["offset_x"] == 15
    assert metadata["offset_y"] == 15
    assert metadata["scale_factor"] == 1.0

def test_extract_diagram_with_text_removal():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image.fill(255) # white background
    image[20:80, 20:80] = 0 # black square (diagram)
    image[10:15, 10:15] = 0 # small noise (text)
    
    bbox = BoundingBox(x=0, y=0, width=100, height=100)
    # Using kernel size > 5 to remove the 5x5 noise
    config = ExtractionConfig(padding=0, remove_text=True, text_removal_kernel_size=10)
    
    cropped, metadata = extract_diagram(image, bbox, config)
    
    assert cropped.shape == (100, 100, 3)
    # The small noise should be removed (become white)
    assert np.all(cropped[10:15, 10:15] == 255)
    # The large block should remain black (at least partially, ignoring edges if affected)
    # Let's check a point inside the large block
    assert np.all(cropped[50, 50] == 0)
