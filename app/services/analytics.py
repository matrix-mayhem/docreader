from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


def load_transactions_frame(db: Session) -> pd.DataFrame:
    rows = db.execute(
        text(
            """
            SELECT id, account_id, category, amount, transaction_date
            FROM transactions
            ORDER BY transaction_date
            """
        )
    ).mappings()
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["transaction_date"] = pd.to_datetime(frame["transaction_date"])
    frame["amount"] = frame["amount"].astype(float)
    return frame


def build_summary(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {
            "total_transactions": 0,
            "total_amount": 0.0,
            "average_amount": 0.0,
            "std_amount": 0.0,
            "p95_amount": 0.0,
            "top_categories": [],
        }

    amounts = frame["amount"].to_numpy()
    top_categories = (
        frame.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values(by="amount", ascending=False)
        .head(5)
    )
    top_categories_payload = [
        {"category": row["category"], "amount": float(row["amount"])}
        for _, row in top_categories.iterrows()
    ]

    return {
        "total_transactions": int(frame.shape[0]),
        "total_amount": float(np.sum(amounts)),
        "average_amount": float(np.mean(amounts)),
        "std_amount": float(np.std(amounts)),
        "p95_amount": float(np.percentile(amounts, 95)),
        "top_categories": top_categories_payload,
    }


def category_trends(frame: pd.DataFrame, freq: str = "M") -> list[dict]:
    if frame.empty:
        return []

    trend_df = (
        frame.set_index("transaction_date")
        .groupby("category")
        .resample(freq)["amount"]
        .sum()
        .reset_index()
    )
    trend_df["period"] = trend_df["transaction_date"].dt.strftime("%Y-%m")
    return trend_df[["period", "category", "amount"]].to_dict(orient="records")


def forecast_next_period(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []

    forecasts: list[dict] = []
    monthly = (
        frame.set_index("transaction_date")
        .groupby("category")
        .resample("M")["amount"]
        .sum()
        .reset_index()
    )

    for category, cat_df in monthly.groupby("category"):
        y = cat_df["amount"].to_numpy(dtype=float)
        x = np.arange(len(y), dtype=float)

        if len(y) < 2:
            slope = 0.0
            projected = float(y[-1])
        else:
            slope, intercept = np.polyfit(x, y, 1)
            projected = float(slope * len(y) + intercept)

        forecasts.append(
            {
                "category": category,
                "projected_next_period": round(max(projected, 0.0), 2),
                "slope": round(float(slope), 4),
            }
        )

    return sorted(forecasts, key=lambda value: value["projected_next_period"], reverse=True)


def detect_anomalies(frame: pd.DataFrame, threshold: float = 2.0) -> list[dict]:
    if frame.empty:
        return []

    amount_mean = frame["amount"].mean()
    amount_std = frame["amount"].std(ddof=0)
    if amount_std == 0:
        return []

    frame = frame.copy()
    frame["z_score"] = (frame["amount"] - amount_mean) / amount_std
    anomalies = frame[np.abs(frame["z_score"]) >= threshold]

    return [
        {
            "transaction_id": int(row["id"]),
            "z_score": round(float(row["z_score"]), 3),
            "amount": float(row["amount"]),
            "category": row["category"],
            "transaction_date": row["transaction_date"].date(),
        }
        for _, row in anomalies.sort_values("z_score", key=lambda s: s.abs(), ascending=False).iterrows()
    ]
