"""Instrumented replica of analysis.py text-region detection, per fixture."""
import sys
import cv2
from pathlib import Path
from collections import Counter
from app.pipeline.preprocessing import preprocess_image

fixture = sys.argv[1]
pre = preprocess_image(Path(fixture), Path('/tmp/qa_debug_pre'))
gray = cv2.imread(pre.preprocessed_path, cv2.IMREAD_GRAYSCALE)
ih, iw = gray.shape[:2]
print(f'image {iw}x{ih}')

_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
cc_n, cc_labels, cc_stats, cc_centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

rejects = Counter()
glyphs = []
for i in range(1, cc_n):
    x = int(cc_stats[i, cv2.CC_STAT_LEFT]); y = int(cc_stats[i, cv2.CC_STAT_TOP])
    w = int(cc_stats[i, cv2.CC_STAT_WIDTH]); h = int(cc_stats[i, cv2.CC_STAT_HEIGHT])
    area = int(cc_stats[i, cv2.CC_STAT_AREA])
    if not (w >= 2 and h >= 4):
        rejects['tiny'] += 1; continue
    if not (w <= max(14, 0.09 * iw)):
        rejects['too_wide'] += 1; continue
    if not (h <= max(10, 0.16 * ih)):
        rejects['too_tall'] += 1; continue
    if not (3 <= area <= 0.03 * iw * ih):
        rejects['area'] += 1; continue
    glyphs.append({'x': x, 'y': y, 'w': w, 'h': h})

print('components:', cc_n - 1, '| glyph-like:', len(glyphs), '| rejects:', dict(rejects))
if glyphs:
    hs = sorted(g['h'] for g in glyphs)
    ws = sorted(g['w'] for g in glyphs)
    print('glyph h range:', hs[0], '-', hs[-1], '| w range:', ws[0], '-', ws[-1])

# cluster into lines
glyphs.sort(key=lambda g: (g['y'], g['x']))
lines = []
for g in glyphs:
    placed = False
    for line in lines:
        overlap = min(g['y'] + g['h'], line['y'] + line['h']) - max(g['y'], line['y'])
        if overlap > 0.5 * min(g['h'], line['h']):
            line['glyphs'].append(g)
            line['x'] = min(line['x'], g['x']); line['y'] = min(line['y'], g['y'])
            line['x2'] = max(line['x2'], g['x'] + g['w']); line['y2'] = max(line['y2'], g['y'] + g['h'])
            placed = True
            break
    if not placed:
        lines.append({'x': g['x'], 'y': g['y'], 'x2': g['x'] + g['w'], 'y2': g['y'] + g['h'],
                      'w': g['w'], 'h': g['h'], 'glyphs': [g]})
print('lines:', len(lines), 'with sizes:', sorted((len(l['glyphs']) for l in lines), reverse=True)[:8])

words_total = 0
for line in lines:
    words = []
    current = [line['glyphs'][0]]
    for g in sorted(line['glyphs'], key=lambda gg: gg['x'])[1:]:
        prev = current[-1]
        gap = g['x'] - (prev['x'] + prev['w'])
        if gap <= 3.0 * max(1, min(prev['w'], g['w'])):
            current.append(g)
        else:
            words.append(current); current = [g]
    words.append(current)
    for word in words:
        if len(word) < 2:
            continue
        x = min(g['x'] for g in word); y = min(g['y'] for g in word)
        x2 = max(g['x'] + g['w'] for g in word); y2 = max(g['y'] + g['h'] for g in word)
        w, h = x2 - x, y2 - y
        reasons = []
        if h > max(10, 0.16 * ih): reasons.append(f'h={h}')
        if w < 12: reasons.append(f'w={w}<12')
        if w > 0.6 * iw: reasons.append(f'w={w}>0.6*iw')
        if reasons:
            print('  word rejected:', reasons, 'nglyphs=', len(word), 'at', (x, y))
        else:
            words_total += 1
print('FINAL text regions:', words_total)
