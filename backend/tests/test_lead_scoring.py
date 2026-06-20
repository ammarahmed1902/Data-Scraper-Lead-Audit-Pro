"""Tests for lead scoring engine."""

from types import SimpleNamespace

from app.services.scoring.engine import LeadScoringEngine


def test_sales_potential_with_contact():
    lead = SimpleNamespace(
        business_name="Acme Corp",
        website_url="https://acme.com",
        phone_number="+1 555 0100",
        email_address="hello@acme.com",
        city="Austin",
        country="USA",
        imported_website_id=None,
    )
    score = LeadScoringEngine._sales_potential_score(lead, None)
    assert score >= 60


def test_classify_hot_lead():
    classification = LeadScoringEngine._classify(
        composite=72.0,
        sales_potential=55.0,
        opportunities=[
            {"severity": "high", "category": "missing_seo", "code": "X", "title": "t", "description": "d"},
            {"severity": "high", "category": "poor_performance", "code": "Y", "title": "t", "description": "d"},
        ],
        has_audit=True,
    )
    assert classification == "hot"


def test_seo_opportunity_from_low_score():
    from app.models.audit import AuditReport, SEOReport

    audit = AuditReport(status="completed", overall_score=40.0)
    seo = SEOReport(score=30.0, issues={"items": [{"severity": "high", "code": "MISSING_TITLE"}]})
    audit.seo_report = seo
    opp = LeadScoringEngine._seo_opportunity_score(audit)
    assert opp >= 70
