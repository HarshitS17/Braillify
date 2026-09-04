from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..models.diagram import Diagram
from ..models.extraction import ExtractionConfig, AnalysisConfig
from ..models.simplification import SimplificationConfig
from ..services.storage import StorageService
from ..services.workflow import WorkflowService, WorkflowConfig, PipelineStage
from ..core.exceptions import ProjectNotFoundError

router = APIRouter(prefix="/api/projects/{project_id}/pages/{page_id}/diagrams/{diagram_id}/workflow", tags=["Workflow"])

def get_storage():
    return StorageService()

class WorkflowRequest(BaseModel):
    start_stage: PipelineStage = PipelineStage.EXTRACT
    end_stage: PipelineStage = PipelineStage.PLACE
    extraction_config: ExtractionConfig = ExtractionConfig()
    analysis_config: AnalysisConfig = AnalysisConfig()
    simplification_config: SimplificationConfig = SimplificationConfig()
    debug: bool = False

@router.post("", response_model=Diagram)
async def run_workflow_endpoint(
    project_id: str,
    page_id: str,
    diagram_id: str,
    request: WorkflowRequest,
    storage: StorageService = Depends(get_storage)
):
    try:
        config = WorkflowConfig(
            extraction=request.extraction_config,
            analysis=request.analysis_config,
            simplification=request.simplification_config
        )
        service = WorkflowService(storage)
        diagram = service.run_pipeline(
            project_id=project_id,
            page_id=page_id,
            diagram_id=diagram_id,
            start_stage=request.start_stage,
            end_stage=request.end_stage,
            config=config,
            debug=request.debug
        )
        return diagram
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
