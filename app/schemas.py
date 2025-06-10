from pydantic import BaseModel
from datetime import datetime

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
