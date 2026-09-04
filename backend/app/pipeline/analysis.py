import cv2
import numpy as np
import uuid
from ..models.diagram import DiagramElement, ElementType, SemanticRole
from ..models.extraction import AnalysisConfig

def analyze_structure(image: np.ndarray, config: AnalysisConfig) -> list[DiagramElement]:
    """
    Analyzes the structure of an extracted diagram image to find geometric primitives.
    """
    elements = []
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Binarize and find edges
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 1. Text Regions — glyph clustering
    # Dilating the whole binary with a big kernel merges an entire dense diagram
    # into a single blob and hides the labels inside it. Instead, find small
    # connected components (glyphs) and cluster nearby glyphs into words/labels.
    cc_n, cc_labels, cc_stats, cc_centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    ih, iw = gray.shape[:2]

    glyphs = []
    for i in range(1, cc_n):
        x = int(cc_stats[i, cv2.CC_STAT_LEFT])
        y = int(cc_stats[i, cv2.CC_STAT_TOP])
        w = int(cc_stats[i, cv2.CC_STAT_WIDTH])
        h = int(cc_stats[i, cv2.CC_STAT_HEIGHT])
        area = int(cc_stats[i, cv2.CC_STAT_AREA])
        # Glyph-like: small, letter-sized, non-trivial ink. Diagram strokes
        # (long lines / large shapes) fail these bounds and are left untouched.
        if (
            w >= 2 and h >= 4
            and w <= max(14, 0.09 * iw)
            and h <= max(10, 0.16 * ih)
            and 3 <= area <= 0.03 * iw * ih
        ):
            glyphs.append({"x": x, "y": y, "w": w, "h": h, "label": i, "area": area})

    # Cluster glyphs into text lines (vertical overlap), then into words (gap).
    glyphs.sort(key=lambda g: (g["y"], g["x"]))
    lines: list[dict] = []
    for g in glyphs:
        placed = False
        for line in lines:
            overlap = min(g["y"] + g["h"], line["y"] + line["h"]) - max(g["y"], line["y"])
            if overlap > 0.5 * min(g["h"], line["h"]):
                line["glyphs"].append(g)
                line["x"] = min(line["x"], g["x"])
                line["y"] = min(line["y"], g["y"])
                line["x2"] = max(line["x2"], g["x"] + g["w"])
                line["y2"] = max(line["y2"], g["y"] + g["h"])
                placed = True
                break
        if not placed:
            lines.append({"x": g["x"], "y": g["y"], "x2": g["x"] + g["w"], "y2": g["y"] + g["h"],
                          "w": g["w"], "h": g["h"], "glyphs": [g]})

    text_regions: list[dict] = []
    for line in lines:
        words: list[list[dict]] = []
        current = [line["glyphs"][0]]
        for g in sorted(line["glyphs"], key=lambda gg: gg["x"])[1:]:
            prev = current[-1]
            gap = g["x"] - (prev["x"] + prev["w"])
            if gap <= 3.0 * max(1, min(prev["w"], g["w"])):
                current.append(g)
            else:
                words.append(current)
                current = [g]
        words.append(current)

        for word in words:
            x = min(g["x"] for g in word)
            y = min(g["y"] for g in word)
            x2 = max(g["x"] + g["w"] for g in word)
            y2 = max(g["y"] + g["h"] for g in word)
            w, h = x2 - x, y2 - y
            if len(word) < 2:
                # Single connected component: accept only if it is word-SHAPED.
                # Whole words often merge into one CC (touching glyphs, bold
                # print, scan blur); rejecting singletons silently dropped them.
                # Guards keep arrowheads / short strokes / specks out:
                # text-like aspect ratio, sane height, realistic ink density.
                if w < 15 or h < 8 or h > 0.06 * ih:
                    continue
                aspect = w / max(1.0, float(h))
                if aspect < 1.5 or aspect > 8.0:
                    continue
                # ink density uses the CC area of the singleton
                single = word[0]
                fill = single["area"] / max(1.0, float(w * h))
                if fill < 0.15 or fill > 0.85:
                    continue
            if h <= max(10, 0.16 * ih) and w >= 12 and w <= 0.6 * iw:
                text_regions.append({"x": x, "y": y, "w": w, "h": h})

    masked_binary = binary.copy()
    masked_gray = gray.copy()
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    for tr in text_regions:
        x, y, w, h = tr["x"], tr["y"], tr["w"], tr["h"]
        element = DiagramElement(
            type=ElementType.TEXT_REGION,
            geometry={"x": float(x), "y": float(y), "w": float(w), "h": float(h)},
            semantic_role=SemanticRole.LABEL,
            confidence=0.9
        )
        elements.append(element)
        # Mask the label rect out of geometry/edges so it is not re-detected
        # as lines/shapes.
        cv2.rectangle(masked_binary, (x, y), (x + w, y + h), 0, -1)
        cv2.rectangle(masked_gray, (x, y), (x + w, y + h), 255, -1)
        cv2.rectangle(edges, (x, y), (x + w, y + h), 0, -1)
            
    # 2. (Removed) Filled Regions — previously emitted bbox-only FILLED_REGIONs
    # whose geometry had no `points`, making them invisible in SVG/PDF/canvas and
    # duplicating the contour polygons found in step 5. Contour polygons (step 5)
    # already represent every external outline of the masked binary, so emitting
    # a second, non-renderable representation caused clutter and invisible layers.
    
    # 3. Detect Lines (HoughLinesP)
    lines = cv2.HoughLinesP(
        edges,
        config.line_rho,
        config.line_theta,
        config.line_threshold,
        minLineLength=config.line_min_length,
        maxLineGap=config.line_max_gap
    )
    
    if lines is not None:
        if len(lines.shape) == 3:
            lines = lines.reshape(-1, 4)
        for line in lines:
            x1, y1, x2, y2 = line
            element = DiagramElement(
                type=ElementType.LINE,
                geometry={"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)},
                semantic_role=SemanticRole.STRUCTURE,
                confidence=0.9
            )
            elements.append(element)
            
    # 4. Detect Circles (HoughCircles)
    blurred = cv2.medianBlur(masked_gray, 5)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=config.circle_dp,
        minDist=config.circle_min_dist,
        param1=config.circle_param1,
        param2=config.circle_param2,
        minRadius=config.circle_min_radius,
        maxRadius=config.circle_max_radius
    )
    
    detected_circles = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            x_c, y_c, r = i[0], i[1], i[2]
            detected_circles.append((float(x_c), float(y_c), float(r)))
            element = DiagramElement(
                type=ElementType.CIRCLE,
                geometry={"cx": float(x_c), "cy": float(y_c), "r": float(r)},
                semantic_role=SemanticRole.STRUCTURE,
                confidence=0.85
            )
            elements.append(element)
            
    # 5. Detect Polygons and Curves
    contours, _ = cv2.findContours(masked_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        
        epsilon = config.approx_epsilon_factor * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        num_vertices = len(approx)
        
        if num_vertices >= 3:
            is_circle = False
            if num_vertices >= config.curve_min_vertices:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                    for (cir_x, cir_y, cir_r) in detected_circles:
                        if (cx - cir_x)**2 + (cy - cir_y)**2 < cir_r**2:
                            is_circle = True
                            break
            
            points = [{"x": float(p[0][0]), "y": float(p[0][1])} for p in approx]
            
            if num_vertices >= config.curve_min_vertices and not is_circle:
                element_type = ElementType.CURVE
            else:
                element_type = ElementType.POLYGON
                # Skip large irrelevant polygons or very small noise, but keep small triangles for arrows
                if element_type == ElementType.POLYGON and area < 10 and num_vertices > 4:
                    continue
                
            element = DiagramElement(
                type=element_type,
                geometry={"points": points, "area": float(area)},
                semantic_role=SemanticRole.STRUCTURE,
                confidence=0.8
            )
            elements.append(element)
            
    # 6. Arrows heuristic
    paths = []
    triangles = []
    for el in elements:
        if el.type in (ElementType.LINE, ElementType.CURVE):
            paths.append(el)
        elif el.type == ElementType.POLYGON:
            pts = el.geometry.get("points", [])
            area = el.geometry.get("area", 0)
            if 3 <= len(pts) <= 4 and area < config.arrow_max_head_area:
                triangles.append(el)
                
    arrows = []
    to_remove = set()
    
    for tri in triangles:
        pts = tri.geometry["points"]
        cx = sum(p["x"] for p in pts) / len(pts)
        cy = sum(p["y"] for p in pts) / len(pts)
        
        matched_path = None
        for path in paths:
            if path.id in to_remove:
                continue
                
            if path.type == ElementType.LINE:
                endpoints = [
                    (path.geometry["x1"], path.geometry["y1"]),
                    (path.geometry["x2"], path.geometry["y2"])
                ]
            else:
                path_pts = path.geometry["points"]
                endpoints = [
                    (path_pts[0]["x"], path_pts[0]["y"]),
                    (path_pts[-1]["x"], path_pts[-1]["y"])
                ]
                
            dist1 = np.hypot(cx - endpoints[0][0], cy - endpoints[0][1])
            dist2 = np.hypot(cx - endpoints[1][0], cy - endpoints[1][1])
            
            if min(dist1, dist2) < 20.0:
                matched_path = path
                break
                
        if matched_path:
            arrow_geom = {
                "head": tri.geometry["points"],
                "path": matched_path.geometry
            }
            arrow_el = DiagramElement(
                type=ElementType.ARROW,
                geometry=arrow_geom,
                semantic_role=SemanticRole.ARROW,
                confidence=0.9
            )
            arrows.append(arrow_el)
            to_remove.add(tri.id)
            to_remove.add(matched_path.id)
            
    final_elements = [el for el in elements if el.id not in to_remove]
    final_elements.extend(arrows)
    
    return final_elements
