"""
Heuristic OCR Provider — uses OpenCV contour analysis to detect text-like
regions and return descriptive labels when real OCR (Tesseract) is not available.

This is NOT a real OCR engine. It honestly reports that the labels are
heuristically generated and flags them for human-in-the-loop correction.

Design note:
    The spec says: "If a problem cannot reliably be solved automatically,
    implement a robust heuristic/algorithmic solution and expose a
    human-in-the-loop correction mechanism."
"""
import cv2
import numpy as np
from typing import Any
from .base import OCRProvider


class MockOCRProvider(OCRProvider):
    """
    Heuristic OCR provider for environments without Tesseract.

    Attempts basic text region detection via connected component analysis.
    Returns descriptive placeholder labels (e.g. "Text Region A") and
    sets a low confidence score so the human-in-the-loop editor knows
    these labels require manual correction.
    """

    def __init__(self) -> None:
        self._label_counter = 0  # per-instance counter for unique labels

    def extract_text(self, image: np.ndarray, bbox: dict[str, Any]) -> tuple[str, float]:
        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        w = int(bbox.get("w", bbox.get("width", 50)))
        h = int(bbox.get("h", bbox.get("height", 20)))

        # Clamp to image bounds
        ih, iw = image.shape[:2]
        x1 = max(0, min(x, iw - 1))
        y1 = max(0, min(y, ih - 1))
        x2 = max(0, min(x + w, iw))
        y2 = max(0, min(y + h, ih))

        if x2 <= x1 or y2 <= y1:
            self._label_counter += 1
            return f"Region {self._label_counter}", 0.10

        roi = image[y1:y2, x1:x2]

        # Convert to grayscale and threshold
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Count non-zero pixels as a proxy for "how much text is here"
        text_density = cv2.countNonZero(binary) / max(binary.size, 1)

        # Use connected components to estimate character count
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        # Filter out tiny noise components
        char_like = [
            s for s in stats[1:]  # skip background
            if s[cv2.CC_STAT_WIDTH] > 3 and s[cv2.CC_STAT_HEIGHT] > 3
            and s[cv2.CC_STAT_AREA] > 10
        ]

        self._label_counter += 1
        label_id = self._label_counter

        if len(char_like) == 0:
            # No text-like content found
            return f"Region {label_id}", 0.10
        elif text_density > 0.15 and len(char_like) >= 3:
            # Likely contains a word — assign a descriptive placeholder
            # Use the label counter to generate unique letter-based names
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            idx = (label_id - 1) % len(letters)
            return f"Label {letters[idx]}", 0.40
        else:
            return f"Symbol {label_id}", 0.20
