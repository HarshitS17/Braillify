"""Inspect exported PDF: fonts, raster ink at label boxes (visual proof)."""
import json, sys
import fitz
from app.pipeline.export.pdf import _get_braille_font

pdf_path = sys.argv[1] if len(sys.argv) > 1 else '/Users/saini/Downloads/TextileEd/data/outputs/qa/edit.final.pdf'
diag_path = sys.argv[2]
out_png = sys.argv[3] if len(sys.argv) > 3 else '/Users/saini/Downloads/TextileEd/data/outputs/qa/pdf_raster.png'

print('resolved braille font:', _get_braille_font())
doc = fitz.open(pdf_path)
print('embedded fonts:', doc.get_page_fonts(0))
p = doc[0]
pix = p.get_pixmap(dpi=200)
print('raster:', pix.width, 'x', pix.height)
diag = json.load(open(diag_path))
canvas_w = (diag.get('canvas') or {}).get('width') or 1000
scale = pix.width / canvas_w
proj_dir = diag_path.split('/diagrams/')[0]

label_ids = diag['labels']
label_objs = []
for lid in label_ids:
    lp = f'{proj_dir}/labels/{lid}.json'
    try:
        label_objs.append(json.load(open(lp)))
    except FileNotFoundError:
        print('label file missing:', lp)

def dark_ratio(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(x0*scale), int(y0*scale), int(x1*scale), int(y1*scale)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(pix.width, x1), min(pix.height, y1)
    if x1 <= x0 or y1 <= y0:
        return None
    n = d = 0
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            r, g, b = pix.pixel(xx, yy)[:3]
            n += 1
            if (r + g + b) / 3 < 128:
                d += 1
    return round(d / n, 3) if n else None

labels = label_objs
for lbl in labels:
    pl = lbl.get('placement') or {}
    pos = pl.get('position')
    if not pos:
        print('label %-22r no placement' % (lbl.get('text', '')[:20],))
        continue
    r = dark_ratio(pos['x'], pos['y'], pos['x'] + pl.get('width', 20), pos['y'] + pl.get('height', 8))
    print('label %-22r ink-ratio: %s' % (lbl.get('text', '')[:20], r))

pix.save(out_png)
print('saved raster:', out_png)
