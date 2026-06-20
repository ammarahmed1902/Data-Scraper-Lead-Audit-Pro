"""Directory website scraping for lead discovery."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus, urljoin

import structlog
from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.lead_discovery import DiscoverySourceCategory
from app.services.discovery.extraction_utils import extract_phone
from app.services.discovery.http_client import DiscoveryHttpClient
from app.services.discovery.profile_scraper import ListingCard, ProfileScraper
from app.services.discovery.source_urls import build_location_query

logger = structlog.get_logger(__name__)


class DirectorySearchProvider:
    """Fetch business listings and scrape profile pages for detailed data."""

    def __init__(self, user_agent: str, request_delay_seconds: float = 2.0):
        self.http = DiscoveryHttpClient(
            user_agent=user_agent,
            request_delay_seconds=request_delay_seconds,
            max_retries=settings.DISCOVERY_HTTP_MAX_RETRIES,
            backoff_seconds=settings.DISCOVERY_HTTP_BACKOFF_SECONDS,
        )
        self.profile_scraper = ProfileScraper(self.http)

    def discover(
        self,
        *,
        category: str,
        website: str,
        industry_keyword: str,
        country: str,
        state: str | None,
        city: str | None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        if page > 1:
            return []

        location = build_location_query(city=city, state=state, country=country)

        try:
            if category == DiscoverySourceCategory.GOOGLE_BUSINESS.value:
                listings = self._extract_google_listings(industry_keyword, location, website)
                source = f"google_business:{website}"
            elif category == DiscoverySourceCategory.YELP.value:
                listings = self._extract_yelp_listings(industry_keyword, location, website)
                source = f"yelp:{website}"
            else:
                listings = self._extract_directory_listings(
                    website, industry_keyword, location, country, state, city
                )
                source = f"directory:{website}"

            if not listings:
                logger.warning(
                    "directory_no_listings",
                    category=category,
                    website=website,
                    location=location,
                )
                return []

            return self.profile_scraper.enrich_listings(
                listings,
                source=source,
                industry=industry_keyword,
                max_profiles=settings.DISCOVERY_MAX_PROFILES_PER_SEARCH,
                enabled=settings.DISCOVERY_PROFILE_SCRAPE_ENABLED,
            )
        except Exception as exc:
            logger.warning(
                "directory_search_failed",
                category=category,
                website=website,
                error=str(exc),
            )
            return []

    def _fetch_listing_page(self, url: str) -> BeautifulSoup | None:
        result = self.http.fetch(url)
        if result.error or not result.html:
            logger.warning(
                "directory_listing_fetch_failed",
                url=url,
                error=result.error,
                status_code=result.status_code,
            )
            return None
        return BeautifulSoup(result.html, "lxml")

    def _extract_google_listings(
        self, industry: str, location: str, website: str
    ) -> list[ListingCard]:
        query = quote_plus(f"{industry} in {location}")
        if website == "google_search":
            url = f"https://www.google.com/search?q={query}&tbm=lcl"
        else:
            url = f"https://www.google.com/maps/search/{query}"

        soup = self._fetch_listing_page(url)
        if soup is None:
            return []

        listings: list[ListingCard] = []
        seen: set[str] = set()

        for node in soup.select("a[href*='maps/place'], a[href*='/maps/search']")[:60]:
            href = node.get("href")
            if not href:
                continue
            profile_url = self._normalize_google_href(href)
            name = node.get("aria-label") or node.get_text(strip=True)
            if not name or len(name) < 2 or len(name) > 200:
                continue
            if any(skip in name.lower() for skip in ("directions", "save", "share", "results")):
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            listings.append(
                ListingCard(business_name=name, profile_url=profile_url, address=location)
            )

        for node in soup.select("div[aria-label]")[:40]:
            name = node.get("aria-label", "").strip()
            if not name or len(name) < 2 or name.lower() in seen:
                continue
            if any(skip in name.lower() for skip in ("directions", "save", "share")):
                continue
            seen.add(name.lower())
            listings.append(ListingCard(business_name=name, address=location))

        return listings[: settings.DISCOVERY_MAX_PROFILES_PER_SEARCH]

    def _extract_yelp_listings(
        self, industry: str, location: str, website: str
    ) -> list[ListingCard]:
        base = "https://m.yelp.com" if website == "yelp_mobile" else "https://www.yelp.com"
        url = (
            f"{base}/search?find_desc={quote_plus(industry)}"
            f"&find_loc={quote_plus(location)}"
        )
        soup = self._fetch_listing_page(url)
        if soup is None:
            return []

        listings: list[ListingCard] = []
        seen: set[str] = set()

        for anchor in soup.select("a[href*='/biz/']")[:50]:
            href = anchor.get("href", "")
            name = anchor.get_text(strip=True) or anchor.get("aria-label", "").strip()
            if not name or len(name) < 2:
                continue
            profile_url = urljoin(base, href.split("?")[0])
            key = profile_url.lower()
            if key in seen:
                continue
            seen.add(key)
            parent = anchor.find_parent(["div", "li", "article"])
            phone = extract_phone(parent) if parent else None
            listings.append(
                ListingCard(
                    business_name=name,
                    profile_url=profile_url,
                    phone_number=phone,
                    address=location,
                )
            )

        return listings[: settings.DISCOVERY_MAX_PROFILES_PER_SEARCH]

    def _extract_directory_listings(
        self,
        website: str,
        industry: str,
        location: str,
        country: str,
        state: str | None,
        city: str | None,
    ) -> list[ListingCard]:
        industry_enc = quote_plus(industry)
        loc_enc = quote_plus(location)

        urls = {
            "yellow_pages": (
                f"https://www.yellowpages.com/search?"
                f"search_terms={industry_enc}&geo_location_terms={loc_enc}"
            ),
            "manta": f"https://www.manta.com/search?search={industry_enc}&city={loc_enc}",
            "superpages": f"https://www.superpages.com/search?C={loc_enc}&T={industry_enc}",
            "bbb": f"https://www.bbb.org/search?find_text={industry_enc}&find_loc={loc_enc}",
        }
        url = urls.get(website)
        if not url:
            return []

        soup = self._fetch_listing_page(url)
        if soup is None:
            return []

        hosts = {
            "yellow_pages": "https://www.yellowpages.com",
            "manta": "https://www.manta.com",
            "superpages": "https://www.superpages.com",
            "bbb": "https://www.bbb.org",
        }
        base_host = hosts.get(website, "")

        listings: list[ListingCard] = []
        seen: set[str] = set()

        selectors = [
            "a.business-name",
            ".business-name a",
            ".n a",
            "h2 a",
            "h3 a",
            ".result-title a",
            "a[href*='/profile/']",
            "a[href*='/mip/']",
        ]
        for selector in selectors:
            for node in soup.select(selector)[:60]:
                name = node.get_text(strip=True)
                if not name or len(name) < 2:
                    continue
                href = node.get("href")
                profile_url = self._normalize_directory_href(href, base_host)
                key = (profile_url or name).lower()
                if key in seen:
                    continue
                seen.add(key)

                parent = node.find_parent(["div", "li", "article", "section"])
                phone = extract_phone(parent) if parent else None
                listings.append(
                    ListingCard(
                        business_name=name,
                        profile_url=profile_url,
                        phone_number=phone,
                        address=location,
                        country=country,
                        state=state,
                        city=city,
                    )
                )

        return listings[: settings.DISCOVERY_MAX_PROFILES_PER_SEARCH]

    @staticmethod
    def _normalize_google_href(href: str) -> str | None:
        if href.startswith("/"):
            return f"https://www.google.com{href}"
        if href.startswith("http") and "google.com" in href:
            return href
        return None

    @staticmethod
    def _normalize_directory_href(href: str | None, base_host: str) -> str | None:
        if not href:
            return None
        if href.startswith("//"):
            return f"https:{href}"
        if href.startswith("/") and base_host:
            return f"{base_host}{href}"
        if href.startswith("http"):
            return href
        return None
