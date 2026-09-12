"""Storage service — Vercel Blob backend.

All JSON documents and binary uploads are written to Vercel Blob using 
hierarchical path keys that mirror the original filesystem layout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
import vercel.blob

from ..core.config import Settings, get_settings
from ..core.logging import get_logger
from ..core.exceptions import ProjectNotFoundError
from ..models.project import Project
from ..models.page import Page
from ..models.diagram import Diagram

if TYPE_CHECKING:
    from ..models.label import Label

logger = get_logger("services.storage")


class StorageService:
    """Vercel Blob storage for projects, pages, diagrams, labels and binary uploads.

    Path key convention:
        projects/{project_id}/project.json
        projects/{project_id}/pages/{page_id}/page.json
        projects/{project_id}/pages/{page_id}/{filename}   (uploads)
        projects/{project_id}/diagrams/{diagram_id}/diagram.json
        projects/{project_id}/labels/{label_id}.json
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        # Thin local cache for pipeline processing (OpenCV needs real file paths)
        self.workspace = Path("/tmp/tactile_ed_cache")
        self.workspace.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Private helpers — Blob backend
    # ------------------------------------------------------------------ #

    def _put_json(self, key: str, data: str) -> str:
        """Write a JSON string to Blob, return the public URL."""
        result = vercel.blob.put(key, data.encode("utf-8"), access="public",
                                 content_type="application/json", add_random_suffix=False)
        return result["url"] if isinstance(result, dict) else result.url

    def _put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        result = vercel.blob.put(key, data, access="public", content_type=content_type,
                                 add_random_suffix=False)
        return result["url"] if isinstance(result, dict) else result.url

    def _get_json(self, key: str) -> str | None:
        """Read a JSON string from Blob, or None if not found."""
        try:
            resp = vercel.blob.get(key)
            if resp is None:
                return None
            return resp.read().decode("utf-8")
        except Exception:
            return None

    def _get_bytes(self, key: str) -> bytes | None:
        try:
            resp = vercel.blob.get(key)
            if resp is None:
                return None
            return resp.read()
        except Exception:
            return None

    def _delete(self, key: str) -> None:
        try:
            vercel.blob.delete(key)
        except Exception:
            pass

    def _delete_prefix(self, prefix: str) -> None:
        """Delete all blobs under a prefix."""
        try:
            result = vercel.blob.list_objects(prefix=prefix)
            urls = [b.url if not isinstance(b, dict) else b["url"] for b in result.get("blobs", result.blobs)]
            if urls:
                vercel.blob.delete(urls)
        except Exception as e:
            logger.warning(f"Failed to delete blobs under {prefix}: {e}")

    def _list_prefixes(self, prefix: str, delimiter: str = "/") -> list[str]:
        """List immediate 'subdirectory' prefixes under *prefix*."""
        try:
            result = vercel.blob.list_objects(prefix=prefix)
            blobs = result.get("blobs", result.blobs) if hasattr(result, "get") else result.blobs
            seen: set[str] = set()
            for blob in blobs:
                pathname = blob["pathname"] if isinstance(blob, dict) else blob.pathname
                rest = pathname[len(prefix):]
                if delimiter in rest:
                    child = rest[: rest.index(delimiter)]
                else:
                    continue
                seen.add(child)
            return sorted(seen)
        except Exception:
            return []

    def _exists(self, key: str) -> bool:
        try:
            vercel.blob.head(key)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Project operations
    # ------------------------------------------------------------------ #

    def get_project_dir(self, project_id: str) -> Path:
        return self.workspace / "projects" / project_id

    def save_project(self, project: Project) -> Path:
        json_str = project.model_dump_json(indent=2)
        key = f"projects/{project.id}/project.json"
        self._put_json(key, json_str)
        logger.info(f"Saved project {project.id} to Blob")
        return self.get_project_dir(project.id)

    def load_project(self, project_id: str) -> Project:
        key = f"projects/{project_id}/project.json"
        data = self._get_json(key)
        if data is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return Project.model_validate_json(data)

    def list_projects(self) -> list[Project]:
        projects: list[Project] = []
        for pid in self._list_prefixes("projects/"):
            try:
                projects.append(self.load_project(pid))
            except Exception as e:
                logger.warning(f"Failed to load project {pid}: {e}")
        return projects

    def delete_project(self, project_id: str) -> None:
        if not self._exists(f"projects/{project_id}/project.json"):
            raise ProjectNotFoundError(f"Project {project_id} not found")
        self._delete_prefix(f"projects/{project_id}/")
        logger.info(f"Deleted project {project_id} from Blob")

    # ------------------------------------------------------------------ #
    # Page operations
    # ------------------------------------------------------------------ #

    def get_page_dir(self, project_id: str, page_id: str) -> Path:
        return self.get_project_dir(project_id) / "pages" / page_id

    def get_page_preprocessed_dir(self, project_id: str, page_id: str) -> Path:
        d = self.get_page_dir(project_id, page_id) / "preprocessed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_page(self, page: Page) -> Path:
        json_str = page.model_dump_json(indent=2)
        key = f"projects/{page.project_id}/pages/{page.id}/page.json"
        self._put_json(key, json_str)
        return self.get_page_dir(page.project_id, page.id)

    def load_page(self, project_id: str, page_id: str) -> Page:
        key = f"projects/{project_id}/pages/{page_id}/page.json"
        data = self._get_json(key)
        if data is None:
            raise ProjectNotFoundError(f"Page {page_id} not found in project {project_id}")
        return Page.model_validate_json(data)

    def list_pages(self, project_id: str) -> list[Page]:
        pages: list[Page] = []
        prefix = f"projects/{project_id}/pages/"
        for pgid in self._list_prefixes(prefix):
            try:
                pages.append(self.load_page(project_id, pgid))
            except Exception as e:
                logger.warning(f"Failed to load page {pgid}: {e}")
        return pages

    def save_upload(self, project_id: str, page_id: str, filename: str, content: bytes) -> Path:
        """Save an uploaded file to Blob and cache locally for processing."""
        safe_name = Path(filename).name
        key = f"projects/{project_id}/pages/{page_id}/{safe_name}"
        ext = Path(safe_name).suffix.lower()
        ct_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                  ".tiff": "image/tiff", ".tif": "image/tiff", ".pdf": "application/pdf"}
        ct = ct_map.get(ext, "application/octet-stream")
        
        self._put_bytes(key, content, content_type=ct)
        logger.info(f"Saved upload to Blob: {key} ({len(content)} bytes)")
        
        # Write to local cache for pipeline
        page_dir = self.get_page_dir(project_id, page_id)
        page_dir.mkdir(parents=True, exist_ok=True)
        local_path = page_dir / safe_name
        local_path.write_bytes(content)
        return local_path

    # ------------------------------------------------------------------ #
    # Diagram operations
    # ------------------------------------------------------------------ #

    def get_diagram_dir(self, project_id: str, diagram_id: str) -> Path:
        return self.get_project_dir(project_id) / "diagrams" / diagram_id

    def get_diagram_extracted_path(self, project_id: str, page_id: str, diagram_id: str) -> Path:
        diagram_dir = self.get_diagram_dir(project_id, diagram_id)
        diagram_dir.mkdir(parents=True, exist_ok=True)
        return diagram_dir / "extracted.png"

    def save_diagram(self, diagram: Diagram) -> Path:
        json_str = diagram.model_dump_json(indent=2)
        key = f"projects/{diagram.project_id}/diagrams/{diagram.id}/diagram.json"
        self._put_json(key, json_str)
        logger.info(f"Saved diagram {diagram.id} to Blob")
        return self.get_diagram_dir(diagram.project_id, diagram.id)

    def load_diagram(self, project_id: str, diagram_id: str) -> Diagram:
        key = f"projects/{project_id}/diagrams/{diagram_id}/diagram.json"
        data = self._get_json(key)
        if data is None:
            raise ProjectNotFoundError(f"Diagram {diagram_id} not found in project {project_id}")
        return Diagram.model_validate_json(data)

    def list_diagrams(self, project_id: str) -> list[Diagram]:
        diagrams: list[Diagram] = []
        prefix = f"projects/{project_id}/diagrams/"
        for did in self._list_prefixes(prefix):
            try:
                diagrams.append(self.load_diagram(project_id, did))
            except Exception:
                pass
        return diagrams

    # ------------------------------------------------------------------ #
    # Label operations
    # ------------------------------------------------------------------ #

    def get_label_dir(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "labels"

    def save_label(self, project_id: str, label: "Label") -> Path:
        json_str = label.model_dump_json(indent=2)
        key = f"projects/{project_id}/labels/{label.id}.json"
        self._put_json(key, json_str)
        return self.get_label_dir(project_id) / f"{label.id}.json"

    def load_label(self, project_id: str, label_id: str) -> "Label":
        from ..models.label import Label
        key = f"projects/{project_id}/labels/{label_id}.json"
        data = self._get_json(key)
        if data is None:
            raise FileNotFoundError(f"Label {label_id} not found")
        return Label.model_validate_json(data)

    @property
    def workspace_dir(self) -> Path:
        return self.workspace
