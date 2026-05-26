from celery import current_app as celery_app
from celery.utils.log import get_task_logger
from datetime import datetime
from croniter import croniter

from app.core.database import SessionLocal
from app.models.spider import Spider
from app.models.task import Task

logger = get_task_logger(__name__)


@celery_app.task(name="workers.dispatch_due_spiders")
def dispatch_due_spiders():
    """Check which spiders are due based on cron schedule and dispatch them."""
    db = SessionLocal()
    try:
        spiders = db.query(Spider).filter(
            Spider.enabled == True,
            Spider.schedule_cron.isnot(None),
        ).all()

        now = datetime.utcnow()
        for spider in spiders:
            try:
                cron = croniter(spider.schedule_cron, now)
                prev = cron.get_prev(datetime)
                diff = (now - prev).total_seconds()
                if diff <= 60:
                    task = Task(spider_id=spider.id, status="pending")
                    db.add(task)
                    db.commit()

                    from app.workers.scrape_task import execute_spider
                    execute_spider.delay(spider.id, task.id)
                    logger.info(f"Dispatched spider {spider.name} (id={spider.id})")
            except Exception as e:
                logger.error(f"Error checking spider {spider.id}: {e}")

    finally:
        db.close()
