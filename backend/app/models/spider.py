from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Spider(Base):
    __tablename__ = "spiders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    start_urls = Column(JSON, nullable=False)
    schedule_cron = Column(String(100), nullable=True)
    use_playwright = Column(Boolean, default=False)
    max_depth = Column(Integer, default=3)
    enabled = Column(Boolean, default=True)
    selectors = Column(JSON, nullable=False)
    rate_limit_rps = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
