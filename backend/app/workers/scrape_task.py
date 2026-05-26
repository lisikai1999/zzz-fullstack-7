from celery import current_app as celery_app
from celery.utils.log import get_task_logger
from datetime import datetime
import redis as redis_lib

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.task import Task
from app.models.result import ScrapedItem
from app.models.spider import Spider
from app.services.bloom_dedup import BloomDedup
from app.services.rate_limiter import AdaptiveRateLimiter
from app.services.alert_service import AlertService
from app.scraper.engine import ScrapeEngine
from app.schemas.spider import SpiderSelectors

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="workers.execute_spider", max_retries=3)
def execute_spider(self, spider_id: int, task_id: int):
    redis_client = redis_lib.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    db = SessionLocal()
    engine = None

    try:
        spider = db.query(Spider).filter(Spider.id == spider_id).first()
        if not spider or not spider.enabled:
            return {"status": "skipped", "reason": "spider disabled or not found"}

        task = db.query(Task).filter(Task.id == task_id).first()
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.celery_task_id = self.request.id
        db.commit()

        dedup = BloomDedup(redis_client)
        rate_limiter = AdaptiveRateLimiter(redis_client)
        alert_service = AlertService(db)

        selectors = SpiderSelectors(**spider.selectors)
        engine = ScrapeEngine(
            spider_id=spider.id,
            domain=spider.domain,
            selectors=selectors,
            use_playwright=spider.use_playwright,
            dedup=dedup,
            rate_limiter=rate_limiter,
            alert_service=alert_service,
            task_id=task_id,
        )

        for url, parse_result in engine.run(spider.start_urls, spider.max_depth):
            for item_data in parse_result.items:
                scraped_item = ScrapedItem(
                    task_id=task_id,
                    spider_id=spider_id,
                    url=url,
                    data=item_data,
                )
                db.add(scraped_item)
            db.commit()

            task.urls_scraped = engine.stats["scraped"]
            task.urls_discovered = engine.stats["discovered"]
            task.urls_deduped = engine.stats["deduped"]
            task.items_extracted = engine.stats["items"]
            db.commit()

        task.status = "success"
        task.finished_at = datetime.utcnow()
        db.commit()

        return engine.stats

    except Exception as exc:
        logger.exception(f"Spider {spider_id} failed")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.errors = (task.errors or []) + [{"error": str(exc)}]
            task.finished_at = datetime.utcnow()
            db.commit()
        raise self.retry(exc=exc, countdown=60)

    finally:
        if engine:
            engine.close()
        db.close()
        redis_client.close()
