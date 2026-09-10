from enum import Enum
import cv2
from datetime import datetime, timezone
from pathlib import Path

from typing import Any

from .storage import StorageService
from ..models.diagram import Diagram, DiagramStatus
from ..models.extraction import ExtractionConfig, AnalysisConfig
from ..models.simplification import SimplificationConfig
from ..pipeline.extraction import extract_diagram
from ..pipeline.analysis import analyze_structure
from ..pipeline.simplification import simplify_diagram
from ..pipeline.semantics.orchestrator import CompositeSemanticDetector
from ..pipeline.semantics.heuristic import HeuristicSemanticDetector
from ..pipeline.semantics.ocr import OCRSemanticDetector
from ..pipeline.labels import extract_labels
from ..pipeline.braille_translation import translate_labels
from ..pipeline.placement import place_labels
from ..core.exceptions import ProjectNotFoundError

class PipelineStage(str, Enum):
    EXTRACT = "extract"
    ANALYZE = "analyze"
    SIMPLIFY = "simplify"
    SEMANTICS = "semantics"
    OCR = "ocr"
    TRANSLATE = "translate"
    PLACE = "place"

# Order defines execution flow
STAGE_ORDER = [
    PipelineStage.EXTRACT,
    PipelineStage.ANALYZE,
    PipelineStage.SIMPLIFY,
    PipelineStage.SEMANTICS,
    PipelineStage.OCR,
    PipelineStage.TRANSLATE,
    PipelineStage.PLACE
]

class WorkflowConfig:
    def __init__(
        self,
        extraction: ExtractionConfig = None,
        analysis: AnalysisConfig = None,
        simplification: SimplificationConfig = None
    ):
        self.extraction = extraction or ExtractionConfig()
        self.analysis = analysis or AnalysisConfig()
        self.simplification = simplification or SimplificationConfig()

