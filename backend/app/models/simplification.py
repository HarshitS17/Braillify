from pydantic import BaseModel

class SimplificationConfig(BaseModel):
    minimum_feature_area: float = 50.0
    minimum_line_length: float = 30.0
    dp_epsilon_factor: float = 0.05
    duplicate_overlap_threshold: float = 0.85
