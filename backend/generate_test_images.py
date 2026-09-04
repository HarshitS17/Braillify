import cv2
import numpy as np
from pathlib import Path
import random

def create_math_graph():
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    # Axes
    cv2.line(img, (100, 500), (700, 500), (0,0,0), 2)
    cv2.line(img, (100, 500), (100, 100), (0,0,0), 2)
    # Sine wave
    pts = []
    for x in range(100, 700):
        y = 500 - int(200 * np.abs(np.sin((x-100)/100.0)))
        pts.append((x, y))
    pts = np.array(pts, np.int32)
    cv2.polylines(img, [pts], False, (0,0,0), 2)
    cv2.putText(img, "y = |sin(x)|", (300, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
    return img

def create_circuit_diagram():
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    # Wires
    cv2.line(img, (200, 200), (600, 200), (0,0,0), 2)
    cv2.line(img, (600, 200), (600, 400), (0,0,0), 2)
    cv2.line(img, (600, 400), (200, 400), (0,0,0), 2)
    cv2.line(img, (200, 400), (200, 200), (0,0,0), 2)
    # Resistor
    cv2.rectangle(img, (350, 180), (450, 220), (255,255,255), -1)
    pts = np.array([(350,200), (365,180), (395,220), (425,180), (450,200)], np.int32)
    cv2.polylines(img, [pts], False, (0,0,0), 2)
    cv2.putText(img, "10 Ohms", (360, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    # Battery
    cv2.rectangle(img, (380, 380), (420, 420), (255,255,255), -1)
    cv2.line(img, (380, 390), (420, 390), (0,0,0), 4)
    cv2.line(img, (390, 410), (410, 410), (0,0,0), 2)
    cv2.putText(img, "9V", (390, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    return img

def create_noisy_diagram():
    img = create_math_graph()
    # Add noise
    noise = np.random.normal(0, 25, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def create_empty_diagram():
    return np.ones((600, 800, 3), dtype=np.uint8) * 255

if __name__ == "__main__":
    Path("test_math.png").write_bytes(cv2.imencode(".png", create_math_graph())[1].tobytes())
    Path("test_circuit.png").write_bytes(cv2.imencode(".png", create_circuit_diagram())[1].tobytes())
    Path("test_noisy.png").write_bytes(cv2.imencode(".png", create_noisy_diagram())[1].tobytes())
    Path("test_empty.png").write_bytes(cv2.imencode(".png", create_empty_diagram())[1].tobytes())
    print("Test images generated.")
