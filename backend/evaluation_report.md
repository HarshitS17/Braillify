# TactileEd Academic Evaluation Report

> **Note**: These metrics are measured by running the actual pipeline
> against QA fixture images, not hardcoded values.

## 1. Diagram Detection
- **IoU** (mean best-match): 0.743
- **Precision**: 1.000
- **Recall**: 1.000
- **F1 Score**: 1.000
- **True Positives**: 7
- **False Positives**: 0
- **False Negatives**: 0

### Per-Fixture Results
| Fixture | Expected | Detected | Status | IoU | Time |
|---------|----------|----------|--------|-----|------|
| 01_simple_biology.png | 1 | 1 | TP | 0.828 | 7.8ms |
| 02_complex_biology.png | 1 | 1 | TP | 0.846 | 7.6ms |
| 03_math_graph.png | 1 | 1 | TP | 0.739 | 6.8ms |
| 04_physics.png | 1 | 1 | TP | 0.689 | 6.7ms |
| 05_circuit.png | 1 | 1 | TP | 0.456 | 5.7ms |
| 06_low_quality_scan.png | 1 | 1 | TP | 0.760 | 9.7ms |
| 07_dense_diagram.png | 1 | 1 | TP | 0.887 | 7.1ms |
| 08_blank.png | 0 | 0 | TN | — | 2.5ms |

## 2. Tactile Simplification
- **Whole-element reduction (drops + deduplication)**: 5.7%
- **Vertex/feature reduction (Douglas-Peucker)**: 11.2%
- **Total Analysis Time**: 68.8ms
- **Total Simplification Time**: 30.7ms

### Per-Fixture Results
| Fixture | Orig Elems | Simp Elems | Elem Red % | Orig Verts | Simp Verts | Vert Red % | Analysis (ms) | Simplify (ms) |
|---------|------------|------------|------------|------------|------------|------------|---------------|---------------|
| 01_simple_biology.png | 82 | 80 | 2.4% | 92 | 88 | 4.3% | 11.3 | 2.3 |
| 02_complex_biology.png | 83 | 82 | 1.2% | 86 | 85 | 1.2% | 13.0 | 2.3 |
| 03_math_graph.png | 36 | 33 | 8.3% | 73 | 51 | 30.1% | 4.4 | 0.8 |
| 04_physics.png | 43 | 43 | 0.0% | 45 | 45 | 0.0% | 5.9 | 0.9 |
| 05_circuit.png | 37 | 36 | 2.7% | 63 | 52 | 17.5% | 4.4 | 0.7 |
| 06_low_quality_scan.png | 99 | 91 | 8.1% | 102 | 94 | 7.8% | 15.5 | 2.8 |
| 07_dense_diagram.png | 303 | 279 | 7.9% | 344 | 300 | 12.8% | 14.4 | 20.9 |

## 3. Label Placement
- **Collision Rate**: *(requires full pipeline run with labels)*
- **Human-in-the-Loop Correction Rate**: *(requires real user data)*
