from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..models import User, create_user, database
from ..security import get_current_user, get_password_hash
from ..schemas import UserCreate

router = APIRouter()


@router.post("/users", response_model=dict)
async def api_create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    password_hash = get_password_hash(user.password)
    created = create_user(user.username, password_hash, user.role)
    return {"id": created.id, "username": created.username, "role": created.role}


@router.get("/users", response_model=List[dict])
async def api_get_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    users = [
        {"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active}
        for u in database['users']
    ]
    return users
