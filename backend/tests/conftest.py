import pytest
import fakeredis


@pytest.fixture
def redis_client():
    """Provide a fake Redis client with Lua support for testing."""
    r = fakeredis.FakeRedis(decode_responses=True)
    yield r
    r.flushall()
    r.close()
