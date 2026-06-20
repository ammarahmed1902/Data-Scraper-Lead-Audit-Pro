"""Technical analysis service — SSL, headers, security, crawlability."""

from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import structlog

from app.services.accessibility_service import AccessibilityAnalyzer
from app.services.scraper.html_parser import HtmlParser
from app.services.scraper.page_fetcher import FetchResult, PageFetcher

logger = structlog.get_logger(__name__)

SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
    "x-xss-protection",
]


class TechnicalAnalyzer:
    def __init__(self, fetcher: PageFetcher | None = None):
        self.fetcher = fetcher or PageFetcher()

    def analyze(
        self,
        url: str,
        page: FetchResult | None = None,
        lighthouse_accessibility_score: float | None = None,
    ) -> dict[str, Any]:
        page = page or self.fetcher.fetch(url)
        parsed = urlparse(page.final_url or url)
        hostname = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        ssl_info = self._check_ssl(hostname, port if parsed.scheme == "https" else 443)
        security_headers = self._analyze_security_headers(page.headers)
        technologies = self._detect_technologies(page)
        dns_records = self._resolve_dns(hostname)

        robots_meta = None
        mobile_friendly = False
        indexable = True
        crawlable = True
        if page.html:
            parser = HtmlParser(page.html, page.final_url)
            robots_meta = parser.get_robots_meta()
            mobile_friendly = parser.is_mobile_friendly()
            if robots_meta:
                if "noindex" in robots_meta:
                    indexable = False
                if "nofollow" in robots_meta:
                    crawlable = False

        issues, recommendations = self._build_issues(
            page=page,
            ssl_info=ssl_info,
            security_headers=security_headers,
            mobile_friendly=mobile_friendly,
            indexable=indexable,
            crawlable=crawlable,
        )

        a11y_data = AccessibilityAnalyzer().analyze(
            page, lighthouse_score=lighthouse_accessibility_score
        )
        issues.extend(a11y_data["issues"]["items"])
        recommendations.extend(a11y_data["recommendations"]["items"])

        score = self._calculate_score(issues)
        # Blend technical security score with accessibility
        if a11y_data.get("score") is not None:
            score = round((score * 0.65) + (a11y_data["score"] * 0.35), 1)

        ssl_expiry_raw = ssl_info.get("expiry")
        ssl_expiry = (
            datetime.fromisoformat(ssl_expiry_raw)
            if isinstance(ssl_expiry_raw, str) and ssl_expiry_raw
            else ssl_expiry_raw
        )

        return {
            "score": score,
            "ssl_valid": ssl_info.get("valid"),
            "ssl_expiry": ssl_expiry,
            "http_status_code": page.status_code,
            "server_header": page.headers.get("server"),
            "mobile_friendly": mobile_friendly,
            "indexable": indexable,
            "accessibility_score": a11y_data.get("score"),
            "technologies": technologies,
            "security_headers": security_headers,
            "dns_records": dns_records,
            "issues": {
                "items": issues,
                "meta": {
                    "robots_meta": robots_meta,
                    "mobile_friendly": mobile_friendly,
                    "indexable": indexable,
                    "crawlable": crawlable,
                    "ssl_details": ssl_info,
                    "uses_https": parsed.scheme == "https",
                    "accessibility": a11y_data.get("checks"),
                    "lighthouse_accessibility": lighthouse_accessibility_score,
                },
            },
            "recommendations": {"items": recommendations},
        }

    def _check_ssl(self, hostname: str, port: int) -> dict[str, Any]:
        if not hostname:
            return {"valid": False, "expiry": None, "error": "No hostname"}
        try:
            context = ssl.create_default_context()
            with (
                socket.create_connection((hostname, port), timeout=10) as sock,
                context.wrap_socket(sock, server_hostname=hostname) as secure,
            ):
                cert = secure.getpeercert()
                expiry_str = cert.get("notAfter")
                expiry = None
                if expiry_str:
                    expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z").replace(
                        tzinfo=UTC
                    )
                days_left = (expiry - datetime.now(UTC)).days if expiry else None
                return {
                    "valid": True,
                    "expiry": expiry.isoformat() if expiry else None,
                    "days_until_expiry": days_left,
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                }
        except Exception as exc:
            return {"valid": False, "expiry": None, "error": str(exc)}

    def _analyze_security_headers(self, headers: dict[str, str]) -> dict[str, Any]:
        present: dict[str, str] = {}
        missing: list[str] = []
        for header in SECURITY_HEADERS:
            if header in headers:
                present[header] = headers[header]
            else:
                missing.append(header)
        return {
            "present": present,
            "missing": missing,
            "score": round((len(present) / len(SECURITY_HEADERS)) * 100, 1),
        }

    def _detect_technologies(self, page: FetchResult) -> dict[str, Any]:
        detected: list[str] = []
        server = page.headers.get("server", "").lower()
        powered = page.headers.get("x-powered-by", "").lower()
        html_lower = page.html.lower() if page.html else ""

        if "nginx" in server:
            detected.append("Nginx")
        if "apache" in server:
            detected.append("Apache")
        if "cloudflare" in server or "cf-ray" in page.headers:
            detected.append("Cloudflare")
        if "wp-content" in html_lower or "wordpress" in html_lower:
            detected.append("WordPress")
        if "shopify" in html_lower:
            detected.append("Shopify")
        if "wix.com" in html_lower:
            detected.append("Wix")
        if "squarespace" in html_lower:
            detected.append("Squarespace")
        if "next" in powered or "__next" in html_lower:
            detected.append("Next.js")
        if "react" in powered or "reactroot" in html_lower:
            detected.append("React")
        if powered:
            detected.append(f"X-Powered-By: {page.headers.get('x-powered-by')}")

        return {"detected": list(dict.fromkeys(detected)), "server": page.headers.get("server")}

    def _resolve_dns(self, hostname: str) -> dict[str, Any]:
        if not hostname:
            return {}
        records: dict[str, list[str]] = {"A": [], "AAAA": []}
        try:
            for family in (socket.AF_INET, socket.AF_INET6):
                try:
                    results = socket.getaddrinfo(hostname, None, family)
                    key = "A" if family == socket.AF_INET else "AAAA"
                    for item in results:
                        addr = item[4][0]
                        if addr not in records[key]:
                            records[key].append(addr)
                except socket.gaierror:
                    continue
        except Exception as exc:
            records["error"] = [str(exc)]
        return records

    def _build_issues(
        self,
        *,
        page: FetchResult,
        ssl_info: dict[str, Any],
        security_headers: dict[str, Any],
        mobile_friendly: bool,
        indexable: bool,
        crawlable: bool,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        if page.error or page.status_code >= 400:
            issues.append({"severity": "critical", "code": "HTTP_ERROR", "message": page.error or f"HTTP {page.status_code}"})
            recommendations.append({"priority": "high", "title": "Fix HTTP errors", "description": "Ensure the page returns a 2xx status code."})

        parsed = urlparse(page.final_url or "")
        if parsed.scheme != "https":
            issues.append({"severity": "critical", "code": "NO_HTTPS", "message": "Site is not served over HTTPS"})
            recommendations.append({"priority": "high", "title": "Enable HTTPS", "description": "Install an SSL certificate and redirect HTTP to HTTPS."})

        if not ssl_info.get("valid"):
            issues.append({"severity": "critical", "code": "INVALID_SSL", "message": ssl_info.get("error", "SSL certificate is invalid")})
            recommendations.append({"priority": "high", "title": "Fix SSL certificate", "description": "Renew or install a valid TLS certificate."})
        elif ssl_info.get("days_until_expiry") is not None and ssl_info["days_until_expiry"] < 30:
            issues.append({"severity": "high", "code": "SSL_EXPIRING", "message": f"SSL expires in {ssl_info['days_until_expiry']} days"})
            recommendations.append({"priority": "high", "title": "Renew SSL certificate", "description": "Certificate expires soon — renew before expiry."})

        for header in security_headers.get("missing", []):
            severity = "high" if header == "strict-transport-security" else "medium"
            issues.append({"severity": severity, "code": f"MISSING_{header.upper().replace('-', '_')}", "message": f"Missing {header} header"})
            recommendations.append({"priority": severity, "title": f"Add {header}", "description": f"Configure the {header} response header."})

        if not mobile_friendly:
            issues.append({"severity": "high", "code": "NOT_MOBILE_RESPONSIVE", "message": "Missing responsive viewport configuration"})
            recommendations.append({"priority": "high", "title": "Improve mobile responsiveness", "description": "Add viewport meta tag and test on mobile devices."})

        if not indexable:
            issues.append({"severity": "medium", "code": "NOINDEX", "message": "Page has noindex directive"})
            recommendations.append({"priority": "medium", "title": "Review indexing settings", "description": "Remove noindex if this page should appear in search results."})

        if not crawlable:
            issues.append({"severity": "low", "code": "NOFOLLOW", "message": "Page has nofollow directive"})

        return issues, recommendations

    def _calculate_score(self, issues: list[dict[str, Any]]) -> float:
        score = 100.0
        weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        for issue in issues:
            score -= weights.get(issue.get("severity", "low"), 3)
        return max(0.0, min(100.0, round(score, 1)))


class TechnicalService:
    def analyze(
        self,
        url: str,
        page: FetchResult | None = None,
        lighthouse_accessibility_score: float | None = None,
    ) -> dict[str, Any]:
        return TechnicalAnalyzer().analyze(
            url, page, lighthouse_accessibility_score=lighthouse_accessibility_score
        )
