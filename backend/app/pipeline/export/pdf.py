import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ...models.diagram import Diagram, ElementType
from ...models.label import Label
from ...models.export import ExportConfig, PhysicalUnit

# Braille (Unicode U+2800) is NOT covered by the standard Type1 Helvetica font —
# it renders as boxes/mojibake. Register a TrueType font that includes the
# Braille block when available and fall back to Helvetica otherwise.
_BRAILLE_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        # Linux (Debian/Ubuntu)
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",                 # Linux (Fedora)
    "C:/Windows/Fonts/arialuni.ttf",                          # Windows
    "C:/Windows/Fonts/DejaVuSans.ttf",                        # Windows
]

_braille_font_name = None


def _get_braille_font() -> str:
    global _braille_font_name
    if _braille_font_name:
        return _braille_font_name
    for path in _BRAILLE_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("TactileBraille", path))
                _braille_font_name = "TactileBraille"
                return _braille_font_name
            except Exception:
                continue
    _braille_font_name = "Helvetica"
    return _braille_font_name


def _get_multiplier(unit: PhysicalUnit) -> float:
    if unit == PhysicalUnit.MM:
        return mm
    elif unit == PhysicalUnit.CM:
        return cm
    elif unit == PhysicalUnit.IN:
        return inch
    return mm


def generate_pdf(diagram: Diagram, labels: list[Label], config: ExportConfig) -> bytes:
    """
    Generate a PDF file representing the diagram and its braille labels.
    """
    buffer = io.BytesIO()
    
    # Calculate dimensions in standard points
    multiplier = _get_multiplier(config.unit)
    pdf_w = config.width * multiplier
    pdf_h = config.height * multiplier
    
    c = canvas.Canvas(buffer, pagesize=(pdf_w, pdf_h))
    
    if config.include_metadata:
        c.setTitle(f"Tactile Diagram {diagram.id}")
        c.setAuthor("TactileEd")
        
    # Coordinate Mapping
    # Diagram uses top-left origin pixels. PDF uses bottom-left origin points.
    canvas_w = diagram.canvas.width if diagram.canvas else 800
    canvas_h = diagram.canvas.height if diagram.canvas else 600
    
    # Scale based on width (maintain aspect ratio)
    # The diagram's pixel width is mapped to the requested physical width.
    scale_to_points = pdf_w / canvas_w
    
    # Helper to convert (x, y) pixels to (x, y) PDF points
    def map_pt(x: float, y: float) -> tuple[float, float]:
        px = x * scale_to_points
        py = pdf_h - (y * scale_to_points)
        return px, py
        
    # Draw Geometry
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(config.stroke_width_mm * mm)
    
    for el in diagram.elements:
        g = el.geometry
        
        if el.type == ElementType.LINE and "x1" in g:
            x1, y1 = map_pt(g["x1"], g["y1"])
            x2, y2 = map_pt(g["x2"], g["y2"])
            c.line(x1, y1, x2, y2)
            
        elif el.type == ElementType.CIRCLE and "cx" in g:
            cx, cy = map_pt(g["cx"], g["cy"])
            r = g["r"] * scale_to_points
            c.circle(cx, cy, r, fill=0)
            
        elif el.type in (ElementType.POLYGON, ElementType.CURVE, ElementType.FILLED_REGION) and "points" in g:
            if not g["points"]:
                continue
                
            p = c.beginPath()
            start_x, start_y = map_pt(g["points"][0]["x"], g["points"][0]["y"])
            p.moveTo(start_x, start_y)
            
            for pt in g["points"][1:]:
                px, py = map_pt(pt["x"], pt["y"])
                p.lineTo(px, py)
                
            if el.type in (ElementType.POLYGON, ElementType.FILLED_REGION):
                p.close()
                
            fill = 1 if el.type == ElementType.FILLED_REGION else 0
            if fill:
                c.setFillColorRGB(0, 0, 0)
            c.drawPath(p, stroke=1, fill=fill)
            
    # Draw Labels
    c.setFillColorRGB(0, 0, 0)
    braille_font = _get_braille_font()
    # Braille cells need to be legible; use a comfortable floor size.
    font_size = max(4.0, 3.5 * scale_to_points)
    c.setFont(braille_font, font_size)
    
    for lbl in labels:
        if not lbl.placement:
            continue
            
        # Leader line
        if lbl.placement.leader_line:
            c.saveState()
            c.setDash(2, 2)
            c.setLineWidth((config.stroke_width_mm / 2) * mm)
            ll = lbl.placement.leader_line
            x1, y1 = map_pt(ll.start.x, ll.start.y)
            x2, y2 = map_pt(ll.end.x, ll.end.y)
            c.line(x1, y1, x2, y2)
            c.restoreState()
            
        # Text element
        text_str = lbl.braille.braille_unicode if lbl.braille.braille_unicode else lbl.text
        
        # SVG uses baseline, Reportlab uses baseline. 
        # In our SVG we did `y + height`. Since we flip Y, we use `y + height` in pixel space, 
        # which maps to a lower Y in PDF space.
        tx, ty = map_pt(lbl.placement.position.x, lbl.placement.position.y + lbl.placement.height)
        
        c.drawString(tx, ty, text_str)
        
    c.showPage()
    c.save()
    
    return buffer.getvalue()
