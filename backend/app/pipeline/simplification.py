import cv2
import numpy as np
import math
from ..models.diagram import DiagramElement, ElementType
from ..models.simplification import SimplificationConfig

def get_geometry_stats(element: DiagramElement) -> dict:
    stats = {"area": 0.0, "length": 0.0, "bbox": (0.0, 0.0, 0.0, 0.0)}
    geom = element.geometry
    
    if element.type == ElementType.LINE:
        x1, y1 = geom.get("x1", 0), geom.get("y1", 0)
        x2, y2 = geom.get("x2", 0), geom.get("y2", 0)
        stats["length"] = math.hypot(x2 - x1, y2 - y1)
        stats["bbox"] = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        
    elif element.type in (ElementType.POLYGON, ElementType.CURVE):
        pts = geom.get("points", [])
        if not pts:
            return stats
        np_pts = np.array([[[p["x"], p["y"]]] for p in pts], dtype=np.float32)
        stats["area"] = cv2.contourArea(np_pts)
        is_closed = True if element.type == ElementType.POLYGON else False
        stats["length"] = cv2.arcLength(np_pts, is_closed)
        x, y, w, h = cv2.boundingRect(np_pts)
        stats["bbox"] = (float(x), float(y), float(w), float(h))
        
    elif element.type == ElementType.CIRCLE:
        r = geom.get("r", 0)
        cx = geom.get("cx", 0)
        cy = geom.get("cy", 0)
        stats["area"] = math.pi * (r ** 2)
        stats["length"] = 2 * math.pi * r
        stats["bbox"] = (cx - r, cy - r, 2 * r, 2 * r)
        
    elif element.type in (ElementType.TEXT_REGION, ElementType.FILLED_REGION):
        w = geom.get("w", 0)
        h = geom.get("h", 0)
        stats["area"] = w * h
        stats["length"] = 2 * (w + h)
        stats["bbox"] = (geom.get("x", 0), geom.get("y", 0), w, h)
        
    elif element.type == ElementType.ARROW:
        path = geom.get("path", {})
        if "x1" in path:
            x1, y1 = path.get("x1", 0), path.get("y1", 0)
            x2, y2 = path.get("x2", 0), path.get("y2", 0)
            stats["length"] = math.hypot(x2 - x1, y2 - y1)
            stats["bbox"] = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        elif "points" in path:
            pts = path.get("points", [])
            if pts:
                np_pts = np.array([[[p["x"], p["y"]]] for p in pts], dtype=np.float32)
                stats["length"] = cv2.arcLength(np_pts, False)
                x, y, w, h = cv2.boundingRect(np_pts)
                stats["bbox"] = (float(x), float(y), float(w), float(h))
    
    return stats

def compute_iou(bbox1: tuple, bbox2: tuple) -> float:
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
        
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    area1 = w1 * h1
    area2 = w2 * h2
    
    union_area = area1 + area2 - intersection_area
    if union_area <= 0:
        return 0.0
        
    return intersection_area / union_area

def simplify_diagram(elements: list[DiagramElement], config: SimplificationConfig) -> list[DiagramElement]:
    simplified_elements = []
    
    for el in elements:
        stats = get_geometry_stats(el)
        
        drop_reason = None
        if el.type in (ElementType.POLYGON, ElementType.FILLED_REGION, ElementType.CIRCLE, ElementType.TEXT_REGION):
            if stats["area"] > 0 and stats["area"] < config.minimum_feature_area:
                drop_reason = f"Area {stats['area']:.1f} < {config.minimum_feature_area}"
        elif el.type in (ElementType.LINE, ElementType.CURVE, ElementType.ARROW):
            if stats["length"] > 0 and stats["length"] < config.minimum_line_length:
                drop_reason = f"Length {stats['length']:.1f} < {config.minimum_line_length}"
                
        if drop_reason:
            # Drop the element
            print(f"Dropping {el.type} ({el.id}): {drop_reason}")
            continue
            
        new_el = el.model_copy(deep=True)
        new_el.simplified_from = el.id
        
        if new_el.type in (ElementType.POLYGON, ElementType.CURVE):
            pts = new_el.geometry.get("points", [])
            if len(pts) > 2:
                np_pts = np.array([[[p["x"], p["y"]]] for p in pts], dtype=np.float32)
                is_closed = (new_el.type == ElementType.POLYGON)
                epsilon = config.dp_epsilon_factor * cv2.arcLength(np_pts, is_closed)
                approx = cv2.approxPolyDP(np_pts, epsilon, is_closed)
                
                if len(approx) < len(pts):
                    old_len = len(pts)
                    new_len = len(approx)
                    new_el.geometry["points"] = [{"x": float(p[0][0]), "y": float(p[0][1])} for p in approx]
                    msg = f"DP Simplification: reduced vertices from {old_len} to {new_len}"
                    new_el.metadata["simplification_reason"] = msg
                    print(msg)
                    
        simplified_elements.append(new_el)
        
    final_elements = []
    dropped_indices = set()
    
    for i in range(len(simplified_elements)):
        if i in dropped_indices:
            continue
            
        el1 = simplified_elements[i]
        stats1 = get_geometry_stats(el1)
        bbox1 = stats1["bbox"]
        
        for j in range(i + 1, len(simplified_elements)):
            if j in dropped_indices:
                continue
                
            el2 = simplified_elements[j]
            if el1.type != el2.type:
                continue
                
            stats2 = get_geometry_stats(el2)
            bbox2 = stats2["bbox"]
            
            iou = compute_iou(bbox1, bbox2)
            
            if iou > config.duplicate_overlap_threshold:
                if el2.confidence > el1.confidence:
                    dropped_indices.add(i)
                    print(f"Deduplicating: Dropping {el1.id} in favor of {el2.id} (higher confidence)")
                    break
                else:
                    print(f"Deduplicating: Dropping {el2.id} in favor of {el1.id} (higher confidence or first)")
                    dropped_indices.add(j)
                    
        if i not in dropped_indices:
            final_elements.append(el1)
            
    return final_elements

def count_total_vertices(elements: list[DiagramElement]) -> int:
    """Total point count across all elements — the DP-simplification signal.
    POLYGON/CURVE contribute len(points); other element types contribute 1
    each, since they don't carry a variable-length point list."""
    total = 0
    for el in elements:
        if el.type in (ElementType.POLYGON, ElementType.CURVE):
            pts = el.geometry.get("points", [])
            total += max(len(pts), 1)
        elif el.type == ElementType.ARROW and "points" in el.geometry.get("path", {}):
            pts = el.geometry["path"].get("points", [])
            total += max(len(pts), 1)
        else:
            total += 1
    return total
