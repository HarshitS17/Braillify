from pydantic import BaseModel, Field

class ExtractionConfig(BaseModel):
    padding: int = Field(default=10, ge=0)
    # Keep text in the extracted crop: analysis masks real label regions out of
    # the geometry (bounded text-region heuristic) and the OCR stage reads the
    # same extracted image to produce labels. Removing text here starved OCR.
    remove_text: bool = Field(default=False)
    text_removal_kernel_size: int = Field(default=5, ge=1)

class AnalysisConfig(BaseModel):
    # HoughLinesP
    line_rho: float = Field(default=1.0)
    line_theta: float = Field(default=3.14159265 / 180.0)
    line_threshold: int = Field(default=50, ge=1)
    line_min_length: float = Field(default=20.0, ge=1.0)
    line_max_gap: float = Field(default=10.0, ge=0.0)
    
    # HoughCircles
    circle_dp: float = Field(default=1.2, ge=1.0)
    circle_min_dist: float = Field(default=20.0, ge=1.0)
    circle_param1: float = Field(default=50.0, ge=1.0)
    circle_param2: float = Field(default=30.0, ge=1.0)
    circle_min_radius: int = Field(default=5, ge=0)
    circle_max_radius: int = Field(default=100, ge=0)
    
    # Polygons
    approx_epsilon_factor: float = Field(default=0.02, ge=0.001)
    min_polygon_area: float = Field(default=100.0, ge=1.0)
    
    # Texts
    text_dilation_kernel: tuple[int, int] = Field(default=(15, 3))
    
    # Arrows
    arrow_max_head_area: float = Field(default=150.0, ge=1.0)
    
    # Curves
    curve_min_vertices: int = Field(default=8, ge=3)
