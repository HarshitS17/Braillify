# Tactile Design Guidelines

## Introduction
Tactile graphics provide spatial information to blind and visually impaired individuals through touch.

## Physical Constraints
- Embosser specs vary.
- Standard paper sizes must be respected.

## Minimum Dimensions
- Line width: ≥0.5mm
- Gap between lines: ≥2.5mm
- Minimum feature size: ≥3mm

## Braille Cell Dimensions
- Standard: 6.2mm × 10.0mm per cell
- Inter-cell spacing: 3.5mm

## Maximum Detail Density
Overcrowded diagrams cause tactile confusion.

## Simplification Principles
- Remove gradients, shadows, textures, and tiny details.

## Label Placement
Place labels horizontally if possible. Avoid overlap with lines.

## Leader Lines
Use solid or dashed lines to connect labels to far elements.

## References
BANA (Braille Authority of North America) Tactile Graphics Guidelines.

## Configuration Mapping
These physical constraints are translated into `TACTILE_ED_*` env variables and JSON configs.
