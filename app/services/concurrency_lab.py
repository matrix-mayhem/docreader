from __future__ import annotations

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from pathlib import Path


class StageTimer(AbstractAsyncContextManager):
    """Async context manager that captures elapsed wall clock time."""

    def __init__(self, stage: str):
        self.stage = stage
        self.started_at = 0.0
        self.elapsed_ms = 0.0

    async def __aenter__(self) -> "StageTimer":
        self.started_at = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.elapsed_ms = (time.perf_counter() - self.started_at) * 1000


@dataclass
class DemoResult:
    mode: str
    workers: int
    tasks: int
    elapsed_ms: float
    sample: list[int | float | str]


def _is_prime(candidate: int) -> bool:
    if candidate < 2:
        return False
    if candidate == 2:
        return True
    if candidate % 2 == 0:
        return False

    upper = int(candidate**0.5) + 1
    for factor in range(3, upper, 2):
        if candidate % factor == 0:
            return False
    return True


def nth_prime(n: int) -> int:
    found = 0
    candidate = 1
    while found < n:
        candidate += 1
        if _is_prime(candidate):
            found += 1
    return candidate


def _blocking_io_simulation(index: int, wait_ms: int, scratch_dir: str) -> int:
    path = Path(scratch_dir) / f"io_task_{index}.txt"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"task={index}\n")
    time.sleep(wait_ms / 1000)
    with path.open("r", encoding="utf-8") as handle:
        content = handle.read().strip()
    return len(content)


async def run_async_io_demo(task_count: int, wait_ms: int, concurrency: int) -> DemoResult:
    semaphore = asyncio.Semaphore(concurrency)

    async def _task(index: int) -> int:
        async with semaphore:
            await asyncio.sleep(wait_ms / 1000)
            return index

    async with StageTimer("async-io") as timer:
        results = await asyncio.gather(*(_task(i) for i in range(task_count)))

    return DemoResult(
        mode="async_io",
        workers=concurrency,
        tasks=task_count,
        elapsed_ms=round(timer.elapsed_ms, 2),
        sample=results[:5],
    )


async def run_threaded_io_demo(
    task_count: int,
    wait_ms: int,
    workers: int,
    scratch_dir: str = "/tmp",
) -> DemoResult:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        async with StageTimer("thread-io") as timer:
            futures = [
                loop.run_in_executor(pool, _blocking_io_simulation, i, wait_ms, scratch_dir)
                for i in range(task_count)
            ]
            results = await asyncio.gather(*futures)

    return DemoResult(
        mode="thread_io",
        workers=workers,
        tasks=task_count,
        elapsed_ms=round(timer.elapsed_ms, 2),
        sample=results[:5],
    )


async def run_process_cpu_demo(task_count: int, n: int, workers: int) -> DemoResult:
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        async with StageTimer("process-cpu") as timer:
            futures = [loop.run_in_executor(pool, nth_prime, n + i) for i in range(task_count)]
            results = await asyncio.gather(*futures)

    return DemoResult(
        mode="process_cpu",
        workers=workers,
        tasks=task_count,
        elapsed_ms=round(timer.elapsed_ms, 2),
        sample=results[:5],
    )


async def run_concurrency_showcase(task_count: int = 12) -> list[DemoResult]:
    """Compare asyncio, threads, and processes for common backend workloads."""

    async_result = await run_async_io_demo(task_count=task_count, wait_ms=120, concurrency=4)
    thread_result = await run_threaded_io_demo(task_count=task_count, wait_ms=120, workers=4)
    process_result = await run_process_cpu_demo(task_count=task_count, n=1200, workers=4)
    return [async_result, thread_result, process_result]
