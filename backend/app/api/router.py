from fastapi import APIRouter
from app.api import spiders, tasks, alerts, stats

api_router = APIRouter()
api_router.include_router(spiders.router, prefix="/spiders", tags=["spiders"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
