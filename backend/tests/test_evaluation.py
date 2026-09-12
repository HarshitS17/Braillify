"""
Unit tests for the evaluation metrics functions.
"""
import pytest
from app.models.diagram import BoundingBox, Diagram
from app.models.label import Label, LabelSource, LabelPlacement
from app.models.diagram import Point
from app.pipeline.evaluation import (
    calculate_iou,
    calculate_simplification_ratio,
    calculate_collision_rate,
    calculate_manual_correction_rate
)

# ── IoU Tests ──

def test_iou_perfect_overlap():
    box = BoundingBox(x=0, y=0, width=100, height=100)
    assert calculate_iou(box, box) == 1.0

def test_iou_no_overlap():
    box1 = BoundingBox(x=0, y=0, width=50, height=50)
    box2 = BoundingBox(x=200, y=200, width=50, height=50)
    assert calculate_iou(box1, box2) == 0.0

def test_iou_partial_overlap():
    box1 = BoundingBox(x=0, y=0, width=100, height=100)
    box2 = BoundingBox(x=50, y=50, width=100, height=100)
    iou = calculate_iou(box1, box2)
    # Intersection is 50x50=2500, union is 10000+10000-2500=17500
    assert abs(iou - 2500/17500) < 0.001

def test_iou_contained():
    outer = BoundingBox(x=0, y=0, width=200, height=200)
    inner = BoundingBox(x=50, y=50, width=50, height=50)
    iou = calculate_iou(outer, inner)
    # Intersection = 2500, union = 40000+2500-2500=40000
    assert abs(iou - 2500/40000) < 0.001

# ── Simplification Ratio Tests ──

def test_simplification_no_reduction():
    assert calculate_simplification_ratio(100, 100) == 1.0

def test_simplification_full_reduction():
    assert calculate_simplification_ratio(100, 0) == 0.0

def test_simplification_half():
    assert calculate_simplification_ratio(200, 100) == 0.5

def test_simplification_empty_original():
    assert calculate_simplification_ratio(0, 0) == 1.0

# ── Vertex Reduction Ratio Tests ──

from app.models.diagram import DiagramElement, ElementType
from app.pipeline.simplification import count_total_vertices
from app.pipeline.evaluation import calculate_vertex_reduction_ratio

def test_vertex_reduction():
    assert calculate_vertex_reduction_ratio(10, 5) == 0.5
    assert calculate_vertex_reduction_ratio(10, 10) == 1.0
    assert calculate_vertex_reduction_ratio(0, 0) == 1.0

def test_count_total_vertices():
    el1 = DiagramElement(type=ElementType.POLYGON, geometry={"points": [{"x":0,"y":0}] * 8})
    el2 = DiagramElement(type=ElementType.LINE, geometry={"x1":0, "y1":0, "x2":1, "y2":1})
    el3 = DiagramElement(type=ElementType.ARROW, geometry={"path": {"points": [{"x":0,"y":0}] * 3}})
    assert count_total_vertices([el1, el2, el3]) == 8 + 1 + 3

    # Check DP reduction
    el1_simp = DiagramElement(type=ElementType.POLYGON, geometry={"points": [{"x":0,"y":0}] * 4})
    assert count_total_vertices([el1_simp, el2, el3]) == 4 + 1 + 3

# ── Collision Rate Tests ──

def test_collision_rate_no_collisions():
    diagram = Diagram(project_id="test", page_id="p1")
    labels = [
        Label(diagram_id="d1", text="A", placement=LabelPlacement(position=Point(x=10, y=10), width=30, height=20)),
        Label(diagram_id="d1", text="B", placement=LabelPlacement(position=Point(x=200, y=200), width=30, height=20)),
    ]
    assert calculate_collision_rate(diagram, labels) == 0.0

def test_collision_rate_with_collision():
    diagram = Diagram(project_id="test", page_id="p1")
    labels = [
        Label(diagram_id="d1", text="A", placement=LabelPlacement(position=Point(x=10, y=10), width=50, height=20)),
        Label(diagram_id="d1", text="B", placement=LabelPlacement(position=Point(x=30, y=10), width=50, height=20)),
    ]
    rate = calculate_collision_rate(diagram, labels)
    assert rate > 0

def test_collision_rate_empty():
    diagram = Diagram(project_id="test", page_id="p1")
    assert calculate_collision_rate(diagram, []) == 0.0

# ── Manual Correction Rate Tests ──

def test_manual_correction_rate_none():
    labels = [
        Label(diagram_id="d1", text="A", source=LabelSource.OCR),
        Label(diagram_id="d1", text="B", source=LabelSource.OCR),
    ]
    assert calculate_manual_correction_rate(labels) == 0.0

def test_manual_correction_rate_all():
    labels = [
        Label(diagram_id="d1", text="A", source=LabelSource.MANUAL),
        Label(diagram_id="d1", text="B", source=LabelSource.MANUAL),
    ]
    assert calculate_manual_correction_rate(labels) == 1.0

def test_manual_correction_rate_mixed():
    labels = [
        Label(diagram_id="d1", text="A", source=LabelSource.OCR),
        Label(diagram_id="d1", text="B", source=LabelSource.MANUAL),
    ]
    assert calculate_manual_correction_rate(labels) == 0.5

def test_manual_correction_rate_empty():
    assert calculate_manual_correction_rate([]) == 0.0
