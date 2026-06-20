"""Tests for AI report generation."""

from app.services.ai_report_service import AIReportService


def _sample_audit_data():
    return {
        "score": 45,
        "issues": {
            "items": [
                {"severity": "high", "code": "MISSING_TITLE", "message": "Missing title tag"},
                {"severity": "medium", "code": "THIN_CONTENT", "message": "Thin content detected"},
            ]
        },
        "recommendations": {
            "items": [
                {
                    "title": "Add title tag",
                    "description": "Include a descriptive title for SEO.",
                    "priority": "high",
                }
            ]
        },
        "title_tag": None,
        "h1_count": 0,
        "broken_links": 2,
        "has_sitemap": False,
    }


def test_template_report_has_all_sections():
    seo = _sample_audit_data()
    performance = {
        "score": 55,
        "issues": {"items": [{"severity": "high", "message": "Slow LCP"}]},
        "recommendations": {"items": []},
        "largest_contentful_paint": 4200,
        "first_contentful_paint": 1800,
        "load_time_ms": 3500,
    }
    technical = {
        "score": 70,
        "issues": {"items": []},
        "recommendations": {"items": []},
        "ssl_valid": True,
        "mobile_friendly": True,
        "indexable": True,
    }

    content = AIReportService().generate_full_report(
        url="https://example.com",
        domain="example.com",
        company_name="Example Co",
        seo=seo,
        performance=performance,
        technical=technical,
        overall_score=56.7,
        opportunities=[
            {
                "severity": "high",
                "title": "Missing SEO fundamentals",
                "code": "missing_seo",
            }
        ],
        lead_classification="warm",
    )

    required_keys = {
        "executive_summary",
        "seo_summary",
        "performance_summary",
        "technical_summary",
        "opportunity_summary",
        "client_recommendations",
        "cold_calling_talking_points",
        "sales_pitch_summary",
        "outreach_recommendations",
    }
    assert required_keys.issubset(content.keys())
    assert len(content["cold_calling_talking_points"]) >= 3
    assert len(content["client_recommendations"]) >= 1
    assert "Example Co" in content["executive_summary"]
    assert content["metadata"]["generated_by"] == "template"


def test_talking_points_reference_issues():
    content = AIReportService().generate_full_report(
        url="https://slow.io",
        domain="slow.io",
        company_name="Slow Inc",
        seo={"score": 30, "issues": {"items": [{"severity": "high", "message": "No meta"}]}},
        performance={"score": 25, "issues": {"items": [{"severity": "critical", "message": "Very slow"}]}},
        technical={"score": 40, "issues": {"items": [{"severity": "high", "message": "SSL issue"}]}},
        overall_score=31.7,
    )
    joined = " ".join(content["cold_calling_talking_points"]).lower()
    assert "seo" in joined or "31" in joined


def test_outreach_includes_hot_lead_priority():
    content = AIReportService().generate_full_report(
        url="https://hot.com",
        domain="hot.com",
        company_name="Hot Lead LLC",
        seo={"score": 20, "issues": {"items": []}},
        performance={"score": 20, "issues": {"items": []}},
        technical={"score": 20, "issues": {"items": []}},
        overall_score=20,
        lead_classification="hot",
    )
    channels = [r["channel"] for r in content["outreach_recommendations"]]
    assert "Priority" in channels
