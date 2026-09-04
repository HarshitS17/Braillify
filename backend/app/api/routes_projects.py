from fastapi import APIRouter, HTTPException, Depends
from ..models.project import Project, ProjectCreate, ProjectSummary
from ..services.storage import StorageService
from ..core.logging import get_logger

logger = get_logger("api.projects")
router = APIRouter(prefix="/api/projects", tags=["projects"])

def get_storage() -> StorageService:
    return StorageService()

@router.post("", response_model=ProjectSummary, status_code=201)
async def create_project(data: ProjectCreate, storage: StorageService = Depends(get_storage)) -> ProjectSummary:
    project = Project(name=data.name, description=data.description)
    project.workspace_path = str(storage.get_project_dir(project.id))
    storage.save_project(project)
    logger.info(f"Created project: {project.id} - {project.name}")
    return ProjectSummary(**project.model_dump())

@router.get("", response_model=list[ProjectSummary])
async def list_projects(storage: StorageService = Depends(get_storage)) -> list[ProjectSummary]:
    projects = storage.list_projects()
    return [ProjectSummary(**p.model_dump()) for p in projects]

@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(project_id: str, storage: StorageService = Depends(get_storage)) -> ProjectSummary:
    try:
        project = storage.load_project(project_id)
        return ProjectSummary(**project.model_dump())
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, storage: StorageService = Depends(get_storage)) -> None:
    try:
        storage.delete_project(project_id)
        logger.info(f"Deleted project: {project_id}")
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")
