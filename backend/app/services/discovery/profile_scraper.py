"""Business profile page scraping for detailed lead extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import structlog
from bs4 import BeautifulSoup

from app.services.discovery.extraction_utils import (
    extract_email,
    extract_json_ld_business,
    extract_phone,
    extract_website_link,
    fields_from_json_ld,
    is_platform_listing_url,
)
from app.services.discovery.http_client import DiscoveryHttpClient

logger = structlog.get_logger(__name__)


@dataclass
class ListingCard:
    business_name: str
    profile_url: str | None = None
    phone_number: str | None = None
    address: str | None = None
    website_url: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None


@dataclass
class ProfileScrapeResult:
    data: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    status: str = "success"


class ProfileScraper:
    """Visit individual business profile pages to extract detailed contact data."""

    def __init__(self, http: DiscoveryHttpClient):
        self.http = http

    def enrich_listings(
        self,
        listings: list[ListingCard],
        *,
        source: str,
        industry: str,
        max_profiles: int,
        enabled: bool = True,
    ) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        profiles_visited = 0

        for listing in listings:
            if profiles_visited >= max_profiles:
                break

            lead = self._listing_to_lead(listing, source=source, industry=industry)
            errors: list[str] = []

            if enabled and listing.profile_url:
                profiles_visited += 1
                result = self.scrape_profile(
                    profile_url=listing.profile_url,
                    listing=listing,
                    industry=industry,
                    source=source,
                )
                lead = self._merge_lead(lead, result.data)
                errors.extend(result.errors)
                lead["scrape_status"] = result.status
            elif listing.profile_url:
                lead["scrape_status"] = "skipped"
            else:
                lead["scrape_status"] = "partial" if self._has_contact_data(lead) else "failed"
                errors.append("No profile URL found on listing card")

            lead["profile_url"] = listing.profile_url
            lead["scrape_errors"] = errors or None
            raw = lead.get("raw_data") or {}
            raw["profiles_visited"] = profiles_visited
            lead["raw_data"] = raw
            leads.append(lead)

        return leads

    def scrape_profile(
        self,
        *,
        profile_url: str,
        listing: ListingCard,
        industry: str,
        source: str,
    ) -> ProfileScrapeResult:
        errors: list[str] = []
        fetch = self.http.fetch(profile_url)

        if fetch.error or not fetch.html:
            errors.append(fetch.error or "Empty profile page")
            logger.warning(
                "profile_fetch_failed",
                profile_url=profile_url,
                error=fetch.error,
                status_code=fetch.status_code,
            )
            return ProfileScrapeResult(
                data=self._listing_to_lead(listing, source=source, industry=industry),
                errors=errors,
                status="failed",
            )

        soup = BeautifulSoup(fetch.html, "lxml")
        host = urlparse(profile_url).netloc.lower()

        if "yelp.com" in host:
            parsed = self._parse_yelp_profile(soup, fetch.html)
        elif "yellowpages.com" in host:
            parsed = self._parse_yellowpages_profile(soup, fetch.html)
        elif "bbb.org" in host:
            parsed = self._parse_bbb_profile(soup, fetch.html)
        elif "manta.com" in host:
            parsed = self._parse_manta_profile(soup, fetch.html)
        elif "superpages.com" in host:
            parsed = self._parse_superpages_profile(soup, fetch.html)
        elif "google.com" in host:
            parsed = self._parse_google_place(soup, fetch.html)
        else:
            parsed = self._parse_generic_profile(soup, fetch.html)

        base = self._listing_to_lead(listing, source=source, industry=industry)
        merged = self._merge_lead(base, parsed)

        missing = []
        if not merged.get("phone_number"):
            missing.append("phone")
        if not merged.get("website_url"):
            missing.append("website")
        if not merged.get("address"):
            missing.append("address")

        if missing:
            errors.append(f"Missing fields after profile scrape: {', '.join(missing)}")

        status = "success"
        if missing and self._has_contact_data(merged):
            status = "partial"
        elif missing:
            status = "partial" if merged.get("business_name") else "failed"

        return ProfileScrapeResult(data=merged, errors=errors, status=status)

    def _parse_yelp_profile(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        name = soup.select_one("h1")
        if name:
            data["business_name"] = name.get_text(strip=True)

        data["phone_number"] = extract_phone(soup, html)
        data["email_address"] = extract_email(soup, html)

        for anchor in soup.select('a[href*="biz_redir"], a[href*="redirect_url"]'):
            href = anchor.get("href", "")
            if "url=" in href:
                from urllib.parse import parse_qs, urlparse as up

                qs = parse_qs(up(href).query)
                redirect = qs.get("url", [None])[0]
                if redirect and not is_platform_listing_url(redirect):
                    data["website_url"] = redirect
                    break

        if not data.get("website_url"):
            website = extract_website_link(soup, "https://www.yelp.com")
            if website:
                data["website_url"] = website

        address = soup.select_one("address, p[class*='address']")
        if address:
            data["address"] = address.get_text(" ", strip=True)

        ld = extract_json_ld_business(soup)
        if ld:
            data = self._merge_lead(data, fields_from_json_ld(ld))
        return data

    def _parse_yellowpages_profile(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        name = soup.select_one("h1.business-name, h1")
        if name:
            data["business_name"] = name.get_text(strip=True)

        phone = soup.select_one(".phone, .sales-info .phone, a[href^='tel:']")
        if phone:
            data["phone_number"] = extract_phone(soup, phone.get_text(" ", strip=True))

        website = soup.select_one("a.website-link, a.track-visit-website")
        if website and website.get("href", "").startswith("http"):
            href = website["href"]
            if not is_platform_listing_url(href):
                data["website_url"] = href

        address = soup.select_one(".address, .street-address, .locality")
        if address:
            data["address"] = address.get_text(" ", strip=True)

        data["email_address"] = extract_email(soup, html)
        ld = extract_json_ld_business(soup)
        if ld:
            data = self._merge_lead(data, fields_from_json_ld(ld))
        return data

    def _parse_bbb_profile(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        name = soup.select_one("h1, .business-name")
        if name:
            data["business_name"] = name.get_text(strip=True)

        data["phone_number"] = extract_phone(soup, html)
        data["email_address"] = extract_email(soup, html)

        website = soup.select_one("a[href^='http'][class*='website'], a.website-link")
        if website:
            href = website.get("href", "")
            if href and not is_platform_listing_url(href):
                data["website_url"] = href

        address = soup.select_one("address, .bpr-address, .business-address")
        if address:
            data["address"] = address.get_text(" ", strip=True)

        ld = extract_json_ld_business(soup)
        if ld:
            data = self._merge_lead(data, fields_from_json_ld(ld))
        return data

    def _parse_manta_profile(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        return self._parse_generic_profile(soup, html)

    def _parse_superpages_profile(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        return self._parse_generic_profile(soup, html)

    def _parse_google_place(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        title = soup.select_one("h1, [data-attrid='title']")
        if title:
            data["business_name"] = title.get_text(strip=True)

        data["phone_number"] = extract_phone(soup, html)
        data["email_address"] = extract_email(soup, html)
        data["website_url"] = extract_website_link(soup, "https://www.google.com")

        address = soup.select_one(
            "[data-item-id='address'], button[data-item-id='address'], .address"
        )
        if address:
            data["address"] = address.get_text(" ", strip=True)

        ld = extract_json_ld_business(soup)
        if ld:
            data = self._merge_lead(data, fields_from_json_ld(ld))
        return data

    def _parse_generic_profile(self, soup: BeautifulSoup, html: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        h1 = soup.select_one("h1")
        if h1:
            data["business_name"] = h1.get_text(strip=True)

        data["phone_number"] = extract_phone(soup, html)
        data["email_address"] = extract_email(soup, html)
        data["website_url"] = extract_website_link(soup, html)

        address = soup.select_one("address")
        if address:
            data["address"] = address.get_text(" ", strip=True)

        ld = extract_json_ld_business(soup)
        if ld:
            data = self._merge_lead(data, fields_from_json_ld(ld))
        return data

    @staticmethod
    def _listing_to_lead(
        listing: ListingCard,
        *,
        source: str,
        industry: str,
    ) -> dict[str, Any]:
        website = listing.website_url
        if website and is_platform_listing_url(website):
            website = None
        return {
            "business_name": listing.business_name[:500],
            "website_url": website,
            "business_category": industry,
            "address": listing.address,
            "city": listing.city,
            "state": listing.state,
            "country": listing.country,
            "phone_number": listing.phone_number,
            "email_address": None,
            "social_profiles": {},
            "source": source,
            "profile_url": listing.profile_url,
            "raw_data": {"listing_source": source},
        }

    @staticmethod
    def _merge_lead(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in patch.items():
            if value is None or value == "":
                continue
            if key == "website_url" and is_platform_listing_url(str(value)):
                continue
            merged[key] = value
        return merged

    @staticmethod
    def _has_contact_data(lead: dict[str, Any]) -> bool:
        return bool(
            lead.get("phone_number")
            or lead.get("email_address")
            or lead.get("website_url")
            or lead.get("address")
        )
