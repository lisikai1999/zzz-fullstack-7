"""Tests for the adaptive rate limiter AIMD algorithm."""
import time
from unittest.mock import patch
from app.services.rate_limiter import AdaptiveRateLimiter, RateLimitConfig


class TestAdaptiveRateLimiter:
    def setup_method(self):
        import fakeredis
        self.r = fakeredis.FakeRedis(decode_responses=True)
        self.config = RateLimitConfig(
            max_rate=10.0,
            min_rate=0.1,
            initial_rate=2.0,
            additive_increase=0.5,
            multiplicative_decrease=0.5,
            success_window=5,
        )
        self.limiter = AdaptiveRateLimiter(self.r, self.config)

    def teardown_method(self):
        self.r.flushall()
        self.r.close()

    def test_initial_state(self):
        stats = self.limiter.get_domain_stats("example.com")
        assert stats["current_rate_rps"] == 2.0

    def test_acquire_returns_wait_time(self):
        with patch("time.time", return_value=1000.0):
            wait1 = self.limiter.acquire("example.com")
        assert wait1 == 0.0

        with patch("time.time", return_value=1000.1):
            wait2 = self.limiter.acquire("example.com")
        assert wait2 > 0

    def test_success_increases_rate_after_window(self):
        domain = "test.com"
        self.limiter._ensure_state(domain)

        for _ in range(5):
            self.limiter.report_success(domain)

        stats = self.limiter.get_domain_stats(domain)
        assert stats["current_rate_rps"] == 2.5

    def test_throttle_halves_rate(self):
        domain = "test.com"
        self.limiter._ensure_state(domain)

        self.limiter.report_throttled(domain)

        stats = self.limiter.get_domain_stats(domain)
        assert stats["current_rate_rps"] == 1.0

    def test_rate_never_exceeds_max(self):
        domain = "test.com"
        self.limiter._ensure_state(domain)
        self.r.hset(f"ratelimit:{domain}", "current_rate", "9.8")

        for _ in range(5):
            self.limiter.report_success(domain)

        stats = self.limiter.get_domain_stats(domain)
        assert stats["current_rate_rps"] == 10.0

    def test_rate_never_drops_below_min(self):
        domain = "test.com"
        self.limiter._ensure_state(domain)
        self.r.hset(f"ratelimit:{domain}", "current_rate", "0.15")

        self.limiter.report_throttled(domain)

        stats = self.limiter.get_domain_stats(domain)
        assert stats["current_rate_rps"] == 0.1

    def test_reset_domain(self):
        domain = "test.com"
        self.limiter._ensure_state(domain)
        self.limiter.report_throttled(domain)

        self.limiter.reset_domain(domain)

        stats = self.limiter.get_domain_stats(domain)
        assert stats["current_rate_rps"] == 2.0

    def test_multiple_domains_independent(self):
        self.limiter._ensure_state("a.com")
        self.limiter._ensure_state("b.com")

        self.limiter.report_throttled("a.com")

        stats_a = self.limiter.get_domain_stats("a.com")
        stats_b = self.limiter.get_domain_stats("b.com")
        assert stats_a["current_rate_rps"] == 1.0
        assert stats_b["current_rate_rps"] == 2.0
