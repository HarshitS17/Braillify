"""End-to-end pipeline profiler — times each stage on a representative
diagram and reports per-stage timing with a 500ms flag threshold.

Usage:
    cd backend && source .venv/bin/activate && python scripts/profile_pipeline.py
"""

import os
import sys
import time
import cv2
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.detection import DiagramDetector
from app.pipeline.analysis import analyze_structure
from app.pipeline.simplification import simplify_diagram
from app.pipeline.preprocessing import preprocess_image
from app.models.preprocessing import PreprocessingConfig
from app.models.extraction import AnalysisConfig
from app.models.simplification import SimplificationConfig

QA_DIR = Path(__file__).parent.parent / "qa_fixtures"
TMP_DIR = Path(__file__).parent.parent / "workspace" / "_profile_tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD_MS = 500


def profile():
    img_path = QA_DIR / "01_simple_biology.png"
    if not img_path.exists():
        print("Fixture missing — run qa_fixtures.py first.")
        return

    print("=" * 60)
    print("TactileEd Pipeline Profiler")
    print("=" * 60)
    print(f"Input: {img_path.name}")
    print()

    timings: list[tuple[str, float]] = []

    # 1. Preprocessing
    t0 = time.perf_counter()
    result = preprocess_image(img_path, TMP_DIR, PreprocessingConfig(), page_id="profile", save_debug=False)
    dt = time.perf_counter() - t0
    timings.append(("Preprocessing", dt))

    # Load preprocessed image for downstream stages
    preprocessed_path = result.preprocessed_path
    img = cv2.imread(preprocessed_path)

    # 2. Detection
    t0 = time.perf_counter()
    detector = DiagramDetector()
    candidates = detector.detect(img)
    dt = time.perf_counter() - t0
    timings.append(("Detection (multi-scale)", dt))

    # 3. Analysis (structure extraction)
    t0 = time.perf_counter()
    elements = analyze_structure(img, AnalysisConfig())
    dt = time.perf_counter() - t0
    timings.append(("Analysis", dt))

    # 4. Simplification
    t0 = time.perf_counter()
    simplified = simplify_diagram(elements, SimplificationConfig())
    dt = time.perf_counter() - t0
    timings.append(("Simplification", dt))

    # 5. OCR (mock — since Tesseract may not be installed)
    t0 = time.perf_counter()
    try:
        from app.pipeline.ocr.tesseract import TesseractOCRProvider
        provider = TesseractOCRProvider()
        if not provider.is_available:
            raise ImportError("Tesseract not available")
        ocr_name = "OCR (Tesseract)"
    except Exception:
        from app.pipeline.ocr.mock import MockOCRProvider
        provider = MockOCRProvider()
        ocr_name = "OCR (Mock/Heuristic)"
    # Run OCR on a sample text region if available
    text_elements = [e for e in elements if e.type.value == "text_region"]
    for te in text_elements[:3]:
        provider.extract_text(img, te.geometry)
    dt = time.perf_counter() - t0
    timings.append((ocr_name, dt))

    # 6. Braille translation
    t0 = time.perf_counter()
    from app.pipeline.braille.grade1_english import Grade1EnglishTranslator
    translator = Grade1EnglishTranslator()
    sample_texts = ["Nucleus", "Cell Wall", "Mitochondria", "Vacuole", "Endoplasmic Reticulum"]
    for text in sample_texts:
        translator.translate(text)
    dt = time.perf_counter() - t0
    timings.append(("Braille Translation", dt))

    # 7. SVG export (dry run — generate SVG string)
    t0 = time.perf_counter()
    try:
        from app.pipeline.export.svg import render_svg
        from app.models.diagram import Diagram
        from app.models.export import ExportConfig
        diagram = Diagram(project_id="profile", page_id="p1")
        diagram.elements = simplified
        svg = render_svg(diagram, [], ExportConfig())
        dt = time.perf_counter() - t0
        timings.append(("SVG Export", dt))
    except Exception as e:
        dt = time.perf_counter() - t0
        timings.append((f"SVG Export (error: {e})", dt))

    # 8. PDF export
    t0 = time.perf_counter()
    try:
        from app.pipeline.export.pdf import render_pdf
        from app.models.diagram import Diagram
        from app.models.export import ExportConfig
        diagram = Diagram(project_id="profile", page_id="p1")
        diagram.elements = simplified
        pdf = render_pdf(diagram, [], ExportConfig())
        dt = time.perf_counter() - t0
        timings.append(("PDF Export", dt))
    except Exception as e:
        dt = time.perf_counter() - t0
        timings.append((f"PDF Export (error: {e})", dt))

    # Report
    print(f"{'Stage':<35} {'Time':>10} {'Status':>10}")
    print("-" * 60)
    total = 0.0
    for name, dt in timings:
        ms = dt * 1000
        total += ms
        flag = "⚠ SLOW" if ms > THRESHOLD_MS else "✓"
        print(f"  {name:<33} {ms:>8.1f}ms {flag:>10}")
    print("-" * 60)
    print(f"  {'TOTAL':<33} {total:>8.1f}ms")
    print()
    print(f"Stages > {THRESHOLD_MS}ms threshold: {sum(1 for _, dt in timings if dt * 1000 > THRESHOLD_MS)}")


if __name__ == "__main__":
    profile()
