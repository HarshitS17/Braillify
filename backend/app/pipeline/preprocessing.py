import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF

from ..core.logging import get_logger
from ..core.exceptions import FileFormatError, ProcessingError
from ..models.preprocessing import (
    PreprocessingConfig, PreprocessingResult, PreprocessingStage, StageResult,
)

logger = get_logger("pipeline.preprocessing")


# --- Image Loading ---

def load_image(file_path: Path) -> np.ndarray:
    """Load an image file (PNG, JPG, TIFF) as a BGR numpy array.
    
    Raises FileFormatError if the file cannot be read.
    """
    if not file_path.exists():
        raise FileFormatError(f"File not found: {file_path}")
    
    img = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileFormatError(f"Failed to decode image: {file_path}")
    
    logger.info(f"Loaded image: {file_path} ({img.shape[1]}x{img.shape[0]})")
    return img


def render_pdf_page(pdf_path: Path, page_number: int = 0, dpi: int = 300) -> np.ndarray:
    """Render a single PDF page to a BGR numpy array.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: 0-indexed page number
        dpi: Resolution for rendering
    
    Returns:
        BGR numpy array of the rendered page
    """
    if not pdf_path.exists():
        raise FileFormatError(f"PDF file not found: {pdf_path}")
    
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        raise FileFormatError(f"Failed to open PDF: {e}")
    
    if page_number >= len(doc):
        raise FileFormatError(
            f"Page {page_number} out of range (PDF has {len(doc)} pages)"
        )
    
    page = doc[page_number]
    # Calculate zoom for desired DPI (PDF default is 72 DPI)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix)
    
    # Convert to numpy array
    img_data = np.frombuffer(pixmap.samples, dtype=np.uint8)
    if pixmap.n == 4:  # RGBA
        img = img_data.reshape(pixmap.h, pixmap.w, 4)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pixmap.n == 3:  # RGB
        img = img_data.reshape(pixmap.h, pixmap.w, 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:  # Grayscale
        img = img_data.reshape(pixmap.h, pixmap.w)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    doc.close()
    logger.info(
        f"Rendered PDF page {page_number} at {dpi} DPI: {img.shape[1]}x{img.shape[0]}"
    )
    return img


# --- Preprocessing Stages (Pure Functions) ---

def to_grayscale(image: np.ndarray) -> tuple[np.ndarray, dict]:
    """Convert BGR image to grayscale.
    
    Returns:
        (grayscale_image, metadata_dict)
    """
    if len(image.shape) == 2:
        return image.copy(), {"already_grayscale": True}
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    metadata = {
        "input_channels": image.shape[2] if len(image.shape) == 3 else 1,
        "output_shape": list(gray.shape),
    }
    return gray, metadata


def reduce_noise(
    image: np.ndarray, config: PreprocessingConfig
) -> tuple[np.ndarray, dict]:
    """Apply noise reduction using Gaussian blur followed by non-local means.
    
    Operates on grayscale image.
    """
    # Ensure kernel size is odd
    k = config.gaussian_kernel_size
    if k % 2 == 0:
        k += 1
    
    # Gaussian blur for initial smoothing
    blurred = cv2.GaussianBlur(image, (k, k), 0)
    
    # Non-local means denoising for detail preservation
    denoised = cv2.fastNlMeansDenoising(
        blurred,
        h=config.nlm_h,
        templateWindowSize=config.nlm_template_window,
        searchWindowSize=config.nlm_search_window,
    )
    
    metadata = {
        "gaussian_kernel": k,
        "nlm_h": config.nlm_h,
        "nlm_template_window": config.nlm_template_window,
        "nlm_search_window": config.nlm_search_window,
        "noise_reduction_estimate": float(np.std(image.astype(float) - denoised.astype(float))),
    }
    return denoised, metadata


def correct_illumination(
    image: np.ndarray, config: PreprocessingConfig
) -> tuple[np.ndarray, dict]:
    """Apply CLAHE for contrast-limited adaptive histogram equalization."""
    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=(config.clahe_grid_size, config.clahe_grid_size),
    )
    corrected = clahe.apply(image)
    
    metadata = {
        "clahe_clip_limit": config.clahe_clip_limit,
        "clahe_grid_size": config.clahe_grid_size,
        "mean_before": float(np.mean(image)),
        "mean_after": float(np.mean(corrected)),
        "std_before": float(np.std(image)),
        "std_after": float(np.std(corrected)),
    }
    return corrected, metadata


