from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ScrapedItem(Base):
    __tablename__ = "scraped_items"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    spider_id = Column(Integer, ForeignKey("spiders.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    data = Column(JSON, nullable=False)
    selector_used = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
