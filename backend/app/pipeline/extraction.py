import cv2
import numpy as np
from ..models.diagram import BoundingBox
from ..models.extraction import ExtractionConfig

def extract_diagram(image: np.ndarray, bbox: BoundingBox, config: ExtractionConfig) -> tuple[np.ndarray, dict]:
    """
    Extracts a diagram from an image based on a bounding box.
    """
    h, w = image.shape[:2]
    
    # Calculate bounding box with padding
    x = max(0, int(bbox.x) - config.padding)
    y = max(0, int(bbox.y) - config.padding)
    x_end = min(w, int(bbox.x + bbox.width) + config.padding)
    y_end = min(h, int(bbox.y + bbox.height) + config.padding)
    
    cropped = image[y:y_end, x:x_end].copy()
    
    if config.remove_text:
        # Convert to grayscale if necessary
        if len(cropped.shape) == 3:
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        else:
            gray = cropped.copy()
            
        # Binarize (assuming dark foreground on light background)
        # Using Otsu's thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological opening to remove small objects (like text)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, 
            (config.text_removal_kernel_size, config.text_removal_kernel_size)
        )
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Reconstruct the image: mask out the removed text
        # Places where opened is 0 but binary was 255 are the text fragments removed
        removed_mask = cv2.bitwise_and(binary, cv2.bitwise_not(opened))
        
        if len(cropped.shape) == 3:
            cropped[removed_mask == 255] = [255, 255, 255]
        else:
            cropped[removed_mask == 255] = 255
            
    metadata = {
        "offset_x": float(x),
        "offset_y": float(y),
        "scale_factor": 1.0
    }
    
    return cropped, metadata
