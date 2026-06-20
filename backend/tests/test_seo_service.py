"""SEO analyzer unit tests."""

from app.services.scraper.page_fetcher import FetchResult
from app.services.seo_service import SEOAnalyzer

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Acme Corp - Best Widgets Online</title>
  <meta name="description" content="Acme Corp provides the best widgets for your business needs with fast shipping and great support worldwide.">
  <link rel="canonical" href="https://example.com/">
  <meta property="og:title" content="Acme Corp">
  <meta property="og:description" content="Best widgets online">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script type="application/ld+json">{"@type": "Organization", "name": "Acme"}</script>
</head>
<body>
  <h1>Welcome to Acme</h1>
  <h2>Our Products</h2>
  <h3>Widget Pro</h3>
  <img src="/hero.jpg" alt="Hero banner">
  <img src="/logo.png">
  <a href="/about">About</a>
  <a href="https://external.com">External</a>
</body>
</html>
"""


def test_seo_analyzer_extracts_meta_and_headings():
    page = FetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html=SAMPLE_HTML,
        headers={},
        elapsed_ms=100,
        content_length=len(SAMPLE_HTML),
    )
    result = SEOAnalyzer().analyze("https://example.com", page)

    assert result["title_tag"] == "Acme Corp - Best Widgets Online"
    assert result["h1_count"] == 1
    assert result["score"] > 50
    assert result["issues"]["meta"]["h2_tags"] == ["Our Products"]
    assert result["issues"]["meta"]["open_graph"]["og:title"] == "Acme Corp"
    assert result["issues"]["meta"]["structured_data_count"] == 1
    assert result["issues"]["meta"]["alt_tags"]["missing_alt"] == 1


def test_seo_analyzer_failed_fetch():
    page = FetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=0,
        html="",
        headers={},
        elapsed_ms=0,
        content_length=0,
        error="Connection refused",
    )
    result = SEOAnalyzer().analyze("https://example.com", page)
    assert result["score"] == 0
    assert result["issues"]["items"][0]["code"] == "FETCH_FAILED"
