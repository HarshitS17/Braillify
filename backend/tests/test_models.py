import pytest
from app.models.project import Project, ProjectCreate, ProjectStatus
from app.models.page import Page, PageMetadata, PageStatus
from app.models.diagram import (
    Diagram, DiagramElement, DiagramCandidate, Canvas,
    BoundingBox, Point, ElementType, SemanticRole, CoordinateUnit,
    DetectionFeatures, DiagramStatus,
)
from app.models.component import Component, ComponentType
from app.models.label import Label, BrailleRepresentation, LabelPlacement, LabelSource


class TestProjectModels:
    def test_project_create_valid(self):
        pc = ProjectCreate(name="Test Project", description="A test")
        assert pc.name == "Test Project"

    def test_project_create_empty_name_fails(self):
        with pytest.raises(Exception):
            ProjectCreate(name="", description="")

    def test_project_defaults(self):
        p = Project(name="Test")
        assert p.status == ProjectStatus.CREATED
        assert p.page_count == 0
        assert p.id  # auto-generated


class TestPageModels:
    def test_page_creation(self):
        meta = PageMetadata(
            original_filename="test.png",
            file_format="png",
            file_size_bytes=1024,
            width_px=800,
            height_px=600,
        )
        page = Page(project_id="proj-1", metadata=meta)
        assert page.status == PageStatus.UPLOADED
        assert page.metadata.width_px == 800


class TestDiagramModels:
    def test_canvas_with_units(self):
        c = Canvas(width=1200, height=800, unit=CoordinateUnit.PX)
        assert c.unit == CoordinateUnit.PX

    def test_bounding_box(self):
        bb = BoundingBox(x=10, y=20, width=100, height=50)
        assert bb.unit == CoordinateUnit.PX

    def test_diagram_element(self):
        elem = DiagramElement(
            type=ElementType.POLYGON,
            geometry={"points": [[0, 0], [100, 0], [100, 100], [0, 100]]},
        )
        assert elem.type == ElementType.POLYGON
        assert elem.semantic_role == SemanticRole.UNKNOWN
        assert elem.confidence == 1.0

    def test_diagram_candidate(self):
        candidate = DiagramCandidate(
            bbox=BoundingBox(x=50, y=50, width=200, height=150),
            confidence=0.87,
            features=DetectionFeatures(edge_density=0.4, text_density=0.1),
            classification_reason="High edge density, low text density",
        )
        assert candidate.confidence == 0.87
        assert not candidate.accepted

    def test_diagram_defaults(self):
        d = Diagram(page_id="page-1", project_id="proj-1")
        assert d.status == DiagramStatus.CANDIDATE
        assert d.elements == []
        assert d.scale_factor == 1.0


class TestComponentModels:
    def test_component_defaults(self):
        c = Component(diagram_id="diag-1")
        assert c.type == ComponentType.UNKNOWN
        assert c.confidence == 0.0


class TestLabelModels:
    def test_label_creation(self):
        label = Label(
            diagram_id="diag-1",
            text="Nucleus",
            braille=BrailleRepresentation(
                braille_unicode="⠠⠝⠥⠉⠇⠑⠥⠎",
                grade=1,
                language="en",
            ),
        )
        assert label.text == "Nucleus"
        assert label.source == LabelSource.GENERATED

    def test_label_placement(self):
        placement = LabelPlacement(
            position=Point(x=100, y=200),
            width=80,
            height=20,
        )
        assert placement.unit == CoordinateUnit.PX
        assert not placement.is_manual
