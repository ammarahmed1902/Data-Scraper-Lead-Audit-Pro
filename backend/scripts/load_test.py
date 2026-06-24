#!/usr/bin/env python3
"""
Load test harness for Lead Audit Pro API (QA-013).

Runs a configurable smoke/load scenario against a running API instance.
For full 10K website / 100K audit validation, increase --websites and --audits
on staging hardware with Celery workers running.

Usage:
  cd backend
  python -m scripts.load_test --base-url http://127.0.0.1:8000 --email admin@leadaudit.pro --password Admin123!ChangeMe

  # Heavier run (staging)
  python -m scripts.load_test --websites 200 --audits 50 --concurrency 8
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field

import httpx

DEFAULT_EMAIL = "admin@leadaudit.pro"
DEFAULT_PASSWORD = "Admin123!ChangeMe"


@dataclass
class StepResult:
    name: str
    total: int
    successes: int
    failures: int
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def p95_ms(self) -> float | None:
        if not self.latencies_ms:
            return None
        sorted_vals = sorted(self.latencies_ms)
        idx = max(0, int(len(sorted_vals) * 0.95) - 1)
        return sorted_vals[idx]

    @property
    def avg_ms(self) -> float | None:
        if not self.latencies_ms:
            return None
        return statistics.mean(self.latencies_ms)


@dataclass
class LoadTestReport:
    base_url: str
    steps: list[StepResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def add(self, step: StepResult) -> None:
        self.steps.append(step)

    def elapsed_s(self) -> float:
        end = self.finished_at or time.time()
        return end - self.started_at


async def login(client: httpx.AsyncClient, email: str, password: str) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    response.raise_for_status()
    tokens = response.json()["tokens"]
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"


async def run_step(
    name: str,
    count: int,
    concurrency: int,
    worker,
) -> StepResult:
    sem = asyncio.Semaphore(concurrency)
    result = StepResult(name=name, total=count, successes=0, failures=0)

    async def one(index: int) -> None:
        async with sem:
            started = time.perf_counter()
            try:
                await worker(index)
                result.successes += 1
                result.latencies_ms.append((time.perf_counter() - started) * 1000)
            except Exception:
                result.failures += 1

    await asyncio.gather(*(one(i) for i in range(count)))
    return result


async def main() -> int:
    parser = argparse.ArgumentParser(description="Lead Audit Pro API load test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--websites", type=int, default=25, help="Websites to create")
    parser.add_argument("--audits", type=int, default=10, help="Audits to queue")
    parser.add_argument("--list-pages", type=int, default=5, help="Website list requests")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    report = LoadTestReport(base_url=args.base_url.rstrip("/"))
    timeout = httpx.Timeout(120.0, connect=10.0)

    async with httpx.AsyncClient(base_url=report.base_url, timeout=timeout) as client:
        health = await client.get("/health")
        health.raise_for_status()

        await login(client, args.email, args.password)

        created_website_ids: list[str] = []

        async def create_website(index: int) -> None:
            suffix = uuid.uuid4().hex[:8]
            response = await client.post(
                "/api/v1/websites",
                json={
                    "url": f"https://loadtest-{suffix}.example.com",
                    "company_name": f"Load Test Co {index}",
                },
            )
            response.raise_for_status()
            created_website_ids.append(response.json()["id"])

        website_step = await run_step(
            "create_website",
            args.websites,
            args.concurrency,
            create_website,
        )
        report.add(website_step)

        if created_website_ids and args.audits > 0:
            audit_targets = created_website_ids[: args.audits]

            async def create_audit(index: int) -> None:
                website_id = audit_targets[index % len(audit_targets)]
                response = await client.post(
                    "/api/v1/audits",
                    json={"website_id": website_id},
                )
                response.raise_for_status()

            audit_step = await run_step(
                "create_audit",
                min(args.audits, len(audit_targets)),
                args.concurrency,
                create_audit,
            )
            report.add(audit_step)

            bulk_ids = created_website_ids[: min(10, len(created_website_ids))]
            started = time.perf_counter()
            bulk_response = await client.post(
                "/api/v1/audits/bulk",
                json={"website_ids": bulk_ids},
            )
            bulk_response.raise_for_status()
            bulk_ms = (time.perf_counter() - started) * 1000
            bulk_data = bulk_response.json()
            report.add(
                StepResult(
                    name="bulk_audit",
                    total=1,
                    successes=1,
                    failures=0,
                    latencies_ms=[bulk_ms],
                )
            )
            print(f"Bulk audit queued: {bulk_data.get('queued', 0)} audits in {bulk_ms:.0f}ms")

        async def list_websites(_: int) -> None:
            response = await client.get("/api/v1/websites?page=1&page_size=20")
            response.raise_for_status()

        list_step = await run_step(
            "list_websites",
            args.list_pages,
            args.concurrency,
            list_websites,
        )
        report.add(list_step)

        async def analytics_overview(_: int) -> None:
            response = await client.get("/api/v1/analytics/overview")
            response.raise_for_status()

        analytics_step = await run_step(
            "analytics_overview",
            3,
            args.concurrency,
            analytics_overview,
        )
        report.add(analytics_step)

    report.finished_at = time.time()

    print("")
    print("=== Load Test Report ===")
    print(f"Base URL: {report.base_url}")
    print(f"Duration: {report.elapsed_s():.1f}s")
    print("")
    print(f"{'Step':<20} {'OK':>6} {'Fail':>6} {'Avg ms':>10} {'P95 ms':>10}")
    print("-" * 56)
    all_ok = True
    for step in report.steps:
        avg = step.avg_ms
        p95 = step.p95_ms
        print(
            f"{step.name:<20} {step.successes:>6} {step.failures:>6} "
            f"{avg:>10.1f} {p95:>10.1f}"
            if avg is not None and p95 is not None
            else f"{step.name:<20} {step.successes:>6} {step.failures:>6} {'—':>10} {'—':>10}"
        )
        if step.failures:
            all_ok = False

    print("")
    if all_ok:
        print("Result: PASS (smoke/load scenario completed)")
        print(
            "Note: Scale to --websites 10000 --audits 1000 on staging with Celery workers "
            "for full QA-013 validation."
        )
        return 0

    print("Result: FAIL (see failures above)")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
