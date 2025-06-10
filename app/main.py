from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import csv
import io
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from contextlib import asynccontextmanager

from .models import (
    User,
    Project,
    Batch,
    PerformanceLog,
    Assignment,
    Shift,
    QualityLog,
    Issue,
    Article,
    database,
    AuditLog,
    IntegrationKey,
    get_user_by_username,
)
from .models import (
    create_user,
    get_user,
    update_user,
    deactivate_user,
    update_batch_status,
    create_project,
    create_batch,
    assign_operator,
    get_assignments_for_user,
    create_shift,
    get_shifts_for_user,
    log_quality,
    error_counts_by_operator,
    error_counts_by_project,
    create_issue,
    update_issue_status,
    get_issues,
    create_article,
    list_articles,
    log_audit,
    create_api_key,
    get_api_key,
    get_audit_logs,
)
from .models import get_batch, log_performance

SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
APP_ENV = os.getenv("APP_ENV", "development")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple RBAC permissions
PERMISSIONS = {
    "Admin": {
        "create_user",
        "edit_user",
        "deactivate_user",
        "view_users",
        "create_project",
        "create_batch",
        "assign_operator",
        "create_shift",
        "view_dashboard",
        "view_quality",
        "generate_report",
        "create_article",
        "manage_issue",
        "create_api_key",
        "view_audit",
        "export_workhours",
    },
    "Manager": {
        "create_project",
        "create_batch",
        "assign_operator",
        "create_shift",
        "view_dashboard",
        "view_quality",
        "generate_report",
        "create_article",
        "manage_issue",
    },
    "Operator": {
        "create_issue",
    },
}


def check_permission(user: User, action: str):
    allowed = PERMISSIONS.get(user.role, set())
    if action not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized")


