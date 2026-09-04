import pytest
from app.models.diagram import DiagramElement, ElementType, SemanticRole
from app.models.simplification import SimplificationConfig
from app.pipeline.simplification import simplify_diagram

def test_simplification_filtering_small_line():
    config = SimplificationConfig(minimum_line_length=30.0)
    # Line length = sqrt((10-0)^2 + (0-0)^2) = 10, which is < 30
    el1 = DiagramElement(
        type=ElementType.LINE,
        geometry={"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0},
        semantic_role=SemanticRole.STRUCTURE
    )
    
    # Line length = 50, which is >= 30
    el2 = DiagramElement(
        type=ElementType.LINE,
        geometry={"x1": 0.0, "y1": 0.0, "x2": 50.0, "y2": 0.0},
        semantic_role=SemanticRole.STRUCTURE
    )
    
    elements = [el1, el2]
    simplified = simplify_diagram(elements, config)
    
    assert len(simplified) == 1
    assert simplified[0].simplified_from == el2.id

def test_simplification_dp_smoothing():
    config = SimplificationConfig(dp_epsilon_factor=0.05)
    
    # Polygon with many points, mostly on a straight line
    points = [
        {"x": 0.0, "y": 0.0},
        {"x": 50.0, "y": 1.0}, # Slight deviation, should be smoothed out
        {"x": 100.0, "y": 0.0},
        {"x": 100.0, "y": 100.0},
        {"x": 0.0, "y": 100.0}
    ]
    
    el = DiagramElement(
        type=ElementType.POLYGON,
        geometry={"points": points},
        semantic_role=SemanticRole.STRUCTURE
    )
    
    simplified = simplify_diagram([el], config)
    
    assert len(simplified) == 1
    new_el = simplified[0]
    assert new_el.simplified_from == el.id
    
    new_points = new_el.geometry["points"]
    # The point (50, 1) should be removed by DP smoothing
    assert len(new_points) < len(points)
    assert "simplification_reason" in new_el.metadata
    assert "DP Simplification" in new_el.metadata["simplification_reason"]

def test_simplification_deduplication():
    config = SimplificationConfig(duplicate_overlap_threshold=0.85)
    
    points1 = [
        {"x": 0.0, "y": 0.0},
        {"x": 100.0, "y": 0.0},
        {"x": 100.0, "y": 100.0},
        {"x": 0.0, "y": 100.0}
    ]
    
    # Almost identical
    points2 = [
        {"x": 1.0, "y": 1.0},
        {"x": 101.0, "y": 1.0},
        {"x": 101.0, "y": 101.0},
        {"x": 1.0, "y": 101.0}
    ]
    
    el1 = DiagramElement(
        type=ElementType.POLYGON,
        geometry={"points": points1},
        confidence=0.8
    )
    
    el2 = DiagramElement(
        type=ElementType.POLYGON,
        geometry={"points": points2},
        confidence=0.9 # Higher confidence
    )
    
    simplified = simplify_diagram([el1, el2], config)
    
    # Should deduplicate to keep only one (the one with higher confidence)
    assert len(simplified) == 1
    assert simplified[0].simplified_from == el2.id
