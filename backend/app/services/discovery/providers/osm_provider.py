"""OpenStreetMap Nominatim + Overpass business listing provider."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog

from app.services.discovery.industry_mapping import osm_tags_for_industry

logger = structlog.get_logger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class OSMBusinessProvider:
    """Discover businesses from public OpenStreetMap data."""

    def __init__(
        self,
        user_agent: str,
        request_delay_seconds: float = 1.0,
        max_results: int = 100,
    ):
        self.user_agent = user_agent
        self.request_delay_seconds = request_delay_seconds
        self.max_results = max_results
        self._last_request_at = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.request_delay_seconds:
            time.sleep(self.request_delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent, "Accept": "application/json"}

    def discover(
        self,
        *,
        industry_keyword: str,
        country: str,
        state: str | None,
        city: str | None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        """
        Returns (leads, has_more_pages).
        Pagination is simulated by offset into Overpass results.
        """
        bbox = self._geocode_bbox(country=country, state=state, city=city)
        if not bbox:
            logger.warning(
                "osm_geocode_failed",
                country=country,
                state=state,
                city=city,
            )
            return [], False

        all_leads = self._query_overpass(
            industry_keyword=industry_keyword,
            bbox=bbox,
            country=country,
            state=state,
            city=city,
        )

        offset = (page - 1) * page_size
        page_leads = all_leads[offset : offset + page_size]
        has_more = offset + page_size < len(all_leads)
        return page_leads, has_more

    def _geocode_bbox(
        self,
        *,
        country: str,
        state: str | None,
        city: str | None,
    ) -> tuple[float, float, float, float] | None:
        params: dict[str, str] = {"format": "json", "limit": "1", "addressdetails": "1"}
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        params["country"] = country

        self._rate_limit()
        try:
            with httpx.Client(timeout=30.0, headers=self._headers()) as client:
                response = client.get(f"{NOMINATIM_URL}?{urlencode(params)}")
                response.raise_for_status()
                results = response.json()
        except Exception as exc:
            logger.exception("nominatim_request_failed", error=str(exc))
            return None

        if not results:
            return None

        bbox = results[0].get("boundingbox")
        if not bbox or len(bbox) != 4:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            delta = 0.15 if city else (0.8 if state else 2.5)
            return (lat - delta, lon - delta, lat + delta, lon + delta)

        south, north, west, east = map(float, bbox)
        return (south, west, north, east)

    def _query_overpass(
        self,
        *,
        industry_keyword: str,
        bbox: tuple[float, float, float, float],
        country: str,
        state: str | None,
        city: str | None,
    ) -> list[dict[str, Any]]:
        south, west, north, east = bbox
        osm_tags = osm_tags_for_industry(industry_keyword)

        tag_filters: list[str] = []
        for key, value in osm_tags:
            tag_filters.append(f'node["{key}"="{value}"]({south},{west},{north},{east});')
            tag_filters.append(f'way["{key}"="{value}"]({south},{west},{north},{east});')

        keyword_safe = industry_keyword.replace('"', "").replace("\\", "")[:50]
        tag_filters.append(
            f'node["name"~"{keyword_safe}",i]({south},{west},{north},{east});'
        )
        tag_filters.append(
            f'way["name"~"{keyword_safe}",i]({south},{west},{north},{east});'
        )

        query = f"""
        [out:json][timeout:90];
        (
          {"".join(tag_filters)}
        );
        out center tags {self.max_results};
        """

        self._rate_limit()
        try:
            with httpx.Client(timeout=120.0, headers=self._headers()) as client:
                response = client.post(OVERPASS_URL, data={"data": query})
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.exception("overpass_request_failed", error=str(exc))
            return []

        leads: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for element in data.get("elements", []):
            tags = element.get("tags") or {}
            name = tags.get("name") or tags.get("brand")
            if not name:
                continue

            name_key = name.strip().lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            lat = element.get("lat") or (element.get("center") or {}).get("lat")
            lon = element.get("lon") or (element.get("center") or {}).get("lon")

            address_parts = [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
            ]
            street_line = " ".join(p for p in address_parts if p)

            leads.append(
                {
                    "business_name": name.strip(),
                    "website_url": tags.get("website") or tags.get("contact:website"),
                    "business_category": tags.get("amenity")
                    or tags.get("shop")
                    or tags.get("office")
                    or industry_keyword,
                    "address": street_line or tags.get("addr:full"),
                    "city": tags.get("addr:city") or city,
                    "state": tags.get("addr:state") or state,
                    "country": tags.get("addr:country") or country,
                    "phone_number": tags.get("phone") or tags.get("contact:phone"),
                    "email_address": tags.get("email") or tags.get("contact:email"),
                    "social_profiles": self._social_from_tags(tags),
                    "source": "openstreetmap",
                    "raw_data": {
                        "osm_id": element.get("id"),
                        "osm_type": element.get("type"),
                        "lat": lat,
                        "lon": lon,
                        "tags": tags,
                    },
                }
            )

        return leads

    @staticmethod
    def _social_from_tags(tags: dict[str, str]) -> dict[str, str]:
        profiles: dict[str, str] = {}
        mapping = {
            "contact:facebook": "facebook",
            "contact:instagram": "instagram",
            "contact:twitter": "twitter",
            "contact:linkedin": "linkedin",
            "contact:youtube": "youtube",
        }
        for tag_key, platform in mapping.items():
            if tags.get(tag_key):
                profiles[platform] = tags[tag_key]
        return profiles
