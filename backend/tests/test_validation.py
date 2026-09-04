"""
Tests for the tactile design validation engine.
"""

import pytest
from app.models.diagram import Diagram, DiagramElement, ElementType, Canvas, Point
from app.models.label import Label, LabelPlacement
from app.pipeline.validation.engine import run_validation
from app.models.validation import ValidationLevel

def test_feature_size_validator():
    # A tiny feature
    el = DiagramElement(type=ElementType.FILLED_REGION, geometry={"x": 10, "y": 10, "w": 2, "h": 2})
    diagram = Diagram(project_id="test", page_id="p1", elements=[el])
    
    result = run_validation(diagram, [])
    
    assert len(result.warnings) == 1
    assert "below minimum tactile threshold" in result.warnings[0].message
    assert result.warnings[0].element_ids == [el.id]

def test_bounds_validator():
    # Element out of bounds
    el = DiagramElement(type=ElementType.LINE, geometry={"x": 900, "y": 10, "w": 10, "h": 10})
    diagram = Diagram(project_id="test", page_id="p1", canvas=Canvas(width=800, height=600), elements=[el])
    
    result = run_validation(diagram, [])
    
    assert len(result.errors) == 1
    assert "extends beyond the printable canvas bounds" in result.errors[0].message

def test_label_collision_validator():
    diagram = Diagram(project_id="test", page_id="p1", elements=[])
    
    # Overlapping labels
    l1 = Label(diagram_id=diagram.id, text="A", placement=LabelPlacement(position=Point(x=10, y=10), width=50, height=20))
    l2 = Label(diagram_id=diagram.id, text="B", placement=LabelPlacement(position=Point(x=30, y=10), width=50, height=20))
    
    result = run_validation(diagram, [l1, l2])
    
    assert len(result.errors) == 1
    assert "overlap with each other" in result.errors[0].message
    
def test_label_spacing_validator():
    diagram = Diagram(project_id="test", page_id="p1", elements=[])
    
    # Close but not overlapping labels (gap is 5px)
    l1 = Label(diagram_id=diagram.id, text="A", placement=LabelPlacement(position=Point(x=10, y=10), width=50, height=20))
    l2 = Label(diagram_id=diagram.id, text="B", placement=LabelPlacement(position=Point(x=65, y=10), width=50, height=20))
    
    result = run_validation(diagram, [l1, l2])
    
    # LabelSpacingValidator uses 8px min_gap by default, gap is 5px -> should warn
    assert len(result.warnings) == 1
    assert "too close together" in result.warnings[0].message

def test_is_valid_property():
    diagram = Diagram(project_id="test", page_id="p1", elements=[])
    result = run_validation(diagram, [])
    assert result.is_valid == True
    
    # Inject an error
    l1 = Label(diagram_id=diagram.id, text="A", placement=LabelPlacement(position=Point(x=10, y=10), width=50, height=20))
    l2 = Label(diagram_id=diagram.id, text="B", placement=LabelPlacement(position=Point(x=30, y=10), width=50, height=20))
    
    result = run_validation(diagram, [l1, l2])
    assert result.is_valid == False
