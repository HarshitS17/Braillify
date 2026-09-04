"""QA fixture generator — realistic textbook-style diagrams for E2E testing."""
import cv2
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent / "qa_fixtures"
OUT.mkdir(exist_ok=True)


def _canvas(w=1000, h=700):
    return np.ones((h, w, 3), dtype=np.uint8) * 255


def _save(img: np.ndarray, name: str, w: int | None = None, h: int | None = None):
    if w is None or h is None:
        w, h = img.shape[1], img.shape[0]
    target = np.ones((h, w, 3), dtype=np.uint8) * 255
    y0, x0 = (h - img.shape[0]) // 2, (w - img.shape[1]) // 2
    target[y0:y0 + img.shape[0], x0:x0 + img.shape[1]] = img
    cv2.imwrite(str(OUT / name), target)
    print(f"  wrote {name} ({w}x{h})")


def simple_biology():
    img = _canvas(1000, 700)
    cv2.rectangle(img, (250, 150), (750, 550), (0, 0, 0), 3)          # cell wall
    cv2.rectangle(img, (265, 165), (735, 535), (0, 0, 0), 2)          # membrane
    cv2.circle(img, (500, 350), 60, (0, 0, 0), 2)                     # nucleus
    cv2.circle(img, (500, 350), 20, (0, 0, 0), -1)                    # nucleolus
    cv2.ellipse(img, (500, 350), (180, 90), 0, 0, 360, (0, 0, 0), 2)  # vacuole
    for (x1, y1, x2, y2) in [(450, 200, 350, 140), (620, 300, 720, 240), (500, 500, 400, 580)]:
        cv2.line(img, (x1, y1), (x2, y2), (0, 0, 0), 1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Cell", (340, 130), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Wall", (340, 155), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Nucleus", (720, 250), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Vacuole", (390, 610), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Plant Cell", (400, 60), font, 1.0, (0, 0, 0), 2)
    _save(img, "01_simple_biology.png")


def complex_biology():
    img = _canvas(1000, 700)
    cv2.rectangle(img, (150, 100), (850, 600), (0, 0, 0), 3)
    cv2.circle(img, (500, 350), 70, (0, 0, 0), 2)
    cv2.circle(img, (500, 350), 25, (0, 0, 0), -1)
    for (cx, cy, rx, ry) in [(300, 250, 60, 30), (700, 480, 60, 30), (650, 220, 50, 25)]:
        cv2.ellipse(img, (cx, cy), (rx, ry), 0, 0, 360, (0, 0, 0), 2)
    pts = np.array([(250, 400), (300, 420), (350, 390), (400, 430), (450, 400)])
    cv2.polylines(img, [pts], False, (0, 0, 0), 2)
    for y in range(480, 550, 12):
        cv2.ellipse(img, (700, y), (60, 5), 0, 180, 360, (0, 0, 0), 1)
    rng = np.random.default_rng(42)
    for _ in range(18):
        x, y = int(rng.integers(200, 800)), int(rng.integers(140, 560))
        cv2.circle(img, (x, y), 3, (0, 0, 0), -1)
    labels = ["Nucleus", "Mitochondria", "ER", "Golgi", "Ribosome"]
    targets = [(500, 350), (300, 250), (350, 410), (700, 510), (700, 150)]
    for txt, (tx, ty) in zip(labels, targets):
        cv2.putText(img, txt, (tx - 50, ty + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.line(img, (tx, ty + 40), (tx - 10, ty + 60), (0, 0, 0), 1)
    _save(img, "02_complex_biology.png")
def math_graph():
    img = _canvas(1000, 700)
    cv2.line(img, (150, 550), (900, 550), (0, 0, 0), 3)
    cv2.line(img, (150, 550), (150, 100), (0, 0, 0), 3)
    for x in range(220, 850, 60):
        cv2.line(img, (x, 545), (x, 555), (0, 0, 0), 1)
    for y in range(160, 520, 60):
        cv2.line(img, (145, y), (155, y), (0, 0, 0), 1)
    pts = []
    for x in range(180, 820):
        y = int(100 + ((x - 500) ** 2) / 400.0)
        if y < 540:
            pts.append((x, y))
    pts = np.array(pts, np.int32).reshape(-1, 1, 2)
    cv2.polylines(img, [pts], False, (0, 0, 0), 2)
    for (px, py) in [(180, 356), (500, 100), (820, 356)]:
        cv2.circle(img, (px, py), 5, (0, 0, 0), -1)
    cv2.putText(img, "y", (920, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "x", (900, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "y = x^2", (620, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    _save(img, "03_math_graph.png")


def physics():
    img = _canvas(1000, 700)
    pts = np.array([(100, 620), (820, 620), (560, 180)], np.int32)
    cv2.polylines(img, [pts], True, (0, 0, 0), 3)
    bx0, by0 = 480, 390
    cv2.rectangle(img, (bx0, by0), (bx0 + 110, by0 - 70), (0, 0, 0), 2)
    cv2.arrowedLine(img, (bx0 + 55, by0), (bx0 + 55, by0 + 130), (0, 0, 0), 2)        # weight
    cv2.arrowedLine(img, (bx0 + 55, by0 - 70), (bx0 + 115, by0 - 115), (0, 0, 0), 2)  # normal
    cv2.arrowedLine(img, (bx0, by0 - 35), (bx0 - 100, by0 - 15), (0, 0, 0), 2)        # friction
    cv2.arrowedLine(img, (bx0 + 110, by0 - 35), (bx0 + 230, by0 - 35), (0, 0, 0), 2)  # applied
    labels = ["mg", "Normal", "Friction", "Applied"]
    tx = [bx0 + 70, bx0 + 130, bx0 - 260, bx0 + 240]
    ty = [by0 + 160, by0 - 150, by0 + 10, by0 - 50]
    for txt, x, y in zip(labels, tx, ty):
        cv2.putText(img, txt, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    _save(img, "04_physics.png")


def circuit():
    img = _canvas(1000, 700)
    cv2.line(img, (200, 200), (800, 200), (0, 0, 0), 2)
    cv2.line(img, (800, 200), (800, 500), (0, 0, 0), 2)
    cv2.line(img, (800, 500), (200, 500), (0, 0, 0), 2)
    cv2.line(img, (200, 500), (200, 200), (0, 0, 0), 2)
    rpts = np.array([(450, 200), (470, 170), (510, 230), (550, 170), (590, 230), (610, 200)], np.int32)
    cv2.polylines(img, [rpts], False, (0, 0, 0), 2)
    cv2.rectangle(img, (370, 480), (430, 520), (255, 255, 255), -1)
    cv2.line(img, (370, 490), (430, 490), (0, 0, 0), 4)
    cv2.line(img, (390, 510), (410, 510), (0, 0, 0), 3)
    cv2.circle(img, (500, 300), 30, (0, 0, 0), 2)
    cv2.line(img, (480, 285), (520, 315), (0, 0, 0), 2)
    cv2.line(img, (520, 285), (480, 315), (0, 0, 0), 2)
    cv2.line(img, (200, 350), (280, 350), (0, 0, 0), 2)
    cv2.line(img, (320, 350), (400, 350), (0, 0, 0), 2)
    cv2.line(img, (280, 350), (340, 320), (0, 0, 0), 2)
    for (nx, ny) in [(200, 200), (800, 200), (800, 500), (200, 500)]:
        cv2.circle(img, (nx, ny), 6, (0, 0, 0), -1)
    cv2.putText(img, "R = 10Ω", (500, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "9V", (380, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Bulb", (540, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(img, "Switch", (250, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    _save(img, "05_circuit.png")


def low_quality_scan():
    from pathlib import Path as P
    base = cv2.imread(str(OUT / "02_complex_biology.png"))
    if base is None:
        complex_biology()
        base = cv2.imread(str(OUT / "02_complex_biology.png"))
    h, w = base.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 3.0, 1.0)
    base = cv2.warpAffine(base, M, (w, h), borderValue=(255, 255, 255))
    base = cv2.convertScaleAbs(base, alpha=0.6, beta=60)
    noise = np.random.normal(0, 15, base.shape).astype(np.int16)
    base = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    grad = np.linspace(0, 60, h, dtype=np.float32)
    shadow = np.tile(grad[:, None, None], (1, w, 1))
    base = np.clip(base.astype(np.float32) + shadow, 0, 255).astype(np.uint8)
    tmp = str(OUT / "_tmp_q6.jpg")
    cv2.imwrite(tmp, base, [cv2.IMWRITE_JPEG_QUALITY, 40])
    base = cv2.imread(tmp)
    (OUT / "_tmp_q6.jpg").unlink(missing_ok=True)
    _save(base, "06_low_quality_scan.png")


def dense_diagram():
    img = _canvas(1000, 700)
    rng = np.random.default_rng(7)
    for row in range(4):
        for col in range(4):
            x0, y0 = 120 + col * 210, 90 + row * 150
            cv2.rectangle(img, (x0, y0), (x0 + 120, y0 + 60), (0, 0, 0), 2)
            if row < 3:
                cv2.arrowedLine(img, (x0 + 60, y0 + 60), (x0 + 60, y0 + 150), (0, 0, 0), 1)
            if col < 3:
                cv2.arrowedLine(img, (x0 + 120, y0 + 30), (x0 + 210, y0 + 30), (0, 0, 0), 1)
            cv2.putText(img, f"S{row}{col}", (x0 + 30, y0 + 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    for _ in range(25):
        x, y = int(rng.integers(60, 940)), int(rng.integers(40, 660))
        r = int(rng.integers(6, 20))
        cv2.circle(img, (x, y), r, (0, 0, 0), 1)
    _save(img, "07_dense_diagram.png")


def invalid_inputs():
    blank = np.ones((600, 800, 3), dtype=np.uint8) * 255
    _save(blank, "08_blank.png", 800, 600)
    png = cv2.imencode(".png", _canvas(800, 600))[1].tobytes()
    corrupt = png[: len(png) // 2]
    (OUT / "09_corrupt.png").write_bytes(corrupt)
    print("  wrote 09_corrupt.png (truncated PNG)")
    (OUT / "10_not_an_image.txt").write_text("This is not an image at all.")
    print("  wrote 10_not_an_image.txt")
    (OUT / "11_malformed.pdf").write_bytes(b"%PDF-1.4\nThis is not a real PDF body...")
    print("  wrote 11_malformed.pdf")


if __name__ == "__main__":
    print("Generating QA fixtures into", OUT)
    simple_biology()
    complex_biology()
    math_graph()
    physics()
    circuit()
    dense_diagram()
    low_quality_scan()
    invalid_inputs()
    print("Done.")