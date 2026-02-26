# Financial Analytics API (FastAPI + Pandas + SQL + NumPy)

Production-style backend project for transaction ingestion and analytics workloads, plus a **senior-level concurrency lab** for mastering async patterns in FastAPI.

## Stack
- **FastAPI** for API contracts and dependency injection.
- **SQLAlchemy + SQLite** for durable SQL storage.
- **Pandas** for tabular transformations and feature engineering.
- **NumPy** for statistical computations and lightweight forecasting.
- **asyncio + thread/process executors** for concurrency strategy demonstrations.

## Features
- Single transaction write endpoint.
- Bulk CSV ingestion endpoint.
- KPI summary endpoint (mean, std, p95, top categories).
- Category trend endpoint with time-based resampling.
- Linear forecast endpoint using NumPy polyfit.
- Anomaly detection endpoint using z-score thresholding.
- **Concurrency lab endpoint** comparing:
  - Native async I/O (`asyncio` + semaphores)
  - Thread pools for blocking I/O
  - Process pools for CPU-bound work

## Project layout
```text
app/
  main.py                   # FastAPI app + endpoints
  database.py               # engine/session/base
  models.py                 # SQLAlchemy transaction model
  schemas.py                # Pydantic request/response models
  services/
    analytics.py            # pandas/numpy analytics workflows
    concurrency_lab.py      # async/thread/process concurrency exercises
tests/
  test_analytics.py
  test_concurrency_lab.py
```

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`.

## API overview
- `GET /health`
- `POST /transactions`
- `POST /transactions/ingest` (CSV upload)
- `GET /analytics/summary`
- `GET /analytics/trends`
- `GET /analytics/forecast`
- `GET /analytics/anomalies`
- `GET /lab/concurrency?task_count=12`

## Learning path for async/concurrency mastery
Use `/lab/concurrency` and observe runtime differences while changing `task_count`.

1. **I/O-bound with async**: `run_async_io_demo` uses semaphore-limited coroutines and `await asyncio.sleep`.
2. **Blocking I/O with threads**: `run_threaded_io_demo` offloads file + sleep work to `ThreadPoolExecutor`.
3. **CPU-bound with processes**: `run_process_cpu_demo` runs prime calculations in `ProcessPoolExecutor`.
4. **Context managers**: `StageTimer` is an async context manager (`__aenter__` / `__aexit__`) that captures duration for each experiment.

## CSV schema for ingestion
```csv
account_id,category,amount,transaction_date
acct-001,cloud,129.50,2024-01-10
acct-002,payroll,5600.00,2024-01-15
```
