# Financial Analytics API (FastAPI + Pandas + SQL + NumPy)

Production-style backend project for transaction ingestion and analytics workloads.

## Stack
- **FastAPI** for API contracts and dependency injection.
- **SQLAlchemy + SQLite** for durable SQL storage.
- **Pandas** for tabular transformations and feature engineering.
- **NumPy** for statistical computations and lightweight forecasting.

## Features
- Single transaction write endpoint.
- Bulk CSV ingestion endpoint.
- KPI summary endpoint (mean, std, p95, top categories).
- Category trend endpoint with time-based resampling.
- Linear forecast endpoint using NumPy polyfit.
- Anomaly detection endpoint using z-score thresholding.

## Project layout
```text
app/
  main.py               # FastAPI app + endpoints
  database.py           # engine/session/base
  models.py             # SQLAlchemy transaction model
  schemas.py            # Pydantic request/response models
  services/
    analytics.py        # pandas/numpy analytics workflows
tests/
  test_analytics.py
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

## CSV schema for ingestion
```csv
account_id,category,amount,transaction_date
acct-001,cloud,129.50,2024-01-10
acct-002,payroll,5600.00,2024-01-15
```
