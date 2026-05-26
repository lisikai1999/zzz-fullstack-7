import time
import httpx
from urllib.parse import urljoin, urlparse
from typing import Generator, Optional
from app.scraper.parser import PageParser, ParseResult
from app.scraper.playwright_fetcher import PlaywrightFetcher
from app.services.bloom_dedup import BloomDedup
from app.services.rate_limiter import AdaptiveRateLimiter
from app.services.alert_service import AlertService
from app.schemas.spider import SpiderSelectors


class ScrapeEngine:
    """Orchestrates fetching, parsing, dedup, and rate limiting."""

    def __init__(
        self,
        spider_id: int,
        domain: str,
        selectors: SpiderSelectors,
        use_playwright: bool,
        dedup: BloomDedup,
        rate_limiter: AdaptiveRateLimiter,
        alert_service: AlertService,
        task_id: int,
    ):
        self.spider_id = spider_id
        self.domain = domain
        self.selectors = selectors
        self.dedup = dedup
        self.rate_limiter = rate_limiter
        self.alert_service = alert_service
        self.task_id = task_id
        self.parser = PageParser()
        self.playwright = PlaywrightFetcher() if use_playwright else None
        self.stats = {"discovered": 0, "scraped": 0, "deduped": 0, "items": 0}

    def run(self, urls: list[str], max_depth: int = 3) -> Generator[tuple[str, ParseResult], None, None]:
        queue = [(url, 0) for url in urls]

        while queue:
            url, depth = queue.pop(0)
            self.stats["discovered"] += 1

            if self.dedup.is_duplicate(self.domain, url):
                self.stats["deduped"] += 1
                continue

            self.dedup.mark_seen(self.domain, url)

            wait = self.rate_limiter.acquire(self.domain)
            if wait > 0:
                time.sleep(wait)

            html_content, status_code = self._fetch(url)

            if status_code == 429:
                self.rate_limiter.report_throttled(self.domain)
                queue.append((url, depth))
                time.sleep(2)
                continue
            elif status_code != 200 or html_content is None:
                continue

            self.rate_limiter.report_success(self.domain)
            self.stats["scraped"] += 1

            parse_result = self.parser.parse(html_content, self.selectors)
            self.stats["items"] += len(parse_result.items)

            self._check_alerts(url, parse_result)

            yield url, parse_result

            if depth < max_depth:
                next_page = self.parser.get_next_page(html_content, self.selectors)
                if next_page:
                    abs_url = urljoin(url, next_page)
                    if self._same_domain(abs_url):
                        queue.append((abs_url, depth + 1))

    def _fetch(self, url: str) -> tuple[Optional[str], int]:
        try:
            if self.playwright:
                return self.playwright.fetch(url)
            resp = httpx.get(url, timeout=30, follow_redirects=True, headers={
                "User-Agent": "Mozilla/5.0 (compatible; ScraperPlatform/1.0)"
            })
            return resp.text, resp.status_code
        except Exception:
            return None, 0

    def _same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == self.domain

    def _check_alerts(self, url: str, result: ParseResult) -> None:
        if result.failures:
            self.alert_service.create_alert(
                spider_id=self.spider_id,
                task_id=self.task_id,
                alert_type="selector_failure",
                severity="critical",
                message=f"All selectors failed for fields: {[f['field'] for f in result.failures]}",
                context={"url": url, "failures": result.failures},
            )

        for field_name, stats in result.field_stats.items():
            if stats["total"] > 0:
                yield_pct = stats["extracted"] / stats["total"]
                field_cfg = next(
                    (f for f in self.selectors.fields if f.field_name == field_name), None
                )
                if field_cfg and yield_pct < field_cfg.min_yield_pct:
                    self.alert_service.create_alert(
                        spider_id=self.spider_id,
                        task_id=self.task_id,
                        alert_type="yield_drop",
                        severity="warning",
                        message=f"Field '{field_name}' yield {yield_pct:.0%} below threshold {field_cfg.min_yield_pct:.0%}",
                        context={"url": url, "field": field_name, "yield_pct": yield_pct},
                    )

    def close(self):
        if self.playwright:
            self.playwright.close()
