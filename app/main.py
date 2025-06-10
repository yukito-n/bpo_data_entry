from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from .models import User, Project, Batch, PerformanceLog, database, get_user_by_username
from .models import create_user, get_user, update_batch_status, create_project, create_batch
from .models import get_batch, log_performance

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()


@app.get("/")
def read_root():
    """Simple heartbeat endpoint."""
    return {"message": "BPO API is running"}


@app.on_event("startup")
def create_default_admin():
    """Ensure an admin user exists so the API can be used immediately."""
    if not get_user_by_username("admin"):
        create_user("admin", get_password_hash("admin123"), "Admin")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str


class ProjectCreate(BaseModel):
    name: str
    client_name: str


class BatchCreate(BaseModel):
    project_id: int
    reception_date: datetime
    due_date: datetime
    initial_volume: int


class StatusUpdate(BaseModel):
    status: str


class PerformanceStart(BaseModel):
    batch_id: int


class PerformanceStop(BaseModel):
    batch_id: int
    items_processed: int
    log_id: int


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=dict)
async def api_create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    password_hash = get_password_hash(user.password)
    created = create_user(user.username, password_hash, user.role)
    return {"id": created.id, "username": created.username, "role": created.role}


@app.get("/users", response_model=List[dict])
async def api_get_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    users = [
        {"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active}
        for u in database['users']
    ]
    return users


@app.post("/projects", response_model=dict)
async def api_create_project(project: ProjectCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    created = create_project(project.name, project.client_name)
    return {"id": created.id, "name": created.name}


@app.post("/batches", response_model=dict)
async def api_create_batch(batch: BatchCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    created = create_batch(batch.project_id, batch.reception_date, batch.due_date, batch.initial_volume)
    return {"id": created.id, "status": created.status}


@app.put("/batches/{batch_id}/status")
async def api_update_status(batch_id: int, status: StatusUpdate, current_user: User = Depends(get_current_user)):
    batch = get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    update_batch_status(batch, status.status)
    return {"status": batch.status}


@app.post("/performance/start", response_model=dict)
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


@app.post("/performance/stop", response_model=dict)
async def api_stop_performance(stop: PerformanceStop, current_user: User = Depends(get_current_user)):
    log = next((l for l in database['performance_logs'] if l.id == stop.log_id and l.user_id == current_user.id), None)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    log.end_time = datetime.utcnow()
    log.items_processed = stop.items_processed
    return {"duration": (log.end_time - log.start_time).total_seconds()}
