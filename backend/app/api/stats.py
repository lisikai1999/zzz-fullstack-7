from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import redis

from app.core.deps import get_db, get_redis
from app.models.spider import Spider
from app.models.task import Task
from app.models.alert import Alert
from app.models.result import ScrapedItem
from app.services.rate_limiter import AdaptiveRateLimiter
from app.services.bloom_dedup import BloomDedup

router = APIRouter()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "total_spiders": db.query(Spider).count(),
        "enabled_spiders": db.query(Spider).filter(Spider.enabled == True).count(),
        "tasks_today": db.query(Task).filter(Task.created_at >= today).count(),
        "running_tasks": db.query(Task).filter(Task.status == "running").count(),
        "items_today": db.query(ScrapedItem).filter(ScrapedItem.created_at >= today).count(),
        "unacked_alerts": db.query(Alert).filter(Alert.acknowledged == False).count(),
    }


@router.get("/rate-limits")
def rate_limits(db: Session = Depends(get_db), r: redis.Redis = Depends(get_redis)):
    domains = [row[0] for row in db.query(Spider.domain).distinct().all()]
    limiter = AdaptiveRateLimiter(r)
    return [limiter.get_domain_stats(d) for d in domains]


@router.get("/bloom")
def bloom_stats(db: Session = Depends(get_db), r: redis.Redis = Depends(get_redis)):
    domains = [row[0] for row in db.query(Spider.domain).distinct().all()]
    dedup = BloomDedup(r)
    return [{"domain": d, **dedup.stats(d)} for d in domains]
