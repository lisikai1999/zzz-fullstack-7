from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    spider_id = Column(Integer, ForeignKey("spiders.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="warning")
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
