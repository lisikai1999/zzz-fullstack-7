"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.database import Base
from app.core.deps import get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestSpiderAPI:
    def test_create_spider(self):
        resp = client.post("/api/v1/spiders", json={
            "name": "test_spider",
            "domain": "example.com",
            "start_urls": ["https://example.com"],
            "selectors": {
                "fields": [{
                    "field_name": "title",
                    "selectors": [{"type": "css", "expression": "h1"}],
                    "required": True,
                    "min_yield_pct": 0.8,
                }]
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test_spider"
        assert data["id"] >= 1

    def test_list_spiders(self):
        client.post("/api/v1/spiders", json={
            "name": "s1", "domain": "a.com", "start_urls": ["https://a.com"],
            "selectors": {"fields": []},
        })
        resp = client.get("/api/v1/spiders")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_update_spider(self):
        create = client.post("/api/v1/spiders", json={
            "name": "s2", "domain": "b.com", "start_urls": ["https://b.com"],
            "selectors": {"fields": []},
        })
        sid = create.json()["id"]
        resp = client.put(f"/api/v1/spiders/{sid}", json={"max_depth": 5})
        assert resp.status_code == 200
        assert resp.json()["max_depth"] == 5

    def test_delete_spider(self):
        create = client.post("/api/v1/spiders", json={
            "name": "s3", "domain": "c.com", "start_urls": ["https://c.com"],
            "selectors": {"fields": []},
        })
        sid = create.json()["id"]
        resp = client.delete(f"/api/v1/spiders/{sid}")
        assert resp.status_code == 200

        get_resp = client.get(f"/api/v1/spiders/{sid}")
        assert get_resp.status_code == 404


class TestAlertAPI:
    def test_alert_summary_empty(self):
        resp = client.get("/api/v1/alerts/summary")
        assert resp.status_code == 200
        assert resp.json()["total_unacked"] == 0
