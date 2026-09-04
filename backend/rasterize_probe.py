import fitz
import cairosvg
import numpy as np
import cv2

# Rasterize PDF
pdf = fitz.open('/tmp/probe.pdf')
page = pdf[0]
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
if pix.n > 3:
    img = img[:, :, :3]
print('PDF raster', img.shape)
# Look at label region (multiple labels at scale 2). Labels at y=100px area,
# scaled by scale_to_points = 595/800*2 = 1.488? Compute ink in that band.
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
dark = (gray < 128).sum()
print('PDF dark pixels:', dark)

# Rasterize SVG
svg_png = cairosvg.svg2png(url='/tmp/probe.svg', output_width=1000)
n = np.frombuffer(svg_png, dtype=np.uint8)
svg_img = cv2.imdecode(n, cv2.IMREAD_GRAYSCALE)
print('SVG raster', svg_img.shape, 'dark:', (svg_img < 128).sum())

# Where are the labels? SVG labels are drawn at positions 50..170 px * scale.
scale = 210 / 800
label_y_px = int(100 * scale * (1000 / (210 * scale)))  # map: output_width unit is user units 210mm? cairosvg uses width attr mm => treat
print('label y (approximate):', label_y_px)

# Save rasterized crops for evidence
cv2.imwrite('/tmp/probe_pdf.png', img)
cv2.imwrite('/tmp/probe_svg.png', svg_img)
print('saved /tmp/probe_pdf.png /tmp/probe_svg.png')