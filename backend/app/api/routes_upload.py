from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pathlib import Path
import uuid

from ..models.page import Page, PageMetadata, PageStatus
from ..models.project import ProjectStatus
from ..services.storage import StorageService
from ..core.config import get_settings, Settings
from ..core.logging import get_logger
from ..core.exceptions import FileFormatError
from ..pipeline.preprocessing import render_pdf_page
import cv2

logger = get_logger("api.upload")
router = APIRouter(prefix="/api", tags=["upload"])

def get_storage() -> StorageService:
    return StorageService()

@router.get("/projects/{project_id}/pages/{page_id}/image")
def get_page_image(
    project_id: str,
    page_id: str,
    storage: StorageService = Depends(get_storage),
):
    """Serve the page preview image.

    For PDFs this is the rasterized page (page_N.png) that the pipeline
    actually processed; for image uploads it is the original file. The
    frontend editor overlays detection boxes on this image, so it must be
    pixel-consistent with what detection ran on.
    """
    page = storage.load_page(project_id, page_id)
    page_dir = Path(page.original_path).parent if page.original_path else storage.get_page_dir(project_id, page_id)
    candidates = []
    if page.metadata.source_pdf_page is not None:
        candidates.append(page_dir / f"page_{page.metadata.source_pdf_page}.png")
    candidates.append(Path(page.original_path) if page.original_path else None)
    for candidate in candidates:
        if candidate and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="Page image not found")


@router.post("/projects/{project_id}/pages")
async def upload_page(
    project_id: str,
    file: UploadFile = File(...),
    pdf_page: int = Query(default=0, ge=0, description="Page number for PDF files (0-indexed)"),
    storage: StorageService = Depends(get_storage),
) -> dict:
    """Upload a textbook page image or PDF to a project.
    
    Supported formats: PNG, JPG/JPEG, TIFF, PDF.
    For PDFs, renders the specified page at the configured DPI.
    """
    settings = get_settings()
    
    # Validate project exists
    try:
        project = storage.load_project(project_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate filename and extension
    if not file.filename:
        raise HTTPException(status_code=422, detail="No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file format '{ext}'. Allowed: {sorted(settings.allowed_extensions)}",
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size} bytes). Maximum: {max_bytes} bytes ({settings.max_upload_size_mb} MB)",
        )
    
    if file_size == 0:
        raise HTTPException(status_code=422, detail="Empty file")
    
    # Create page
    page_id = str(uuid.uuid4())
    
    # Save the raw upload
    saved_path = storage.save_upload(project_id, page_id, file.filename, content)
    
    # Handle PDF: render the specified page to PNG
    is_pdf = ext == ".pdf"
    if is_pdf:
        try:
            rendered = render_pdf_page(saved_path, page_number=pdf_page, dpi=settings.default_dpi)
            png_path = saved_path.parent / f"page_{pdf_page}.png"
            cv2.imwrite(str(png_path), rendered)
            width, height = rendered.shape[1], rendered.shape[0]
            original_path = str(png_path)
            logger.info(f"Rendered PDF page {pdf_page} to {png_path}")
        except FileFormatError:
            raise
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to render PDF page: {e}")
    else:
        # For image files, read dimensions
        import numpy as np
        img_array = np.frombuffer(content, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=422, detail="Failed to decode image file")
        width, height = img.shape[1], img.shape[0]
        original_path = str(saved_path)
    
    # Create page metadata
    page = Page(
        id=page_id,
        project_id=project_id,
        status=PageStatus.UPLOADED,
        metadata=PageMetadata(
            original_filename=file.filename,
            file_format=ext.lstrip("."),
            file_size_bytes=file_size,
            width_px=width,
            height_px=height,
            dpi=settings.default_dpi if is_pdf else None,
            source_pdf_page=pdf_page if is_pdf else None,
        ),
        original_path=original_path,
    )
    storage.save_page(page)
    
    # Update project page count
    project.page_count = len(storage.list_pages(project_id))
    project.status = ProjectStatus.PROCESSING
    storage.save_project(project)
    
    logger.info(f"Uploaded page {page_id} to project {project_id}: {file.filename} ({width}x{height})")
    
    return {
        "page_id": page_id,
        "project_id": project_id,
        "filename": file.filename,
        "format": ext.lstrip("."),
        "width": width,
        "height": height,
        "file_size_bytes": file_size,
        "status": page.status.value,
    }


@router.get("/projects/{project_id}/pages")
async def list_pages(
    project_id: str,
    storage: StorageService = Depends(get_storage),
) -> list[dict]:
    """List all pages in a project."""
    try:
        storage.load_project(project_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")
    
    pages = storage.list_pages(project_id)
    return [
        {
            "page_id": p.id,
            "project_id": p.project_id,
            "filename": p.metadata.original_filename,
            "format": p.metadata.file_format,
            "width": p.metadata.width_px,
            "height": p.metadata.height_px,
            "status": p.status.value,
        }
        for p in pages
    ]
