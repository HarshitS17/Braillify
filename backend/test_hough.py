import cv2
import numpy as np

image = np.zeros((200, 200, 3), dtype=np.uint8)
image.fill(255)
cv2.line(image, (10, 10), (10, 100), (0, 0, 0), 2)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
edges = cv2.Canny(gray, 50, 150, apertureSize=3)
lines = cv2.HoughLinesP(edges, 1.0, np.pi/180, 50, minLineLength=20, maxLineGap=10)
print(lines.shape)
print(lines)
