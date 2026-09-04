import json
import cv2
import numpy as np
from pathlib import Path
from app.pipeline.debug import DebugArtifactCollector

def test_debug_artifact_collector(tmp_path):
    collector = DebugArtifactCollector("test_proj", "test_diag", base_dir=str(tmp_path))
    
    # Save Image
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    p_img = collector.save_image("00_test", img)
    assert p_img.exists()
    
    # Save SVG
    svg = "<svg></svg>"
    p_svg = collector.save_svg("01_test", svg)
    assert p_svg.exists()
    assert p_svg.read_text() == svg
    
    # Save JSON
    data = {"key": "value"}
    p_json = collector.save_json("02_test", data)
    assert p_json.exists()
    assert json.loads(p_json.read_text()) == data
    
    # Generate Manifest
    p_man = collector.generate_manifest()
    assert p_man.exists()
    
    man_data = json.loads(p_man.read_text())
    assert man_data["project_id"] == "test_proj"
    assert man_data["artifact_count"] == 3
    assert len(man_data["artifacts"]) == 3
    
    stages = [a["stage"] for a in man_data["artifacts"]]
    assert "00_test" in stages
    assert "01_test" in stages
    assert "02_test" in stages
