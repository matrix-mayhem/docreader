from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    account_id: str = Field(min_length=3, max_length=64)
    category: str = Field(min_length=2, max_length=128)
    amount: float
    transaction_date: date


class TransactionRead(TransactionCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BulkIngestResponse(BaseModel):
    rows_ingested: int


class SummaryResponse(BaseModel):
    total_transactions: int
    total_amount: float
    average_amount: float
    std_amount: float
    p95_amount: float
    top_categories: list[dict[str, float | str]]


class CategoryTrendPoint(BaseModel):
    period: str
    category: str
    amount: float


class ForecastResponse(BaseModel):
    category: str
    projected_next_period: float
    slope: float


class AnomalyResponse(BaseModel):
    transaction_id: int
    z_score: float
    amount: float
    category: str
    transaction_date: date


class ConcurrencyDemoResponse(BaseModel):
    mode: str
    workers: int
    tasks: int
    elapsed_ms: float
    sample: list[int | float | str]
