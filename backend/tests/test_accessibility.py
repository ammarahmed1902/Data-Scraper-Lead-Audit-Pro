"""Tests for accessibility analyzer."""

from app.services.accessibility_service import AccessibilityAnalyzer
from app.services.scraper.page_fetcher import FetchResult


def test_accessibility_missing_lang():
    html = "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>"
    page = FetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html=html,
        headers={},
        elapsed_ms=100,
        content_length=len(html),
    )
    result = AccessibilityAnalyzer().analyze(page)
    assert result["score"] < 100
    codes = [i["code"] for i in result["issues"]["items"]]
    assert "MISSING_LANG" in codes


def test_accessibility_lighthouse_blend():
    html = '<html lang="en"><head><title>Test</title></head><body><main><h1>Hi</h1></main></body></html>'
    page = FetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html=html,
        headers={},
        elapsed_ms=100,
        content_length=len(html),
    )
    result = AccessibilityAnalyzer().analyze(page, lighthouse_score=90.0)
    assert result["score"] >= 85
    assert result["lighthouse_score"] == 90.0
