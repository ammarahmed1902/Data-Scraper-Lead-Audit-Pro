"""Extract contact info, services, team, and content from HTML pages."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{3,4}[\s.-]?\d{3,4}",
)

SKIP_EMAIL_DOMAINS = (
    "example.com",
    "wixpress.com",
    "sentry.io",
    "schema.org",
    "domain.com",
    "email.com",
    "yourcompany.com",
)


class ContentExtractor:
    """Parse business content from crawled HTML pages."""

    def extract_company_name(self, soup: BeautifulSoup, fallback: str | None = None) -> str | None:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            return og_site["content"].strip()
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            for sep in ("|", "-", "–", "—", ":"):
                if sep in title:
                    return title.split(sep)[0].strip()
            return title
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return fallback

    def extract_meta_description(self, soup: BeautifulSoup) -> str | None:
        tag = soup.find("meta", attrs={"name": "description"})
        if tag and tag.get("content"):
            return tag["content"].strip()
        og = soup.find("meta", property="og:description")
        if og and og.get("content"):
            return og["content"].strip()
        return None

    def extract_main_text(self, soup: BeautifulSoup, max_chars: int = 8000) -> str:
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.body
        if not main:
            return ""
        text = " ".join(main.get_text(separator=" ", strip=True).split())
        return text[:max_chars]

    def extract_emails(self, soup: BeautifulSoup, html: str) -> list[str]:
        found: set[str] = set()
        for anchor in soup.select('a[href^="mailto:"]'):
            href = anchor.get("href", "")
            email = href.replace("mailto:", "").split("?")[0].strip().lower()
            if self._valid_email(email):
                found.add(email)
        for match in EMAIL_PATTERN.findall(html):
            email = match.lower()
            if self._valid_email(email):
                found.add(email)
        return sorted(found)

    def extract_phones(self, soup: BeautifulSoup, html: str) -> list[str]:
        found: set[str] = set()
        for anchor in soup.select('a[href^="tel:"]'):
            phone = anchor.get("href", "").replace("tel:", "").strip()
            normalized = re.sub(r"\s+", " ", phone)
            if len(re.sub(r"\D", "", normalized)) >= 7:
                found.add(normalized)
        for match in PHONE_PATTERN.findall(html):
            cleaned = re.sub(r"\s+", " ", match.strip())
            digits = re.sub(r"\D", "", cleaned)
            if 7 <= len(digits) <= 15:
                found.add(cleaned)
        return sorted(found)[:10]

    def extract_services(self, soup: BeautifulSoup) -> list[str]:
        services: list[str] = []
        selectors = [
            "section[class*='service'] li",
            "div[class*='service'] h2",
            "div[class*='service'] h3",
            "ul.services li",
            ".service-item",
            ".services-list li",
        ]
        for selector in selectors:
            for el in soup.select(selector)[:20]:
                text = el.get_text(strip=True)
                if 3 < len(text) < 200 and text not in services:
                    services.append(text)
        return services[:25]

    def extract_team_members(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        members: list[dict[str, str]] = []
        containers = soup.select(
            "[class*='team'] [class*='member'], "
            "[class*='staff'] [class*='member'], "
            ".team-member, .staff-member, .person"
        )
        for container in containers[:20]:
            name_el = container.find(["h2", "h3", "h4", "strong", "span"])
            title_el = container.find(["p", "span", "em"])
            name = name_el.get_text(strip=True) if name_el else None
            title = title_el.get_text(strip=True) if title_el else None
            if name and 2 < len(name) < 100:
                members.append({"name": name, "title": title or ""})
        return members

    def extract_contact_data(self, soup: BeautifulSoup, page_url: str) -> dict[str, Any]:
        data: dict[str, Any] = {"page_url": page_url}
        address_el = soup.find("address")
        if address_el:
            data["address"] = address_el.get_text(" ", strip=True)

        for label in soup.find_all(string=re.compile(r"(hours|opening)", re.I)):
            parent = label.parent if isinstance(label, Tag) else None
            if parent:
                data["hours"] = parent.get_text(" ", strip=True)[:500]
                break

        labels = {}
        for dt in soup.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                labels[dt.get_text(strip=True)] = dd.get_text(strip=True)
        if labels:
            data["labeled_fields"] = labels

        return data

    @staticmethod
    def _valid_email(email: str) -> bool:
        if not EMAIL_PATTERN.fullmatch(email):
            return False
        domain = email.split("@")[-1]
        return not any(skip in domain for skip in SKIP_EMAIL_DOMAINS)
