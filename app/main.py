from fastapi import FastAPI

from .models import create_user, get_user_by_username
from .security import get_password_hash
from .api import auth, users, projects, batches, performance

app = FastAPI()


@app.on_event("startup")
def create_default_admin():
    """Ensure an admin user exists so the API can be used immediately."""
    if not get_user_by_username("admin"):
        create_user("admin", get_password_hash("admin123"), "Admin")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(batches.router)
app.include_router(performance.router)
