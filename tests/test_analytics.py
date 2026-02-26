from __future__ import annotations

import pandas as pd

from app.services.analytics import build_summary, detect_anomalies, forecast_next_period


def test_build_summary_returns_aggregates() -> None:
    frame = pd.DataFrame(
        [
            {"id": 1, "category": "cloud", "amount": 100.0, "transaction_date": "2024-01-01"},
            {"id": 2, "category": "cloud", "amount": 120.0, "transaction_date": "2024-02-01"},
            {"id": 3, "category": "payroll", "amount": 400.0, "transaction_date": "2024-03-01"},
        ]
    )

    summary = build_summary(frame)

    assert summary["total_transactions"] == 3
    assert summary["total_amount"] == 620.0
    assert summary["top_categories"][0]["category"] == "payroll"


def test_forecast_and_anomalies() -> None:
    frame = pd.DataFrame(
        [
            {"id": 1, "category": "ops", "amount": 100.0, "transaction_date": "2024-01-01"},
            {"id": 2, "category": "ops", "amount": 130.0, "transaction_date": "2024-02-01"},
            {"id": 3, "category": "ops", "amount": 170.0, "transaction_date": "2024-03-01"},
            {"id": 4, "category": "ops", "amount": 900.0, "transaction_date": "2024-04-01"},
        ]
    )
    frame["transaction_date"] = pd.to_datetime(frame["transaction_date"])

    forecast = forecast_next_period(frame)
    anomalies = detect_anomalies(frame, threshold=1.5)

    assert forecast
    assert forecast[0]["projected_next_period"] >= 0
    assert anomalies[0]["transaction_id"] == 4
