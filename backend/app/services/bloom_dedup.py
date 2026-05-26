import redis


class BloomDedup:
    """Per-domain URL deduplication using Redis Bloom filters."""

    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client
        self._initialized: set[str] = set()

    def _key(self, domain: str) -> str:
        return f"bf:{domain}"

    def _ensure_filter(self, domain: str) -> None:
        key = self._key(domain)
        if domain in self._initialized:
            return
        try:
            self.r.execute_command(
                "BF.RESERVE", key,
                0.001,
                10_000_000,
                "EXPANSION", 2,
            )
        except redis.ResponseError as e:
            if "item exists" not in str(e).lower():
                raise
        self._initialized.add(domain)

    def is_duplicate(self, domain: str, url: str) -> bool:
        """Returns True if URL was probably seen before."""
        self._ensure_filter(domain)
        return bool(self.r.execute_command("BF.EXISTS", self._key(domain), url))

    def mark_seen(self, domain: str, url: str) -> bool:
        """Add URL to filter. Returns True if it was already present (duplicate)."""
        self._ensure_filter(domain)
        result = self.r.execute_command("BF.ADD", self._key(domain), url)
        return result == 0

    def bulk_check_and_add(self, domain: str, urls: list[str]) -> list[str]:
        """Returns list of NEW (non-duplicate) URLs after adding all."""
        if not urls:
            return []
        self._ensure_filter(domain)
        key = self._key(domain)
        results = self.r.execute_command("BF.MADD", key, *urls)
        return [url for url, added in zip(urls, results) if added == 1]

    def reset_domain(self, domain: str) -> None:
        """Delete and recreate bloom filter for a domain."""
        self.r.delete(self._key(domain))
        self._initialized.discard(domain)
        self._ensure_filter(domain)

    def stats(self, domain: str) -> dict:
        """Get bloom filter info for a domain."""
        key = self._key(domain)
        try:
            info = self.r.execute_command("BF.INFO", key)
            return dict(zip(info[::2], info[1::2]))
        except redis.ResponseError:
            return {}
