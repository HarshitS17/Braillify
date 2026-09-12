"""Lightweight owner-token authentication.

This is NOT a full user-account system — it's a simple opaque token
generated on project creation and required for mutating operations on
that project.  Closes the gap where any caller with a project ID could
delete it.
"""

from fastapi import Header, HTTPException, Depends
from ..services.storage import StorageService
from ..core.exceptions import ProjectNotFoundError


def verify_owner_token(
    project_id: str,
    token: str,
    storage: StorageService,
) -> None:
    """Raise 403 if *token* does not match the project's owner_token."""
    try:
        project = storage.load_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_token != token:
        raise HTTPException(status_code=403, detail="Invalid owner token")
