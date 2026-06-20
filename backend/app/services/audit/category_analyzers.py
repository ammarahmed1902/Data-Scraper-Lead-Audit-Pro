"""Specialized audit category analyzers (functional, mobile, marketing, CRO, etc.)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.services.audit.category_helpers import build_category, score_from_issues
from app.services.scoring.opportunity_detector import CONVERSION_PATTERNS, TRACKING_PATTERNS
from app.services.scraper.html_parser import HtmlParser
from app.services.scraper.page_fetcher import FetchResult

LEGAL_PATH_HINTS = ("privacy", "terms", "cookie", "legal", "disclaimer")
SOCIAL_DOMAINS = (
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
)
TRUST_SIGNAL_PATTERNS = (
    r"\b(?:ssl|secure|encrypted)\b",
    r"\b(?:bbb|accredited|certified|licensed|insured)\b",
    r"\b(?:testimonial|review|rating|★|stars)\b",
    r"\b(?:money[- ]back|satisfaction guarantee|warranty)\b",
)


class FunctionalAnalyzer:
    """Verify buttons, forms, links, and interactive elements."""

    def analyze(self, page: FetchResult, parser: HtmlParser) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        if page.error or not page.html:
            issues.append({
                "severity": "critical",
                "code": "PAGE_UNREACHABLE",
                "message": page.error or "Page could not be fetched",
            })
            return build_category(score=0, issues=issues, recommendations=recommendations)

        forms = parser.soup.find_all("form")
        buttons = parser.soup.find_all(["button", "input"])
        submit_buttons = [
            b for b in buttons
            if b.name == "button" or b.get("type") in ("submit", "button")
        ]
        nav = parser.soup.find("nav") or parser.soup.find(attrs={"role": "navigation"})
        links = parser.get_links()
        internal = [l for l in links if l["type"] == "internal"]
        external = [l for l in links if l["type"] == "external"]
        scripts = parser.soup.find_all("script", src=True)
        empty_links = [
            a for a in parser.soup.find_all("a", href=True)
            if not a.get_text(strip=True) and not a.get("aria-label")
        ]

        if not forms and not any(
            re.search(p, page.html, re.I) for p in CONVERSION_PATTERNS[:2]
        ):
            issues.append({
                "severity": "medium",
                "code": "NO_FORMS",
                "message": "No HTML forms detected on the page",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Add contact or lead forms",
                "description": "Provide at least one form for user interaction and lead capture.",
            })

        if not submit_buttons:
            issues.append({
                "severity": "low",
                "code": "NO_BUTTONS",
                "message": "No interactive buttons found",
            })

        if not nav:
            issues.append({
                "severity": "medium",
                "code": "NO_NAVIGATION",
                "message": "No <nav> or navigation landmark detected",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Add clear navigation",
                "description": "Use a <nav> element or role=navigation for primary menus.",
            })

        if empty_links:
            issues.append({
                "severity": "medium",
                "code": "EMPTY_LINKS",
                "message": f"{len(empty_links)} links have no accessible text",
            })

        if page.status_code >= 400:
            issues.append({
                "severity": "critical",
                "code": "HTTP_ERROR",
                "message": f"Page returned HTTP {page.status_code}",
            })

        if len(scripts) > 40:
            issues.append({
                "severity": "low",
                "code": "HEAVY_JAVASCRIPT",
                "message": f"{len(scripts)} external script tags may affect reliability",
            })
            recommendations.append({
                "priority": "low",
                "title": "Audit JavaScript dependencies",
                "description": "Reduce script count and test critical paths after JS loads.",
            })

        checks = {
            "forms_count": len(forms),
            "buttons_count": len(submit_buttons),
            "internal_links": len(internal),
            "external_links": len(external),
            "script_tags": len(scripts),
            "has_navigation": bool(nav),
            "http_status": page.status_code,
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class MobileAnalyzer:
    """Mobile responsiveness and touch usability heuristics."""

    def analyze(self, page: FetchResult, parser: HtmlParser) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        viewport = parser.get_viewport_meta()
        mobile_friendly = parser.is_mobile_friendly()
        small_buttons = 0
        touch_targets = 0

        for el in parser.soup.find_all(["button", "a", "input"]):
            style = el.get("style", "")
            if "font-size" in style and any(s in style for s in ("10px", "11px", "12px")):
                small_buttons += 1
            if el.name in ("button", "a") and el.get_text(strip=True):
                touch_targets += 1

        if not viewport:
            issues.append({
                "severity": "critical",
                "code": "NO_VIEWPORT",
                "message": "Missing viewport meta tag",
            })
            recommendations.append({
                "priority": "high",
                "title": "Add viewport meta tag",
                "description": 'Use <meta name="viewport" content="width=device-width, initial-scale=1">.',
            })
        elif not mobile_friendly:
            issues.append({
                "severity": "high",
                "code": "INVALID_VIEWPORT",
                "message": "Viewport meta tag does not include width=device-width",
            })

        fixed_width_tables = len(parser.soup.find_all("table", width=True))
        if fixed_width_tables:
            issues.append({
                "severity": "medium",
                "code": "FIXED_WIDTH_LAYOUT",
                "message": f"{fixed_width_tables} tables use fixed widths",
            })

        if small_buttons > 3:
            issues.append({
                "severity": "medium",
                "code": "SMALL_TOUCH_TARGETS",
                "message": f"{small_buttons} elements may have undersized touch targets",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Increase touch target size",
                "description": "Buttons and links should be at least 44×44px with adequate spacing.",
            })

        images = parser.soup.find_all("img")
        missing_srcset = sum(1 for img in images if not img.get("srcset") and img.get("src"))
        if images and missing_srcset / max(len(images), 1) > 0.8:
            issues.append({
                "severity": "low",
                "code": "NO_RESPONSIVE_IMAGES",
                "message": "Most images lack srcset for responsive delivery",
            })

        checks = {
            "viewport_meta": viewport or "missing",
            "mobile_friendly": mobile_friendly,
            "touch_targets": touch_targets,
            "responsive_image_ratio": round(
                1 - (missing_srcset / max(len(images), 1)), 2
            ) if images else 1,
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class SecurityAnalyzer:
    """SSL, HTTPS, headers, mixed content, and cookie security."""

    def analyze(
        self,
        page: FetchResult,
        *,
        tech_data: dict[str, Any],
    ) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        parsed = urlparse(page.final_url or page.url)
        uses_https = parsed.scheme == "https"
        ssl_valid = tech_data.get("ssl_valid")
        security_headers = tech_data.get("security_headers") or {}
        missing_headers = security_headers.get("missing", [])

        if not uses_https:
            issues.append({
                "severity": "critical",
                "code": "NO_HTTPS",
                "message": "Site is not served over HTTPS",
            })
            recommendations.append({
                "priority": "high",
                "title": "Enable HTTPS",
                "description": "Install an SSL certificate and redirect HTTP to HTTPS.",
            })

        if ssl_valid is False:
            issues.append({
                "severity": "critical",
                "code": "INVALID_SSL",
                "message": "SSL certificate is invalid or expired",
            })

        for header in missing_headers:
            severity = "high" if header == "strict-transport-security" else "medium"
            issues.append({
                "severity": severity,
                "code": f"MISSING_{header.upper().replace('-', '_')}",
                "message": f"Missing security header: {header}",
            })

        if missing_headers:
            recommendations.append({
                "priority": "high",
                "title": "Configure security headers",
                "description": "Add HSTS, CSP, X-Frame-Options, and related headers.",
            })

        mixed_content = 0
        if page.html and uses_https:
            mixed_content = len(
                re.findall(r'(?:src|href)=["\']http://[^"\']+', page.html, re.I)
            )
            if mixed_content:
                issues.append({
                    "severity": "high",
                    "code": "MIXED_CONTENT",
                    "message": f"{mixed_content} HTTP resources on HTTPS page",
                })
                recommendations.append({
                    "priority": "high",
                    "title": "Fix mixed content",
                    "description": "Serve all assets over HTTPS to avoid browser warnings.",
                })

        set_cookie = page.headers.get("set-cookie", "")
        if set_cookie and "secure" not in set_cookie.lower():
            issues.append({
                "severity": "medium",
                "code": "INSECURE_COOKIE",
                "message": "Set-Cookie header missing Secure flag",
            })

        checks = {
            "uses_https": uses_https,
            "ssl_valid": ssl_valid,
            "security_headers_present": len(security_headers.get("present", {})),
            "security_headers_missing": len(missing_headers),
            "mixed_content_count": mixed_content,
        }
        header_score = security_headers.get("score")
        score = header_score if header_score is not None else score_from_issues(issues)
        if ssl_valid is False:
            score = min(score, 20.0)
        return build_category(
            score=round(score, 1),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class TechnicalSEOAnalyzer:
    """Crawlability, indexability, redirects, sitemap, robots, structured data."""

    def analyze(
        self,
        page: FetchResult,
        parser: HtmlParser,
        *,
        seo_data: dict[str, Any],
        tech_data: dict[str, Any],
    ) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        seo_issues = (seo_data.get("issues") or {}).get("items", [])
        for item in seo_issues:
            if item.get("code") in (
                "MISSING_SITEMAP",
                "MISSING_ROBOTS_TXT",
                "MISSING_CANONICAL",
                "MISSING_STRUCTURED_DATA",
                "BROKEN_LINKS",
            ):
                issues.append(item)

        if tech_data.get("indexable") is False:
            issues.append({
                "severity": "high",
                "code": "NOINDEX",
                "message": "Page has noindex directive",
            })

        redirect_count = len(page.redirects)
        if redirect_count > 2:
            issues.append({
                "severity": "medium",
                "code": "REDIRECT_CHAIN",
                "message": f"{redirect_count} redirects before final URL",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Shorten redirect chains",
                "description": "Use a single 301 redirect to the canonical URL.",
            })

        if page.url.rstrip("/") != page.final_url.rstrip("/"):
            issues.append({
                "severity": "low",
                "code": "URL_NORMALIZATION",
                "message": "Requested URL differs from final URL",
            })

        structured = parser.get_structured_data()
        h1s = parser.get_headings(1)
        canonical = parser.get_canonical()

        checks = {
            "has_sitemap": seo_data.get("has_sitemap"),
            "has_robots_txt": seo_data.get("has_robots_txt"),
            "canonical_url": canonical,
            "structured_data_schemas": len(structured),
            "indexable": tech_data.get("indexable"),
            "redirect_count": redirect_count,
            "h1_count": len(h1s),
            "broken_links": seo_data.get("broken_links", 0),
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class SEOStrategyAnalyzer:
    """Content depth, keyword alignment, internal linking strategy."""

    def analyze(self, parser: HtmlParser, *, domain: str | None = None) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        text = parser.soup.get_text(" ", strip=True)
        word_count = len(text.split())
        title = parser.get_title() or ""
        h1s = parser.get_headings(1)
        h2s = parser.get_headings(2)
        links = parser.get_links()
        internal = [l for l in links if l["type"] == "internal"]

        if word_count < 300:
            issues.append({
                "severity": "high",
                "code": "THIN_CONTENT",
                "message": f"Page has only ~{word_count} words (thin content)",
            })
            recommendations.append({
                "priority": "high",
                "title": "Expand page content",
                "description": "Add substantive copy (300+ words) targeting user intent.",
            })

        if h1s and title and h1s[0].lower() not in title.lower() and title.lower() not in h1s[0].lower():
            issues.append({
                "severity": "medium",
                "code": "TITLE_H1_MISMATCH",
                "message": "Title tag and H1 are not aligned",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Align title and H1",
                "description": "Use consistent primary keywords in title and H1.",
            })

        if len(internal) < 3:
            issues.append({
                "severity": "medium",
                "code": "WEAK_INTERNAL_LINKING",
                "message": f"Only {len(internal)} internal links found",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Strengthen internal linking",
                "description": "Link to related service pages and cornerstone content.",
            })

        if len(h2s) < 2 and word_count > 400:
            issues.append({
                "severity": "low",
                "code": "WEAK_CONTENT_STRUCTURE",
                "message": "Long content lacks H2 section structure",
            })

        checks = {
            "word_count": word_count,
            "internal_links": len(internal),
            "h2_sections": len(h2s),
            "title_length": len(title),
            "domain": domain,
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class MarketingAnalyzer:
    """Brand presence, tracking, social integration, trust signals."""

    def analyze(self, page: FetchResult, parser: HtmlParser) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []
        html_lower = (page.html or "").lower()

        tracking_found: list[str] = []
        for name, patterns in TRACKING_PATTERNS.items():
            if any(re.search(p, html_lower, re.I) for p in patterns):
                tracking_found.append(name)

        social_links = [
            l for l in parser.get_links()
            if any(d in l["url"].lower() for d in SOCIAL_DOMAINS)
        ]
        og = parser.get_open_graph()
        trust_signals = sum(
            1 for pattern in TRUST_SIGNAL_PATTERNS if re.search(pattern, html_lower, re.I)
        )

        if not tracking_found:
            issues.append({
                "severity": "high",
                "code": "NO_ANALYTICS",
                "message": "No analytics or tracking pixels detected",
            })
            recommendations.append({
                "priority": "high",
                "title": "Install analytics",
                "description": "Add Google Analytics, GTM, or equivalent conversion tracking.",
            })

        if not social_links:
            issues.append({
                "severity": "medium",
                "code": "NO_SOCIAL_LINKS",
                "message": "No social media profile links found",
            })

        if not og.get("og:image"):
            issues.append({
                "severity": "low",
                "code": "NO_SOCIAL_IMAGE",
                "message": "Missing og:image for social sharing",
            })

        if trust_signals < 2:
            issues.append({
                "severity": "medium",
                "code": "WEAK_TRUST_SIGNALS",
                "message": "Limited trust signals (reviews, certifications, guarantees)",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Add trust signals",
                "description": "Display testimonials, certifications, and security badges.",
            })

        checks = {
            "tracking_tools": tracking_found,
            "social_profiles": len(social_links),
            "open_graph_complete": bool(og.get("og:title") and og.get("og:description")),
            "trust_signal_count": trust_signals,
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class CROAnalyzer:
    """Conversion rate optimization — CTAs, forms, user journey."""

    def analyze(self, page: FetchResult, parser: HtmlParser) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []
        html = page.html or ""

        has_form = bool(re.search(CONVERSION_PATTERNS[1], html, re.I))
        has_submit = bool(re.search(CONVERSION_PATTERNS[0], html, re.I))
        has_cta_class = bool(re.search(CONVERSION_PATTERNS[4], html, re.I))
        has_tel = bool(re.search(CONVERSION_PATTERNS[2], html, re.I))
        has_mailto = bool(re.search(CONVERSION_PATTERNS[3], html, re.I))

        cta_buttons = parser.soup.find_all(
            ["a", "button"],
            class_=re.compile(r"cta|btn-primary|call-to-action|get-started|contact", re.I),
        )
        above_fold_cta = len(cta_buttons) > 0

        if not has_form and not has_submit:
            issues.append({
                "severity": "high",
                "code": "NO_LEAD_FORM",
                "message": "No lead capture form detected",
            })
            recommendations.append({
                "priority": "high",
                "title": "Add a lead generation form",
                "description": "Place a contact or quote form above the fold.",
            })

        if not (has_cta_class or cta_buttons):
            issues.append({
                "severity": "high",
                "code": "NO_CTA",
                "message": "No prominent call-to-action buttons found",
            })
            recommendations.append({
                "priority": "high",
                "title": "Improve CTA visibility",
                "description": "Use contrasting buttons with action-oriented copy.",
            })

        if not has_tel and not has_mailto:
            issues.append({
                "severity": "medium",
                "code": "NO_DIRECT_CONTACT",
                "message": "No click-to-call or mailto links",
            })

        if not above_fold_cta:
            recommendations.append({
                "priority": "medium",
                "title": "Test CTA placement",
                "description": "A/B test primary CTA above the fold vs. sticky footer bar.",
            })

        checks = {
            "has_form": has_form,
            "has_submit_button": has_submit,
            "cta_elements": len(cta_buttons),
            "has_click_to_call": has_tel,
            "has_email_link": has_mailto,
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class QAAnalyzer:
    """Quality assurance — favicon, legal pages, consistency checks."""

    def analyze(self, page: FetchResult, parser: HtmlParser) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        favicon = parser.soup.find("link", rel=re.compile(r"icon", re.I))
        lang = parser.soup.find("html")
        html_lang = lang.get("lang") if lang else None
        links = parser.get_links()

        legal_links = [
            l for l in links
            if any(hint in l["url"].lower() for hint in LEGAL_PATH_HINTS)
        ]

        if not favicon:
            issues.append({
                "severity": "low",
                "code": "MISSING_FAVICON",
                "message": "No favicon link tag found",
            })

        if not html_lang:
            issues.append({
                "severity": "medium",
                "code": "MISSING_HTML_LANG",
                "message": "HTML element missing lang attribute",
            })

        if not legal_links:
            issues.append({
                "severity": "medium",
                "code": "MISSING_LEGAL_PAGES",
                "message": "No privacy policy or terms links detected",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Add legal pages",
                "description": "Link to privacy policy and terms of service in the footer.",
            })

        duplicate_titles = len(parser.soup.find_all("title"))
        if duplicate_titles > 1:
            issues.append({
                "severity": "medium",
                "code": "DUPLICATE_TITLE_TAGS",
                "message": f"Found {duplicate_titles} <title> elements",
            })

        checks = {
            "has_favicon": bool(favicon),
            "html_lang": html_lang,
            "legal_page_links": len(legal_links),
            "title_tag_count": duplicate_titles,
        }
        return build_category(
            score=score_from_issues(issues),
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class AccessibilityCategoryAnalyzer:
    """Wrap accessibility analyzer output into category breakdown format."""

    def from_a11y_data(self, a11y_data: dict[str, Any]) -> dict[str, Any]:
        issues = (a11y_data.get("issues") or {}).get("items", [])
        recommendations = (a11y_data.get("recommendations") or {}).get("items", [])
        checks = a11y_data.get("checks") or {}
        score = a11y_data.get("score")
        return build_category(
            score=score,
            issues=issues,
            recommendations=recommendations,
            checks=checks,
        )


class TechnologyAnalyzer:
    """Technology stack summary for the Technology tab."""

    def analyze(self, tech_data: dict[str, Any]) -> dict[str, Any]:
        technologies = tech_data.get("technologies") or {}
        detected = technologies.get("detected", [])
        cms = next(
            (t for t in detected if t in ("WordPress", "Shopify", "Wix", "Squarespace", "Next.js")),
            None,
        )
        framework = next(
            (t for t in detected if t in ("Next.js", "React")),
            None,
        )
        checks = {
            "technology_stack": detected,
            "cms_platform": cms,
            "framework": framework,
            "server": technologies.get("server"),
        }
        return build_category(
            score=100.0 if detected else 70.0,
            issues=[],
            recommendations=[],
            checks=checks,
        )
