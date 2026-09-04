import fitz
import numpy as np

pdf = fitz.open('/tmp/probe2.pdf')
print('pages:', len(pdf))
pix = pdf[0].get_pixmap(matrix=fitz.Matrix(2, 2))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
gray = np.asarray(img).mean(axis=2)
dark = gray < 128
print('raster', img.shape, 'dark px', int(dark.sum()), 'pct', round(100 * dark.mean(), 2))
rows = dark.any(axis=1).nonzero()[0]
cols = dark.any(axis=0).nonzero()[0]
print('dark rows', (rows.min(), rows.max()) if len(rows) else None)
print('dark cols', (cols.min(), cols.max()) if len(cols) else None)
# Histogram of dark pixels per row to spot large filled bands
band = np.where(dark, 1, 0).sum(axis=1)
# print rows with >30% dark
thick = [(int(y), int(band[y]), int(100 * band[y] / img.shape[1])) for y in range(img.shape[0]) if band[y] > img.shape[1] * 0.5]
print('thick bands (>50% width):', thick[:10])
# Save a downscaled PNG for the record
import cv2
cv2.imwrite('/tmp/probe2_raster.png', img)
print('saved /tmp/probe2_raster.png')