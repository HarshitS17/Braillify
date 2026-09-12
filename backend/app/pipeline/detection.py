import cv2
import numpy as np
import logging
from ..models.diagram import DiagramCandidate, BoundingBox, DetectionFeatures

logger = logging.getLogger("pipeline.detection")

# ---------------------------------------------------------------------------
# Multi-scale detection configuration
# ---------------------------------------------------------------------------
# Each scale is (kernel_size, iterations).  Smaller kernels preserve separate
# close-together diagrams; larger kernels connect fragments of a single sparse
# diagram.  Running all three and merging via NMS gives the best of both.
_SCALES = [
    ((7, 7), 2),    # fine — preserves close-together separate diagrams
    ((15, 15), 3),  # medium — the original single-scale setting
    ((25, 25), 4),  # coarse — connects fragments of sparse diagrams
]

# IoU threshold for Non-Maximum Suppression: if two candidate boxes overlap
# more than this, the lower-confidence one is suppressed.
_NMS_IOU_THRESHOLD = 0.45


def _iou(a: BoundingBox, b: BoundingBox) -> float:
    """Intersection-over-Union of two axis-aligned bounding boxes."""
    x1 = max(a.x, b.x)
    y1 = max(a.y, b.y)
    x2 = min(a.x + a.width, b.x + b.width)
    y2 = min(a.y + a.height, b.y + b.height)

    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = a.width * a.height
    area_b = b.width * b.height
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms(candidates: list[DiagramCandidate], iou_thresh: float) -> list[DiagramCandidate]:
    """Greedy Non-Maximum Suppression: keep the highest-confidence candidate
    and suppress all candidates whose IoU with it exceeds *iou_thresh*,
    then repeat for the remaining candidates."""
    if not candidates:
        return []
    # Sort descending by confidence (stable)
    remaining = sorted(candidates, key=lambda c: c.confidence, reverse=True)
    kept: list[DiagramCandidate] = []
    while remaining:
        best = remaining.pop(0)
        kept.append(best)
        remaining = [
            c for c in remaining
            if _iou(best.bbox, c.bbox) < iou_thresh
        ]
    return kept


def _estimate_text_density(gray_roi: np.ndarray) -> float:
    """Estimate what fraction of the ROI area is occupied by text-like
    connected components (small, horizontally-elongated blobs).

    Returns a value in [0, 1].  A high value (> 0.5) suggests the region
    is a text paragraph rather than a diagram.
    """
    if gray_roi.size == 0:
        return 0.0
    h, w = gray_roi.shape[:2]
    area = h * w
    if area == 0:
        return 0.0

    # Binarise
    _, binary = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    text_area = 0
    for i in range(1, num_labels):  # skip background
        cw = stats[i, cv2.CC_STAT_WIDTH]
        ch = stats[i, cv2.CC_STAT_HEIGHT]
        ca = stats[i, cv2.CC_STAT_AREA]
        # Text-like heuristic: aspect ratio > 1, height < 6% of ROI,
        # width < 60% of ROI, non-trivial area.
        if ch < 1:
            continue
        aspect = cw / float(ch)
        if 0.3 < aspect < 8.0 and ch < 0.06 * h and cw < 0.6 * w and ca > 10:
            text_area += ca
    return text_area / area


