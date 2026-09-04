"""
Tests for the constraint-based label placement engine.
"""

import pytest
from app.models.diagram import Diagram, DiagramElement, ElementType, Canvas, Point
from app.models.label import Label
from app.pipeline.placement import place_labels, PlacementConfig


def test_placement_no_conflict():
    # Setup a simple diagram with a single element
    el = DiagramElement(type=ElementType.FILLED_REGION, geometry={"x": 100, "y": 100, "w": 50, "h": 50})
    diagram = Diagram(
        project_id="test",
        page_id="p1",
        canvas=Canvas(width=800, height=600),
        elements=[el]
    )
    
    label = Label(
        diagram_id=diagram.id,
        text="Node",
        target_element_id=el.id
    )
    
    # Run placement
    result = place_labels([label], diagram)
    assert len(result) == 1
    placed = result[0].placement
    
    # It should have found a valid placement without a leader line
    assert placed is not None
    assert placed.placement_score < 50.0
    assert placed.leader_line is None
    
    # Ensure it's not placed directly over the element (x,y of label vs x,y of element)
    # The default candidate offset is 15.
    # Label should be outside the 100-150 range.
    assert (placed.position.x + placed.width <= 100) or (placed.position.x >= 150) or \
           (placed.position.y + placed.height <= 100) or (placed.position.y >= 150)


def test_placement_leader_line_fallback():
    # Setup a diagram where the target element takes up most of the space
    el = DiagramElement(type=ElementType.FILLED_REGION, geometry={"x": 0, "y": 0, "w": 800, "h": 600})
    diagram = Diagram(
        project_id="test",
        page_id="p1",
        canvas=Canvas(width=800, height=600),
        elements=[el]
    )
    
    label = Label(
        diagram_id=diagram.id,
        text="Huge Background",
        target_element_id=el.id
    )
    
    # We lower the leader line threshold to force it
    config = PlacementConfig(leader_line_threshold=0.0)
    
    result = place_labels([label], diagram, config=config)
    placed = result[0].placement
    
    assert placed is not None
    assert placed.leader_line is not None
    assert isinstance(placed.leader_line.start, Point)
    assert isinstance(placed.leader_line.end, Point)


def test_placement_missing_target():
    diagram = Diagram(
        project_id="test",
        page_id="p1",
        elements=[]
    )
    label = Label(
        diagram_id=diagram.id,
        text="Orphan",
        target_element_id="missing"
    )
    
    result = place_labels([label], diagram)
    # Shouldn't crash, should just flag as no_target
    assert result[0].metadata.get("placement_status") == "no_target"
    assert result[0].placement is None
