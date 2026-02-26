from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services.concurrency_lab import nth_prime, run_async_io_demo, run_process_cpu_demo


def test_nth_prime_is_deterministic() -> None:
    assert nth_prime(1) == 2
    assert nth_prime(10) == 29


def test_async_io_demo_returns_shape() -> None:
    result = asyncio.run(run_async_io_demo(task_count=5, wait_ms=5, concurrency=2))

    assert result.mode == "async_io"
    assert result.tasks == 5
    assert len(result.sample) == 5


def test_process_cpu_demo_returns_results() -> None:
    result = asyncio.run(run_process_cpu_demo(task_count=2, n=50, workers=2))

    assert result.mode == "process_cpu"
    assert result.tasks == 2
    assert all(isinstance(value, int) for value in result.sample)


def test_concurrency_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/lab/concurrency", params={"task_count": 4})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    assert {item["mode"] for item in payload} == {"async_io", "thread_io", "process_cpu"}