class DiagramDetector:
    def __init__(
        self,
        min_area_ratio: float = 0.02,
        max_area_ratio: float = 0.9,
        min_aspect_ratio: float = 0.1,
        max_aspect_ratio: float = 10.0,
    ):
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio

    # ------------------------------------------------------------------
    # Single-scale candidate extraction
    # ------------------------------------------------------------------
    def _detect_at_scale(
        self,
        gray: np.ndarray,
        thresh: np.ndarray,
        kernel_size: tuple[int, int],
        iterations: int,
    ) -> list[DiagramCandidate]:
        """Run detection at a single dilation scale and return raw candidates."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        dilated = cv2.dilate(thresh, kernel, iterations=iterations)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        img_h, img_w = gray.shape[:2]
        img_area = img_w * img_h
        candidates: list[DiagramCandidate] = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            area_ratio = area / img_area
            aspect_ratio = w / float(h) if h > 0 else 0

            if area_ratio < self.min_area_ratio or area_ratio > self.max_area_ratio:
                continue
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue

            # --- Feature extraction on original grayscale ROI ---
            roi = gray[y : y + h, x : x + w]
            edges = cv2.Canny(roi, 50, 150)
            edge_density = float(np.sum(edges > 0) / area) if area > 0 else 0.0

            sub_contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = len(sub_contours)
            has_enclosed = contour_count > 5

            text_density = _estimate_text_density(roi)

            features = DetectionFeatures(
                edge_density=edge_density,
                text_density=text_density,
                component_density=float(contour_count / area * 1000) if area > 0 else 0.0,
                contour_count=contour_count,
                has_enclosed_regions=has_enclosed,
            )

            # --- Confidence scoring ---
            # Base: edge complexity
            confidence = min(1.0, edge_density * 3.0 + (0.2 if has_enclosed else 0.0))

            # Penalise text-heavy regions: a pure text block is not a diagram
            if text_density > 0.6:
                confidence *= 0.3
                reason = "Text-heavy region — likely a paragraph, not a diagram."
            elif text_density > 0.3:
                confidence *= 0.7
                reason = "Mixed text/diagram region with moderate text density."
            else:
                reason = "Region meets geometric criteria with sufficient edge complexity."

            candidate = DiagramCandidate(
                bbox=BoundingBox(x=float(x), y=float(y), width=float(w), height=float(h)),
                confidence=confidence,
                features=features,
                classification_reason=reason,
            )
            candidates.append(candidate)

        return candidates

    # ------------------------------------------------------------------
    # Thresholding with adaptive fallback
    # ------------------------------------------------------------------
    @staticmethod
    def _threshold(gray: np.ndarray) -> np.ndarray:
        """Otsu thresholding with an adaptive-threshold fallback.

        Otsu assumes a bimodal histogram (foreground + background).  When the
        image is very low-contrast or has uneven illumination the histogram is
        unimodal and Otsu picks a poor split.  We detect this by checking the
        ratio of foreground pixels: if Otsu produces < 1 % or > 60 % foreground
        we fall back to adaptive mean thresholding which handles uneven lighting
        better.
        """
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        fg_ratio = np.count_nonzero(otsu) / otsu.size if otsu.size > 0 else 0

        if 0.01 < fg_ratio < 0.60:
            return otsu

        logger.debug(
            "Otsu fg_ratio=%.3f out of range — falling back to adaptive threshold", fg_ratio
        )
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, blockSize=25, C=10
        )
        return adaptive

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detect(self, image: np.ndarray) -> list[DiagramCandidate]:
        """Detect diagram candidates in a preprocessed image.

        Uses multi-scale dilation (fine / medium / coarse) to generate
        candidates at different granularities, then merges them with
        Non-Maximum Suppression so that closely-spaced separate diagrams
        are not accidentally merged, while fragments of a single sparse
        diagram are not accidentally split.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        thresh = self._threshold(gray)

        # Collect candidates across all scales
        all_candidates: list[DiagramCandidate] = []
        for kernel_size, iterations in _SCALES:
            scale_candidates = self._detect_at_scale(gray, thresh, kernel_size, iterations)
            logger.debug(
                "Scale %s × %d → %d raw candidates",
                kernel_size,
                iterations,
                len(scale_candidates),
            )
            all_candidates.extend(scale_candidates)

        # Merge via NMS
        merged = _nms(all_candidates, _NMS_IOU_THRESHOLD)

        # Sort by confidence descending
        merged.sort(key=lambda c: c.confidence, reverse=True)
        logger.info(
            "Detection: %d raw candidates across %d scales → %d after NMS",
            len(all_candidates),
            len(_SCALES),
            len(merged),
        )
        return merged
