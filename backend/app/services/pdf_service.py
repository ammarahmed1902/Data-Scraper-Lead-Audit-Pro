"""PDF report generation using ReportLab."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings


class PDFService:
    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or settings.REPORT_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def generate_audit_pdf(
        self,
        *,
        report_id: uuid.UUID,
        title: str,
        audit_data: dict[str, Any],
        branding: dict[str, str] | None = None,
    ) -> tuple[str, int]:
        filename = f"report_{report_id}.pdf"
        file_path = self.storage_path / filename
        brand_name = (branding or {}).get("company_name", settings.APP_NAME)
        brand_color = colors.HexColor((branding or {}).get("primary_color", "#6366f1"))

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "BrandTitle",
            parent=styles["Title"],
            textColor=brand_color,
            fontSize=22,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            textColor=brand_color,
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
        )
        body_style = styles["BodyText"]

        story: list[Any] = []
        story.append(Paragraph(brand_name, title_style))
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(
            Paragraph(
                f"Generated {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.25 * inch))

        overall = audit_data.get("overall_score")
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(audit_data.get("summary") or "No summary available.", body_style))
        story.append(Spacer(1, 0.15 * inch))

        score_data = [
            ["Category", "Score"],
            ["Overall", f"{overall}/100" if overall is not None else "N/A"],
            ["SEO", f"{audit_data.get('seo_score')}/100" if audit_data.get("seo_score") is not None else "N/A"],
            ["Performance", f"{audit_data.get('performance_score')}/100" if audit_data.get("performance_score") is not None else "N/A"],
            ["Technical", f"{audit_data.get('technical_score')}/100" if audit_data.get("technical_score") is not None else "N/A"],
        ]
        score_table = Table(score_data, colWidths=[3 * inch, 2 * inch])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), brand_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(score_table)

        for section_key, section_title in [
            ("seo", "SEO Analysis"),
            ("performance", "Performance Analysis"),
            ("technical", "Technical Analysis"),
        ]:
            section = audit_data.get(section_key) or {}
            story.append(Paragraph(section_title, heading_style))
            story.append(Paragraph(f"Score: {section.get('score', 'N/A')}/100", body_style))

            issues = (section.get("issues") or {}).get("items", [])
            if issues:
                story.append(Paragraph("<b>Issues</b>", body_style))
                for issue in issues[:10]:
                    story.append(
                        Paragraph(
                            f"• [{issue.get('severity', 'info').upper()}] {issue.get('message', '')}",
                            body_style,
                        )
                    )

            recs = (section.get("recommendations") or {}).get("items", [])
            if recs:
                story.append(Spacer(1, 0.1 * inch))
                story.append(Paragraph("<b>Recommendations</b>", body_style))
                for rec in recs[:8]:
                    story.append(
                        Paragraph(
                            f"• <b>{rec.get('title', '')}</b>: {rec.get('description', '')}",
                            body_style,
                        )
                    )

        sales = audit_data.get("sales_opportunity")
        if sales:
            story.append(Paragraph("Sales Opportunity", heading_style))
            story.append(Paragraph(sales, body_style))

        doc.build(story)
        file_size = file_path.stat().st_size
        return str(file_path), file_size
