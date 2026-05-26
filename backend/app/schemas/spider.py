from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SelectorRule(BaseModel):
    type: str  # "css" or "xpath"
    expression: str
    attribute: Optional[str] = None


class FieldExtractor(BaseModel):
    field_name: str
    selectors: list[SelectorRule]
    required: bool = True
    min_yield_pct: float = 0.8


class SpiderSelectors(BaseModel):
    fields: list[FieldExtractor]
    pagination: Optional[SelectorRule] = None
    item_container: Optional[SelectorRule] = None


class SpiderCreate(BaseModel):
    name: str
    domain: str
    start_urls: list[str]
    schedule_cron: Optional[str] = None
    use_playwright: bool = False
    max_depth: int = 3
    selectors: dict
    rate_limit_rps: Optional[int] = None


class SpiderUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    start_urls: Optional[list[str]] = None
    schedule_cron: Optional[str] = None
    use_playwright: Optional[bool] = None
    max_depth: Optional[int] = None
    enabled: Optional[bool] = None
    selectors: Optional[dict] = None
    rate_limit_rps: Optional[int] = None


class SpiderResponse(BaseModel):
    id: int
    name: str
    domain: str
    start_urls: list[str]
    schedule_cron: Optional[str]
    use_playwright: bool
    max_depth: int
    enabled: bool
    selectors: dict
    rate_limit_rps: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
