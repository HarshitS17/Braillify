"""
Constraint-based Braille label placement algorithm.

For each label, generates candidate positions around its target element,
scores them using a weighted penalty function, and selects the minimum-cost
valid placement.  When no valid placement exists the algorithm falls back to
leader lines and, ultimately, flags the label for manual review.

Penalty components
------------------
- ``distance_to_target``           – distance from label centre to target centre
- ``overlap_penalty``              – overlap with existing diagram geometry
- ``boundary_penalty``             – how far the label sticks outside canvas
- ``label_overlap_penalty``        – overlap with already-placed labels
- ``readability_penalty``          – labels too close together to read by touch

Placement cascade
-----------------
1. Try 8 candidate positions (top, bottom, left, right, 4 diagonals).
2. If best score exceeds threshold → try repositioned candidates (farther out).
3. If still bad → attach a leader line from the closest valid position.
4. If nothing works → flag for manual review.
"""

from dataclasses import dataclass
from ..models.diagram import DiagramElement, Diagram, BoundingBox, Point
from ..models.label import Label, LabelPlacement, LeaderLine


# ── Configuration ───────────────────────────────────────────────────────────

@dataclass
class PlacementConfig:
    """Tuneable parameters for the placement algorithm."""
    label_char_width: float = 8.0    # Approximate width per Braille cell (px)
    label_height: float = 14.0       # Approximate height of a Braille label (px)
    candidate_offset: float = 15.0   # Gap between target bbox edge and label
    far_offset_multiplier: float = 2.5  # Multiplier for repositioned candidates
    max_acceptable_score: float = 50.0  # Above this → try fallback strategies
    leader_line_threshold: float = 80.0  # Above this → attach a leader line
    canvas_width: float = 800.0
    canvas_height: float = 600.0
    # Penalty weights
    w_distance: float = 1.0
    w_overlap: float = 20.0
    w_boundary: float = 15.0
    w_label_overlap: float = 25.0
    w_readability: float = 5.0
    min_label_spacing: float = 10.0  # Minimum gap between labels for readability


# ── Geometry helpers ────────────────────────────────────────────────────────

def _bbox_from_element(el: DiagramElement) -> tuple[float, float, float, float]:
    """Return (x, y, w, h) for an element's geometry."""
    g = el.geometry
    if "x" in g and "w" in g:
        return g["x"], g["y"], g["w"], g["h"]
    if "cx" in g and "r" in g:
        r = g["r"]
        return g["cx"] - r, g["cy"] - r, 2 * r, 2 * r
    if "x1" in g:
        x1, y1, x2, y2 = g["x1"], g["y1"], g["x2"], g["y2"]
        return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
    if "points" in g:
        xs = [p["x"] for p in g["points"]]
        ys = [p["y"] for p in g["points"]]
        x_min, y_min = min(xs), min(ys)
        return x_min, y_min, max(xs) - x_min, max(ys) - y_min
    return 0, 0, 0, 0


def _rect_overlap(ax, ay, aw, ah, bx, by, bw, bh) -> float:
    """Compute area of overlap between two axis-aligned rectangles."""
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    return ix * iy


def _centre(x, y, w, h) -> tuple[float, float]:
    return x + w / 2, y + h / 2


# ── Candidate generation ───────────────────────────────────────────────────

def _generate_candidates(
    tx: float, ty: float, tw: float, th: float,
    lw: float, lh: float,
    offset: float,
) -> list[tuple[float, float]]:
    """Generate 8 candidate (x, y) positions around the target bbox."""
    cx, cy = _centre(tx, ty, tw, th)
    half_tw, half_th = tw / 2, th / 2

    return [
        # top-centre
        (cx - lw / 2, ty - lh - offset),
        # bottom-centre
        (cx - lw / 2, ty + th + offset),
        # left-centre
        (tx - lw - offset, cy - lh / 2),
        # right-centre
        (tx + tw + offset, cy - lh / 2),
        # top-left diagonal
        (tx - lw - offset, ty - lh - offset),
        # top-right diagonal
        (tx + tw + offset, ty - lh - offset),
        # bottom-left diagonal
        (tx - lw - offset, ty + th + offset),
        # bottom-right diagonal
        (tx + tw + offset, ty + th + offset),
    ]


# ── Scoring ─────────────────────────────────────────────────────────────────