def detect_skew_angle(
    image: np.ndarray, config: PreprocessingConfig
) -> tuple[float, dict]:
    """Detect page skew angle using Hough Line Transform.
    
    Returns:
        (angle_degrees, metadata_dict)
        Angle is in degrees, positive = clockwise skew.
    """
    # Edge detection for line finding
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # Probabilistic Hough Line Transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=config.hough_threshold,
        minLineLength=config.hough_min_line_length,
        maxLineGap=config.hough_max_line_gap,
    )
    
    if lines is None or len(lines) == 0:
        return 0.0, {"lines_detected": 0, "skew_detected": False}
    
    # Normalize line array shape for OpenCV 4.x (N,1,4) and 5.x (N,4) compatibility
    lines_array = np.array(lines).reshape(-1, 4)
    
    # Calculate angles of detected lines
    angles = []
    for x1, y1, x2, y2 in lines_array:
        if x2 - x1 == 0:
            continue
        angle = np.degrees(np.arctan2(float(y2 - y1), float(x2 - x1)))
        # Only consider near-horizontal lines (likely text baselines)
        if abs(angle) < config.deskew_max_angle:
            angles.append(angle)
    
    if not angles:
        return 0.0, {"lines_detected": len(lines), "near_horizontal": 0, "skew_detected": False}
    
    # Use median angle as the skew estimate (robust to outliers)
    median_angle = float(np.median(angles))
    
    metadata = {
        "lines_detected": len(lines),
        "near_horizontal": len(angles),
        "angle_median": median_angle,
        "angle_std": float(np.std(angles)),
        "skew_detected": abs(median_angle) > 0.5,  # threshold for significant skew
    }
    return median_angle, metadata


