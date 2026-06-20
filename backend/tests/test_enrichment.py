"""Tests for business enrichment extractors and tech detection."""

from app.services.enrichment.content_extractor import ContentExtractor
from app.services.enrichment.tech_detector import TechStackDetector
from app.services.scraper.page_fetcher import FetchResult


def test_extract_emails_from_mailto():
    html = '<html><body><a href="mailto:hello@example.org">Email</a></body></html>'
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    extractor = ContentExtractor()
    emails = extractor.extract_emails(soup, html)
    assert "hello@example.org" in emails


def test_detect_wordpress():
    html = '<html><link href="/wp-content/themes/foo/style.css"></html>'
    page = FetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html=html,
        headers={},
        elapsed_ms=100,
        content_length=len(html),
    )
    result = TechStackDetector().detect(page)
    assert result["cms_detected"]["wordpress"] is True
    assert result["cms_platform"] == "wordpress"
    assert "WordPress" in result["technology_stack"]


def test_detect_shopify():
    html = '<html><script src="https://cdn.shopify.com/s/files/1.js"></script></html>'
    page = FetchResult(
        url="https://shop.example.com",
        final_url="https://shop.example.com",
        status_code=200,
        html=html,
        headers={},
        elapsed_ms=100,
        content_length=len(html),
    )
    result = TechStackDetector().detect(page)
    assert result["cms_detected"]["shopify"] is True
    assert result["cms_platform"] == "shopify"
