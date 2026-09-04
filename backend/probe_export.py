import json, glob
from app.models.diagram import Diagram
from app.models.label import Label, LabelPlacement, BrailleRepresentation, Point
from app.models.export import ExportConfig
from app.pipeline.export.pdf import generate_pdf
from app.pipeline.export.svg import generate_svg

js = json.load(open(glob.glob('workspace/projects/*/diagrams/*/diagram.json', recursive=True)[0]))
d = Diagram(**js)
labels = []
for i, txt in enumerate(['Nucleus', 'Vacuole', 'Cell']):
    br = BrailleRepresentation(braille_unicode='\u2820\u2809\u2815\u2811\u2811', braille_dots='6-14-15-123-123') if i == 2 else BrailleRepresentation()
    labels.append(Label(id=f'lbl{i}', diagram_id=d.id, text=txt, braille=br,
                        placement=LabelPlacement(position=Point(x=50 + 40 * i, y=100), width=60, height=14)))

svg = generate_svg(d, labels, ExportConfig())
open('/tmp/probe.svg', 'w').write(svg)
print('SVG ok, len', len(svg))
for lbl in labels:
    lbl.braille = BrilleRepresentation() if False else None
# fix labels so all have braille
for i, lbl in enumerate(labels):
    lbl.braille = BrailleRepresentation(braille_unicode='\u2820\u2809\u2815', braille_dots='6-14-15')
try:
    pdf = generate_pdf(d, labels, ExportConfig())
    open('/tmp/probe.pdf', 'wb').write(pdf)
    print('PDF ok, len', len(pdf))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('PDF FAILED:', repr(e))