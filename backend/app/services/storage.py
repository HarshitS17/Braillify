import json
import shutil
from pathlib import Path
from ..core.config import Settings, get_settings
from ..core.logging import get_logger
from ..core.exceptions import ProjectNotFoundError
from ..models.project import Project
from ..models.page import Page
from ..models.diagram import Diagram

logger = get_logger("services.storage")


class StorageService:
    """Filesystem-based storage for projects, pages, and artifacts.
    
    Directory structure:
    workspace/
      projects/
        {project_id}/
          project.json
          pages/
            {page_id}/
              original.{ext}
              preprocessed/
                grayscale.png
                denoised.png
                thresholded.png
                ...
              page.json
          diagrams/
            {diagram_id}/
              ...
    """
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.workspace = self.settings.workspace_dir
        self.projects_dir = self.workspace / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Project operations ---
    
    def get_project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id
    
    def save_project(self, project: Project) -> Path:
        project_dir = self.get_project_dir(project.id)
        project_dir.mkdir(parents=True, exist_ok=True)
        project_file = project_dir / "project.json"
        project_file.write_text(project.model_dump_json(indent=2))
        logger.info(f"Saved project {project.id} to {project_file}")
        return project_dir
    
    def load_project(self, project_id: str) -> Project:
        project_file = self.get_project_dir(project_id) / "project.json"
        if not project_file.exists():
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return Project.model_validate_json(project_file.read_text())
    
    def list_projects(self) -> list[Project]:
        projects = []
        if not self.projects_dir.exists():
            return projects
        for project_dir in sorted(self.projects_dir.iterdir()):
            project_file = project_dir / "project.json"
            if project_file.exists():
                try:
                    projects.append(Project.model_validate_json(project_file.read_text()))
                except Exception as e:
                    logger.warning(f"Failed to load project from {project_dir}: {e}")
        return projects
    
    def delete_project(self, project_id: str) -> None:
        project_dir = self.get_project_dir(project_id)
        if not project_dir.exists():
            raise ProjectNotFoundError(f"Project {project_id} not found")
        shutil.rmtree(project_dir)
        logger.info(f"Deleted project {project_id}")
    
    # --- Page operations ---
    
    def get_page_dir(self, project_id: str, page_id: str) -> Path:
        return self.get_project_dir(project_id) / "pages" / page_id
    
    def get_page_preprocessed_dir(self, project_id: str, page_id: str) -> Path:
        d = self.get_page_dir(project_id, page_id) / "preprocessed"
        d.mkdir(parents=True, exist_ok=True)
        return d
    
    def save_page(self, page: Page) -> Path:
        page_dir = self.get_page_dir(page.project_id, page.id)
        page_dir.mkdir(parents=True, exist_ok=True)
        page_file = page_dir / "page.json"
        page_file.write_text(page.model_dump_json(indent=2))
        return page_dir
    
    def load_page(self, project_id: str, page_id: str) -> Page:
        page_file = self.get_page_dir(project_id, page_id) / "page.json"
        if not page_file.exists():
            raise ProjectNotFoundError(f"Page {page_id} not found in project {project_id}")
        return Page.model_validate_json(page_file.read_text())
    
    def list_pages(self, project_id: str) -> list[Page]:
        pages_dir = self.get_project_dir(project_id) / "pages"
        pages = []
        if not pages_dir.exists():
            return pages
        for page_dir in sorted(pages_dir.iterdir()):
            page_file = page_dir / "page.json"
            if page_file.exists():
                try:
                    pages.append(Page.model_validate_json(page_file.read_text()))
                except Exception as e:
                    logger.warning(f"Failed to load page from {page_dir}: {e}")
        return pages
    
    def save_upload(self, project_id: str, page_id: str, filename: str, content: bytes) -> Path:
        """Save an uploaded file to the page directory."""
        page_dir = self.get_page_dir(project_id, page_id)
        page_dir.mkdir(parents=True, exist_ok=True)
        # Sanitize filename
        safe_name = Path(filename).name  # strip any directory traversal
        file_path = page_dir / safe_name
        file_path.write_bytes(content)
        logger.info(f"Saved upload: {file_path} ({len(content)} bytes)")
        return file_path

    # --- Diagram operations ---
    
    def get_diagram_dir(self, project_id: str, diagram_id: str) -> Path:
        return self.get_project_dir(project_id) / "diagrams" / diagram_id

    def get_diagram_extracted_path(self, project_id: str, page_id: str, diagram_id: str) -> Path:
        diagram_dir = self.get_diagram_dir(project_id, diagram_id)
        diagram_dir.mkdir(parents=True, exist_ok=True)
        return diagram_dir / "extracted.png"

    def save_diagram(self, diagram: Diagram) -> Path:
        diagram_dir = self.get_diagram_dir(diagram.project_id, diagram.id)
        diagram_dir.mkdir(parents=True, exist_ok=True)
        diagram_file = diagram_dir / "diagram.json"
        diagram_file.write_text(diagram.model_dump_json(indent=2))
        logger.info(f"Saved diagram {diagram.id} to {diagram_file}")
        return diagram_dir

    def load_diagram(self, project_id: str, diagram_id: str) -> Diagram:
        diagram_file = self.get_diagram_dir(project_id, diagram_id) / "diagram.json"
        if not diagram_file.exists():
            raise ProjectNotFoundError(f"Diagram {diagram_id} not found in project {project_id}")
        return Diagram.model_validate_json(diagram_file.read_text())

    def list_diagrams(self, project_id: str) -> list[Diagram]:
        diagrams_dir = self.get_project_dir(project_id) / "diagrams"
        diagrams = []
        if not diagrams_dir.exists():
            return diagrams
        for diagram_dir in sorted(diagrams_dir.iterdir()):
            diagram_file = diagram_dir / "diagram.json"
            if diagram_file.exists():
                try:
                    diagrams.append(Diagram.model_validate_json(diagram_file.read_text()))
                except Exception as e:
                    pass
        return diagrams

    # --- Label operations ---
    
    def get_label_dir(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "labels"
        
    def save_label(self, project_id: str, label) -> Path:
        label_dir = self.get_label_dir(project_id)
        label_dir.mkdir(parents=True, exist_ok=True)
        label_file = label_dir / f"{label.id}.json"
        label_file.write_text(label.model_dump_json(indent=2))
        return label_file
        
    def load_label(self, project_id: str, label_id: str):
        from ..models.label import Label
        label_file = self.get_label_dir(project_id) / f"{label_id}.json"
        if not label_file.exists():
            raise FileNotFoundError(f"Label {label_id} not found")
        return Label.model_validate_json(label_file.read_text())
