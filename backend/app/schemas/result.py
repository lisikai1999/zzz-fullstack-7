from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScrapedItemResponse(BaseModel):
    id: int
    task_id: int
    spider_id: int
    url: str
    data: dict
    selector_used: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
