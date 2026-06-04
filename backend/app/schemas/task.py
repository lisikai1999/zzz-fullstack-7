from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskResponse(BaseModel):
    id: int
    spider_id: int
    celery_task_id: Optional[str]
    status: str
    urls_discovered: int
    urls_scraped: int
    urls_deduped: int
    urls_rate_limited: int
    items_extracted: int
    errors: Optional[list]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