async def require_api_key(x_api_key: str = Header(...)) -> IntegrationKey:
    key = get_api_key(x_api_key)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure an admin user exists on startup."""
    if not get_user_by_username("admin"):
        create_user("admin", get_password_hash("admin123"), "Admin")
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
if APP_ENV.lower() == "test":
    # Serve additional pages when running in a test environment
    app.mount("/test", StaticFiles(directory="app/static/test", html=True), name="test")


@app.get("/ui")
def serve_ui():
    """Return a simple HTML interface."""
    return FileResponse("app/static/index.html")


@app.get("/")
def read_root():
    """Simple heartbeat endpoint."""
    return {"message": "BPO API is running"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str


class Register(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


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


class AssignmentCreate(BaseModel):
    user_id: int
    batch_id: int


class ShiftCreate(BaseModel):
    user_id: int
    start_time: datetime
    end_time: datetime


class QualityCreate(BaseModel):
    batch_id: int
    operator_id: int
    error_type: str


class IssueCreate(BaseModel):
    batch_id: int
    description: str
    assigned_to: int


class IssueUpdate(BaseModel):
    status: str


class ArticleCreate(BaseModel):
    title: str
    content: str


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


@app.post("/register", response_model=dict)
async def api_register(user: Register):
    if get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    password_hash = get_password_hash(user.password)
    created = create_user(user.username, password_hash, "Operator")
    return {"id": created.id, "username": created.username, "role": created.role}


@app.post("/users", response_model=dict)
async def api_create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_user")
    password_hash = get_password_hash(user.password)
    created = create_user(user.username, password_hash, user.role)
    log_audit(current_user.id, f"create_user:{created.id}")
    return {"id": created.id, "username": created.username, "role": created.role}


@app.patch("/users/{user_id}", response_model=dict)
async def api_update_user(user_id: int, data: UserUpdate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "edit_user")
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    password_hash = get_password_hash(data.password) if data.password else None
    update_user(user, username=data.username, password_hash=password_hash, role=data.role)
    log_audit(current_user.id, f"edit_user:{user_id}")
    return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}


@app.post("/users/{user_id}/deactivate", response_model=dict)
async def api_deactivate_user(user_id: int, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "deactivate_user")
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    deactivate_user(user)
    log_audit(current_user.id, f"deactivate_user:{user_id}")
    return {"id": user.id, "is_active": user.is_active}


@app.get("/users", response_model=List[dict])
async def api_get_users(current_user: User = Depends(get_current_user)):
    check_permission(current_user, "view_users")
    users = [
        {"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active}
        for u in database['users']
    ]
    return users


@app.post("/projects", response_model=dict)
async def api_create_project(project: ProjectCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_project")
    created = create_project(project.name, project.client_name)
    log_audit(current_user.id, f"create_project:{created.id}")
    return {"id": created.id, "name": created.name}


@app.get("/projects", response_model=List[dict])
async def api_list_projects(current_user: User = Depends(get_current_user)):
    """Return all projects."""
    return [
        {"id": p.id, "name": p.name, "client_name": p.client_name}
        for p in database["projects"]
    ]


@app.post("/batches", response_model=dict)
async def api_create_batch(batch: BatchCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_batch")
    created = create_batch(batch.project_id, batch.reception_date, batch.due_date, batch.initial_volume)
    log_audit(current_user.id, f"create_batch:{created.id}")
    return {"id": created.id, "status": created.status}


@app.put("/batches/{batch_id}/status")
async def api_update_status(batch_id: int, status: StatusUpdate, current_user: User = Depends(get_current_user)):
    batch = get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    update_batch_status(batch, status.status)
    return {"status": batch.status}


@app.get("/batches", response_model=List[dict])
async def api_list_batches(project_id: Optional[int] = None, current_user: User = Depends(get_current_user)):
    """Return batches, optionally filtered by project."""
    batches = database["batches"]
    if project_id is not None:
        batches = [b for b in batches if b.project_id == project_id]
    return [
        {
            "id": b.id,
            "project_id": b.project_id,
            "status": b.status,
            "reception_date": b.reception_date.isoformat(),
            "due_date": b.due_date.isoformat(),
            "initial_volume": b.initial_volume,
        }
        for b in batches
    ]


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


@app.post("/assignments", response_model=dict)
async def api_assign_operator(assignment: AssignmentCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "assign_operator")
    created = assign_operator(assignment.user_id, assignment.batch_id)
    return {"id": created.id, "user_id": created.user_id, "batch_id": created.batch_id}


@app.get("/assignments/{user_id}", response_model=List[dict])
async def api_get_assignments(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["Admin", "Manager"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    assigns = get_assignments_for_user(user_id)
    return [{"id": a.id, "user_id": a.user_id, "batch_id": a.batch_id} for a in assigns]


@app.post("/shifts", response_model=dict)
async def api_create_shift(shift: ShiftCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_shift")
    created = create_shift(shift.user_id, shift.start_time, shift.end_time)
    log_audit(current_user.id, f"create_shift:{created.id}")
    return {"id": created.id}


@app.get("/shifts", response_model=List[dict])
async def api_get_shifts(user_id: Optional[int] = None, current_user: User = Depends(get_current_user)):
    if user_id is not None:
        if current_user.role not in ["Admin", "Manager"] and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        user_id = current_user.id
    shifts = get_shifts_for_user(user_id)
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
        }
        for s in shifts
    ]


@app.post("/quality", response_model=dict)
async def api_log_quality(q: QualityCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "view_quality")
    created = log_quality(q.batch_id, q.operator_id, q.error_type)
    return {"id": created.id}


@app.get("/quality/stats", response_model=dict)
async def api_quality_stats(current_user: User = Depends(get_current_user)):
    check_permission(current_user, "view_quality")
    return {
        "by_operator": error_counts_by_operator(),
        "by_project": error_counts_by_project(),
    }


@app.post("/issues", response_model=dict)
async def api_create_issue(issue: IssueCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_issue")
    created = create_issue(issue.batch_id, issue.description, current_user.id, issue.assigned_to)
    return {"id": created.id}


@app.post("/issues/{issue_id}/status", response_model=dict)
async def api_update_issue_status(issue_id: int, data: IssueUpdate, current_user: User = Depends(get_current_user)):
    issue = next((i for i in database['issues'] if i.id == issue_id), None)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if current_user.id != issue.assigned_to:
        check_permission(current_user, "manage_issue")
    update_issue_status(issue, data.status)
    return {"status": issue.status}


@app.get("/issues", response_model=List[dict])
async def api_get_issues_endpoint(current_user: User = Depends(get_current_user)):
    check_permission(current_user, "manage_issue")
    issues = get_issues(current_user.id if current_user.role == "Manager" else None)
    return [
        {
            "id": i.id,
            "batch_id": i.batch_id,
            "description": i.description,
            "status": i.status,
            "assigned_to": i.assigned_to,
        }
        for i in issues
    ]


@app.post("/articles", response_model=dict)
async def api_create_article(article: ArticleCreate, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_article")
    created = create_article(article.title, article.content)
    return {"id": created.id}


@app.get("/articles", response_model=List[dict])
async def api_list_articles(current_user: User = Depends(get_current_user)):
    arts = list_articles()
    return [
        {"id": a.id, "title": a.title, "content": a.content}
        for a in arts
    ]


@app.get("/report")
async def api_report(month: str, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "generate_report")
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1)
    if mon == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, mon + 1, 1)
    user_stats = {}
    for log in database['performance_logs']:
        if log.end_time and start <= log.end_time < end:
            hours = (log.end_time - log.start_time).total_seconds() / 3600
            stats = user_stats.setdefault(log.user_id, {"items": 0, "hours": 0.0, "errors": 0})
            stats["items"] += log.items_processed
            stats["hours"] += hours
    for q in database['quality_logs']:
        stats = user_stats.setdefault(q.operator_id, {"items": 0, "hours": 0.0, "errors": 0})
        stats["errors"] += 1
    HOURLY_RATE = 10
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "items", "hours", "errors", "cost"])
    for uid, s in user_stats.items():
        cost = s["hours"] * HOURLY_RATE
        writer.writerow([uid, s["items"], f"{s['hours']:.2f}", s["errors"], f"{cost:.2f}"])
    output.seek(0)
    log_audit(current_user.id, "generate_report")
    return StreamingResponse(output, media_type="text/csv")


@app.get("/dashboard", response_model=dict)
async def api_dashboard(current_user: User = Depends(get_current_user)):
    check_permission(current_user, "view_dashboard")
    daily_totals = {}
    for log in database['performance_logs']:
        if log.end_time:
            day = log.end_time.date().isoformat()
            daily_totals[day] = daily_totals.get(day, 0) + log.items_processed

    batch_stats = {}
    for log in database['performance_logs']:
        if log.end_time:
            duration = (log.end_time - log.start_time).total_seconds()
            data = batch_stats.setdefault(log.batch_id, {"time": 0, "items": 0})
            data["time"] += duration
            data["items"] += log.items_processed
    avg_time_per_item = {
        bid: (d["time"] / d["items"] if d["items"] else 0)
        for bid, d in batch_stats.items()
    }

    user_stats = {}
    for log in database['performance_logs']:
        if log.end_time:
            hours = (log.end_time - log.start_time).total_seconds() / 3600
            stats = user_stats.setdefault(log.user_id, {"items": 0, "hours": 0.0})
            stats["items"] += log.items_processed
            stats["hours"] += hours
    leaderboard = [
        {
            "user_id": uid,
            "items_per_hour": (s["items"] / s["hours"] if s["hours"] else 0),
        }
        for uid, s in user_stats.items()
    ]
    leaderboard.sort(key=lambda x: x["items_per_hour"], reverse=True)

    error_counts = error_counts_by_operator()
    error_rates = {
        uid: (
            sum(types.values()) / user_stats.get(uid, {}).get("items", 1)
        )
        for uid, types in error_counts.items()
    }

    HOURLY_RATE = 10
    cost_analysis = {
        uid: user_stats[uid]["hours"] * HOURLY_RATE
        for uid in user_stats
    }

    return {
        "daily_totals": daily_totals,
        "average_time_per_item": avg_time_per_item,
        "leaderboard": leaderboard,
        "error_rates": error_rates,
        "cost_analysis": cost_analysis,
    }


@app.post("/api_keys", response_model=dict)
async def api_create_api_key(description: str, current_user: User = Depends(get_current_user)):
    check_permission(current_user, "create_api_key")
    key = create_api_key(description)
    log_audit(current_user.id, f"create_api_key:{key.id}")
    return {"key": key.key}


@app.get("/audit_logs", response_model=List[dict])
async def api_get_logs(current_user: User = Depends(get_current_user)):
    check_permission(current_user, "view_audit")
    logs = get_audit_logs()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "timestamp": l.timestamp.isoformat(),
        }
        for l in logs
    ]


@app.post("/integration/batches", response_model=dict)
async def api_integration_batch(batch: BatchCreate, key: IntegrationKey = Depends(require_api_key)):
    created = create_batch(batch.project_id, batch.reception_date, batch.due_date, batch.initial_volume)
    return {"id": created.id}


@app.get("/integration/workhours")
async def api_export_workhours(key: IntegrationKey = Depends(require_api_key)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "batch_id", "items", "hours"])
    for log in database['performance_logs']:
        if log.end_time:
            hours = (log.end_time - log.start_time).total_seconds() / 3600
            writer.writerow([log.user_id, log.batch_id, log.items_processed, f"{hours:.2f}"])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv")


@app.get("/client/projects/{project_id}", response_model=dict)
async def client_get_project(project_id: int, key: IntegrationKey = Depends(require_api_key)):
    project = next((p for p in database['projects'] if p.id == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    batches = [b for b in database['batches'] if b.project_id == project_id]
    return {
        "project": {"id": project.id, "name": project.name, "client_name": project.client_name},
        "batches": [{"id": b.id, "status": b.status} for b in batches],
    }
