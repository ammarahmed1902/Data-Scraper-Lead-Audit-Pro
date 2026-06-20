"""Shared helpers for structured audit category results."""

from __future__ import annotations

from typing import Any

SEVERITY_WEIGHTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}


def build_category(
    *,
    score: float | None,
    issues: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    checks: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "score": score,
        "issues": {"items": issues},
        "recommendations": {"items": recommendations},
        "checks": checks or {},
    }


def score_from_issues(
    issues: list[dict[str, Any]],
    *,
    base: float = 100.0,
) -> float:
    penalty = 0.0
    for issue in issues:
        severity = str(issue.get("severity", "medium")).lower()
        penalty += SEVERITY_WEIGHTS.get(severity, 5)
    return max(0.0, round(base - penalty, 1))


def merge_issue_lists(*lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for items in lists:
        for item in items:
            key = f"{item.get('code')}:{item.get('message')}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged
