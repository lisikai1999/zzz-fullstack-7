from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import redis

from app.core.deps import get_db, get_redis
from app.models.spider import Spider
from app.models.task import Task
from app.schemas.spider import SpiderCreate, SpiderUpdate, SpiderResponse
from app.services.bloom_dedup import BloomDedup
from app.workers.scrape_task import execute_spider

router = APIRouter()


@router.get("/", response_model=list[SpiderResponse])
def list_spiders(db: Session = Depends(get_db)):
    return db.query(Spider).order_by(Spider.created_at.desc()).all()


@router.post("/", response_model=SpiderResponse)
def create_spider(data: SpiderCreate, db: Session = Depends(get_db)):
    spider = Spider(**data.model_dump())
    db.add(spider)
    db.commit()
    db.refresh(spider)
    return spider


@router.get("/{spider_id}", response_model=SpiderResponse)
def get_spider(spider_id: int, db: Session = Depends(get_db)):
    spider = db.query(Spider).filter(Spider.id == spider_id).first()
    if not spider:
        raise HTTPException(status_code=404, detail="Spider not found")
    return spider


@router.put("/{spider_id}", response_model=SpiderResponse)
def update_spider(spider_id: int, data: SpiderUpdate, db: Session = Depends(get_db)):
    spider = db.query(Spider).filter(Spider.id == spider_id).first()
    if not spider:
        raise HTTPException(status_code=404, detail="Spider not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(spider, key, value)
    db.commit()
    db.refresh(spider)
    return spider


@router.delete("/{spider_id}")
def delete_spider(spider_id: int, db: Session = Depends(get_db)):
    spider = db.query(Spider).filter(Spider.id == spider_id).first()
    if not spider:
        raise HTTPException(status_code=404, detail="Spider not found")
    db.delete(spider)
    db.commit()
    return {"ok": True}


@router.post("/{spider_id}/run")
def trigger_run(spider_id: int, db: Session = Depends(get_db)):
    spider = db.query(Spider).filter(Spider.id == spider_id).first()
    if not spider:
        raise HTTPException(status_code=404, detail="Spider not found")
    task = Task(spider_id=spider_id, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    execute_spider.delay(spider_id, task.id)
    return {"task_id": task.id, "status": "dispatched"}


@router.post("/{spider_id}/reset-bloom")
def reset_bloom(spider_id: int, db: Session = Depends(get_db), r: redis.Redis = Depends(get_redis)):
    spider = db.query(Spider).filter(Spider.id == spider_id).first()
    if not spider:
        raise HTTPException(status_code=404, detail="Spider not found")
    dedup = BloomDedup(r)
    dedup.reset_domain(spider.domain)
    return {"ok": True, "domain": spider.domain}
