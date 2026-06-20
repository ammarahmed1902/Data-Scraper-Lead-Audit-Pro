"""Duplicate detection helpers for discovered leads."""

from __future__ import annotations

import hashlib
import re

from app.utils.helpers import extract_domain


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return None
    return digits[-10:] if len(digits) >= 10 else digits


def build_dedup_key(
    *,
    business_name: str,
    domain: str | None,
    phone: str | None,
    city: str | None,
) -> str:
    """Stable key for duplicate detection within and across searches."""
    norm_domain = domain.lower() if domain else None
    norm_phone = normalize_phone(phone)
    if norm_domain:
        return f"domain:{norm_domain}"
    if norm_phone:
        return f"phone:{norm_phone}"
    name_part = re.sub(r"[^a-z0-9]+", "", business_name.lower())[:80]
    city_part = re.sub(r"[^a-z0-9]+", "", (city or "").lower())[:40]
    raw = f"name:{name_part}|city:{city_part}"
    return f"hash:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


def domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return extract_domain(url)
    except Exception:
        return None
