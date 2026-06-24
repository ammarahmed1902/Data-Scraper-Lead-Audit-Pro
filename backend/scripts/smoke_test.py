#!/usr/bin/env python3
"""
End-to-end API smoke test for QA sign-off.
Verifies auth and core flows without a browser.

Usage:
  cd backend
  python -m scripts.smoke_test
"""

from __future__ import annotations

import asyncio
import sys
import uuid

import httpx

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "admin@leadaudit.pro"
PASSWORD = "Admin123!ChangeMe"


async def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Health
        r = await client.get("/health")
        checks.append(("health", r.status_code == 200, r.text[:80]))

        # Login
        r = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
        ok = r.status_code == 200 and "access_token" in r.json().get("tokens", {})
        checks.append(("login", ok, str(r.status_code)))
        if not ok:
            print("Login failed — cannot continue")
            for name, passed, detail in checks:
                print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")
            return 1

        token = r.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Protected endpoints
        endpoints = [
            ("websites_list", "GET", "/api/v1/websites?page=1&page_size=5"),
            ("audits_list", "GET", "/api/v1/audits?page=1&page_size=5"),
            ("analytics", "GET", "/api/v1/analytics/overview"),
            ("discovery", "GET", "/api/v1/discovery/searches?page=1&page_size=5"),
            ("scoring", "GET", "/api/v1/scoring/dashboard"),
            ("exports", "GET", "/api/v1/exports?page=1"),
            ("reports", "GET", "/api/v1/reports?page=1&page_size=5"),
        ]

        for name, method, path in endpoints:
            resp = await client.request(method, path, headers=headers)
            checks.append((name, resp.status_code < 400, str(resp.status_code)))

        # Create + read website
        create = await client.post(
            "/api/v1/websites",
            headers=headers,
            json={
                "url": f"https://smoke-{uuid.uuid4().hex[:8]}.example.com",
                "company_name": "Smoke Test",
            },
        )
        checks.append(("website_create", create.status_code < 400, str(create.status_code)))
        website_id = create.json().get("id") if create.status_code < 400 else None

        if website_id:
            detail = await client.get(f"/api/v1/websites/{website_id}", headers=headers)
            checks.append(("website_detail", detail.status_code == 200, str(detail.status_code)))

            audit = await client.post(
                "/api/v1/audits",
                headers=headers,
                json={"website_id": website_id},
            )
            checks.append(("audit_create", audit.status_code < 400, str(audit.status_code)))

        # Me endpoint
        me = await client.get("/api/v1/auth/me", headers=headers)
        checks.append(("auth_me", me.status_code == 200, me.json().get("email", "")))

    print("=== QA Smoke Test (API) ===")
    failed = 0
    for name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        if not passed:
            failed += 1

    print("")
    if failed == 0:
        print("Result: ALL CHECKS PASSED")
        return 0
    print(f"Result: {failed} check(s) failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
