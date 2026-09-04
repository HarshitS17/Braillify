import pytest
import numpy as np
import cv2
from app.models.extraction import AnalysisConfig
from app.pipeline.analysis import analyze_structure
from app.models.diagram import ElementType

def test_analyze_structure():
    # Create an image with a line, circle, and triangle (polygon)
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image.fill(255)
    
    # Draw a line
    cv2.line(image, (10, 10), (10, 100), (0, 0, 0), 2)
    # Draw a circle
    cv2.circle(image, (100, 100), 20, (0, 0, 0), 2)
    # Draw a polygon (triangle)
    pts = np.array([[150, 150], [180, 150], [165, 180]], np.int32)
    cv2.polylines(image, [pts], True, (0, 0, 0), 2)
    
    config = AnalysisConfig()
    config.line_min_length = 20
    config.circle_min_radius = 10
    config.circle_max_radius = 30
    
    elements = analyze_structure(image, config)
    
    types = [el.type for el in elements]
    
    assert ElementType.LINE in types
    assert ElementType.CIRCLE in types
    assert ElementType.POLYGON in types

def test_analyze_structure_text_and_filled():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image.fill(255)
    
    # Draw text
    cv2.putText(image, "Hello", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Draw a large filled rectangle
    cv2.rectangle(image, (100, 100), (180, 180), (0, 0, 0), -1)
    
    config = AnalysisConfig()
    # Dilate enough to merge text characters
    config.text_dilation_kernel = (15, 3)
    config.min_polygon_area = 500
    
    elements = analyze_structure(image, config)
    types = [el.type for el in elements]
    
    assert ElementType.TEXT_REGION in types
    # The filled rectangle's outline is captured by a contour POLYGON (with
    # explicit points) rather than a bbox-only FILLED_REGION, so it is renderable
    # in SVG/PDF/canvas. Verify the geometry representation is complete.
    polygons = [el for el in elements if el.type == ElementType.POLYGON]
    assert any("points" in el.geometry and len(el.geometry["points"]) >= 3 for el in polygons)

def test_analyze_structure_curve():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image.fill(255)
    
    # Draw a wavy curve
    pts = []
    for x in range(20, 180, 10):
        y = int(100 + 30 * np.sin(x / 20.0))
        pts.append([x, y])
    pts = np.array(pts, np.int32)
    cv2.polylines(image, [pts], False, (0, 0, 0), 2)
    
    config = AnalysisConfig()
    config.curve_min_vertices = 8
    
    elements = analyze_structure(image, config)
    types = [el.type for el in elements]
    
    # Due to approxPolyDP, a wavy line with many points should be a CURVE
    assert ElementType.CURVE in types

def test_analyze_structure_arrow():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image.fill(255)
    
    # Draw a vertical line
    cv2.line(image, (50, 50), (50, 140), (0, 0, 0), 2)
    
    # Draw an arrowhead (triangle) near the end of the line
    pts = np.array([[40, 145], [60, 145], [50, 165]], np.int32)
    cv2.fillPoly(image, [pts], (0, 0, 0))
    
    config = AnalysisConfig()
    config.arrow_max_head_area = 300
    config.line_min_length = 50
    
    elements = analyze_structure(image, config)
    types = [el.type for el in elements]
    
    # The line and triangle should be combined into an ARROW
    assert ElementType.ARROW in types
