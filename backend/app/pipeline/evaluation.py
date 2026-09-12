from ..models.diagram import BoundingBox, Diagram
from ..models.label import Label, LabelSource
from ..pipeline.validation.labels import _rect_overlap

def calculate_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Calculate Intersection over Union for two bounding boxes."""
    x1 = max(box1.x, box2.x)
    y1 = max(box1.y, box2.y)
    x2 = min(box1.x + box1.width, box2.x + box2.width)
    y2 = min(box1.y + box1.height, box2.y + box2.height)
    
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    box1_area = box1.width * box1.height
    box2_area = box2.width * box2.height
    union_area = box1_area + box2_area - inter_area
    
    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def calculate_simplification_ratio(original_count: int, simplified_count: int) -> float:
    """Returns ratio of elements preserved (0.0 to 1.0). Lower means more simplified.
    Note: This only measures whole-element drops/deduplication. It cannot see
    vertex-level reduction (e.g. Douglas-Peucker)."""
    if original_count == 0:
        return 1.0
    return simplified_count / original_count

def calculate_vertex_reduction_ratio(original_vertex_count: int, simplified_vertex_count: int) -> float:
    """Ratio of vertices/points preserved (0.0 to 1.0). Lower means more
    geometric detail was removed by DP simplification. Distinct from
    calculate_simplification_ratio, which only measures whole-element
    drops/deduplication and cannot see vertex-level reduction."""
    if original_vertex_count == 0:
        return 1.0
    return simplified_vertex_count / original_vertex_count

def calculate_collision_rate(diagram: Diagram, labels: list[Label]) -> float:
    """Returns percentage of labels that have a collision with geometry or other labels."""
    placed = [lbl for lbl in labels if lbl.placement]
    if not placed:
        return 0.0
        
    collisions = 0
    for i, l1 in enumerate(placed):
        has_col = False
        p1 = l1.placement
        if not p1: continue
        
        # Check label-to-label
        for j in range(i + 1, len(placed)):
            l2 = placed[j]
            p2 = l2.placement
            if p2:
                overlap = _rect_overlap(
                    p1.position.x, p1.position.y, p1.width, p1.height,
                    p2.position.x, p2.position.y, p2.width, p2.height
                )
                if overlap > 0:
                    has_col = True
                    break
        
        if has_col:
            collisions += 1
            
    return collisions / len(placed)

def calculate_manual_correction_rate(labels: list[Label]) -> float:
    """Returns percentage of labels that were manually edited."""
    if not labels:
        return 0.0
    manual = sum(1 for lbl in labels if lbl.source == LabelSource.MANUAL)
    return manual / len(labels)
