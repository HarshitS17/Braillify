"""Create a realistic textbook-style PDF fixture (vector text + shapes, A4 landscape)."""
import fitz

doc = fitz.open()
page = doc.new_page(width=842, height=595)  # A4 landscape, points

W, H = 842, 595

# Title
page.insert_text((60, 50), "Figure 3.2  The Human Heart", fontsize=16, fontname="hebo")

# Diagram frame
page.draw_rect(fitz.Rect(60, 80, 780, 500), color=(0, 0, 0), width=1.2)

# Body: large ellipse (heart body) + two top arcs (atria)
body = fitz.Rect(300, 200, 540, 420)
page.draw_oval(body, color=(0, 0, 0), width=2)
page.draw_oval(fitz.Rect(320, 150, 420, 230), color=(0, 0, 0), width=1.6)
page.draw_oval(fitz.Rect(430, 150, 530, 230), color=(0, 0, 0), width=1.6)

# Internal septum + valves (lines)
page.draw_line(fitz.Point(420, 220), fitz.Point(420, 400), color=(0, 0, 0), width=1.4)
page.draw_line(fitz.Point(340, 300), fitz.Point(500, 300), color=(0, 0, 0), width=1.2)
page.draw_line(fitz.Point(340, 360), fitz.Point(500, 360), color=(0, 0, 0), width=1.2)

# Blood vessels: aorta up, pulmonary artery, vena cava
page.draw_line(fitz.Point(400, 150), fitz.Point(380, 100), color=(0, 0, 0), width=2.5)
page.draw_line(fitz.Point(460, 150), fitz.Point(480, 100), color=(0, 0, 0), width=2.5)
page.draw_line(fitz.Point(300, 250), fitz.Point(240, 250), color=(0, 0, 0), width=2.5)

# Arrows showing flow (leader lines with arrowheads)
for p0, p1 in [((380, 100), (350, 110)), ((480, 100), (510, 110)), ((240, 250), (250, 280))]:
    page.draw_line(fitz.Point(*p0), fitz.Point(*p1), color=(0, 0, 0), width=1)
    x0, y0 = p0
    page.draw_polyline([fitz.Point(x0 + 8, y0 + 2), fitz.Point(x0, y0), fitz.Point(x0 + 4, y0 - 8)],
                       color=(0, 0, 0), width=1)

# Labels
labels = [
    ((300, 105), "Aorta"),
    ((490, 105), "Pulmonary artery"),
    ((150, 240), "Vena cava"),
    ((560, 230), "Left atrium"),
    ((560, 300), "Left ventricle"),
    ((560, 380), "Right ventricle"),
    ((330, 440), "Septum"),
]
for (x, y), text in labels:
    page.insert_text((x, y), text, fontsize=12, fontname="helv")
    # leader line from label toward diagram
    page.draw_line(fitz.Point(x - 8, y - 4), fitz.Point(x - 30, y - 4), color=(0, 0, 0), width=0.8)

# Caption
page.insert_text((60, 530), "Fig 3.2 - Structure of the human heart. Blood flow is indicated by arrows.",
                 fontsize=10, fontname="helv")

doc.save("qa_fixtures/09_textbook_page.pdf")
doc.close()
print("created qa_fixtures/09_textbook_page.pdf")
