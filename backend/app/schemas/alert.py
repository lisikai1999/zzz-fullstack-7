from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    spider_id: int
    task_id: Optional[int]
    alert_type: str
    severity: str
    message: str
    context: Optional[dict]
    acknowledged: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
