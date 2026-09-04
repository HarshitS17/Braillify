from .base import Validator
from ...models.diagram import Diagram
from ...models.label import Label
from ...models.validation import ValidationMessage, ValidationLevel
from .geometry import _bbox_from_element

def _rect_overlap(ax, ay, aw, ah, bx, by, bw, bh) -> float:
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    return ix * iy

class LabelCollisionValidator(Validator):
    def validate(self, diagram: Diagram, labels: list[Label]) -> list[ValidationMessage]:
        messages = []
        
        placed = [lbl for lbl in labels if lbl.placement]
        
        # Check label-to-label collision (ERROR)
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                l1 = placed[i]
                l2 = placed[j]
                
                p1 = l1.placement
                p2 = l2.placement
                
                if not p1 or not p2: continue
                
                overlap = _rect_overlap(
                    p1.position.x, p1.position.y, p1.width, p1.height,
                    p2.position.x, p2.position.y, p2.width, p2.height
                )
                
                if overlap > 0:
                    messages.append(ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message="Braille labels overlap with each other.",
                        label_ids=[l1.id, l2.id]
                    ))
                    
        # Check label-to-geometry collision (WARNING)
        for lbl in placed:
            p = lbl.placement
            if not p: continue
            
            for el in diagram.elements:
                if el.id == lbl.target_element_id:
                    # It's somewhat okay if it slightly overlaps its target, but we still check
                    pass
                
                ex, ey, ew, eh = _bbox_from_element(el)
                if ew == 0 and eh == 0:
                    continue
                    
                overlap = _rect_overlap(
                    p.position.x, p.position.y, p.width, p.height,
                    ex, ey, ew, eh
                )
                if overlap > 0:
                    messages.append(ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message="Braille label overlaps with diagram geometry.",
                        label_ids=[lbl.id],
                        element_ids=[el.id]
                    ))
                    
        return messages

class LabelSpacingValidator(Validator):
    def __init__(self, min_gap: float = 8.0):
        self.min_gap = min_gap
        
    def validate(self, diagram: Diagram, labels: list[Label]) -> list[ValidationMessage]:
        messages = []
        placed = [lbl for lbl in labels if lbl.placement]
        
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                l1 = placed[i]
                l2 = placed[j]
                
                p1 = l1.placement
                p2 = l2.placement
                
                gap_x = max(0, max(p1.position.x, p2.position.x) - min(p1.position.x + p1.width, p2.position.x + p2.width))
                gap_y = max(0, max(p1.position.y, p2.position.y) - min(p1.position.y + p1.height, p2.position.y + p2.height))
                gap = (gap_x**2 + gap_y**2)**0.5
                
                if gap > 0 and gap < self.min_gap:
                    messages.append(ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Labels are too close together ({gap:.1f}px) for tactile readability.",
                        label_ids=[l1.id, l2.id]
                    ))
        return messages
