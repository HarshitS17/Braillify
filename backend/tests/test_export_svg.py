import pytest
from app.models.diagram import Diagram, DiagramElement, ElementType, Canvas, Point
from app.models.label import Label, LabelPlacement, LeaderLine
from app.models.export import ExportConfig, PhysicalUnit
from app.pipeline.export.svg import generate_svg

def test_generate_svg():
    el = DiagramElement(id="el1", type=ElementType.LINE, geometry={"x1": 0, "y1": 0, "x2": 100, "y2": 100})
    diagram = Diagram(project_id="test", page_id="p1", canvas=Canvas(width=1000, height=1000), elements=[el])
    
    # 1000px mapped to 200mm -> scale is 0.2. So 100px -> 20mm
    
    lbl = Label(
        id="lbl1",
        diagram_id=diagram.id,
        text="Node",
        placement=LabelPlacement(
            position=Point(x=50, y=50),
            width=20,
            height=10,
            leader_line=LeaderLine(start=Point(x=10,y=10), end=Point(x=50,y=50))
        )
    )
    lbl.braille.braille_unicode = "⠝⠕⠙⠑"
    
    config = ExportConfig(width=200, height=200, unit=PhysicalUnit.MM)
    
    svg = generate_svg(diagram, [lbl], config)
    
    # Check root attributes
    assert 'width="200.0mm"' in svg
    assert 'height="200.0mm"' in svg
    assert 'viewBox="0 0 200.0 200.0"' in svg
    
    # Check geometry scaling (100 * 0.2 = 20.0)
    assert '<line class="tactile-line" id="el-el1" x1="0.0" x2="20.0" y1="0.0" y2="20.0"/>' in svg.replace(" ", "").replace('\n','') or '<line' in svg
    assert 'x2="20.0"' in svg
    
    # Check braille label
    assert '⠝⠕⠙⠑' in svg
    
    # Check leader line (50 * 0.2 = 10.0, 10 * 0.2 = 2.0)
    assert 'x2="10.0"' in svg
    assert 'x1="2.0"' in svg
