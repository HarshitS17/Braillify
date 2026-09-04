"""
Comprehensive end-to-end test script for TactileEd.
Tests every pipeline stage with a realistic synthetic biology diagram.
Uses httpx (already in the venv) to call the actual running server.
"""
import asyncio
import json
import sys
import traceback
import numpy as np
import cv2
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api"
RESULTS: list[dict] = []


def log(stage: str, status: str, detail: str = ""):
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"  {icon} [{stage}] {status} {detail}")
    RESULTS.append({"stage": stage, "status": status, "detail": detail})


def create_biology_diagram() -> np.ndarray:
    """
    Creates a realistic synthetic biology-style cell diagram with:
    - An outer cell membrane (ellipse)
    - A nucleus (inner circle)
    - Organelles (smaller shapes)
    - Text labels: "Nucleus", "Cell Membrane", "Mitochondria"
    """
    w, h = 800, 600
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # white background

    # Cell membrane (outer ellipse)
    cv2.ellipse(img, (400, 300), (350, 250), 0, 0, 360, (0, 0, 0), 3)

    # Nucleus (circle)
    cv2.circle(img, (400, 280), 80, (0, 0, 0), 2)
    cv2.circle(img, (400, 280), 60, (80, 80, 80), 1)  # inner membrane

    # Nucleolus (small filled circle inside nucleus)
    cv2.circle(img, (420, 270), 15, (0, 0, 0), -1)

    # Mitochondria (ellipses scattered around)
    cv2.ellipse(img, (200, 200), (40, 15), 30, 0, 360, (0, 0, 0), 2)
    cv2.ellipse(img, (600, 350), (35, 12), -20, 0, 360, (0, 0, 0), 2)
    cv2.ellipse(img, (250, 420), (38, 14), 45, 0, 360, (0, 0, 0), 2)

    # Ribosomes (tiny dots)
    for pos in [(500, 200), (520, 210), (510, 230), (490, 180), (530, 190)]:
        cv2.circle(img, pos, 3, (0, 0, 0), -1)

    # Endoplasmic reticulum (wavy lines)
    pts = np.array([(300, 400), (330, 380), (360, 410), (390, 390), (420, 420)], np.int32)
    cv2.polylines(img, [pts], False, (0, 0, 0), 2)

    # Leader lines
    cv2.line(img, (400, 200), (400, 150), (100, 100, 100), 1)
    cv2.line(img, (200, 200), (120, 150), (100, 100, 100), 1)
    cv2.line(img, (710, 300), (750, 300), (100, 100, 100), 1)

    # Text labels (clear, readable)
    cv2.putText(img, "Nucleus", (350, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Mitochondria", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Cell Membrane", (550, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Ribosomes", (500, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(img, "ER", (310, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    return img


async def test_full_pipeline():
    print("\n" + "=" * 60)
    print("TactileEd End-to-End Pipeline Test")
    print("=" * 60 + "\n")

    # Create test image
    print("[Setup] Creating realistic biology diagram...")
    img = create_biology_diagram()
    img_path = Path("test_biology_diagram.png")
    cv2.imwrite(str(img_path), img)
    print(f"  Saved to {img_path} ({img.shape[1]}x{img.shape[0]})")

    async with httpx.AsyncClient(timeout=30.0) as client:

        # --- 1. Health Check ---
        print("\n--- Stage 1: Health Check ---")
        try:
            r = await client.get(f"{BASE_URL}/health")
            data = r.json()
            assert r.status_code == 200
            assert data["status"] == "healthy"
            log("Health", "PASS", f"v{data['version']}")
        except Exception as e:
            log("Health", "FAIL", str(e))
            print("  Cannot proceed without backend!")
            return

        # --- 2. Create Project ---
        print("\n--- Stage 2: Create Project ---")
        try:
            r = await client.post(f"{API}/projects", json={"name": "E2E Biology Test", "description": "Cell diagram"})
            assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
            project = r.json()
            project_id = project["id"]
            log("CreateProject", "PASS", f"id={project_id[:8]}...")
        except Exception as e:
            log("CreateProject", "FAIL", str(e))
            return

        # --- 3. Upload Page ---
        print("\n--- Stage 3: Upload Page ---")
        try:
            with open(img_path, "rb") as f:
                r = await client.post(f"{API}/projects/{project_id}/pages", files={"file": f})
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            upload = r.json()
            page_id = upload["page_id"]
            log("Upload", "PASS", f"page_id={page_id[:8]}..., dims={upload.get('width', '?')}x{upload.get('height', '?')}")
        except Exception as e:
            log("Upload", "FAIL", str(e))
            return

        # --- 4. Preprocess ---
        print("\n--- Stage 4: Preprocess ---")
        try:
            r = await client.post(f"{API}/projects/{project_id}/pages/{page_id}/preprocess")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            preprocess = r.json()
            log("Preprocess", "PASS", f"stages={preprocess.get('stages_completed', '?')}")
        except Exception as e:
            log("Preprocess", "FAIL", str(e))
            return

        # --- 5. Detect Diagrams ---
        print("\n--- Stage 5: Detect Diagrams ---")
        try:
            r = await client.post(f"{API}/projects/{project_id}/pages/{page_id}/detect")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            candidates = r.json()
            assert len(candidates) > 0, "No diagram candidates detected!"
            log("Detect", "PASS", f"{len(candidates)} candidate(s) detected")
            for i, c in enumerate(candidates):
                bb = c["bbox"]
                print(f"    Candidate {i}: x={bb['x']:.0f} y={bb['y']:.0f} w={bb['width']:.0f} h={bb['height']:.0f} conf={c['confidence']:.2f}")
        except Exception as e:
            log("Detect", "FAIL", str(e))
            return

        # --- 6. Save Diagram (accept first candidate) ---
        print("\n--- Stage 6: Save Diagram ---")
        candidate = candidates[0]
        candidate["accepted"] = True
        try:
            r = await client.post(f"{API}/projects/{project_id}/pages/{page_id}/diagrams", json=[candidate])
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            saved = r.json()
            diagram_id = saved[0]["id"]
            log("SaveDiagram", "PASS", f"diagram_id={diagram_id[:8]}...")
        except Exception as e:
            log("SaveDiagram", "FAIL", str(e))
            return

        # --- 7. Run Full Workflow (Extract → Place) ---
        print("\n--- Stage 7: Run Full Workflow ---")
        try:
            r = await client.post(
                f"{API}/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/workflow",
                json={"start_stage": "extract", "end_stage": "place", "debug": True}
            )
            if r.status_code != 200:
                print(f"  ❌ Workflow HTTP {r.status_code}")
                try:
                    err = r.json()
                    print(f"  Error: {json.dumps(err, indent=2)}")
                except:
                    print(f"  Body: {r.text[:500]}")
                log("Workflow", "FAIL", f"HTTP {r.status_code}: {r.text[:200]}")
                return
            
            diagram_data = r.json()
            log("Workflow", "PASS", f"status={diagram_data.get('status', '?')}")
            print(f"    Elements: {len(diagram_data.get('elements', []))}")
            print(f"    Components: {len(diagram_data.get('components', []))}")
            print(f"    Labels: {len(diagram_data.get('labels', []))}")
            print(f"    Processing log:")
            for entry in diagram_data.get("processing_log", []):
                print(f"      - {entry}")
        except Exception as e:
            log("Workflow", "FAIL", traceback.format_exc())
            return

        # --- 8. Check intermediate artifacts ---
        print("\n--- Stage 8: Check Debug Artifacts ---")
        try:
            debug_dir = Path(f"workspace/projects/{project_id}/debug/{diagram_id}")
            if debug_dir.exists():
                manifest_path = debug_dir / "manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    log("DebugArtifacts", "PASS", f"{manifest['artifact_count']} artifacts generated")
                    for art in manifest["artifacts"]:
                        print(f"    {art['stage']}.{art['type']}")
                else:
                    log("DebugArtifacts", "WARN", "No manifest.json found")
            else:
                log("DebugArtifacts", "WARN", f"Debug dir not found: {debug_dir}")
        except Exception as e:
            log("DebugArtifacts", "FAIL", str(e))

        # --- 9. Load labels and check Braille ---
        print("\n--- Stage 9: Verify Braille Translation ---")
        label_ids = diagram_data.get("labels", [])
        if not label_ids:
            log("Braille", "WARN", "No labels generated (MockOCR may not have found ANNOTATION components)")
        else:
            for lid in label_ids:
                try:
                    label_file = Path(f"workspace/projects/{project_id}/labels/{lid}.json")
                    label_data = json.loads(label_file.read_text())
                    text = label_data.get("text", "")
                    braille = label_data.get("braille", {})
                    braille_unicode = braille.get("braille_unicode", "") if braille else ""
                    print(f"    Label: '{text}' → Braille: '{braille_unicode}'")
                    if braille_unicode:
                        log(f"Braille({text})", "PASS", braille_unicode)
                    else:
                        log(f"Braille({text})", "WARN", "No braille generated")
                except Exception as e:
                    log(f"Braille({lid[:8]})", "FAIL", str(e))

        # --- 10. Validate ---
        print("\n--- Stage 10: Validate ---")
        try:
            r = await client.get(f"{API}/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/validate")
            if r.status_code == 200:
                validation = r.json()
                log("Validate", "PASS", f"valid={validation.get('is_valid', '?')}, issues={len(validation.get('issues', []))}")
            else:
                log("Validate", "FAIL", f"HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            log("Validate", "FAIL", str(e))

        # --- 11. Export SVG ---
        print("\n--- Stage 11: Export SVG ---")
        try:
            r = await client.post(
                f"{API}/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/export/svg",
                json={"config": {}}
            )
            if r.status_code == 200:
                svg_content = r.text
                svg_path = Path("test_output.svg")
                svg_path.write_text(svg_content)
                has_braille = "⠠" in svg_content or "⠁" in svg_content  # Braille chars
                log("ExportSVG", "PASS", f"size={len(svg_content)} bytes, has_braille={has_braille}")
            else:
                log("ExportSVG", "FAIL", f"HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            log("ExportSVG", "FAIL", str(e))

        # --- 12. Export PDF ---
        print("\n--- Stage 12: Export PDF ---")
        try:
            r = await client.post(
                f"{API}/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/export/pdf",
                json={"config": {}}
            )
            if r.status_code == 200:
                pdf_path = Path("test_output.pdf")
                pdf_path.write_bytes(r.content)
                log("ExportPDF", "PASS", f"size={len(r.content)} bytes")
            else:
                log("ExportPDF", "FAIL", f"HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            log("ExportPDF", "FAIL", str(e))

    # --- Summary ---
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    warned = sum(1 for r in RESULTS if r["status"] == "WARN")
    print(f"  PASS: {passed}  |  FAIL: {failed}  |  WARN: {warned}")
    print()
    if failed > 0:
        print("FAILED STAGES:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"  ❌ {r['stage']}: {r['detail'][:200]}")
    print()


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
