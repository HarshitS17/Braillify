import cv2, glob, os, json
import numpy as np
from app.pipeline.analysis import analyze_structure
from app.models.extraction import AnalysisConfig

# Find the most recent extracted.png for the complex biology runs
paths = glob.glob('workspace/projects/*/diagrams/*/extracted.png')
paths.sort(key=lambda p: os.path.getmtime(p))
print('latest extracted:', paths[-1] if paths else 'none')
if paths:
    img = cv2.imread(paths[-1])
    print('extracted img shape', img.shape)
    cfg = AnalysisConfig()
    els = analyze_structure(img, cfg)
    from collections import Counter
    print('types:', Counter(e.type.value for e in els))
    tr = [e for e in els if e.type.value == 'text_region']
    print('text regions:', len(tr))
    for e in tr[:8]:
        print(' ', e.geometry)
    # Show the binary to understand what's happening
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, cfg.text_dilation_kernel)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print('dilated text contours:', len(contours))
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        roi = binary[y:y+h, x:x+w]
        num_labels, _ = cv2.connectedComponents(roi, connectivity=8)
        print(f'  bbox=({x},{y},{w}x{h}) num_labels={num_labels} passes={(3 <= num_labels <= 40) and h <= max(8,0.12*gray.shape[0]) and w <= max(30,0.5*gray.shape[1])}')