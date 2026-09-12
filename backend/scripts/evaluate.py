"""Real evaluation harness — runs the actual pipeline against QA fixtures
and measures detection, simplification, and label metrics against ground
truth instead of using hardcoded mock data.

Usage:
    cd backend && source .venv/bin/activate && python scripts/evaluate.py
"""

import os
import sys
import json
import time
import cv2
import numpy as np
from pathlib import Path

# Add backend dir to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.detection import DiagramDetector
from app.pipeline.analysis import analyze_structure
from app.pipeline.simplification import simplify_diagram
from app.pipeline.evaluation import calculate_iou
from app.models.diagram import BoundingBox, Diagram
from app.models.extraction import AnalysisConfig
from app.models.simplification import SimplificationConfig

QA_DIR = Path(__file__).parent.parent / "qa_fixtures"
GT_PATH = QA_DIR / "ground_truth.json"
REPORT_PATH = Path(__file__).parent.parent / "evaluation_report.md"


def load_ground_truth() -> dict:
    with open(GT_PATH) as f:
        return json.load(f)["fixtures"]


def evaluate_detection(ground_truth: dict) -> dict:
    """Run detector on each fixture image and compute P/R/F1/IoU."""
    detector = DiagramDetector()
    tp = fp = fn = 0
    iou_scores: list[float] = []
    per_fixture: list[dict] = []

    for filename, gt in ground_truth.items():
        img_path = QA_DIR / filename
        if not img_path.exists():
            print(f"  ⚠ {filename} missing — skipping")
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  ⚠ {filename} unreadable — skipping")
            continue

        t0 = time.perf_counter()
        candidates = detector.detect(img)
        dt = time.perf_counter() - t0

        expected = gt["expected_diagrams"]
        detected = len(candidates)
        gt_bbox = gt.get("ground_truth_bbox")

        result = {
            "file": filename,
            "expected": expected,
            "detected": detected,
            "time_ms": round(dt * 1000, 1),
        }

        if expected == 0:
            # True negative: no diagrams expected
            if detected == 0:
                result["status"] = "TN"
            else:
                fp += detected
                result["status"] = f"FP({detected})"
        else:
            # Should detect at least one diagram
            if detected == 0:
                fn += 1
                result["status"] = "FN"
                result["iou"] = 0.0
            else:
                tp += 1
                if gt_bbox:
                    gt_bb = BoundingBox(**gt_bbox)
                    best_iou = max(
                        calculate_iou(gt_bb, BoundingBox(x=c.bbox.x, y=c.bbox.y, width=c.bbox.width, height=c.bbox.height))
                        for c in candidates
                    )
                    iou_scores.append(best_iou)
                    result["iou"] = round(best_iou, 3)
                    result["status"] = "TP"
                    # Extra detections beyond the expected count
                    if detected > expected:
                        fp += detected - expected
                else:
                    result["status"] = "TP (no bbox GT)"

        per_fixture.append(result)
        status = result["status"]
        iou_str = f" IoU={result.get('iou', 'N/A')}" if "iou" in result else ""
        print(f"  {filename}: {status} ({detected} detected){iou_str} [{dt*1000:.0f}ms]")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    mean_iou = float(np.mean(iou_scores)) if iou_scores else 0.0

    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "mean_iou": round(mean_iou, 3),
        "per_fixture": per_fixture,
    }


from app.pipeline.preprocessing import preprocess_image
from app.pipeline.extraction import extract_diagram
from app.models.preprocessing import PreprocessingConfig
from app.models.extraction import ExtractionConfig
from app.pipeline.evaluation import calculate_simplification_ratio, calculate_vertex_reduction_ratio
from app.pipeline.simplification import count_total_vertices

