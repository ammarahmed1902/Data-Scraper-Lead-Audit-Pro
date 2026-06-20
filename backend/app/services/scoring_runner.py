"""Synchronous lead scoring runner for Celery workers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session, selectinload

from app.models.audit import AuditReport, AuditStatus
from app.models.enrichment import BusinessEnrichment
from app.models.lead_discovery import DiscoveredLead
from app.models.lead_scoring import LeadScore, ScoringJob, ScoringJobStatus, ScoringJobType
from app.services.scoring.engine import LeadScoringEngine

logger = structlog.get_logger(__name__)


class LeadScoringRunner:
    def __init__(self, session: Session):
        self.session = session
        self.engine = LeadScoringEngine()

    def run(self, job_id: uuid.UUID) -> ScoringJob:
        job = self.session.get(ScoringJob, job_id)
        if job is None:
            raise ValueError(f"Scoring job {job_id} not found")

        if job.status in (ScoringJobStatus.COMPLETED.value, ScoringJobStatus.FAILED.value):
            return job

        job.status = ScoringJobStatus.RUNNING.value
        job.started_at = datetime.now(UTC)
        job.error_message = None
        self.session.flush()

        try:
            lead_ids = self._resolve_lead_ids(job)
            job.total_leads = len(lead_ids)
            self.session.flush()

            for lead_id in lead_ids:
                try:
                    self._score_lead(lead_id, job.user_id)
                    job.processed_leads += 1
                except Exception:
                    logger.exception("scoring_lead_failed", lead_id=str(lead_id))
                    job.failed_leads += 1
                self.session.flush()

            self._update_rankings(job.user_id, job.search_id)
            job.status = ScoringJobStatus.COMPLETED.value
            job.completed_at = datetime.now(UTC)
            logger.info(
                "scoring_job_completed",
                job_id=str(job_id),
                processed=job.processed_leads,
            )
        except Exception as exc:
            logger.exception("scoring_job_failed", job_id=str(job_id))
            job.status = ScoringJobStatus.FAILED.value
            job.error_message = str(exc)[:2000]
            job.completed_at = datetime.now(UTC)

        self.session.flush()
        return job

    def score_lead_sync(self, lead_id: uuid.UUID, user_id: uuid.UUID) -> LeadScore:
        return self._score_lead(lead_id, user_id)

    def _resolve_lead_ids(self, job: ScoringJob) -> list[uuid.UUID]:
        if job.job_type == ScoringJobType.SINGLE_LEAD.value:
            if job.lead_id is None:
                raise ValueError("Single lead job missing lead_id")
            return [job.lead_id]

        if job.job_type == ScoringJobType.SEARCH_BULK.value:
            if job.search_id is None:
                raise ValueError("Bulk job missing search_id")
            rows = (
                self.session.query(DiscoveredLead.id)
                .filter(
                    DiscoveredLead.search_id == job.search_id,
                    DiscoveredLead.user_id == job.user_id,
                    DiscoveredLead.is_duplicate.is_(False),
                )
                .all()
            )
            return [row[0] for row in rows]

        rows = (
            self.session.query(DiscoveredLead.id)
            .filter(
                DiscoveredLead.user_id == job.user_id,
                DiscoveredLead.is_duplicate.is_(False),
            )
            .all()
        )
        return [row[0] for row in rows]

    def _score_lead(self, lead_id: uuid.UUID, user_id: uuid.UUID) -> LeadScore:
        lead = self.session.get(DiscoveredLead, lead_id)
        if lead is None:
            raise ValueError(f"Lead {lead_id} not found")
        if lead.user_id != user_id:
            raise ValueError("Lead ownership mismatch")

        enrichment = (
            self.session.query(BusinessEnrichment)
            .filter(BusinessEnrichment.lead_id == lead_id)
            .one_or_none()
        )

        audit = None
        if lead.imported_website_id:
            audit = (
                self.session.query(AuditReport)
                .options(
                    selectinload(AuditReport.seo_report),
                    selectinload(AuditReport.performance_report),
                    selectinload(AuditReport.technical_report),
                )
                .filter(
                    AuditReport.website_id == lead.imported_website_id,
                    AuditReport.status == AuditStatus.COMPLETED.value,
                )
                .order_by(AuditReport.completed_at.desc())
                .first()
            )

        result = self.engine.score(lead, audit, enrichment)

        record = (
            self.session.query(LeadScore)
            .filter(LeadScore.lead_id == lead_id)
            .one_or_none()
        )
        if record is None:
            record = LeadScore(lead_id=lead_id, user_id=user_id)
            self.session.add(record)

        record.audit_id = uuid.UUID(result["audit_id"]) if result.get("audit_id") else None
        record.website_quality_score = result.get("website_quality_score")
        record.seo_opportunity_score = result.get("seo_opportunity_score")
        record.technical_opportunity_score = result.get("technical_opportunity_score")
        record.sales_potential_score = result.get("sales_potential_score")
        record.composite_score = result.get("composite_score")
        record.classification = result.get("classification")
        record.opportunities = result.get("opportunities")
        record.opportunity_summary = result.get("opportunity_summary")
        record.scored_at = datetime.now(UTC)
        self.session.flush()
        return record

    def _update_rankings(
        self, user_id: uuid.UUID, search_id: uuid.UUID | None
    ) -> None:
        query = self.session.query(LeadScore).join(
            DiscoveredLead, LeadScore.lead_id == DiscoveredLead.id
        ).filter(LeadScore.user_id == user_id)

        if search_id:
            query = query.filter(DiscoveredLead.search_id == search_id)

        scores = query.order_by(LeadScore.composite_score.desc().nullslast()).all()
        for rank, score in enumerate(scores, start=1):
            score.ranking = rank
        self.session.flush()
