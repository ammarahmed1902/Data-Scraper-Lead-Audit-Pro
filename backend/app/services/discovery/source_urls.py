"""Build public directory search URLs for lead discovery."""

from __future__ import annotations

from urllib.parse import quote_plus

from app.models.lead_discovery import DiscoverySourceCategory


def build_location_query(*, city: str | None, state: str | None, country: str) -> str:
    parts = [p for p in (city, state, country) if p and p.strip()]
    return ", ".join(parts)


def build_source_search_url(
    *,
    category: str,
    website: str,
    industry_keyword: str,
    country: str,
    state: str | None,
    city: str | None,
) -> str:
    location = build_location_query(city=city, state=state, country=country)
    industry = industry_keyword.strip()
    loc_enc = quote_plus(location)
    industry_enc = quote_plus(industry)

    if category == DiscoverySourceCategory.GOOGLE_BUSINESS.value:
        return f"https://www.google.com/maps/search/{quote_plus(f'{industry} in {location}')}"

    if category == DiscoverySourceCategory.YELP.value:
        return f"https://www.yelp.com/search?find_desc={industry_enc}&find_loc={loc_enc}"

    directory_urls = {
        "yellow_pages": (
            f"https://www.yellowpages.com/search?"
            f"search_terms={industry_enc}&geo_location_terms={loc_enc}"
        ),
        "manta": f"https://www.manta.com/search?search={industry_enc}&city={loc_enc}",
        "superpages": (
            f"https://www.superpages.com/search?"
            f"C={loc_enc}&T={industry_enc}"
        ),
        "bbb": f"https://www.bbb.org/search?find_text={industry_enc}&find_loc={loc_enc}",
    }
    return directory_urls.get(
        website,
        f"https://www.google.com/search?q={quote_plus(f'{industry} {location} business directory')}",
    )
