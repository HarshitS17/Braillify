import zipfile
import html
from pathlib import Path

def create_styled_docx(output_path: Path):
    # XML templates
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="2D3748"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="276" w:lineRule="auto" w:after="160"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

    # Helper functions to build WordprocessingML
    def p(text="", bold=False, italic=False, size=22, color="2D3748", space_after=160, space_before=0, heading=0, align=None):
        align_xml = f'<w:jc w:val="{align}"/>' if align else ""
        sp_before = f'w:before="{space_before}"' if space_before else ""
        sp_after = f'w:after="{space_after}"' if space_after else ""
        spacing_xml = f'<w:spacing {sp_before} {sp_after} w:line="276" w:lineRule="auto"/>'
        
        b_xml = "<w:b/>" if bold else ""
        i_xml = "<w:i/>" if italic else ""
        
        escaped_text = html.escape(text)
        
        return f"""
        <w:p>
          <w:pPr>
            {align_xml}
            {spacing_xml}
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI"/>
              {b_xml}
              {i_xml}
              <w:sz w:val="{size}"/>
              <w:color w:val="{color}"/>
            </w:rPr>
            <w:t xml:space="preserve">{escaped_text}</w:t>
          </w:r>
        </w:p>"""

    def table_row(cells, is_header=False):
        row_xml = "<w:tr>"
        for cell_text, width, bg_color in cells:
            b_xml = "<w:b/>" if is_header else ""
            txt_color = "1A365D" if is_header else "2D3748"
            f_size = 20 if is_header else 19
            shd_xml = f'<w:shd w:val="clear" w:color="auto" w:fill="{bg_color}"/>' if bg_color else ""
            
            row_xml += f"""
            <w:tc>
              <w:tcPr>
                <w:tcW w:w="{width}" w:type="dxa"/>
                {shd_xml}
                <w:tcMar>
                  <w:top w:w="120" w:type="dxa"/>
                  <w:bottom w:w="120" w:type="dxa"/>
                  <w:left w:w="160" w:type="dxa"/>
                  <w:right w:w="160" w:type="dxa"/>
                </w:tcMar>
              </w:tcPr>
              <w:p>
                <w:pPr>
                  <w:spacing w:after="40" w:before="40"/>
                </w:pPr>
                <w:r>
                  <w:rPr>
                    <w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI"/>
                    {b_xml}
                    <w:sz w:val="{f_size}"/>
                    <w:color w:val="{txt_color}"/>
                  </w:rPr>
                  <w:t xml:space="preserve">{html.escape(cell_text)}</w:t>
                </w:r>
              </w:p>
            </w:tc>"""
        row_xml += "</w:tr>"
        return row_xml

    def create_table(headers, rows):
        tbl = """
        <w:tbl>
          <w:tblPr>
            <w:tblW w:w="9360" w:type="dxa"/>
            <w:tblBorders>
              <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/>
              <w:left w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/>
              <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/>
              <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/>
              <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
              <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
            </w:tblBorders>
          </w:tblPr>"""
        
        # Header
        header_cells = [(h[0], h[1], "EDF2F7") for h in headers]
        tbl += table_row(header_cells, is_header=True)
        
        # Data Rows
        for i, row in enumerate(rows):
            bg = "F7FAFC" if i % 2 == 1 else "FFFFFF"
            cells = [(row[0], headers[0][1], bg), (row[1], headers[1][1], bg), (row[2], headers[2][1], bg)]
            tbl += table_row(cells, is_header=False)
            
        tbl += "</w:tbl>"
        return tbl

    def bullet_item(bold_prefix, text):
        return f"""
        <w:p>
          <w:pPr>
            <w:pStyle w:val="ListParagraph"/>
            <w:numPr>
              <w:ilvl w:val="0"/>
            </w:numPr>
            <w:spacing w:after="80" w:before="20"/>
            <w:ind w:left="400" w:hanging="200"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI"/>
              <w:b/>
              <w:sz w:val="21"/>
              <w:color w:val="1A365D"/>
            </w:rPr>
            <w:t xml:space="preserve">•  {html.escape(bold_prefix)}: </w:t>
          </w:r>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI"/>
              <w:sz w:val="21"/>
              <w:color w:val="2D3748"/>
            </w:rPr>
            <w:t xml:space="preserve">{html.escape(text)}</w:t>
          </w:r>
        </w:p>"""

    # Assemble Document Content
    doc_body = []
    
    # Title & Subtitle
    doc_body.append(p("TACTILEED: IMPLEMENTATION STATUS & TECHNOLOGY STACK", bold=True, size=32, color="1E3A8A", space_before=100, space_after=120))
    doc_body.append(p("Comprehensive architecture, pipeline capabilities, and library inventory.", italic=True, size=22, color="64748B", space_after=350))
    
    # Section 1
    doc_body.append(p("1. What is Currently Working?", bold=True, size=26, color="1E3A8A", space_before=200, space_after=120))
    doc_body.append(p("All 15 pipeline stages are fully implemented and verified end-to-end, including Braille positioning and multi-format exports.", size=21, color="334155", space_after=180))
    
    headers = [("Pipeline Stage / Feature", "3200"), ("Status", "1200"), ("Implementation Details", "4960")]
    rows = [
        ("Upload scanned textbook/image", "✅ Working", "Supports PNG, JPG, TIFF, and multi-page PDF rendering via PyMuPDF."),
        ("Detect diagram from page", "✅ Working", "Page layout segmentation & bounding box candidate proposal."),
        ("Separate diagram from body text", "✅ Working", "Region cropping, text-density masking, and connected component filtering."),
        ("OpenCV preprocessing", "✅ Working", "Grayscale conversion, bilateral/Gaussian filtering, Otsu/adaptive thresholding, deskewing."),
        ("Edge detection", "✅ Working", "Canny edge detection and morphological gradient filters."),
        ("Contour detection", "✅ Working", "cv2.findContours, hierarchy tree analysis, polygon approximation (Douglas-Peucker)."),
        ("Remove shading/background", "✅ Working", "Morphological opening background subtraction and illumination normalization."),
        ("Convert image to line art", "✅ Working", "Morphological thinning / skeletonization, noise reduction, and line normalization."),
        ("Vectorization", "✅ Working", "Native OpenCV contour-to-vector primitives (paths, lines, polygons, circles, curves)."),
        ("Braille generation", "✅ Working", "Grade 1 English Braille translation mapping text to Unicode Braille (e.g. ⠠⠝⠥⠉⠇⠑⠥⠎)."),
        ("Braille positioning", "✅ Working", "Heuristic placement engine with collision avoidance and leader-line routing."),
        ("Overlap detection", "✅ Working", "Bounding box / IoU collision detection between tactile graphics and Braille boxes."),
        ("SVG generation", "✅ Working", "Structured multi-layer tactile SVGs (diagram, braille, leader lines) with tactile stroke widths."),
        ("PDF generation", "✅ Working", "Embosser-ready tactile PDF exports."),
        ("Complete end-to-end pipeline", "✅ Working", "Orchestrated via FastAPI workflow API and verified by automated end-to-end test suite.")
    ]
    doc_body.append(create_table(headers, rows))
    
    # Section 2
    doc_body.append(p("2. Technologies and Libraries Actually Used", bold=True, size=26, color="1E3A8A", space_before=400, space_after=140))
    
    doc_body.append(p("Backend & Processing (Python 3.12+ / 3.14)", bold=True, size=23, color="0F766E", space_before=150, space_after=100))
    doc_body.append(bullet_item("FastAPI & Uvicorn", "Asynchronous REST API backend, endpoints, and workflow routing."))
    doc_body.append(bullet_item("OpenCV (opencv-python-headless)", "Computer vision pipeline, filtering, edge/contour detection, Hough transforms, and connected components."))
    doc_body.append(bullet_item("NumPy", "Multidimensional array manipulation for image masks, thresholds, and spatial coordinates."))
    doc_body.append(bullet_item("Pillow (PIL)", "Image decoding, encoding, format conversions, and metadata handling."))
    doc_body.append(bullet_item("scikit-image", "Advanced morphological thinning, skeletonization, and image analysis."))
    doc_body.append(bullet_item("Shapely", "2D computational geometry, polygon intersections, and collision/overlap detection."))
    doc_body.append(bullet_item("PyMuPDF (fitz)", "High-DPI rasterization of uploaded PDF pages into image arrays."))
    doc_body.append(bullet_item("svgwrite", "Tactile SVG document generation, layer grouping, and Braille symbol rendering."))
    doc_body.append(bullet_item("ReportLab & CairoSVG", "Tactile PDF rendering, vector conversions, and embosser formatting."))
    doc_body.append(bullet_item("Pydantic", "Data modeling, schema validation, and pipeline state persistence."))
    
    doc_body.append(p("Frontend (Web UI)", bold=True, size=23, color="0F766E", space_before=250, space_after=100))
    doc_body.append(bullet_item("React 19", "Modern component hierarchy and interactive pipeline interface."))
    doc_body.append(bullet_item("TypeScript", "Strict type safety for state management, canvas drawing, and API communication."))
    doc_body.append(bullet_item("Vite", "Next-generation frontend tooling and fast HMR dev server."))
    doc_body.append(bullet_item("TailwindCSS", "Utility-first CSS styling and responsive layout system."))
    doc_body.append(bullet_item("HTML / CSS / JavaScript", "Core browser standards, interactive SVG rendering, and DOM manipulation."))
    
    doc_body.append(p("Clarifications on Specific Tools", bold=True, size=23, color="0F766E", space_before=250, space_after=100))
    doc_body.append(bullet_item("Tesseract OCR", "Not currently used as an external binary dependency. Text detection uses an OpenCV connected-component heuristic provider (MockOCRProvider) designed for human-in-the-loop verification/editing."))
    doc_body.append(bullet_item("Potrace", "Not using the external Potrace C binary. Vectorization is implemented natively via OpenCV contour extraction + Douglas-Peucker polygon approximation + geometric primitive fitting."))

    # Construct complete document.xml
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {''.join(doc_body)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    # Create Zip / Docx
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", root_rels)
        docx.writestr("word/_rels/document.xml.rels", doc_rels)
        docx.writestr("word/styles.xml", styles_xml)
        docx.writestr("word/document.xml", document_xml)

if __name__ == "__main__":
    out = Path("/Users/saini/Downloads/TextileEd/pipeline_status_and_tech_stack.docx")
    create_styled_docx(out)
    print(f"Generated {out} successfully ({out.stat().st_size} bytes)")
