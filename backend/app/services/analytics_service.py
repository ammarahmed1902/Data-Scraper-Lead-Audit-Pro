"""Analytics aggregation service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditReport, AuditStatus
from app.models.website import Website
from app.schemas.analytics import (
    AnalyticsOverview,
    AuditTrendPoint,
    DashboardStats,
    ScoreDistribution,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview(
        self,
        owner_id: uuid.UUID,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> AnalyticsOverview:
        stats = await self._get_stats(owner_id, date_from, date_to)
        distribution = await self._get_score_distribution(owner_id)
        trends = await self._get_trends(owner_id, days=30)
        top_issues = await self._get_top_issues(owner_id)
        return AnalyticsOverview(
            stats=stats,
            score_distribution=distribution,
            audit_trends=trends,
            top_issues=top_issues,
        )

    async def _get_stats(
        self, owner_id: uuid.UUID, date_from: str | None, date_to: str | None
    ) -> DashboardStats:
        website_count = await self.session.scalar(
            select(func.count()).select_from(Website).where(Website.owner_id == owner_id)
        )
        audit_query = (
            select(AuditReport)
            .join(Website, AuditReport.website_id == Website.id)
            .where(Website.owner_id == owner_id)
        )
        audits = (await self.session.execute(audit_query)).scalars().all()

        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        completed = [a for a in audits if a.status == AuditStatus.COMPLETED.value]
        pending = [a for a in audits if a.status in (AuditStatus.PENDING.value, AuditStatus.RUNNING.value)]
        scores = [a.overall_score for a in completed if a.overall_score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        return DashboardStats(
            total_websites=website_count or 0,
            total_audits=len(audits),
            pending_audits=len(pending),
            completed_audits=len(completed),
            average_score=avg_score,
            audits_this_week=sum(1 for a in audits if a.created_at >= week_ago),
            audits_this_month=sum(1 for a in audits if a.created_at >= month_ago),
        )

    async def _get_score_distribution(self, owner_id: uuid.UUID) -> list[ScoreDistribution]:
        audits = (
            await self.session.execute(
                select(AuditReport.overall_score)
                .join(Website, AuditReport.website_id == Website.id)
                .where(
                    Website.owner_id == owner_id,
                    AuditReport.status == AuditStatus.COMPLETED.value,
                    AuditReport.overall_score.isnot(None),
                )
            )
        ).scalars().all()

        buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
        for score in audits:
            if score is None:
                continue
            if score <= 25:
                buckets["0-25"] += 1
            elif score <= 50:
                buckets["26-50"] += 1
            elif score <= 75:
                buckets["51-75"] += 1
            else:
                buckets["76-100"] += 1

        return [ScoreDistribution(range_label=k, count=v) for k, v in buckets.items()]

    async def _get_trends(self, owner_id: uuid.UUID, days: int = 30) -> list[AuditTrendPoint]:
        since = datetime.now(UTC) - timedelta(days=days)
        audits = (
            await self.session.execute(
                select(AuditReport)
                .join(Website, AuditReport.website_id == Website.id)
                .where(Website.owner_id == owner_id, AuditReport.created_at >= since)
            )
        ).scalars().all()

        by_date: dict[str, list[AuditReport]] = {}
        for audit in audits:
            key = audit.created_at.strftime("%Y-%m-%d")
            by_date.setdefault(key, []).append(audit)

        return [
            AuditTrendPoint(
                date=date,
                count=len(day_audits),
                average_score=round(
                    sum(a.overall_score for a in day_audits if a.overall_score is not None)
                    / max(1, len([a for a in day_audits if a.overall_score is not None])),
                    1,
                )
                if any(a.overall_score is not None for a in day_audits)
                else None,
            )
            for date, day_audits in sorted(by_date.items())
        ]

    async def _get_top_issues(self, owner_id: uuid.UUID, limit: int = 10) -> list[dict]:
        from app.models.audit import SEOReport, TechnicalReport

        issue_counts: dict[str, int] = {}

        seo_issues_rows = (
            await self.session.execute(
                select(SEOReport.issues)
                .join(AuditReport, SEOReport.audit_report_id == AuditReport.id)
                .join(Website, AuditReport.website_id == Website.id)
                .where(Website.owner_id == owner_id)
            )
        ).scalars().all()

        for issues in seo_issues_rows:
            items = (issues or {}).get("items", [])
            for item in items:
                code = item.get("code", "UNKNOWN")
                issue_counts[code] = issue_counts.get(code, 0) + 1

        tech_issues_rows = (
            await self.session.execute(
                select(TechnicalReport.issues)
                .join(AuditReport, TechnicalReport.audit_report_id == AuditReport.id)
                .join(Website, AuditReport.website_id == Website.id)
                .where(Website.owner_id == owner_id)
            )
        ).scalars().all()

        for issues in tech_issues_rows:
            items = (issues or {}).get("items", [])
            for item in items:
                code = item.get("code", "UNKNOWN")
                issue_counts[code] = issue_counts.get(code, 0) + 1

        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"code": code, "count": count} for code, count in sorted_issues]

    async def get_trends(self, owner_id: uuid.UUID, period: str) -> list[AuditTrendPoint]:
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
        return await self._get_trends(owner_id, days)

    async def get_score_distribution(self, owner_id: uuid.UUID) -> list[ScoreDistribution]:
        return await self._get_score_distribution(owner_id)

    async def get_top_issues(self, owner_id: uuid.UUID, limit: int = 10) -> list[dict]:
        return await self._get_top_issues(owner_id, limit)
