import redis
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        client.close()
