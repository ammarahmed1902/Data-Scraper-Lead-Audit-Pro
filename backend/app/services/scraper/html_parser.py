"""HTML parsing utilities using BeautifulSoup."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class HtmlParser:
    def __init__(self, html: str, base_url: str):
        self.base_url = base_url
        self.soup = BeautifulSoup(html, "lxml")
        self.domain = urlparse(base_url).netloc.lower().removeprefix("www.")

    def get_title(self) -> str | None:
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.strip()
        og = self.soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()
        return None

    def get_meta_description(self) -> str | None:
        tag = self.soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if tag and tag.get("content"):
            return tag["content"].strip()
        og = self.soup.find("meta", property="og:description")
        if og and og.get("content"):
            return og["content"].strip()
        return None

    def get_headings(self, level: int) -> list[str]:
        return [
            h.get_text(strip=True)
            for h in self.soup.find_all(f"h{level}")
            if h.get_text(strip=True)
        ]

    def get_canonical(self) -> str | None:
        tag = self.soup.find("link", rel="canonical")
        if tag and tag.get("href"):
            return urljoin(self.base_url, tag["href"])
        return None

    def get_robots_meta(self) -> str | None:
        tag = self.soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        return tag.get("content", "").lower() if tag else None

    def get_viewport_meta(self) -> str | None:
        tag = self.soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
        return tag.get("content") if tag else None

    def get_open_graph(self) -> dict[str, str]:
        og: dict[str, str] = {}
        for tag in self.soup.find_all("meta"):
            prop = tag.get("property", "")
            if prop.startswith("og:") and tag.get("content"):
                og[prop] = tag["content"].strip()
        return og

    def get_structured_data(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for script in self.soup.find_all("script", type="application/ld+json"):
            text = script.string or script.get_text()
            if not text:
                continue
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    results.extend(item for item in data if isinstance(item, dict))
                elif isinstance(data, dict):
                    results.append(data)
            except json.JSONDecodeError:
                continue
        return results

    def get_images_alt_analysis(self) -> dict[str, Any]:
        images = self.soup.find_all("img")
        missing = 0
        empty = 0
        samples: list[dict[str, str]] = []
        for img in images:
            alt = img.get("alt")
            src = img.get("src", "")
            if alt is None:
                missing += 1
                if len(samples) < 10:
                    samples.append({"src": src, "issue": "missing_alt"})
            elif not str(alt).strip():
                empty += 1
                if len(samples) < 10:
                    samples.append({"src": src, "issue": "empty_alt"})
        return {
            "total_images": len(images),
            "missing_alt": missing,
            "empty_alt": empty,
            "samples": samples,
        }

    def get_links(self) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        seen: set[str] = set()
        for a in self.soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            absolute = urljoin(self.base_url, href)
            if absolute in seen:
                continue
            seen.add(absolute)
            parsed = urlparse(absolute)
            link_domain = parsed.netloc.lower().removeprefix("www.")
            links.append(
                {
                    "url": absolute,
                    "text": a.get_text(strip=True)[:200],
                    "type": "internal" if link_domain == self.domain else "external",
                }
            )
        return links

    def is_mobile_friendly(self) -> bool:
        viewport = self.get_viewport_meta()
        if not viewport:
            return False
        return "width=device-width" in viewport.lower()
