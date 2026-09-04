import pytest
from app.models.diagram import Diagram, DiagramElement, ElementType, Canvas, Point
from app.models.label import Label, LabelPlacement, LeaderLine
from app.models.export import ExportConfig, PhysicalUnit
from app.pipeline.export.pdf import generate_pdf

def test_generate_pdf():
    el = DiagramElement(id="el1", type=ElementType.FILLED_REGION, geometry={"points": [{"x": 10, "y": 10}, {"x": 20, "y": 10}, {"x": 20, "y": 20}]})
    diagram = Diagram(project_id="test", page_id="p1", canvas=Canvas(width=1000, height=1000), elements=[el])
    
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
    
    pdf_bytes = generate_pdf(diagram, [lbl], config)
    
    # Check that it returns bytes and starts with the PDF magic number
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    # Check for EOF marker
    assert b"%%EOF" in pdf_bytes
