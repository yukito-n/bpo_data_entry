from fastapi import APIRouter, Depends, HTTPException

from ..models import User, create_project
from ..security import get_current_user
from ..schemas import ProjectCreate

router = APIRouter()


@router.post("/projects", response_model=dict)
async def api_create_project(project: ProjectCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    created = create_project(project.name, project.client_name)
    return {"id": created.id, "name": created.name}
