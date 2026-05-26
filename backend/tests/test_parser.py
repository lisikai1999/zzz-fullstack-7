"""Tests for the PageParser with selector fallback logic."""
from app.scraper.parser import PageParser, ParseResult
from app.schemas.spider import SpiderSelectors, FieldExtractor, SelectorRule


def make_selectors(fields, container=None):
    return SpiderSelectors(fields=fields, item_container=container)


class TestPageParser:
    def setup_method(self):
        self.parser = PageParser()

    def test_primary_selector_matches(self):
        html = '<div class="item"><h2 class="title">Hello</h2></div>'
        selectors = make_selectors([
            FieldExtractor(
                field_name="title",
                selectors=[
                    SelectorRule(type="css", expression="h2.title"),
                    SelectorRule(type="css", expression="h3.fallback"),
                ],
            )
        ])
        result = self.parser.parse(html, selectors)
        assert len(result.items) == 1
        assert result.items[0]["title"] == "Hello"
        assert result.field_stats["title"]["selector_levels"] == [0]

    def test_fallback_selector_used_when_primary_fails(self):
        html = '<div class="item"><h3 class="alt-title">Fallback</h3></div>'
        selectors = make_selectors([
            FieldExtractor(
                field_name="title",
                selectors=[
                    SelectorRule(type="css", expression="h2.title"),
                    SelectorRule(type="css", expression="h3.alt-title"),
                ],
            )
        ])
        result = self.parser.parse(html, selectors)
        assert len(result.items) == 1
        assert result.items[0]["title"] == "Fallback"
        assert result.field_stats["title"]["selector_levels"] == [1]

    def test_all_selectors_fail_records_failure(self):
        html = '<div class="item"><p>No match</p></div>'
        selectors = make_selectors([
            FieldExtractor(
                field_name="title",
                required=True,
                selectors=[
                    SelectorRule(type="css", expression="h2.title"),
                    SelectorRule(type="css", expression="h3.title"),
                ],
            )
        ])
        result = self.parser.parse(html, selectors)
        assert len(result.items) == 0
        assert len(result.failures) == 1
        assert result.failures[0]["field"] == "title"

    def test_item_container_extracts_multiple_items(self):
        html = '''
        <div class="list">
            <div class="card"><span class="name">A</span></div>
            <div class="card"><span class="name">B</span></div>
            <div class="card"><span class="name">C</span></div>
        </div>
        '''
        selectors = make_selectors(
            fields=[
                FieldExtractor(
                    field_name="name",
                    selectors=[SelectorRule(type="css", expression="span.name")],
                )
            ],
            container=SelectorRule(type="css", expression="div.card"),
        )
        result = self.parser.parse(html, selectors)
        assert len(result.items) == 3
        assert [item["name"] for item in result.items] == ["A", "B", "C"]

    def test_xpath_selector(self):
        html = '<div data-price="19.99">Product</div>'
        selectors = make_selectors([
            FieldExtractor(
                field_name="price",
                selectors=[
                    SelectorRule(type="xpath", expression="//div/@data-price"),
                ],
            )
        ])
        result = self.parser.parse(html, selectors)
        assert len(result.items) == 1
        assert result.items[0]["price"] == "19.99"

    def test_attribute_extraction(self):
        html = '<a href="https://example.com" class="link">Click</a>'
        selectors = make_selectors([
            FieldExtractor(
                field_name="url",
                selectors=[
                    SelectorRule(type="css", expression="a.link", attribute="href"),
                ],
            )
        ])
        result = self.parser.parse(html, selectors)
        assert result.items[0]["url"] == "https://example.com"

    def test_next_page_extraction(self):
        html = '<a class="next" href="/page/2">Next</a>'
        selectors = SpiderSelectors(
            fields=[],
            pagination=SelectorRule(type="css", expression="a.next", attribute="href"),
        )
        result = self.parser.get_next_page(html, selectors)
        assert result == "/page/2"

    def test_field_stats_yield(self):
        html = '''
        <div class="item"><h2 class="t">A</h2></div>
        <div class="item"><h2 class="t">B</h2></div>
        <div class="item"><p>No title here</p></div>
        '''
        selectors = make_selectors(
            fields=[
                FieldExtractor(
                    field_name="title",
                    required=False,
                    selectors=[SelectorRule(type="css", expression="h2.t")],
                )
            ],
            container=SelectorRule(type="css", expression="div.item"),
        )
        result = self.parser.parse(html, selectors)
        stats = result.field_stats["title"]
        assert stats["total"] == 3
        assert stats["extracted"] == 2
