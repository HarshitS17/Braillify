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
| 01_simple_biology.png | 1 | 1 | TP | 0.828 | 7.9ms |
| 02_complex_biology.png | 1 | 1 | TP | 0.846 | 7.1ms |
| 03_math_graph.png | 1 | 1 | TP | 0.739 | 6.5ms |
| 04_physics.png | 1 | 1 | TP | 0.689 | 6.1ms |
| 05_circuit.png | 1 | 1 | TP | 0.456 | 5.4ms |
| 06_low_quality_scan.png | 1 | 1 | TP | 0.760 | 9.3ms |
| 07_dense_diagram.png | 1 | 1 | TP | 0.887 | 7.2ms |
| 08_blank.png | 0 | 0 | TN | — | 2.2ms |

## 2. Tactile Simplification
- **Original Elements**: 62
- **Simplified Elements**: 62
- **Feature Reduction**: 0.0%
- **Analysis Time**: 10.4ms
- **Simplification Time**: 1.5ms

## 3. Label Placement
- **Collision Rate**: *(requires full pipeline run with labels)*
- **Human-in-the-Loop Correction Rate**: *(requires real user data)*
