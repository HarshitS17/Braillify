"""Debug: run analysis on a fixture and report element types found."""
import sys
import numpy as np
import cv2
from app.pipeline.preprocessing import preprocess_image
from app.pipeline.analysis import analyze_structure
from app.models.extraction import AnalysisConfig

fixture = sys.argv[1]
img = cv2.imread(fixture)
print('image:', img.shape if img is not None else 'LOAD FAILED')
from pathlib import Path
import os
pre = preprocess_image(Path(fixture), Path('/tmp/qa_debug_pre'))
if isinstance(pre, dict):
    processed = pre.get('processed_image') or pre.get('image')
else:
    p = getattr(pre, 'preprocessed_path', None)
    processed = cv2.imread(p, cv2.IMREAD_GRAYSCALE) if p and os.path.exists(p) else None
if processed is None:
    raise SystemExit('could not obtain processed image: %r' % type(pre))
print('processed shape:', processed.shape)
config = AnalysisConfig()
elements = analyze_structure(processed, config)
from collections import Counter
print('element types:', Counter(e.type.value for e in elements))

# --- Replicate the glyph stage with diagnostics ---
gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY) if processed.ndim == 3 else processed.copy()
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
ih, iw = gray.shape[:2]
cc_n, _, cc_stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
glyphish, near_miss = [], []
for i in range(1, cc_n):
    x, y = int(cc_stats[i, cv2.CC_STAT_LEFT]), int(cc_stats[i, cv2.CC_STAT_TOP])
    w, h = int(cc_stats[i, cv2.CC_STAT_WIDTH]), int(cc_stats[i, cv2.CC_STAT_HEIGHT])
    area = int(cc_stats[i, cv2.CC_STAT_AREA])
    if (w >= 2 and h >= 4 and w <= max(14, 0.09 * iw) and h <= max(10, 0.16 * ih) and 3 <= area <= 0.03 * iw * ih):
        glyphish.append((x, y, w, h, area))
    elif area >= 3 and h <= 0.3 * ih and w <= 0.3 * iw:
        near_miss.append((x, y, w, h, area))
print(f'glyph-pass CCs: {len(glyphish)} | near-miss CCs: {len(near_miss)}')
print('glyph-pass sample:', glyphish[:20])
print('near-miss sample (too big / rejected):', sorted(near_miss, key=lambda t: -t[2])[:20])
tr = [e for e in elements if e.type.value == 'text_region']
print('text regions:', len(tr))
for e in tr[:6]:
    print('  TR geom:', e.geometry)
# Show size distribution of all elements
areas = []
for e in elements:
    g = e.geometry
    if 'w' in g:
        areas.append((g['w'], g['h']))
print('sample sizes:', sorted(areas, key=lambda t: t[0])[:10], '...', sorted(areas, key=lambda t: t[0])[-5:])