def _score_candidate(
    lx: float, ly: float, lw: float, lh: float,
    tx: float, ty: float, tw: float, th: float,
    elements: list[DiagramElement],
    placed: list[tuple[float, float, float, float]],
    cfg: PlacementConfig,
) -> float:
    """Compute a placement cost (lower is better)."""
    tcx, tcy = _centre(tx, ty, tw, th)
    lcx, lcy = _centre(lx, ly, lw, lh)

    # 1. Distance to target
    dist = ((lcx - tcx) ** 2 + (lcy - tcy) ** 2) ** 0.5
    cost = cfg.w_distance * dist

    # 2. Overlap with diagram geometry
    for el in elements:
        ex, ey, ew, eh = _bbox_from_element(el)
        overlap = _rect_overlap(lx, ly, lw, lh, ex, ey, ew, eh)
        if overlap > 0:
            cost += cfg.w_overlap * (overlap / max(lw * lh, 1))

    # 3. Boundary penalty (canvas overflow)
    overshoot = 0.0
    if lx < 0:
        overshoot += abs(lx)
    if ly < 0:
        overshoot += abs(ly)
    if lx + lw > cfg.canvas_width:
        overshoot += (lx + lw) - cfg.canvas_width
    if ly + lh > cfg.canvas_height:
        overshoot += (ly + lh) - cfg.canvas_height
    cost += cfg.w_boundary * overshoot

    # 4. Label-overlap penalty
    for px, py, pw, ph in placed:
        overlap = _rect_overlap(lx, ly, lw, lh, px, py, pw, ph)
        if overlap > 0:
            cost += cfg.w_label_overlap * (overlap / max(lw * lh, 1))

    # 5. Readability penalty (too close to another label)
    for px, py, pw, ph in placed:
        gap_x = max(0, max(px, lx) - min(px + pw, lx + lw))
        gap_y = max(0, max(py, ly) - min(py + ph, ly + lh))
        gap = (gap_x ** 2 + gap_y ** 2) ** 0.5
        if gap < cfg.min_label_spacing:
            cost += cfg.w_readability * (cfg.min_label_spacing - gap)

    return cost


# ── Public API ──────────────────────────────────────────────────────────────

def place_labels(
    labels: list[Label],
    diagram: Diagram,
    config: PlacementConfig | None = None,
) -> list[Label]:
    """
    Place all *labels* on the *diagram* using constraint-based optimisation.

    Modifies each label's ``placement`` field in-place and returns the list.
    """
    cfg = config or PlacementConfig()

    if diagram.canvas:
        cfg.canvas_width = diagram.canvas.width
        cfg.canvas_height = diagram.canvas.height

    element_map = {el.id: el for el in diagram.elements}
    placed_rects: list[tuple[float, float, float, float]] = []  # (x, y, w, h)

    for label in labels:
        # Determine target bbox
        target_el = element_map.get(label.target_element_id or "")
        if target_el is None:
            # No target element → skip (or flag manual)
            label.metadata["placement_status"] = "no_target"
            continue

        tx, ty, tw, th = _bbox_from_element(target_el)
        braille_len = len(label.braille.braille_unicode) if label.braille.braille_unicode else len(label.text)
        lw = max(braille_len * cfg.label_char_width, 20)
        lh = cfg.label_height

        # --- Phase 1: standard candidates ---
        candidates = _generate_candidates(tx, ty, tw, th, lw, lh, cfg.candidate_offset)
        best_pos, best_score = candidates[0], float("inf")
        for cx, cy in candidates:
            s = _score_candidate(cx, cy, lw, lh, tx, ty, tw, th, diagram.elements, placed_rects, cfg)
            if s < best_score:
                best_score = s
                best_pos = (cx, cy)

        # --- Phase 2: repositioned (farther out) ---
        if best_score > cfg.max_acceptable_score:
            far_offset = cfg.candidate_offset * cfg.far_offset_multiplier
            far_candidates = _generate_candidates(tx, ty, tw, th, lw, lh, far_offset)
            for cx, cy in far_candidates:
                s = _score_candidate(cx, cy, lw, lh, tx, ty, tw, th, diagram.elements, placed_rects, cfg)
                if s < best_score:
                    best_score = s
                    best_pos = (cx, cy)

        # --- Phase 3: leader line ---
        needs_leader = best_score > cfg.leader_line_threshold
        leader = None
        if needs_leader:
            tcx, tcy = _centre(tx, ty, tw, th)
            lcx, lcy = _centre(best_pos[0], best_pos[1], lw, lh)
            leader = LeaderLine(
                start=Point(x=tcx, y=tcy),
                end=Point(x=lcx, y=lcy),
            )

        # --- Phase 4: flag for manual review if score is catastrophic ---
        if best_score > cfg.leader_line_threshold * 2:
            label.metadata["placement_status"] = "manual_review"
        else:
            label.metadata["placement_status"] = "auto"

        label.placement = LabelPlacement(
            position=Point(x=best_pos[0], y=best_pos[1]),
            width=lw,
            height=lh,
            leader_line=leader,
            placement_score=best_score,
        )

        placed_rects.append((best_pos[0], best_pos[1], lw, lh))

    return labels
