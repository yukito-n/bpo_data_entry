from fastapi import APIRouter, Depends, HTTPException

from ..models import User, create_batch, get_batch, update_batch_status
from ..security import get_current_user
from ..schemas import BatchCreate, StatusUpdate

router = APIRouter()


@router.post("/batches", response_model=dict)
async def api_create_batch(batch: BatchCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    created = create_batch(batch.project_id, batch.reception_date, batch.due_date, batch.initial_volume)
    return {"id": created.id, "status": created.status}


@router.put("/batches/{batch_id}/status")
async def api_update_status(batch_id: int, status: StatusUpdate, current_user: User = Depends(get_current_user)):
    batch = get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    update_batch_status(batch, status.status)
    return {"status": batch.status}
