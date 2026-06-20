"""Map industry keywords to OpenStreetMap tags for business discovery."""

from __future__ import annotations

# (key, value) OSM tag pairs; first match wins in Overpass OR clause
INDUSTRY_OSM_TAGS: dict[str, list[tuple[str, str]]] = {
    "dentist": [("amenity", "dentist"), ("healthcare", "dentist")],
    "dental": [("amenity", "dentist"), ("healthcare", "dentist")],
    "restaurant": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "coffee": [("amenity", "cafe")],
    "hotel": [("tourism", "hotel")],
    "lawyer": [("office", "lawyer"), ("amenity", "lawyer")],
    "attorney": [("office", "lawyer")],
    "plumber": [("craft", "plumber")],
    "electrician": [("craft", "electrician")],
    "gym": [("leisure", "fitness_centre"), ("amenity", "gym")],
    "pharmacy": [("amenity", "pharmacy")],
    "hospital": [("amenity", "hospital")],
    "clinic": [("amenity", "clinic")],
    "veterinary": [("amenity", "veterinary")],
    "salon": [("shop", "hairdresser"), ("shop", "beauty")],
    "barber": [("shop", "hairdresser")],
    "real estate": [("office", "estate_agent")],
    "accountant": [("office", "accountant")],
    "insurance": [("office", "insurance")],
    "bank": [("amenity", "bank")],
    "school": [("amenity", "school")],
    "auto repair": [("shop", "car_repair")],
    "car dealer": [("shop", "car")],
    "supermarket": [("shop", "supermarket")],
    "bakery": [("shop", "bakery")],
    "florist": [("shop", "florist")],
    "pet": [("shop", "pet")],
    "optician": [("shop", "optician")],
    "chiropractor": [("healthcare", "chiropractor")],
    "physiotherapist": [("healthcare", "physiotherapist")],
}


def osm_tags_for_industry(keyword: str) -> list[tuple[str, str]]:
    normalized = keyword.strip().lower()
    if normalized in INDUSTRY_OSM_TAGS:
        return INDUSTRY_OSM_TAGS[normalized]
    for key, tags in INDUSTRY_OSM_TAGS.items():
        if key in normalized or normalized in key:
            return tags
    return []
