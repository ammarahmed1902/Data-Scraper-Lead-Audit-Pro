"""PDF report generation using ReportLab."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
        subheading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = styles["BodyText"]

        ai = audit_data.get("ai_content") or {}
        story: list[Any] = []

        story.append(Paragraph(brand_name, title_style))
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(
            Paragraph(
                f"Generated {datetime.now(UTC).strftime('%B %d, %Y at %H:%M UTC')}",
                styles["Normal"],
            )
        )
        if audit_data.get("company_name"):
            story.append(Paragraph(f"Client: {audit_data['company_name']}", styles["Normal"]))
        if audit_data.get("url"):
            story.append(Paragraph(f"URL: {audit_data['url']}", styles["Normal"]))
        story.append(Spacer(1, 0.25 * inch))

        overall = audit_data.get("overall_score")
        score_data = [
            ["Category", "Score"],
            ["Overall", f"{overall}/100" if overall is not None else "N/A"],
            ["SEO", self._score_cell(audit_data.get("seo_score"))],
            ["Performance", self._score_cell(audit_data.get("performance_score"))],
            ["Technical", self._score_cell(audit_data.get("technical_score"))],
        ]
        score_table = Table(score_data, colWidths=[3 * inch, 2 * inch])
        score_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), brand_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ])
        )
        story.append(score_table)
        story.append(Spacer(1, 0.2 * inch))

        self._add_section(story, "Executive Summary", heading_style, body_style,
                          ai.get("executive_summary") or audit_data.get("summary"))
        self._add_section(story, "SEO Summary", heading_style, body_style, ai.get("seo_summary"))
        self._add_section(story, "Performance Summary", heading_style, body_style,
                          ai.get("performance_summary"))
        self._add_section(story, "Technical Summary", heading_style, body_style,
                          ai.get("technical_summary"))
        self._add_section(story, "Opportunity Summary", heading_style, body_style,
                          ai.get("opportunity_summary"))

        recs = ai.get("client_recommendations") or []
        if recs:
            story.append(Paragraph("Client Recommendations", heading_style))
            for rec in recs[:12]:
                story.append(Paragraph(
                    f"• <b>[{rec.get('priority', 'medium').upper()}] {rec.get('title', '')}</b>: "
                    f"{rec.get('description', '')}",
                    body_style,
                ))

        points = ai.get("cold_calling_talking_points") or []
        if points:
            story.append(PageBreak())
            story.append(Paragraph("Sales Enablement", heading_style))
            story.append(Paragraph("Cold Calling Talking Points", subheading_style))
            for point in points:
                story.append(Paragraph(f"• {point}", body_style))

        pitch = ai.get("sales_pitch_summary")
        if pitch:
            story.append(Paragraph("Sales Pitch Summary", subheading_style))
            story.append(Paragraph(pitch, body_style))

        outreach = ai.get("outreach_recommendations") or []
        if outreach:
            story.append(Paragraph("Outreach Recommendations", subheading_style))
            for item in outreach:
                story.append(Paragraph(
                    f"• <b>{item.get('channel', '')}</b> ({item.get('timing', '')}): "
                    f"{item.get('message', '')}",
                    body_style,
                ))

        story.append(PageBreak())
        for section_key, section_title in [
            ("seo", "SEO Analysis Details"),
            ("performance", "Performance Analysis Details"),
            ("technical", "Technical Analysis Details"),
        ]:
            section = audit_data.get(section_key) or {}
            story.append(Paragraph(section_title, heading_style))
            story.append(Paragraph(f"Score: {section.get('score', 'N/A')}/100", body_style))
            for issue in (section.get("issues") or {}).get("items", [])[:8]:
                story.append(Paragraph(
                    f"• [{issue.get('severity', 'info').upper()}] {issue.get('message', '')}",
                    body_style,
                ))

        doc.build(story)
        return str(file_path), file_path.stat().st_size

    @staticmethod
    def _score_cell(score) -> str:
        return f"{score}/100" if score is not None else "N/A"

    @staticmethod
    def _add_section(story, title, heading_style, body_style, text):
        if not text:
            return
        story.append(Paragraph(title, heading_style))
        for para in str(text).split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), body_style))
        story.append(Spacer(1, 0.1 * inch))
