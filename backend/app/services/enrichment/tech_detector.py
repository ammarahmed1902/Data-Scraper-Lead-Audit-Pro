"""CMS and technology stack detection from HTML and headers."""

from __future__ import annotations

from typing import Any

from app.services.scraper.page_fetcher import FetchResult

CMS_PLATFORMS = (
    "wordpress",
    "shopify",
    "wix",
    "squarespace",
    "webflow",
    "react",
    "nextjs",
    "laravel",
    "php",
)


class TechStackDetector:
    """Detect CMS platforms and frameworks from page signals."""

    def detect(self, page: FetchResult) -> dict[str, Any]:
        html_lower = (page.html or "").lower()
        headers = {k.lower(): v for k, v in page.headers.items()}
        server = headers.get("server", "").lower()
        powered = headers.get("x-powered-by", "").lower()

        cms: dict[str, bool] = dict.fromkeys(CMS_PLATFORMS, False)
        stack: list[str] = []

        # WordPress
        if any(
            sig in html_lower
            for sig in ("wp-content", "wp-includes", "wordpress", "/xmlrpc.php")
        ):
            cms["wordpress"] = True
            stack.append("WordPress")

        # Shopify
        if any(sig in html_lower for sig in ("cdn.shopify.com", "shopify", "myshopify.com")):
            cms["shopify"] = True
            stack.append("Shopify")

        # Wix
        if any(sig in html_lower for sig in ("wix.com", "static.wixstatic.com", "x-wix-")):
            cms["wix"] = True
            stack.append("Wix")

        # Squarespace
        if any(sig in html_lower for sig in ("squarespace.com", "static.squarespace.com")):
            cms["squarespace"] = True
            stack.append("Squarespace")

        # Webflow
        if any(sig in html_lower for sig in ("webflow.com", "webflow.io", "data-wf-page")):
            cms["webflow"] = True
            stack.append("Webflow")

        # Next.js
        if any(sig in html_lower for sig in ("__next", "_next/static", "id=\"__next\"")):
            cms["nextjs"] = True
            stack.append("Next.js")

        # React
        if any(
            sig in html_lower
            for sig in ("reactroot", "data-reactroot", "react-dom", "__react")
        ) or "react" in powered:
            cms["react"] = True
            if "React" not in stack:
                stack.append("React")

        # Laravel
        if any(sig in html_lower for sig in ("laravel", "csrf-token")) and "laravel" in html_lower:
            cms["laravel"] = True
            stack.append("Laravel")
        if "laravel" in powered:
            cms["laravel"] = True
            if "Laravel" not in stack:
                stack.append("Laravel")

        # PHP
        if "php" in powered or ".php" in html_lower or "x-powered-by: php" in f"{powered}":
            cms["php"] = True
            stack.append("PHP")

        # Infrastructure hints
        if "nginx" in server and "Nginx" not in stack:
            stack.append("Nginx")
        if "apache" in server and "Apache" not in stack:
            stack.append("Apache")
        if headers.get("cf-ray") or "cloudflare" in server:
            stack.append("Cloudflare")

        primary = self._primary_cms(cms)
        return {
            "cms_detected": cms,
            "cms_platform": primary,
            "technology_stack": list(dict.fromkeys(stack)),
        }

    @staticmethod
    def _primary_cms(cms: dict[str, bool]) -> str | None:
        priority = (
            "wordpress",
            "shopify",
            "wix",
            "squarespace",
            "webflow",
            "nextjs",
            "laravel",
        )
        for platform in priority:
            if cms.get(platform):
                return platform
        if cms.get("react"):
            return "react"
        if cms.get("php"):
            return "php"
        return None
