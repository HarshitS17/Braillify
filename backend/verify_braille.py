"""Verify braille glyph rendering in PDF (Helvetica vs Arial Unicode) and mock OCR output."""
import io
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
import numpy as np

BRAILLE = '\u2820\u2809\u2815\u2819\u2811'  # ⠠⠉⠑⠇⠇ (Cell)

# --- A) Helvetica ---
buf = io.BytesIO()
c = rl_canvas.Canvas(buf, pagesize=(210 * mm, 100 * mm))
c.setFont('Helvetica', 20)
c.drawString(50, 50, BRAILLE)
c.save()
pdf = fitz.open(stream=buf.getvalue(), filetype='pdf')
pix = pdf[0].get_pixmap(matrix=fitz.Matrix(3, 3))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
ink = int((img < 128).sum())
print('Helvetica braille ink px:', ink)

# --- B) Arial Unicode (TTF) ---
try:
    pdfmetrics.registerFont(TTFont('ArialUni', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
    buf2 = io.BytesIO()
    c2 = rl_canvas.Canvas(buf2, pagesize=(210 * mm, 100 * mm))
    c2.setFont('ArialUni', 20)
    c2.drawString(50, 50, BRAILLE)
    c2.save()
    pdf2 = fitz.open(stream=buf2.getvalue(), filetype='pdf')
    pix2 = pdf2[0].get_pixmap(matrix=fitz.Matrix(3, 3))
    img2 = np.frombuffer(pix2.samples, dtype=np.uint8).reshape(pix2.h, pix2.w, pix2.n)[:, :, :3]
    ink2 = int((img2 < 128).sum())
    print('ArialUni braille ink px:', ink2)
except Exception as e:
    print('ArialUni failed:', repr(e))

# --- C) Mock OCR on black 100x100 image ---
import numpy as npx
from app.pipeline.ocr.mock import MockOCRProvider
p = MockOCRProvider()
text, conf = p.extract_text(npx.zeros((100, 100, 3), dtype=npx.uint8), {"x": 10, "y": 20, "w": 100, "h": 20})
print('mock OCR black image ->', repr(text), conf)