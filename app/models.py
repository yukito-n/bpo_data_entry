from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

# In-memory 'database'
database = {
    'users': [],
    'projects': [],
    'batches': [],
    'performance_logs': [],
    'assignments': [],
    'shifts': [],
    'quality_logs': [],
    'issues': [],
    'articles': [],
}


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: str
    is_active: bool = True


def get_user(user_id: int) -> Optional[User]:
    return next((u for u in database['users'] if u.id == user_id), None)


def get_user_by_username(username: str) -> Optional[User]:
    return next((u for u in database['users'] if u.username == username), None)


def create_user(username: str, password_hash: str, role: str) -> User:
    user = User(id=len(database['users']) + 1, username=username, password_hash=password_hash, role=role)
    database['users'].append(user)
    return user


def update_user(user: User, *, username: Optional[str] = None, password_hash: Optional[str] = None, role: Optional[str] = None):
    if username is not None:
        user.username = username
    if password_hash is not None:
        user.password_hash = password_hash
    if role is not None:
        user.role = role
    return user


def deactivate_user(user: User):
    user.is_active = False


@dataclass
class Project:
    id: int
    name: str
    client_name: str


def create_project(name: str, client_name: str) -> Project:
    project = Project(id=len(database['projects']) + 1, name=name, client_name=client_name)
    database['projects'].append(project)
    return project


@dataclass
class Batch:
    id: int
    project_id: int
    reception_date: datetime
    due_date: datetime
    initial_volume: int
    status: str = "Received"


def create_batch(project_id: int, reception_date: datetime, due_date: datetime, initial_volume: int) -> Batch:
    batch = Batch(
        id=len(database['batches']) + 1,
        project_id=project_id,
        reception_date=reception_date,
        due_date=due_date,
        initial_volume=initial_volume,
    )
    database['batches'].append(batch)
    return batch


def get_batch(batch_id: int) -> Optional[Batch]:
    return next((b for b in database['batches'] if b.id == batch_id), None)


def update_batch_status(batch: Batch, status: str):
    batch.status = status


@dataclass
class PerformanceLog:
    user_id: int
    batch_id: int
    start_time: datetime
    end_time: Optional[datetime]
    items_processed: int
    id: int = field(default_factory=lambda: len(database['performance_logs']) + 1)


def log_performance(user_id: int, batch_id: int, items_processed: int, start_time: datetime, end_time: datetime):
    log = PerformanceLog(user_id=user_id, batch_id=batch_id, items_processed=items_processed, start_time=start_time, end_time=end_time)
    database['performance_logs'].append(log)
    return log


@dataclass
class Assignment:
    id: int
    user_id: int
    batch_id: int


def assign_operator(user_id: int, batch_id: int) -> Assignment:
    assignment = Assignment(id=len(database['assignments']) + 1, user_id=user_id, batch_id=batch_id)
    database['assignments'].append(assignment)
    return assignment


def get_assignments_for_user(user_id: int) -> List[Assignment]:
    return [a for a in database['assignments'] if a.user_id == user_id]


@dataclass
class Shift:
    id: int
    user_id: int
    start_time: datetime
    end_time: datetime


def create_shift(user_id: int, start_time: datetime, end_time: datetime) -> Shift:
    shift = Shift(id=len(database['shifts']) + 1, user_id=user_id, start_time=start_time, end_time=end_time)
    database['shifts'].append(shift)
    return shift


def get_shifts_for_user(user_id: int) -> List[Shift]:
    return [s for s in database['shifts'] if s.user_id == user_id]


@dataclass
class QualityLog:
    id: int
    batch_id: int
    operator_id: int
    error_type: str


@dataclass
class Issue:
    id: int
    batch_id: int
    description: str
    status: str
    created_by: int
    assigned_to: int
    created_at: datetime


def create_issue(batch_id: int, description: str, created_by: int, assigned_to: int) -> Issue:
    issue = Issue(
        id=len(database['issues']) + 1,
        batch_id=batch_id,
        description=description,
        status='Open',
        created_by=created_by,
        assigned_to=assigned_to,
        created_at=datetime.utcnow(),
    )
    database.setdefault('issues', []).append(issue)
    return issue


def update_issue_status(issue: Issue, status: str):
    issue.status = status
    return issue


def get_issues(assigned_to: Optional[int] = None) -> List[Issue]:
    issues = database.get('issues', [])
    if assigned_to is not None:
        return [i for i in issues if i.assigned_to == assigned_to]
    return issues


@dataclass
class Article:
    id: int
    title: str
    content: str


def create_article(title: str, content: str) -> Article:
    article = Article(id=len(database.setdefault('articles', [])) + 1, title=title, content=content)
    database['articles'].append(article)
    return article


def list_articles() -> List[Article]:
    return database.get('articles', [])


def log_quality(batch_id: int, operator_id: int, error_type: str) -> QualityLog:
    qlog = QualityLog(id=len(database['quality_logs']) + 1, batch_id=batch_id, operator_id=operator_id, error_type=error_type)
    database['quality_logs'].append(qlog)
    return qlog


def error_counts_by_operator() -> dict:
    counts = {}
    for q in database['quality_logs']:
        op = counts.setdefault(q.operator_id, {})
        op[q.error_type] = op.get(q.error_type, 0) + 1
    return counts


def error_counts_by_project() -> dict:
    counts = {}
    for q in database['quality_logs']:
        batch = get_batch(q.batch_id)
        if batch:
            proj = counts.setdefault(batch.project_id, {})
            proj[q.error_type] = proj.get(q.error_type, 0) + 1
    return counts

