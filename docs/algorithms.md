# Algorithms

## Overview

TactileEd uses a deterministic computer vision pipeline to convert raster textbook diagrams into simplified tactile vector graphics. Every algorithm is chosen for explainability, reproducibility, and academic defensibility over raw performance.

This document describes the algorithmic approach for each pipeline stage and records the results of Phase 0 technical spikes.

---

## Pipeline Stage Algorithms

### 1. Preprocessing

| Algorithm | Purpose | Library |
|---|---|---|
| Adaptive Thresholding (Gaussian) | Binarize images under uneven illumination | OpenCV `adaptiveThreshold` |
| Deskewing via Hough Transform | Correct rotated scans | OpenCV `HoughLinesP` |
| Gaussian Blur / Non-local Means | Noise reduction | OpenCV |
| CLAHE | Contrast-limited adaptive histogram equalization | OpenCV |
| Otsu's Method | Global threshold when illumination is uniform | OpenCV |

All preprocessing parameters are configurable and logged. The original image is never modified.

### 2. Diagram Region Detection

A layered scoring approach combines multiple signals:

1. **Connected Component Analysis** — `cv2.connectedComponentsWithStats` identifies dense non-text clusters.
2. **Contour Analysis** — `cv2.findContours` with area/aspect-ratio filtering identifies candidate regions.
3. **Edge Density** — Canny edge ratio within sliding windows distinguishes diagrams from text blocks.
4. **Text Density** — OCR-detected text density helps exclude body-text regions.
5. **Whitespace Analysis** — Large whitespace gaps suggest region boundaries.
6. **Geometric Grouping** — Nearby components are merged into candidate bounding boxes.

Each candidate is scored:
```
score = w1 * edge_density + w2 * (1 - text_density) + w3 * component_density + w4 * enclosure_score
```

Candidates are ranked by score. The user can accept, reject, manually draw, resize, merge, or split regions.

**Important**: Automatic detection accuracy on diverse layouts will be mediocre — the manual region tool is a co-equal feature, not a fallback.

### 3. Vectorization (COMMITTED PRIMARY METHOD)

**Primary**: OpenCV contour-to-polygon conversion.

```
Binary image
  → cv2.findContours(image, RETR_TREE, CHAIN_APPROX_SIMPLE)
  → for each contour:
      epsilon = 0.02 * cv2.arcLength(contour, True)
      approx = cv2.approxPolyDP(contour, epsilon, True)
      → classify by vertex count and geometry
```

Shape classification heuristics:
| Vertex Count | Classification | Additional Check |
|---|---|---|
| 3 | Triangle | — |
| 4 | Rectangle / Square | Aspect ratio, right angles |
| 5-8 | Irregular polygon | — |
| > 8 | Circle / Ellipse | Circularity ratio |

**Why not Potrace?** OpenCV contour-to-polygon is:
- Portable (no external binary dependency)
- Deterministic
- Easy to explain in a viva
- Easy to unit test

Potrace-style tracing may be added later as a comparison for Phase 16 evaluation.

### 4. Tactile Simplification

| Algorithm | Purpose |
|---|---|
| Douglas-Peucker (`cv2.approxPolyDP`) | Reduce polygon vertex count while preserving shape |
| Small-component filtering | Remove features below `minimum_feature_size` |
| Line merging | Combine near-parallel duplicate lines |
| Gap normalization | Enforce `minimum_gap` between adjacent features |
| Topology preservation | Ensure simplification doesn't merge or disconnect regions |

Simplification records every transformation:
```json
{
  "original_element_id": "elem_12",
  "simplified_element_id": "elem_12_s",
  "transformation": "douglas_peucker",
  "vertices_before": 47,
  "vertices_after": 8,
  "area_change_pct": -2.3
}
```

### 5. Braille Translation

**Primary**: `liblouis` via Python `louis` bindings (Grade 1 English, table `en-us-g1.ctb`).

**Fallback**: Pure-Python Grade 1 Braille table (see spike results below).

