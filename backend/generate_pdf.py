from reportlab.pdfgen import canvas
c = canvas.Canvas("test_diagram.pdf")
c.drawString(100, 750, "Test Diagram in PDF")
c.rect(100, 600, 200, 100)
c.save()
