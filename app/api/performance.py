from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..models import PerformanceLog, database, User
from ..security import get_current_user
from ..schemas import PerformanceStart, PerformanceStop

router = APIRouter()


@router.post("/performance/start", response_model=dict)
async def api_start_performance(start: PerformanceStart, current_user: User = Depends(get_current_user)):
    log = PerformanceLog(
        user_id=current_user.id,
        batch_id=start.batch_id,
        start_time=datetime.utcnow(),
        end_time=None,
        items_processed=0,
    )
    database['performance_logs'].append(log)
    return {"log_id": log.id}


@router.post("/performance/stop", response_model=dict)
async def api_stop_performance(stop: PerformanceStop, current_user: User = Depends(get_current_user)):
    log = next((l for l in database['performance_logs'] if l.id == stop.log_id and l.user_id == current_user.id), None)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    log.end_time = datetime.utcnow()
    log.items_processed = stop.items_processed
    return {"duration": (log.end_time - log.start_time).total_seconds()}
