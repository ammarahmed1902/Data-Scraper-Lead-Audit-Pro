"""Auto-score leads after audit or enrichment completes."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.orm import Session

from app.models.lead_discovery import DiscoveredLead
from app.services.scoring_runner import LeadScoringRunner

logger = structlog.get_logger(__name__)


def auto_score_lead_for_website(session: Session, website_id: uuid.UUID) -> None:
    """Score the discovered lead linked to a website, if any."""
    lead = (
        session.query(DiscoveredLead)
        .filter(DiscoveredLead.imported_website_id == website_id)
        .first()
    )
    if lead is None:
        return
    try:
        LeadScoringRunner(session).score_lead_sync(lead.id, lead.user_id)
        logger.info("auto_score_after_audit", lead_id=str(lead.id), website_id=str(website_id))
    except Exception:
        logger.exception("auto_score_failed", lead_id=str(lead.id))


def auto_score_lead(session: Session, lead_id: uuid.UUID, user_id: uuid.UUID) -> None:
    try:
        LeadScoringRunner(session).score_lead_sync(lead_id, user_id)
        logger.info("auto_score_lead", lead_id=str(lead_id))
    except Exception:
        logger.exception("auto_score_failed", lead_id=str(lead_id))