class WorkflowService:
    def __init__(self, storage: StorageService):
        self.storage = storage

    def run_pipeline(
        self,
        project_id: str,
        page_id: str,
        diagram_id: str,
        start_stage: PipelineStage,
        end_stage: PipelineStage,
        config: WorkflowConfig,
        debug: bool = False
    ) -> Diagram:
        diagram = self.storage.load_diagram(project_id, diagram_id)
        
        collector = None
        if debug:
            from ..pipeline.debug import DebugArtifactCollector
            collector = DebugArtifactCollector(project_id, diagram_id, base_dir=str(self.storage.workspace_dir))
        
        start_idx = STAGE_ORDER.index(start_stage)
        end_idx = STAGE_ORDER.index(end_stage)
        
        if start_idx > end_idx:
            raise ValueError("start_stage must be before or equal to end_stage")
            
        stages_to_run = STAGE_ORDER[start_idx:end_idx + 1]
        
        for stage in stages_to_run:
            if stage == PipelineStage.EXTRACT:
                self._run_extract(diagram, project_id, page_id, config.extraction, collector)
            elif stage == PipelineStage.ANALYZE:
                self._run_analyze(diagram, project_id, page_id, config.analysis, collector)
            elif stage == PipelineStage.SIMPLIFY:
                self._run_simplify(diagram, config.simplification, collector)
            elif stage == PipelineStage.SEMANTICS:
                self._run_semantics(diagram, collector)
            elif stage == PipelineStage.OCR:
                self._run_ocr(diagram, project_id, collector)
            elif stage == PipelineStage.TRANSLATE:
                self._run_translate(diagram, project_id, collector)
            elif stage == PipelineStage.PLACE:
                self._run_place(diagram, project_id, collector)
                
        if collector:
            collector.generate_manifest()
                
        diagram.updated_at = datetime.now(timezone.utc)
        self.storage.save_diagram(diagram)
        return diagram

    def _run_extract(self, diagram: Diagram, project_id: str, page_id: str, config: ExtractionConfig, collector=None):
        page = self.storage.load_page(project_id, page_id)
        if not page.preprocessed_path or not Path(page.preprocessed_path).exists():
            raise ValueError("Page preprocessed image not found")
        image_path = Path(page.preprocessed_path)
        image = cv2.imread(str(image_path))
        if image is None: raise ValueError("Failed to load image")
        
        if collector:
            collector.save_image("00_original", image)
            
        cropped, metadata = extract_diagram(image, diagram.source_bbox, config)
        extracted_path = self.storage.get_diagram_extracted_path(project_id, page_id, diagram.id)
        cv2.imwrite(str(extracted_path), cropped)
        
        if collector:
            collector.save_image("01_extracted", cropped)
        
        diagram.status = DiagramStatus.EXTRACTED
        diagram.page_offset_x = metadata["offset_x"]
        diagram.page_offset_y = metadata["offset_y"]
        diagram.scale_factor = metadata["scale_factor"]
        diagram.processing_log.append("Workflow: Extracted diagram")

    def _run_analyze(self, diagram: Diagram, project_id: str, page_id: str, config: AnalysisConfig, collector=None):
        extracted_path = self.storage.get_diagram_extracted_path(project_id, page_id, diagram.id)
        image = cv2.imread(str(extracted_path))
        if image is None: raise ValueError("Failed to load extracted image")
        
        diagram.elements = analyze_structure(image, config)
        diagram.status = DiagramStatus.VECTORIZED
        diagram.processing_log.append("Workflow: Analyzed structure")
        
        if collector:
            collector.save_json("02_vectorized_elements", [e.model_dump() for e in diagram.elements])

    def _run_simplify(self, diagram: Diagram, config: SimplificationConfig, collector=None):
        diagram.elements = simplify_diagram(diagram.elements, config)
        diagram.status = DiagramStatus.SIMPLIFIED
        diagram.processing_log.append("Workflow: Simplified elements")
        
        if collector:
            collector.save_json("03_simplified_elements", [e.model_dump() for e in diagram.elements])
            
            from ..pipeline.export.svg import generate_svg
            from ..models.export import ExportConfig
            # Generate intermediate SVG
            svg = generate_svg(diagram, [], ExportConfig())
            collector.save_svg("03_simplified", svg)

    def _run_semantics(self, diagram: Diagram, collector=None):
        orchestrator = CompositeSemanticDetector([HeuristicSemanticDetector(), OCRSemanticDetector()])
        components = orchestrator.detect(diagram.elements)
        for comp in components:
            comp.diagram_id = diagram.id
        diagram.components = components
        diagram.status = DiagramStatus.LABELED
        diagram.processing_log.append("Workflow: Semantic detection")
        
        if collector:
            collector.save_json("04_semantics", [c.model_dump() for c in components])

    def _run_ocr(self, diagram: Diagram, project_id: str, collector=None):
        from ..pipeline.ocr.mock import MockOCRProvider
        extracted_path = self.storage.get_diagram_extracted_path(project_id, diagram.page_id, diagram.id)
        image = cv2.imread(str(extracted_path))
        if image is None:
            raise ValueError("Failed to load extracted image for OCR")
            
        from ..pipeline.ocr.tesseract import TesseractOCRProvider
        from ..pipeline.ocr.mock import MockOCRProvider
        
        provider = TesseractOCRProvider()
        if not getattr(provider, 'is_available', False):
            provider = MockOCRProvider()
            
        labels = extract_labels(diagram, image, provider)
        
        # Merge with existing labels
        existing = {lbl.id: lbl for lbl in [self.storage.load_label(project_id, lid) for lid in diagram.labels]}
        new_ids = []
        for lbl in labels:
            if lbl.id in existing and existing[lbl.id].source == "manual":
                # keep manual overrides
                new_ids.append(lbl.id)
            else:
                self.storage.save_label(project_id, lbl)
                new_ids.append(lbl.id)
                
        diagram.labels = new_ids
        diagram.processing_log.append("Workflow: OCR extraction")
        
        if collector:
            saved_labels = [self.storage.load_label(project_id, lid) for lid in diagram.labels]
            collector.save_json("05_ocr_labels", [l.model_dump() for l in saved_labels])

    def _run_translate(self, diagram: Diagram, project_id: str, collector=None):
        labels = [self.storage.load_label(project_id, lid) for lid in diagram.labels]
        translate_labels(labels)
        for lbl in labels:
            self.storage.save_label(project_id, lbl)
        diagram.processing_log.append("Workflow: Braille translation")
        
        if collector:
            collector.save_json("06_translated_labels", [l.model_dump() for l in labels])

    def _run_place(self, diagram: Diagram, project_id: str, collector=None):
        labels = [self.storage.load_label(project_id, lid) for lid in diagram.labels]
        labels = place_labels(labels, diagram)
        for lbl in labels:
            self.storage.save_label(project_id, lbl)
        diagram.processing_log.append("Workflow: Label placement")
        
        if collector:
            collector.save_json("07_placed_labels", [l.model_dump() for l in labels])
            
            from ..pipeline.export.svg import generate_svg
            from ..models.export import ExportConfig
            # Final output map
            svg = generate_svg(diagram, labels, ExportConfig())
            collector.save_svg("08_final", svg)
