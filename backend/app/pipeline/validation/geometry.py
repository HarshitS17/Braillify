from .base import Validator
from ...models.diagram import Diagram, ElementType
from ...models.label import Label
from ...models.validation import ValidationMessage, ValidationLevel

def _bbox_from_element(el) -> tuple[float, float, float, float]:
    g = el.geometry
    if "x" in g and "w" in g:
        return g["x"], g["y"], g["w"], g["h"]
    if "cx" in g and "r" in g:
        r = g["r"]
        return g["cx"] - r, g["cy"] - r, 2 * r, 2 * r
    if "x1" in g:
        x1, y1, x2, y2 = g["x1"], g["y1"], g["x2"], g["y2"]
        return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
    if "points" in g:
        xs = [p["x"] for p in g["points"]]
        ys = [p["y"] for p in g["points"]]
        x_min, y_min = min(xs), min(ys)
        return x_min, y_min, max(xs) - x_min, max(ys) - y_min
    return 0, 0, 0, 0

class FeatureSizeValidator(Validator):
    def __init__(self, min_area: float = 25.0):
        self.min_area = min_area
        
    def validate(self, diagram: Diagram, labels: list[Label]) -> list[ValidationMessage]:
        messages = []
        for el in diagram.elements:
            if el.type in (ElementType.POLYGON, ElementType.FILLED_REGION):
                # Check area
                area = el.geometry.get("area", 0)
                if not area:
                    _, _, w, h = _bbox_from_element(el)
                    area = w * h
                    
                if area > 0 and area < self.min_area:
                    messages.append(ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Feature area ({area:.1f}) is below minimum tactile threshold.",
                        element_ids=[el.id]
                    ))
        return messages

class BoundsValidator(Validator):
    def validate(self, diagram: Diagram, labels: list[Label]) -> list[ValidationMessage]:
        messages = []
        if not diagram.canvas:
            return messages
            
        cw = diagram.canvas.width
        ch = diagram.canvas.height
        
        for el in diagram.elements:
            x, y, w, h = _bbox_from_element(el)
            if w == 0 and h == 0:
                continue
                
            if x < 0 or y < 0 or x + w > cw or y + h > ch:
                messages.append(ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message="Element extends beyond the printable canvas bounds.",
                    element_ids=[el.id]
                ))
        return messages

class DensityValidator(Validator):
    def __init__(self, max_elements: int = 150):
        self.max_elements = max_elements
        
    def validate(self, diagram: Diagram, labels: list[Label]) -> list[ValidationMessage]:
        messages = []
        if len(diagram.elements) > self.max_elements:
            messages.append(ValidationMessage(
                level=ValidationLevel.SUGGESTION,
                message=f"High tactile density ({len(diagram.elements)} elements). Consider simplifying the diagram to prevent clutter."
            ))
        return messages
