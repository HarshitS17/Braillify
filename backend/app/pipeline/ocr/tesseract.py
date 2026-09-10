import cv2
import numpy as np
from typing import Any
import pytesseract
import logging

from .base import OCRProvider

logger = logging.getLogger("tactile_ed.pipeline.ocr")

class TesseractOCRProvider(OCRProvider):
    """
    Uses Tesseract OCR to extract text from diagram regions.
    Falls back gracefully if Tesseract is not installed on the system.
    """
    def __init__(self, psm=6):
        """
        psm (Page Segmentation Mode):
        6: Assume a single uniform block of text. (Default for labels)
        7: Treat the image as a single text line.
        8: Treat the image as a single word.
        """
        self.psm = psm
        
        # Verify tesseract is available
        try:
            self.version = pytesseract.get_tesseract_version()
            self.is_available = True
            logger.info(f"Tesseract OCR initialized (v{self.version})")
        except Exception as e:
            logger.warning(f"Tesseract OCR is not available on this system. Make sure tesseract is installed. Error: {e}")
            self.is_available = False

    def extract_text(self, image: np.ndarray, bbox: dict[str, Any]) -> tuple[str, float]:
        if not self.is_available:
            return f"[OCR Unavailable]", 0.0

        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        w = int(bbox.get("w", bbox.get("width", 50)))
        h = int(bbox.get("h", bbox.get("height", 20)))

        # Add padding for better OCR recognition
        pad = 5
        h_img, w_img = image.shape[:2]
        
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_img, x + w + pad)
        y2 = min(h_img, y + h + pad)

        roi = image[y1:y2, x1:x2]
        
        if roi.size == 0:
            return "", 0.0
            
        # Preprocessing for better OCR
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi.copy()
            
        # Optional: scale up small text regions (Tesseract performs better on 300+ DPI equivalent)
        if h < 30:
            scale = 2.0
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
        # Binarize
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        # PyTesseract expects black text on white background
        binary = cv2.bitwise_not(binary)

        custom_config = f'--oem 3 --psm {self.psm}'
        
        try:
            # We use image_to_data to get confidence scores
            data = pytesseract.image_to_data(binary, config=custom_config, output_type=pytesseract.Output.DICT)
            
            words = []
            confidences = []
            
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if word and conf > 0:
                    words.append(word)
                    confidences.append(conf)
            
            if not words:
                return "", 0.0
                
            text = " ".join(words)
            avg_conf = sum(confidences) / len(confidences) / 100.0  # Normalize to 0-1
            
            return text, avg_conf
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed on region {bbox}: {e}")
            return "", 0.0
