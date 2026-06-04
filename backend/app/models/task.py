from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    spider_id = Column(Integer, ForeignKey("spiders.id"), nullable=False, index=True)
    celery_task_id = Column(String(255), unique=True, nullable=True)
    status = Column(String(50), default="pending", index=True)
    urls_discovered = Column(Integer, default=0)
    urls_scraped = Column(Integer, default=0)
    urls_deduped = Column(Integer, default=0)
    urls_rate_limited = Column(Integer, default=0)
    items_extracted = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
