import time
from dataclasses import dataclass
import redis


@dataclass
class RateLimitConfig:
    max_rate: float = 10.0
    min_rate: float = 0.1
    initial_rate: float = 2.0
    additive_increase: float = 0.5
    multiplicative_decrease: float = 0.5
    success_window: int = 10


ACQUIRE_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])

local rate = tonumber(redis.call('HGET', key, 'current_rate') or '2.0')
local last_ts = tonumber(redis.call('HGET', key, 'last_request_ts') or '0')

local interval = 1.0 / rate
local next_allowed = last_ts + interval
local wait = 0

if now < next_allowed then
    wait = next_allowed - now
    redis.call('HSET', key, 'last_request_ts', tostring(next_allowed))
else
    wait = 0
    redis.call('HSET', key, 'last_request_ts', tostring(now))
end

return tostring(wait)
"""

SUCCESS_SCRIPT = """
local key = KEYS[1]
local add_inc = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_rate = tonumber(ARGV[3])

local count = redis.call('HINCRBY', key, 'success_count', 1)
if count >= window then
    local rate = tonumber(redis.call('HGET', key, 'current_rate') or '2.0')
    rate = math.min(rate + add_inc, max_rate)
    redis.call('HSET', key, 'current_rate', tostring(rate))
    redis.call('HSET', key, 'success_count', '0')
end
return 1
"""

THROTTLE_SCRIPT = """
local key = KEYS[1]
local md = tonumber(ARGV[1])
local min_rate = tonumber(ARGV[2])

local rate = tonumber(redis.call('HGET', key, 'current_rate') or '2.0')
rate = math.max(rate * md, min_rate)
redis.call('HSET', key, 'current_rate', tostring(rate))
redis.call('HSET', key, 'success_count', '0')
return 1
"""


class AdaptiveRateLimiter:
    """Per-domain AIMD rate limiter with shared state in Redis."""

    def __init__(self, redis_client: redis.Redis, config: RateLimitConfig = None):
        self.r = redis_client
        self.config = config or RateLimitConfig()

    def _key(self, domain: str) -> str:
        return f"ratelimit:{domain}"

    def _ensure_state(self, domain: str) -> None:
        key = self._key(domain)
        if not self.r.exists(key):
            self.r.hset(key, mapping={
                "current_rate": str(self.config.initial_rate),
                "success_count": "0",
                "last_request_ts": "0",
            })

    def acquire(self, domain: str) -> float:
        """
        Get permission to send a request. Returns seconds to wait.
        Atomically updates last_request_ts via Lua.
        """
        self._ensure_state(domain)
        key = self._key(domain)
        now = time.time()
        wait = float(self.r.eval(ACQUIRE_SCRIPT, 1, key, str(now)))
        return wait

    def report_success(self, domain: str) -> None:
        """After success_window consecutive successes, additive increase."""
        self._ensure_state(domain)
        self.r.eval(
            SUCCESS_SCRIPT, 1, self._key(domain),
            str(self.config.additive_increase),
            str(self.config.success_window),
            str(self.config.max_rate),
        )

    def report_throttled(self, domain: str) -> None:
        """On 429: multiplicative decrease (halve rate)."""
        self._ensure_state(domain)
        self.r.eval(
            THROTTLE_SCRIPT, 1, self._key(domain),
            str(self.config.multiplicative_decrease),
            str(self.config.min_rate),
        )

    def get_domain_stats(self, domain: str) -> dict:
        key = self._key(domain)
        state = self.r.hgetall(key)
        if not state:
            return {"domain": domain, "current_rate_rps": self.config.initial_rate}
        return {
            "domain": domain,
            "current_rate_rps": float(state.get("current_rate", self.config.initial_rate)),
            "success_count": int(state.get("success_count", 0)),
        }

    def reset_domain(self, domain: str) -> None:
        self.r.delete(self._key(domain))