def deskew(
    image: np.ndarray, angle: float
) -> tuple[np.ndarray, dict]:
    """Rotate image to correct detected skew.
    
    Args:
        image: Grayscale image
        angle: Skew angle in degrees (positive = clockwise)
    
    Returns:
        (deskewed_image, metadata_dict)
    """
    if abs(angle) < 0.1:  # Skip trivial rotations
        return image.copy(), {"skipped": True, "angle": angle}
    
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    # Rotation matrix (negate angle to correct the skew)
    rotation_matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
    
    # Calculate new bounding box to avoid cropping
    cos = abs(rotation_matrix[0, 0])
    sin = abs(rotation_matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    rotation_matrix[0, 2] += (new_w - w) / 2
    rotation_matrix[1, 2] += (new_h - h) / 2
    
    # Use white background for border fill
    deskewed = cv2.warpAffine(
        image, rotation_matrix, (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    
    metadata = {
        "angle_corrected": angle,
        "original_size": [w, h],
        "new_size": [new_w, new_h],
    }
    return deskewed, metadata


def adaptive_threshold(
    image: np.ndarray, config: PreprocessingConfig
) -> tuple[np.ndarray, dict]:
    """Apply adaptive thresholding to produce a binary image."""
    block_size = config.adaptive_block_size
    if block_size % 2 == 0:
        block_size += 1
    
    binary = cv2.adaptiveThreshold(
        image,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=block_size,
        C=config.adaptive_c,
    )
    
    # Calculate statistics
    white_ratio = float(np.sum(binary == 255)) / binary.size
    
    metadata = {
        "block_size": block_size,
        "constant_c": config.adaptive_c,
        "white_pixel_ratio": white_ratio,
        "black_pixel_ratio": 1.0 - white_ratio,
    }
    return binary, metadata


def normalize_contrast(image: np.ndarray) -> tuple[np.ndarray, dict]:
    """Normalize contrast by stretching the histogram to full 0-255 range."""
    min_val = float(np.min(image))
    max_val = float(np.max(image))
    
    if max_val - min_val < 1:
        return image.copy(), {"skipped": True, "reason": "already_uniform"}
    
    normalized = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
    
    metadata = {
        "input_min": min_val,
        "input_max": max_val,
        "input_range": max_val - min_val,
        "output_min": float(np.min(normalized)),
        "output_max": float(np.max(normalized)),
    }
    return normalized, metadata


def normalize_resolution(
    image: np.ndarray, config: PreprocessingConfig, current_dpi: int | None = None
) -> tuple[np.ndarray, dict]:
    """Normalize image resolution / dimensions.
    
    If current DPI is known and differs from target, resample.
    Otherwise, ensure max dimension doesn't exceed target_max_dimension.
    """
    h, w = image.shape[:2]
    scale = 1.0
    reason = "none"
    
    if current_dpi and current_dpi != config.target_dpi:
        scale = config.target_dpi / current_dpi
        reason = f"dpi_normalization_{current_dpi}_to_{config.target_dpi}"
    elif max(h, w) > config.target_max_dimension:
        scale = config.target_max_dimension / max(h, w)
        reason = f"dimension_reduction_max_{max(h, w)}_to_{config.target_max_dimension}"
    
    if abs(scale - 1.0) < 0.01:
        return image.copy(), {"skipped": True, "reason": "already_at_target"}
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
    
    metadata = {
        "scale_factor": scale,
        "original_size": [w, h],
        "new_size": [new_w, new_h],
        "reason": reason,
        "interpolation": "INTER_AREA" if scale < 1.0 else "INTER_CUBIC",
    }
    return resized, metadata


# --- Debug Artifact Helper ---

def _save_debug_artifact(
    image: np.ndarray, output_dir: Path, stage: PreprocessingStage
) -> str:
    """Save a preprocessing stage image as a debug artifact."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{stage.value}.png"
    path = output_dir / filename
    cv2.imwrite(str(path), image)
    return str(path)


# --- Pipeline Orchestrator ---

def preprocess_image(
    image_path: Path,
    output_dir: Path,
    config: PreprocessingConfig | None = None,
    page_id: str = "",
    save_debug: bool = True,
    source_dpi: int | None = None,
) -> PreprocessingResult:
    """Run the complete preprocessing pipeline on an image.
    
    Args:
        image_path: Path to the input image
        output_dir: Directory for saving preprocessed outputs and debug artifacts
        config: Preprocessing parameters (uses defaults if None)
        page_id: ID of the page being processed
        save_debug: Whether to save intermediate images as debug artifacts
        source_dpi: Known DPI of the source image (if available)
    
    Returns:
        PreprocessingResult with paths and metadata for each stage
    """
    if config is None:
        config = PreprocessingConfig()
    
    result = PreprocessingResult(
        page_id=page_id,
        config=config,
        original_path=str(image_path),
    )
    
    debug_dir = output_dir / "debug" if save_debug else None
    
    try:
        # 1. Load image
        image = load_image(image_path)
        result.original_width = image.shape[1]
        result.original_height = image.shape[0]
        
        if debug_dir:
            path = _save_debug_artifact(image, debug_dir, PreprocessingStage.ORIGINAL)
            result.stages.append(StageResult(
                stage=PreprocessingStage.ORIGINAL, image_path=path,
                metadata={"width": image.shape[1], "height": image.shape[0]},
            ))
        
        # 2. Grayscale
        gray, gray_meta = to_grayscale(image)
        result.grayscale_path = str(output_dir / "grayscale.png")
        cv2.imwrite(result.grayscale_path, gray)
        if debug_dir:
            path = _save_debug_artifact(gray, debug_dir, PreprocessingStage.GRAYSCALE)
            result.stages.append(StageResult(
                stage=PreprocessingStage.GRAYSCALE, image_path=path, metadata=gray_meta,
            ))
        
        # 3. Noise reduction
        denoised, denoise_meta = reduce_noise(gray, config)
        if debug_dir:
            path = _save_debug_artifact(denoised, debug_dir, PreprocessingStage.DENOISED)
            result.stages.append(StageResult(
                stage=PreprocessingStage.DENOISED, image_path=path, metadata=denoise_meta,
            ))
        
        # 4. Illumination correction (CLAHE)
        corrected, clahe_meta = correct_illumination(denoised, config)
        if debug_dir:
            path = _save_debug_artifact(corrected, debug_dir, PreprocessingStage.ILLUMINATION_CORRECTED)
            result.stages.append(StageResult(
                stage=PreprocessingStage.ILLUMINATION_CORRECTED, image_path=path, metadata=clahe_meta,
            ))
        
        # 5. Contrast normalization
        normalized, norm_meta = normalize_contrast(corrected)
        if debug_dir:
            path = _save_debug_artifact(normalized, debug_dir, PreprocessingStage.CONTRAST_NORMALIZED)
            result.stages.append(StageResult(
                stage=PreprocessingStage.CONTRAST_NORMALIZED, image_path=path, metadata=norm_meta,
            ))
        
        # 6. Deskewing
        skew_angle = 0.0
        if config.deskew_enabled:
            skew_angle, skew_meta = detect_skew_angle(normalized, config)
            result.detected_skew_angle = skew_angle
            
            if abs(skew_angle) > 0.5:
                deskewed, deskew_meta = deskew(normalized, skew_angle)
                deskew_meta.update(skew_meta)
            else:
                deskewed = normalized
                deskew_meta = {"skipped": True, **skew_meta}
            
            if debug_dir:
                path = _save_debug_artifact(deskewed, debug_dir, PreprocessingStage.DESKEWED)
                result.stages.append(StageResult(
                    stage=PreprocessingStage.DESKEWED, image_path=path, metadata=deskew_meta,
                ))
        else:
            deskewed = normalized
        
        # 7. Resolution normalization
        res_normalized, res_meta = normalize_resolution(deskewed, config, source_dpi)
        if debug_dir and not res_meta.get("skipped"):
            path = _save_debug_artifact(res_normalized, debug_dir, PreprocessingStage.RESOLUTION_NORMALIZED)
            result.stages.append(StageResult(
                stage=PreprocessingStage.RESOLUTION_NORMALIZED, image_path=path, metadata=res_meta,
            ))
        
        # 8. Adaptive thresholding (binary output)
        binary, thresh_meta = adaptive_threshold(res_normalized, config)
        result.binary_path = str(output_dir / "binary.png")
        cv2.imwrite(result.binary_path, binary)
        if debug_dir:
            path = _save_debug_artifact(binary, debug_dir, PreprocessingStage.THRESHOLDED)
            result.stages.append(StageResult(
                stage=PreprocessingStage.THRESHOLDED, image_path=path, metadata=thresh_meta,
            ))
        
        # Save final preprocessed image (the normalized grayscale before thresholding)
        result.preprocessed_path = str(output_dir / "preprocessed.png")
        cv2.imwrite(result.preprocessed_path, res_normalized)
        result.estimated_dpi = source_dpi or config.target_dpi
        
        result.success = True
        logger.info(f"Preprocessing complete for page {page_id}: {len(result.stages)} stages")
        
    except (FileFormatError, ProcessingError):
        raise
    except Exception as e:
        result.success = False
        result.error_message = str(e)
        logger.error(f"Preprocessing failed for page {page_id}: {e}", exc_info=True)
        raise ProcessingError(f"Preprocessing failed: {e}")
    
    return result
