import cv2
import numpy as np
import logging
from ..models.diagram import DiagramCandidate, BoundingBox, DetectionFeatures

logger = logging.getLogger("pipeline.detection")

class DiagramDetector:
    def __init__(self, 
                 min_area_ratio: float = 0.02, 
                 max_area_ratio: float = 0.9,
                 min_aspect_ratio: float = 0.1,
                 max_aspect_ratio: float = 10.0):
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio

    def detect(self, image: np.ndarray) -> list[DiagramCandidate]:
        """Detect diagram candidates in a preprocessed image."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Assuming image is already preprocessed (e.g. grayscale).
        # We apply thresholding to find connected components.
        # Use THRESH_BINARY_INV so objects are white on black background.
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Dilate to connect nearby components (like text and lines belonging to same diagram)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        dilated = cv2.dilate(thresh, kernel, iterations=3)
        
        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        img_h, img_w = image.shape[:2]
        img_area = img_w * img_h
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            area_ratio = area / img_area
            aspect_ratio = w / float(h) if h > 0 else 0
            
            # Basic geometric filters
            if area_ratio < self.min_area_ratio or area_ratio > self.max_area_ratio:
                continue
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue
                
            # Compute features for this region from original grayscale
            roi = gray[y:y+h, x:x+w]
            edges = cv2.Canny(roi, 50, 150)
            edge_density = float(np.sum(edges > 0) / area)
            
            # Find sub-contours to estimate complexity
            sub_contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = len(sub_contours)
            
            has_enclosed = contour_count > 5
            
            features = DetectionFeatures(
                edge_density=edge_density,
                text_density=0.0,
                component_density=float(contour_count / area * 1000) if area > 0 else 0.0, 
                contour_count=contour_count,
                has_enclosed_regions=has_enclosed
            )
            
            # Simple heuristic confidence score
            confidence = min(1.0, edge_density * 3.0 + (0.2 if has_enclosed else 0.0))
            reason = "Region meets geometric criteria with sufficient edge complexity."
            
            candidate = DiagramCandidate(
                bbox=BoundingBox(x=float(x), y=float(y), width=float(w), height=float(h)),
                confidence=confidence,
                features=features,
                classification_reason=reason
            )
            candidates.append(candidate)
            
        # Sort by confidence descending
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates
