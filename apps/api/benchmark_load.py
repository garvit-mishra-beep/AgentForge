"""Quick throughput benchmark for AgentForge API.

Measures requests per second for key endpoints under concurrent load.

Usage:
    python benchmark_load.py [--base-url http://localhost:8000] [--users 5] [--duration 10]
"""

import argparse
import asyncio
import statistics
import time

import httpx


async def _bench_worker(client: httpx.AsyncClient, url: str, results: list, duration: float):
    start = time.monotonic()
    count = 0
    while time.monotonic() - start < duration:
        try:
            r = await client.get(url)
            _ = r.status_code
            count += 1
        except Exception:
            pass
    results.append(count)


async def _bench_worker_auth(client: httpx.AsyncClient, base_url: str, token: str, results: list, duration: float):
    start = time.monotonic()
    count = 0
    while time.monotonic() - start < duration:
        try:
            r = await client.get(f"{base_url}/api/v1/teams", headers={"Authorization": f"Bearer {token}"})
            _ = r.status_code
            count += 1
        except Exception:
            pass
    results.append(count)


async def benchmark_endpoint(base_url: str, endpoint: str, users: int, duration: int, token: str = ""):
    results: list = []
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        workers = []
        for _ in range(users):
            if token:
                workers.append(_bench_worker_auth(client, base_url, token, results, duration))
            else:
                workers.append(_bench_worker(client, endpoint, results, duration))
        await asyncio.gather(*workers)

    total_reqs = sum(results)
    avg_per_worker = statistics.mean(results) if results else 0
    return {
        "endpoint": endpoint,
        "users": users,
        "duration_s": duration,
        "total_requests": total_reqs,
        "rps": round(total_reqs / duration, 1),
        "avg_req_per_worker": round(avg_per_worker, 1),
        "worker_results": sorted(results, reverse=True),
    }


async def main():
    parser = argparse.ArgumentParser(description="AgentForge throughput benchmark")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--users", type=int, default=5, help="Concurrent users per endpoint")
    parser.add_argument("--duration", type=int, default=10, help="Benchmark duration in seconds")
    args = parser.parse_args()

    print("AgentForge Load Benchmark")
    print(f"  Base URL: {args.base_url}")
    print(f"  Users:    {args.users}")
    print(f"  Duration: {args.duration}s")
    print()

    # Get auth token
    token = ""
    async with httpx.AsyncClient(base_url=args.base_url, timeout=10) as client:
        r = await client.post("/api/v1/auth/login", json={
            "email": "demo@agentforge.dev",
            "password": "changeme",
        })
        if r.status_code == 200:
            token = r.json()["token"]
            print("  Auth: OK (demo user)")
        else:
            print(f"  Auth: login failed ({r.status_code}), running open endpoints only")
        print()

    endpoints = [
        ("/api/v1/health", "Health Check", False),
        ("/api/v1/metrics", "Metrics", False),
        ("/api/v1/keys/providers", "Providers", False),
        ("/api/v1/teams", "List Teams (auth)", True),
    ]

    all_results = []
    for endpoint, label, needs_auth in endpoints:
        if needs_auth and not token:
            print(f"  Skipping {label} (no auth token)")
            continue
        print(f"  Benchmarking {label}...")
        t = await benchmark_endpoint(
            args.base_url, endpoint, args.users, args.duration,
            token=token if needs_auth else "",
        )
        all_results.append(t)
        print(f"    {t['rps']} req/s ({t['total_requests']} requests)")
        print()

    if all_results:
        print("── Summary ──────────────────────────────────────")
        for r in all_results:
            print(f"  {r['endpoint']:40s} {r['rps']:>8.1f} req/s")

        total_rps = sum(r['rps'] for r in all_results)
        print(f"  {'TOTAL':40s} {total_rps:>8.1f} req/s")


if __name__ == "__main__":
    asyncio.run(main())
