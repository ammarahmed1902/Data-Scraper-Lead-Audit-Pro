"""Tests for audit category analyzers and advanced engine."""

from unittest.mock import MagicMock, patch

from app.services.audit.advanced_engine import AdvancedAuditEngine
from app.services.audit.category_analyzers import (
    CROAnalyzer,
    FunctionalAnalyzer,
    MobileAnalyzer,
    QAAnalyzer,
    SecurityAnalyzer,
    TechnologyAnalyzer,
)
from app.services.audit.category_helpers import build_category, score_from_issues
from app.services.scraper.html_parser import HtmlParser
from app.services.scraper.page_fetcher import FetchResult


def _page(html: str, *, url: str = "https://example.com") -> FetchResult:
    return FetchResult(
        url=url,
        final_url=url,
        status_code=200,
        html=html,
        headers={"content-type": "text/html"},
        elapsed_ms=120,
        content_length=len(html),
    )


GOOD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Example Business — Home</title>
  <meta name="description" content="Professional services for local customers.">
  <link rel="canonical" href="https://example.com/">
  <link rel="icon" href="/favicon.ico">
</head>
<body>
  <nav><a href="/about">About</a></nav>
  <main>
    <h1>Welcome</h1>
    <form action="/contact" method="post">
      <label for="email">Email</label>
      <input id="email" name="email" type="email">
      <button type="submit" class="btn-primary cta">Get Started</button>
    </form>
    <a href="tel:+15551234567">Call us</a>
    <a href="mailto:hello@example.com">Email</a>
    <a href="https://facebook.com/example">Facebook</a>
    <a href="/privacy">Privacy Policy</a>
  </main>
</body>
</html>"""


def test_build_category_shape():
    result = build_category(
        score=85.0,
        issues=[{"severity": "low", "code": "X", "message": "test"}],
        recommendations=[{"priority": "low", "title": "T", "description": "D"}],
        checks={"ok": True},
    )
    assert result["score"] == 85.0
    assert len(result["issues"]["items"]) == 1
    assert len(result["recommendations"]["items"]) == 1
    assert result["checks"]["ok"] is True


def test_score_from_issues_penalties():
    issues = [
        {"severity": "critical", "code": "A", "message": "a"},
        {"severity": "low", "code": "B", "message": "b"},
    ]
    assert score_from_issues(issues) == 100 - 25 - 3


def test_functional_analyzer_detects_navigation_and_forms():
    page = _page(GOOD_HTML)
    parser = HtmlParser(page.html, page.final_url)
    result = FunctionalAnalyzer().analyze(page, parser)
    assert result["score"] >= 70
    assert result["checks"]["forms_count"] >= 1
    assert result["checks"]["has_navigation"] is True


def test_mobile_analyzer_requires_viewport():
    page = _page("<html><body><h1>Hi</h1></body></html>")
    parser = HtmlParser(page.html, page.final_url)
    result = MobileAnalyzer().analyze(page, parser)
    codes = [i["code"] for i in result["issues"]["items"]]
    assert "NO_VIEWPORT" in codes
    assert result["score"] < 80


def test_security_analyzer_flags_http():
    page = _page(GOOD_HTML, url="http://example.com")
    page.final_url = "http://example.com"
    tech_data = {"ssl_valid": False, "security_headers": {"missing": ["strict-transport-security"], "present": {}}}
    result = SecurityAnalyzer().analyze(page, tech_data=tech_data)
    codes = [i["code"] for i in result["issues"]["items"]]
    assert "NO_HTTPS" in codes
    assert result["score"] <= 50


def test_cro_analyzer_detects_cta_and_form():
    page = _page(GOOD_HTML)
    parser = HtmlParser(page.html, page.final_url)
    result = CROAnalyzer().analyze(page, parser)
    assert result["checks"]["has_form"] is True
    assert result["score"] >= 60


def test_qa_analyzer_flags_missing_legal_on_sparse_page():
    page = _page("<html><body><h1>Hi</h1></body></html>")
    parser = HtmlParser(page.html, page.final_url)
    result = QAAnalyzer().analyze(page, parser)
    codes = [i["code"] for i in result["issues"]["items"]]
    assert "MISSING_FAVICON" in codes
    assert "MISSING_LEGAL_PAGES" in codes


def test_technology_analyzer_extracts_cms():
    tech_data = {
        "technologies": {
            "detected": ["WordPress", "jQuery"],
            "server": "nginx",
        }
    }
    result = TechnologyAnalyzer().analyze(tech_data)
    assert result["checks"]["cms_platform"] == "WordPress"
    assert "WordPress" in result["checks"]["technology_stack"]


@patch.object(AdvancedAuditEngine, "__init__", lambda self: None)
def test_advanced_engine_run_structure():
    engine = AdvancedAuditEngine()
    engine.fetcher = MagicMock()
    engine.seo = MagicMock()
    engine.performance = MagicMock()
    engine.technical = MagicMock()
    engine.accessibility = MagicMock()
    engine.functional = FunctionalAnalyzer()
    engine.mobile = MobileAnalyzer()
    engine.security = SecurityAnalyzer()
    engine.technical_seo = MagicMock()
    engine.seo_strategy = MagicMock()
    engine.marketing = MagicMock()
    engine.cro = CROAnalyzer()
    engine.qa = QAAnalyzer()
    engine.a11y_category = MagicMock()
    engine.technology = TechnologyAnalyzer()

    page = _page(GOOD_HTML)
    engine.fetcher.fetch.return_value = page
    engine.performance.fetch_lighthouse_accessibility.return_value = 88.0
    engine.seo.analyze.return_value = {
        "score": 80.0,
        "issues": {"items": []},
        "recommendations": {"items": []},
    }
    engine.performance.analyze.return_value = {
        "score": 75.0,
        "issues": {"items": []},
        "recommendations": {"items": []},
        "metrics": {"source": "heuristic"},
    }
    engine.technical.analyze.return_value = {
        "score": 70.0,
        "ssl_valid": True,
        "indexable": True,
        "technologies": {"detected": ["Next.js"]},
        "security_headers": {"missing": [], "present": {}, "score": 90.0},
    }
    engine.accessibility.analyze.return_value = {
        "score": 85.0,
        "issues": {"items": []},
        "recommendations": {"items": []},
        "checks": {},
    }
    engine.technical_seo.analyze.return_value = build_category(score=78.0, issues=[], recommendations=[])
    engine.seo_strategy.analyze.return_value = build_category(score=72.0, issues=[], recommendations=[])
    engine.marketing.analyze.return_value = build_category(score=68.0, issues=[], recommendations=[])
    engine.a11y_category.from_a11y_data.return_value = build_category(
        score=85.0, issues=[], recommendations=[]
    )

    result = engine.run("https://example.com", company_name="Example Co", domain="example.com")

    assert "category_breakdown" in result
    breakdown = result["category_breakdown"]
    for key in (
        "security",
        "mobile",
        "technical_seo",
        "accessibility",
        "marketing",
        "conversion",
        "technology",
        "performance",
        "functional",
        "seo_strategy",
        "qa",
    ):
        assert key in breakdown
        assert "score" in breakdown[key]
        assert "issues" in breakdown[key]
        assert "recommendations" in breakdown[key]

    assert result["scores"]["security"] is not None
    assert result["lead_classification"] in ("hot", "warm", "cold", "low")
    assert result["sales_summary"]
