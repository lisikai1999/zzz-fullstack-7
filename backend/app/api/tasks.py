from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.core.deps import get_db
from app.models.task import Task
from app.models.result import ScrapedItem
from app.schemas.task import TaskResponse
from app.schemas.result import ScrapedItemResponse
from celery_app import celery_app

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    spider_id: int = Query(None),
    status: str = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if spider_id:
        q = q.filter(Task.spider_id == spider_id)
    if status:
        q = q.filter(Task.status == status)
    return q.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.celery_task_id:
        celery_app.control.revoke(task.celery_task_id, terminate=True)
    task.status = "cancelled"
    db.commit()
    return {"ok": True}


@router.get("/{task_id}/items", response_model=list[ScrapedItemResponse])
def get_task_items(
    task_id: int,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    return (
        db.query(ScrapedItem)
        .filter(ScrapedItem.task_id == task_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
