from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    SECRET_KEY: str = "secret"
    DATABASE_URL: str = "sqlite:///./db.sqlite3"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True
