from pydantic import BaseModel, Field
from enum import Enum


class PreprocessingConfig(BaseModel):
    """Configurable parameters for preprocessing. No magic numbers."""
    # Noise reduction
    gaussian_kernel_size: int = Field(default=5, ge=3, description="Gaussian blur kernel size (must be odd)")
    nlm_h: float = Field(default=10.0, ge=0.0, description="Non-local means denoising strength")
    nlm_template_window: int = Field(default=7, ge=3, description="NLM template window size")
    nlm_search_window: int = Field(default=21, ge=3, description="NLM search window size")
    
    # CLAHE (illumination correction)
    clahe_clip_limit: float = Field(default=2.0, ge=0.0, description="CLAHE clip limit")
    clahe_grid_size: int = Field(default=8, ge=2, description="CLAHE grid size")
    
    # Adaptive thresholding
    adaptive_block_size: int = Field(default=11, ge=3, description="Adaptive threshold block size (must be odd)")
    adaptive_c: float = Field(default=2.0, description="Adaptive threshold constant subtracted from mean")
    
    # Deskewing
    deskew_enabled: bool = True
    deskew_max_angle: float = Field(default=15.0, ge=0.0, le=45.0, description="Maximum skew angle to correct")
    hough_threshold: int = Field(default=100, ge=10, description="Hough transform accumulator threshold")
    hough_min_line_length: int = Field(default=100, ge=10, description="Min line length for Hough")
    hough_max_line_gap: int = Field(default=10, ge=1, description="Max gap between line segments for Hough")
    
    # Resolution
    target_dpi: int = Field(default=300, ge=72, description="Target DPI for normalization")
    target_max_dimension: int = Field(default=4000, ge=500, description="Max dimension in pixels after normalization")
    
    # PDF
    pdf_dpi: int = Field(default=300, ge=72, description="DPI for rendering PDF pages")


class PreprocessingStage(str, Enum):
    """Named stages for tracking and debug artifacts."""
    ORIGINAL = "original"
    GRAYSCALE = "grayscale"
    DENOISED = "denoised"
    ILLUMINATION_CORRECTED = "illumination_corrected"
    DESKEWED = "deskewed"
    THRESHOLDED = "thresholded"
    CONTRAST_NORMALIZED = "contrast_normalized"
    RESOLUTION_NORMALIZED = "resolution_normalized"


class StageResult(BaseModel):
    """Result of a single preprocessing stage."""
    stage: PreprocessingStage
    image_path: str | None = None  # path to saved debug artifact
    metadata: dict = Field(default_factory=dict)  # stage-specific metadata
    success: bool = True
    error_message: str | None = None


class PreprocessingResult(BaseModel):
    """Complete result of preprocessing a page image."""
    page_id: str
    config: PreprocessingConfig
    stages: list[StageResult] = Field(default_factory=list)
    
    # Output paths
    original_path: str
    grayscale_path: str | None = None
    binary_path: str | None = None
    preprocessed_path: str | None = None  # final preprocessed image
    
    # Detected properties
    original_width: int = 0
    original_height: int = 0
    detected_skew_angle: float | None = None
    estimated_dpi: int | None = None
    
    success: bool = True
    error_message: str | None = None
