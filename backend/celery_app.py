from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "scraper_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

celery_app.conf.beat_schedule = {
    "dispatch-due-spiders": {
        "task": "workers.dispatch_due_spiders",
        "schedule": 60.0,
    },
}

celery_app.autodiscover_tasks(["app.workers"])
