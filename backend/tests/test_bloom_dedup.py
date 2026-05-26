"""Tests for the Bloom filter dedup service.

Note: fakeredis does not support RedisBloom commands (BF.*).
These tests validate the interface and would require a real Redis
with RedisBloom module for full integration testing.
We test the logic with a mock approach.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.bloom_dedup import BloomDedup


class TestBloomDedup:
    def setup_method(self):
        self.mock_redis = MagicMock()
        self.dedup = BloomDedup(self.mock_redis)

    def test_ensure_filter_creates_on_first_use(self):
        self.mock_redis.execute_command.return_value = "OK"
        self.dedup._ensure_filter("example.com")

        self.mock_redis.execute_command.assert_called_once_with(
            "BF.RESERVE", "bf:example.com",
            0.001, 10_000_000, "EXPANSION", 2,
        )
        assert "example.com" in self.dedup._initialized

    def test_ensure_filter_idempotent(self):
        import redis
        self.mock_redis.execute_command.side_effect = redis.ResponseError("item exists")
        self.dedup._ensure_filter("example.com")
        assert "example.com" in self.dedup._initialized

    def test_is_duplicate_returns_false_for_new(self):
        self.mock_redis.execute_command.side_effect = [
            "OK",  # BF.RESERVE
            0,     # BF.EXISTS returns 0 (not found)
        ]
        assert self.dedup.is_duplicate("example.com", "http://example.com/page1") is False

    def test_is_duplicate_returns_true_for_existing(self):
        self.dedup._initialized.add("example.com")
        self.mock_redis.execute_command.return_value = 1  # BF.EXISTS returns 1
        assert self.dedup.is_duplicate("example.com", "http://example.com/page1") is True

    def test_mark_seen_returns_false_for_new_url(self):
        self.dedup._initialized.add("example.com")
        self.mock_redis.execute_command.return_value = 1  # BF.ADD returns 1 (newly added)
        assert self.dedup.mark_seen("example.com", "http://example.com/new") is False

    def test_mark_seen_returns_true_for_duplicate(self):
        self.dedup._initialized.add("example.com")
        self.mock_redis.execute_command.return_value = 0  # BF.ADD returns 0 (already existed)
        assert self.dedup.mark_seen("example.com", "http://example.com/old") is True

    def test_bulk_check_and_add(self):
        self.dedup._initialized.add("example.com")
        self.mock_redis.execute_command.return_value = [1, 0, 1]  # new, dup, new
        urls = ["http://a.com/1", "http://a.com/2", "http://a.com/3"]
        new_urls = self.dedup.bulk_check_and_add("example.com", urls)
        assert new_urls == ["http://a.com/1", "http://a.com/3"]

    def test_bulk_check_empty_list(self):
        result = self.dedup.bulk_check_and_add("example.com", [])
        assert result == []

    def test_reset_domain(self):
        self.dedup._initialized.add("example.com")
        self.mock_redis.execute_command.return_value = "OK"
        self.dedup.reset_domain("example.com")
        self.mock_redis.delete.assert_called_once_with("bf:example.com")

    def test_stats(self):
        self.mock_redis.execute_command.return_value = [
            "Capacity", 10000000,
            "Size", 1234567,
            "Number of filters", 1,
        ]
        info = self.dedup.stats("example.com")
        assert info["Capacity"] == 10000000
        assert info["Size"] == 1234567
