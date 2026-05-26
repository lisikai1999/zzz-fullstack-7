from dataclasses import dataclass, field
from typing import Optional
from lxml import html
from app.schemas.spider import SpiderSelectors, FieldExtractor, SelectorRule


@dataclass
class ParseResult:
    items: list[dict] = field(default_factory=list)
    field_stats: dict[str, dict] = field(default_factory=dict)
    failures: list[dict] = field(default_factory=list)


class PageParser:
    """Parse HTML using selector config with ordered fallback logic."""

    def parse(self, html_content: str, selectors: SpiderSelectors) -> ParseResult:
        result = ParseResult()
        tree = html.fromstring(html_content)

        if selectors.item_container:
            containers = self._select(tree, selectors.item_container)
        else:
            containers = [tree]

        for field_cfg in selectors.fields:
            result.field_stats[field_cfg.field_name] = {
                "total": len(containers),
                "extracted": 0,
                "selector_levels": [],
            }

        for container in containers:
            item = {}
            for field_cfg in selectors.fields:
                value, level = self._extract_field(container, field_cfg)
                if value is not None:
                    item[field_cfg.field_name] = value
                    result.field_stats[field_cfg.field_name]["extracted"] += 1
                    result.field_stats[field_cfg.field_name]["selector_levels"].append(level)
                elif field_cfg.required:
                    result.failures.append({
                        "field": field_cfg.field_name,
                        "selectors_tried": [s.expression for s in field_cfg.selectors],
                    })
            if item:
                result.items.append(item)

        return result

    def _extract_field(self, element, field_cfg: FieldExtractor) -> tuple[Optional[str], int]:
        for level, selector in enumerate(field_cfg.selectors):
            nodes = self._select(element, selector)
            if nodes:
                value = self._get_value(nodes[0], selector.attribute)
                if value and value.strip():
                    return value.strip(), level
        return None, -1

    def _select(self, element, rule: SelectorRule) -> list:
        try:
            if rule.type == "css":
                return element.cssselect(rule.expression)
            elif rule.type == "xpath":
                result = element.xpath(rule.expression)
                if result and isinstance(result[0], str):
                    return result
                return result
        except Exception:
            return []
        return []

    def _get_value(self, node, attribute: Optional[str]) -> Optional[str]:
        if isinstance(node, str):
            return node
        if attribute is None or attribute == "text":
            return node.text_content()
        return node.get(attribute)

    def get_next_page(self, html_content: str, selectors: SpiderSelectors) -> Optional[str]:
        if not selectors.pagination:
            return None
        tree = html.fromstring(html_content)
        nodes = self._select(tree, selectors.pagination)
        if nodes:
            return self._get_value(nodes[0], selectors.pagination.attribute)
        return None
