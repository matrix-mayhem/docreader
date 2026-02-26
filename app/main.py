from __future__ import annotations

from io import StringIO

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, engine, get_db
from app.services.analytics import (
    build_summary,
    category_trends,
    detect_anomalies,
    forecast_next_period,
    load_transactions_frame,
)

from app.services.concurrency_lab import run_concurrency_showcase

app = FastAPI(title="Financial Analytics API", version="1.0.0")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/transactions", response_model=schemas.TransactionRead)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    entity = models.Transaction(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@app.post("/transactions/ingest", response_model=schemas.BulkIngestResponse)
def ingest_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = file.file.read().decode("utf-8")
    frame = pd.read_csv(StringIO(contents))
    required_columns = {"account_id", "category", "amount", "transaction_date"}
    missing = required_columns - set(frame.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing columns: {sorted(missing)}")

    frame["transaction_date"] = pd.to_datetime(frame["transaction_date"]).dt.date
    entities = [models.Transaction(**item) for item in frame.to_dict(orient="records")]
    db.add_all(entities)
    db.commit()

    return schemas.BulkIngestResponse(rows_ingested=len(entities))


@app.get("/analytics/summary", response_model=schemas.SummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    frame = load_transactions_frame(db)
    return build_summary(frame)


@app.get("/analytics/trends", response_model=list[schemas.CategoryTrendPoint])
def get_trends(db: Session = Depends(get_db)):
    frame = load_transactions_frame(db)
    return category_trends(frame)


@app.get("/analytics/forecast", response_model=list[schemas.ForecastResponse])
def get_forecast(db: Session = Depends(get_db)):
    frame = load_transactions_frame(db)
    return forecast_next_period(frame)


@app.get("/analytics/anomalies", response_model=list[schemas.AnomalyResponse])
def get_anomalies(db: Session = Depends(get_db)):
    frame = load_transactions_frame(db)
    return detect_anomalies(frame)


@app.get("/lab/concurrency", response_model=list[schemas.ConcurrencyDemoResponse])
async def concurrency_lab(task_count: int = 12):
    if task_count < 1 or task_count > 40:
        raise HTTPException(status_code=422, detail="task_count must be between 1 and 40")
    result = await run_concurrency_showcase(task_count=task_count)
    return [item.__dict__ for item in result]