The fallback implements:
- Capital indicator (`⠠`) before uppercase letters
- Number indicator (`⠼`) before digit sequences
- Standard Grade 1 letter-by-letter mapping
- Basic punctuation

Translation is kept separate from rendering — the system stores both original text and Braille representation.

### 6. Label Placement

Constraint-based greedy placement:

1. For each label, generate 8 candidate positions (N, NE, E, SE, S, SW, W, NW) at configurable distance from the target.
2. Score each candidate:
   ```
   cost = w1 * distance_to_target
        + w2 * overlap_with_geometry
        + w3 * overlap_with_other_labels
        + w4 * boundary_violation
        + w5 * readability_penalty
   ```
3. Choose the minimum-cost valid placement.
4. If no valid placement exists: try leader line, then flag for manual review.

---

## Phase 0 Technical Spike Results

### Spike 1: liblouis Braille Library

**Date**: 2026-08-29
**Result**: ❌ FAIL WITH FALLBACK

**Findings**:
- The `louis` Python module is not available as a pip package — it requires system-level installation of `liblouis-dev` and `python3-louis`.
- On macOS (native development), `import louis` fails with `ModuleNotFoundError`.
- On Debian/Ubuntu Docker images, it can be installed via `apt-get install liblouis-dev python3-louis`, but this adds image complexity and ties the Python version to the system package.

**Decision**: Use the **pure-Python Grade 1 Braille fallback** as the primary implementation for Phase 9. This fallback:
- Correctly translates uppercase letters with capital indicator (⠠)
- Correctly handles number sequences with number indicator (⠼)
- Handles basic punctuation
- Produces correct output for test cases:

| Input | Braille Output |
|---|---|
| Nucleus | ⠠⠝⠥⠉⠇⠑⠥⠎ |
| Cell Wall | ⠠⠉⠑⠇⠇⠀⠠⠺⠁⠇⠇ |
| Heart | ⠠⠓⠑⠁⠗⠞ |
| ABC123 | ⠠⠁⠠⠃⠠⠉⠼⠁⠃⠉ |

**Future**: If Grade 2 (contracted) Braille is needed, revisit liblouis installation within Docker.

### Spike 2: OpenCV Contour-to-Polygon Vectorization

**Date**: 2026-08-29
**Result**: ✅ PASS (3/3 shapes detected)

**Test Setup**: Synthetic 500×500 image with three filled black shapes on white background:
- Rectangle (50,50)→(200,150)
- Circle at (350,100) radius 50
- Triangle at vertices (250,400), (150,250), (350,250)

**Pipeline**:
```
BGR → Grayscale → Binary threshold (inv) → findContours(RETR_EXTERNAL) → approxPolyDP(ε=0.02*arcLength)
```

**Results**:

| Shape | Detected As | Approx Vertices | Original Contour Points |
|---|---|---|---|
| Triangle | Triangle | 3 | 203 |
| Circle | Circle (8 vertices) | 8 | 148 |
| Rectangle | Rectangle | 4 | 4 |

**Analysis**:
- `approxPolyDP` with ε=2% of arc length correctly simplifies shapes.
- Circles are approximated as 8-sided polygons, which is appropriate for tactile representation (smooth curves cannot be felt as distinct from 8+ sided polygons).
- Rectangle detection is exact (4 vertices from 4 contour points).
- Triangle detection is exact (3 vertices from 203 raw contour points — massive simplification).

**Conclusion**: The OpenCV contour-to-polygon approach is validated as the primary vectorization method.

**Debug artifacts saved**:
- `data/samples/spike_test_shapes.png` — synthetic input
- `data/samples/spike_test_shapes_debug.png` — detected contours overlay

---

## References

- Braille Authority of North America (BANA), *Guidelines and Standards for Tactile Graphics*, 2010.
- OpenCV Documentation: `findContours`, `approxPolyDP`, `HoughLinesP`.
- Douglas, D.H. & Peucker, T.K. (1973). "Algorithms for the Reduction of the Number of Points Required to Represent a Digitized Line or its Caricature."
- Ramer, U. (1972). "An Iterative Procedure for the Polygonal Approximation of Plane Curves."
