"""
Debug artifact collector for pipeline observability.
Saves intermediate images, SVGs, and JSON data at each pipeline stage
to enable transparent academic evaluation and debugging.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np


class DebugArtifactCollector:
    """
    Collects debug snapshots during pipeline execution.
    
    Usage:
        collector = DebugArtifactCollector(project_id, diagram_id)
        collector.save_image("01_grayscale", gray_image)
        collector.save_json("02_elements", [el.model_dump() for el in elements])
        collector.save_svg("03_vectorized", svg_string)
        collector.generate_manifest()
    """
    
    def __init__(self, project_id: str, diagram_id: str, base_dir: str = "data"):
        self.project_id = project_id
        self.diagram_id = diagram_id
        self.debug_dir = Path(base_dir) / "projects" / project_id / "debug" / diagram_id
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts: list[dict[str, Any]] = []
        self.start_time = datetime.now(timezone.utc)
    
    def save_image(self, stage_name: str, image: np.ndarray) -> Path:
        """Save a NumPy image array as a PNG snapshot."""
        filename = f"{stage_name}.png"
        filepath = self.debug_dir / filename
        cv2.imwrite(str(filepath), image)
        self.artifacts.append({
            "stage": stage_name,
            "type": "image",
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return filepath
    
    def save_svg(self, stage_name: str, svg_string: str) -> Path:
        """Save an SVG string as a file."""
        filename = f"{stage_name}.svg"
        filepath = self.debug_dir / filename
        filepath.write_text(svg_string, encoding="utf-8")
        self.artifacts.append({
            "stage": stage_name,
            "type": "svg",
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return filepath
    
    def save_json(self, stage_name: str, data: Any) -> Path:
        """Save arbitrary data as a JSON file."""
        filename = f"{stage_name}.json"
        filepath = self.debug_dir / filename
        filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        self.artifacts.append({
            "stage": stage_name,
            "type": "json",
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return filepath
    
    def generate_manifest(self) -> Path:
        """Write a manifest.json summarizing all collected debug artifacts."""
        manifest = {
            "project_id": self.project_id,
            "diagram_id": self.diagram_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(self.artifacts),
            "artifacts": self.artifacts
        }
        filepath = self.debug_dir / "manifest.json"
        filepath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return filepath
