from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)

    logs = relationship("PerformanceLog", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    client_name = Column(String)

    batches = relationship("Batch", back_populates="project")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    reception_date = Column(DateTime)
    due_date = Column(DateTime)
    initial_volume = Column(Integer)
    status = Column(String, default="Received")

    project = relationship("Project", back_populates="batches")
    logs = relationship("PerformanceLog", back_populates="batch")


class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    batch_id = Column(Integer, ForeignKey("batches.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    items_processed = Column(Integer)

    user = relationship("User", back_populates="logs")
    batch = relationship("Batch", back_populates="logs")
