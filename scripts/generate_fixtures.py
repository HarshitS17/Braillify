import cv2
import numpy as np
from pathlib import Path

FIXTURE_DIR = Path("data/fixtures")
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

def generate_simple_shapes():
    # White background
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    # Black filled rectangle at (100, 100) to (300, 250)
    cv2.rectangle(img, (100, 100), (300, 250), (0, 0, 0), -1)
    # Black filled circle at (550, 175), radius 75
    cv2.circle(img, (550, 175), 75, (0, 0, 0), -1)
    # Black filled triangle at vertices (400, 500), (250, 350), (550, 350)
    pts = np.array([[400, 500], [250, 350], [550, 350]], np.int32)
    cv2.fillPoly(img, [pts], (0, 0, 0))
    cv2.imwrite(str(FIXTURE_DIR / "simple_shapes.png"), img)
    return img

def generate_text_with_diagram():
    img = np.ones((1000, 800, 3), dtype=np.uint8) * 255
    # Several rows of simulated text
    for y in range(50, 500, 25):
        # vary line length slightly
        length = np.random.randint(600, 700)
        cv2.line(img, (50, y), (50 + length, y), (0, 0, 0), 2)
    
    # Diagram region in the lower half
    cv2.rectangle(img, (50, 550), (750, 950), (200, 200, 200), 1)
    cv2.circle(img, (400, 750), 100, (0, 0, 0), 2)
    cv2.circle(img, (400, 750), 30, (0, 0, 0), -1)
    cv2.line(img, (400, 650), (500, 550), (0, 0, 0), 2)
    
    cv2.imwrite(str(FIXTURE_DIR / "text_with_diagram.png"), img)
    return img

def generate_noisy_diagram(base_img):
    # Add Gaussian noise
    noise = np.random.normal(0, 25, base_img.shape).astype(np.int16)
    noisy = np.clip(base_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Rotate 3 degrees clockwise
    h, w = noisy.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), -3, 1.0) # -3 for clockwise
    rotated = cv2.warpAffine(noisy, M, (w, h), borderValue=(255, 255, 255))
    
    # Salt and pepper noise (~1%)
    s_vs_p = 0.5
    amount = 0.01
    out = np.copy(rotated)
    
    # Salt
    num_salt = np.ceil(amount * rotated.size * s_vs_p)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in rotated.shape]
    out[tuple(coords)] = 255

    # Pepper
    num_pepper = np.ceil(amount * rotated.size * (1. - s_vs_p))
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in rotated.shape]
    out[tuple(coords)] = 0
    
    cv2.imwrite(str(FIXTURE_DIR / "noisy_diagram.png"), out)

def generate_low_contrast():
    img = np.ones((600, 800, 3), dtype=np.uint8) * 200
    color = (80, 80, 80)
    cv2.rectangle(img, (100, 100), (300, 250), color, -1)
    cv2.circle(img, (550, 175), 75, color, -1)
    pts = np.array([[400, 500], [250, 350], [550, 350]], np.int32)
    cv2.fillPoly(img, [pts], color)
    cv2.imwrite(str(FIXTURE_DIR / "low_contrast.png"), img)

def generate_labeled_diagram():
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    # Rectangle labeled "Cell Wall"
    cv2.rectangle(img, (100, 100), (300, 250), (0, 0, 0), -1)
    cv2.putText(img, "Cell Wall", (100, 280), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Circle labeled "Nucleus"
    cv2.circle(img, (550, 175), 75, (0, 0, 0), -1)
    cv2.putText(img, "Nucleus", (550, 280), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Triangle labeled "Mitochondria"
    pts = np.array([[400, 500], [250, 350], [550, 350]], np.int32)
    cv2.fillPoly(img, [pts], (0, 0, 0))
    cv2.putText(img, "Mitochondria", (350, 550), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    cv2.imwrite(str(FIXTURE_DIR / "labeled_diagram.png"), img)

def generate_pdf():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        c = canvas.Canvas(str(FIXTURE_DIR / "simple_page.pdf"), pagesize=letter)
        c.drawString(100, 750, "Test PDF Document")
        c.rect(100, 600, 200, 100, fill=1)
        c.circle(400, 650, 50, fill=1)
        c.save()
    except ImportError:
        print("reportlab not installed, skipping PDF generation")

if __name__ == "__main__":
    base_img = generate_simple_shapes()
    generate_text_with_diagram()
    generate_noisy_diagram(base_img)
    generate_low_contrast()
    generate_labeled_diagram()
    generate_pdf()