def evaluate_simplification(ground_truth: dict) -> dict:
    """Run preprocess -> extract -> analyze -> simplify on all fixtures."""
    per_fixture = []
    total_original_elements = 0
    total_simplified_elements = 0
    total_original_vertices = 0
    total_simplified_vertices = 0
    total_analysis_ms = 0.0
    total_simplify_ms = 0.0

    for filename, gt in ground_truth.items():
        img_path = QA_DIR / filename
        if not img_path.exists():
            continue

        gt_bbox = gt.get("ground_truth_bbox")
        if not gt_bbox:
            # Skip fixtures without a diagram to simplify
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            continue

        # 1. Preprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            preprocessed = preprocess_image(
                image_path=img_path,
                output_dir=tmp_path,
                config=PreprocessingConfig()
            )
            # 2. Extract
            prep_img = cv2.imread(str(preprocessed.preprocessed_path))
            bbox = BoundingBox(**gt_bbox)
            cropped, _ = extract_diagram(prep_img, bbox, ExtractionConfig())

        # 3. Analyze
        t0 = time.perf_counter()
        elements = analyze_structure(cropped, AnalysisConfig())
        dt_analysis = (time.perf_counter() - t0) * 1000
        
        orig_count = len(elements)
        orig_vertices = count_total_vertices(elements)

        # 4. Simplify
        t0 = time.perf_counter()
        simplified_elements = simplify_diagram(elements, SimplificationConfig())
        dt_simplify = (time.perf_counter() - t0) * 1000

        simp_count = len(simplified_elements)
        simp_vertices = count_total_vertices(simplified_elements)
        
        elem_ratio = calculate_simplification_ratio(orig_count, simp_count)
        vert_ratio = calculate_vertex_reduction_ratio(orig_vertices, simp_vertices)
        
        elem_reduction_pct = (1.0 - elem_ratio) * 100
        vert_reduction_pct = (1.0 - vert_ratio) * 100

        per_fixture.append({
            "file": filename,
            "orig_elem": orig_count,
            "simp_elem": simp_count,
            "elem_red_pct": round(elem_reduction_pct, 1),
            "orig_vert": orig_vertices,
            "simp_vert": simp_vertices,
            "vert_red_pct": round(vert_reduction_pct, 1),
            "analysis_ms": round(dt_analysis, 1),
            "simplify_ms": round(dt_simplify, 1)
        })

        total_original_elements += orig_count
        total_simplified_elements += simp_count
        total_original_vertices += orig_vertices
        total_simplified_vertices += simp_vertices
        total_analysis_ms += dt_analysis
        total_simplify_ms += dt_simplify

        print(f"  {filename}: {orig_count} -> {simp_count} elems ({elem_reduction_pct:.1f}%), "
              f"{orig_vertices} -> {simp_vertices} verts ({vert_reduction_pct:.1f}%)")

    # Averages across all fixtures
    overall_elem_ratio = calculate_simplification_ratio(total_original_elements, total_simplified_elements)
    overall_vert_ratio = calculate_vertex_reduction_ratio(total_original_vertices, total_simplified_vertices)
    
    return {
        "original_elements": total_original_elements,
        "simplified_elements": total_simplified_elements,
        "elem_reduction_pct": round((1.0 - overall_elem_ratio) * 100, 1),
        "original_vertices": total_original_vertices,
        "simplified_vertices": total_simplified_vertices,
        "vert_reduction_pct": round((1.0 - overall_vert_ratio) * 100, 1),
        "analysis_ms": round(total_analysis_ms, 1),
        "simplification_ms": round(total_simplify_ms, 1),
        "per_fixture": per_fixture
    }


def generate_report(detection: dict, simplification: dict) -> str:
    """Generate the markdown evaluation report from real measurements."""
    lines = [
        "# TactileEd Academic Evaluation Report",
        "",
        "> **Note**: These metrics are measured by running the actual pipeline",
        "> against QA fixture images, not hardcoded values.",
        "",
        "## 1. Diagram Detection",
        f"- **IoU** (mean best-match): {detection['mean_iou']:.3f}",
        f"- **Precision**: {detection['precision']:.3f}",
        f"- **Recall**: {detection['recall']:.3f}",
        f"- **F1 Score**: {detection['f1']:.3f}",
        f"- **True Positives**: {detection['tp']}",
        f"- **False Positives**: {detection['fp']}",
        f"- **False Negatives**: {detection['fn']}",
        "",
        "### Per-Fixture Results",
        "| Fixture | Expected | Detected | Status | IoU | Time |",
        "|---------|----------|----------|--------|-----|------|",
    ]
    for r in detection["per_fixture"]:
        iou = f"{r['iou']:.3f}" if "iou" in r else "—"
        lines.append(
            f"| {r['file']} | {r['expected']} | {r['detected']} | {r['status']} | {iou} | {r['time_ms']}ms |"
        )

    lines += [
        "",
        "## 2. Tactile Simplification",
        f"- **Whole-element reduction (drops + deduplication)**: {simplification.get('elem_reduction_pct', '?')}%",
        f"- **Vertex/feature reduction (Douglas-Peucker)**: {simplification.get('vert_reduction_pct', '?')}%",
        f"- **Total Analysis Time**: {simplification.get('analysis_ms', '?')}ms",
        f"- **Total Simplification Time**: {simplification.get('simplification_ms', '?')}ms",
        "",
        "### Per-Fixture Results",
        "| Fixture | Orig Elems | Simp Elems | Elem Red % | Orig Verts | Simp Verts | Vert Red % | Analysis (ms) | Simplify (ms) |",
        "|---------|------------|------------|------------|------------|------------|------------|---------------|---------------|",
    ]
    
    for r in simplification.get("per_fixture", []):
        lines.append(
            f"| {r['file']} | {r['orig_elem']} | {r['simp_elem']} | {r['elem_red_pct']}% | "
            f"{r['orig_vert']} | {r['simp_vert']} | {r['vert_red_pct']}% | {r['analysis_ms']} | {r['simplify_ms']} |"
        )

    lines += [
        "",
        "## 3. Label Placement",
        "- **Collision Rate**: *(requires full pipeline run with labels)*",
        "- **Human-in-the-Loop Correction Rate**: *(requires real user data)*",
        "",
    ]
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("TactileEd Real Pipeline Evaluation")
    print("=" * 60)

    gt = load_ground_truth()

    print(f"\n--- 1. Detection ({len(gt)} fixtures) ---")
    detection = evaluate_detection(gt)
    print(f"\n  Summary: P={detection['precision']} R={detection['recall']} F1={detection['f1']} IoU={detection['mean_iou']}")

    print("\n--- 2. Simplification ---")
    simplification = evaluate_simplification(gt)
    print(f"  Summary: {simplification.get('elem_reduction_pct')}% element reduction, {simplification.get('vert_reduction_pct')}% vertex reduction")

    report = generate_report(detection, simplification)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"\n✅ Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
