"""Synchronous business enrichment runner for Celery workers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from app.models.enrichment import (
    BusinessEnrichment,
    EnrichmentJob,
    EnrichmentJobType,
    EnrichmentStatus,
)
from app.models.lead_discovery import DiscoveredLead
from app.services.enrichment.engine import BusinessEnrichmentEngine

logger = structlog.get_logger(__name__)


class EnrichmentRunner:
    def __init__(self, session: Session):
        self.session = session
        self.engine = BusinessEnrichmentEngine()

    def run(self, job_id: uuid.UUID) -> EnrichmentJob:
        job = self.session.get(EnrichmentJob, job_id)
        if job is None:
            raise ValueError(f"Enrichment job {job_id} not found")

        if job.status in (
            EnrichmentStatus.COMPLETED.value,
            EnrichmentStatus.FAILED.value,
        ):
            return job

        job.status = EnrichmentStatus.RUNNING.value
        job.started_at = datetime.now(UTC)
        job.error_message = None
        self.session.flush()

        try:
            if job.job_type == EnrichmentJobType.SINGLE_LEAD.value:
                if job.lead_id is None:
                    raise ValueError("Single lead job missing lead_id")
                try:
                    self._enrich_lead(job, job.lead_id)
                except Exception as exc:
                    logger.exception(
                        "enrichment_lead_failed",
                        job_id=str(job_id),
                        lead_id=str(job.lead_id),
                    )
                    job.failed_leads += 1
                    lead = self.session.get(DiscoveredLead, job.lead_id)
                    if lead:
                        self._upsert_failed(job, lead, str(exc))
                job.processed_leads = 1
                self.session.flush()
            elif job.job_type == EnrichmentJobType.SEARCH_BULK.value:
                if job.search_id is None:
                    raise ValueError("Bulk job missing search_id")
                leads = (
                    self.session.query(DiscoveredLead)
                    .filter(
                        DiscoveredLead.search_id == job.search_id,
                        DiscoveredLead.user_id == job.user_id,
                        DiscoveredLead.is_duplicate.is_(False),
                        DiscoveredLead.website_url.isnot(None),
                    )
                    .all()
                )
                job.total_leads = len(leads)
                self.session.flush()

                for lead in leads:
                    try:
                        self._enrich_lead(job, lead.id)
                    except Exception as exc:
                        logger.exception(
                            "enrichment_lead_failed",
                            job_id=str(job_id),
                            lead_id=str(lead.id),
                        )
                        job.failed_leads += 1
                        self._upsert_failed(job, lead, str(exc))
                    job.processed_leads += 1
                    self.session.flush()

            job.status = EnrichmentStatus.COMPLETED.value
            job.completed_at = datetime.now(UTC)
            logger.info(
                "enrichment_job_completed",
                job_id=str(job_id),
                processed=job.processed_leads,
                failed=job.failed_leads,
            )
        except Exception as exc:
            logger.exception("enrichment_job_failed", job_id=str(job_id))
            job.status = EnrichmentStatus.FAILED.value
            job.error_message = str(exc)[:2000]
            job.completed_at = datetime.now(UTC)

        self.session.flush()
        return job

    def _enrich_lead(self, job: EnrichmentJob, lead_id: uuid.UUID) -> BusinessEnrichment:
        lead = self.session.get(DiscoveredLead, lead_id)
        if lead is None:
            raise ValueError(f"Lead {lead_id} not found")
        if not lead.website_url:
            raise ValueError(f"Lead {lead_id} has no website URL")

        enrichment = (
            self.session.query(BusinessEnrichment)
            .filter(BusinessEnrichment.lead_id == lead_id)
            .one_or_none()
        )
        if enrichment is None:
            enrichment = BusinessEnrichment(
                lead_id=lead_id,
                user_id=job.user_id,
                job_id=job.id,
                status=EnrichmentStatus.RUNNING.value,
            )
            self.session.add(enrichment)
        else:
            enrichment.job_id = job.id
            enrichment.status = EnrichmentStatus.RUNNING.value
            enrichment.error_message = None
        self.session.flush()

        result = self.engine.enrich(
            lead.website_url,
            fallback_name=lead.business_name,
        )

        if result.get("status") == "failed":
            enrichment.status = EnrichmentStatus.FAILED.value
            enrichment.error_message = result.get("error_message")
        else:
            enrichment.status = EnrichmentStatus.COMPLETED.value
            enrichment.company_name = result.get("company_name")
            enrichment.about_us_content = result.get("about_us_content")
            enrichment.services = result.get("services")
            enrichment.contact_page_data = result.get("contact_page_data")
            enrichment.email_addresses = result.get("email_addresses")
            enrichment.phone_numbers = result.get("phone_numbers")
            enrichment.team_members = result.get("team_members")
            enrichment.business_description = result.get("business_description")
            enrichment.technology_stack = result.get("technology_stack")
            enrichment.cms_platform = result.get("cms_platform")
            enrichment.cms_detected = result.get("cms_detected")
            enrichment.pages_crawled = result.get("pages_crawled")
            enrichment.raw_extraction = result.get("raw_extraction")
            enrichment.enriched_at = datetime.now(UTC)
            enrichment.error_message = None

            if result.get("email_addresses") and not lead.email_address:
                lead.email_address = result["email_addresses"][0]
            if result.get("phone_numbers") and not lead.phone_number:
                lead.phone_number = result["phone_numbers"][0]

        self.session.flush()
        if enrichment.status == EnrichmentStatus.COMPLETED.value:
            from app.services.scoring.auto_score import auto_score_lead

            auto_score_lead(self.session, lead_id, job.user_id)
        return enrichment

    def _upsert_failed(
        self, job: EnrichmentJob, lead: DiscoveredLead, error: str
    ) -> None:
        enrichment = (
            self.session.query(BusinessEnrichment)
            .filter(BusinessEnrichment.lead_id == lead.id)
            .one_or_none()
        )
        if enrichment is None:
            enrichment = BusinessEnrichment(
                lead_id=lead.id,
                user_id=job.user_id,
                job_id=job.id,
            )
            self.session.add(enrichment)
        enrichment.status = EnrichmentStatus.FAILED.value
        enrichment.error_message = error[:2000]
        self.session.flush()
