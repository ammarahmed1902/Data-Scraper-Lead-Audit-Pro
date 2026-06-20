"""Shared HTML extraction helpers for discovery scraping."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")

SKIP_EMAIL_DOMAINS = (
    "example.com",
    "wixpress.com",
    "sentry.io",
    "schema.org",
    "yelp.com",
    "yellowpages.com",
)

PLATFORM_HOSTS = (
    "yelp.com",
    "google.com",
    "maps.google.com",
    "yellowpages.com",
    "bbb.org",
    "manta.com",
    "superpages.com",
    "facebook.com",
    "instagram.com",
)


def is_platform_listing_url(url: str | None) -> bool:
    if not url:
        return False
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(platform in host for platform in PLATFORM_HOSTS)


def extract_phone(soup: BeautifulSoup, text: str | None = None) -> str | None:
    for anchor in soup.select('a[href^="tel:"]'):
        href = anchor.get("href", "").replace("tel:", "").strip()
        if href:
            return href
    haystack = text or soup.get_text(" ", strip=True)
    match = PHONE_PATTERN.search(haystack)
    return match.group(1).strip() if match else None


def extract_email(soup: BeautifulSoup, html: str) -> str | None:
    for anchor in soup.select('a[href^="mailto:"]'):
        href = anchor.get("href", "")
        email = href.replace("mailto:", "").split("?")[0].strip().lower()
        if EMAIL_PATTERN.fullmatch(email) and not any(d in email for d in SKIP_EMAIL_DOMAINS):
            return email
    for match in EMAIL_PATTERN.findall(html):
        lowered = match.lower()
        if not any(skip in lowered for skip in SKIP_EMAIL_DOMAINS):
            return lowered
    return None


def extract_website_link(soup: BeautifulSoup, base_url: str) -> str | None:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href.startswith("http"):
            continue
        if is_platform_listing_url(href):
            continue
        text = anchor.get_text(strip=True).lower()
        if any(
            token in text
            for token in ("website", "visit", "business website", "company website")
        ):
            return href
    for anchor in soup.select(
        'a[href^="http"]:not([href*="yelp.com"]):not([href*="google.com"])'
    ):
        href = anchor.get("href", "").strip()
        if href and not is_platform_listing_url(href):
            return href
    return None


def extract_json_ld_business(soup: BeautifulSoup) -> dict[str, Any] | None:
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            types = item_type if isinstance(item_type, list) else [item_type]
            if any(t in ("LocalBusiness", "Organization", "Dentist", "Store") for t in types):
                return item
    return None


def fields_from_json_ld(data: dict[str, Any]) -> dict[str, Any]:
    address = data.get("address")
    street = city = state = country = None
    if isinstance(address, dict):
        street = address.get("streetAddress")
        city = address.get("addressLocality")
        state = address.get("addressRegion")
        country = address.get("addressCountry")
    elif isinstance(address, str):
        street = address

    phone = data.get("telephone")
    email = data.get("email")
    website = data.get("url") or data.get("sameAs")
    if isinstance(website, list):
        website = next((u for u in website if isinstance(u, str) and u.startswith("http")), None)

    return {
        "business_name": data.get("name"),
        "phone_number": phone,
        "email_address": email.lower() if isinstance(email, str) else None,
        "website_url": website if isinstance(website, str) else None,
        "address": street,
        "city": city,
        "state": state,
        "country": country,
    }
