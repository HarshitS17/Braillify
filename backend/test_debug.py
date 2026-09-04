import pytest
import numpy as np
import cv2
from app.models.extraction import AnalysisConfig
from app.pipeline.analysis import analyze_structure

image = np.zeros((200, 200, 3), dtype=np.uint8)
image.fill(255)

cv2.line(image, (50, 50), (50, 140), (0, 0, 0), 2)
pts = np.array([[40, 145], [60, 145], [50, 165]], np.int32)
cv2.fillPoly(image, [pts], (0, 0, 0))

config = AnalysisConfig()
config.arrow_max_head_area = 300
config.line_min_length = 50

elements = analyze_structure(image, config)
for el in elements:
    print(el.type)
