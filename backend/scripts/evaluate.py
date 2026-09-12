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


def evaluate_simplification() -> dict:
    """Run analysis + simplification on a representative fixture and
    report the element reduction ratio."""
    img_path = QA_DIR / "01_simple_biology.png"
    if not img_path.exists():
        return {"error": "fixture missing"}

    img = cv2.imread(str(img_path))
    if img is None:
        return {"error": "unreadable"}

    diagram = Diagram(project_id="eval", page_id="p1")

    t0 = time.perf_counter()
    elements = analyze_structure(img, AnalysisConfig())
    dt_analysis = time.perf_counter() - t0

    original_count = len(elements)

    t0 = time.perf_counter()
    simplified_elements = simplify_diagram(elements, SimplificationConfig())
    dt_simplify = time.perf_counter() - t0

    simplified_count = len(simplified_elements)
    reduction = 1.0 - (simplified_count / original_count) if original_count > 0 else 0.0

    return {
        "original_elements": original_count,
        "simplified_elements": simplified_count,
        "reduction_pct": round(reduction * 100, 1),
        "analysis_ms": round(dt_analysis * 1000, 1),
        "simplification_ms": round(dt_simplify * 1000, 1),
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
        f"- **Original Elements**: {simplification.get('original_elements', '?')}",
        f"- **Simplified Elements**: {simplification.get('simplified_elements', '?')}",
        f"- **Feature Reduction**: {simplification.get('reduction_pct', '?')}%",
        f"- **Analysis Time**: {simplification.get('analysis_ms', '?')}ms",
        f"- **Simplification Time**: {simplification.get('simplification_ms', '?')}ms",
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
    simplification = evaluate_simplification()
    print(f"  {simplification.get('original_elements', '?')} → {simplification.get('simplified_elements', '?')} elements ({simplification.get('reduction_pct', '?')}% reduction)")

    report = generate_report(detection, simplification)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"\n✅ Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
