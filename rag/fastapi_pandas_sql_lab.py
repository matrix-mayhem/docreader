"""Hands-on learning lab for Pandas + SQL + FastAPI concepts.

Run:
    uvicorn rag.fastapi_pandas_sql_lab:app --reload
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import Body, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Pandas + SQL + FastAPI Learning Lab", version="1.0.0")

DB_PATH = Path("rag/lab.db")


# --------------------------
# Database utilities
# --------------------------
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT,
                signup_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_orders_user_date
            ON orders(user_id, order_date);
            """
        )


@app.on_event("startup")
def startup() -> None:
    init_db()


# --------------------------
# Pydantic schemas
# --------------------------
class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    city: str = Field(default="Unknown")
    signup_date: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())


class OrderCreate(BaseModel):
    user_id: int
    category: str = Field(min_length=1)
    amount: float = Field(gt=0)
    order_date: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())


# --------------------------
# Seed + CRUD scenarios
# --------------------------
@app.post("/lab/seed")
def seed_data() -> dict:
    users = [
        (1, "Asha", "Delhi", "2024-01-10"),
        (2, "Ben", "Mumbai", "2024-02-01"),
        (3, "Cara", "Delhi", "2024-03-15"),
        (4, "Dev", "Bengaluru", "2024-04-02"),
    ]
    orders = [
        (1, 1, "books", 1200, "2024-05-01"),
        (2, 1, "tech", 3500, "2024-05-02"),
        (3, 2, "books", 800, "2024-05-02"),
        (4, 3, "fashion", 2200, "2024-05-03"),
        (5, 3, "books", 600, "2024-05-10"),
        (6, 4, "tech", 9000, "2024-05-10"),
    ]

    with get_conn() as conn:
        conn.execute("DELETE FROM orders")
        conn.execute("DELETE FROM users")
        conn.executemany("INSERT INTO users(user_id, name, city, signup_date) VALUES (?, ?, ?, ?)", users)
        conn.executemany(
            "INSERT INTO orders(order_id, user_id, category, amount, order_date) VALUES (?, ?, ?, ?, ?)",
            orders,
        )

    return {"message": "Seeded users and orders"}


@app.post("/lab/users")
def create_user(payload: Annotated[UserCreate, Body(...)]) -> dict:
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO users(name, city, signup_date) VALUES (?, ?, ?)",
            (payload.name, payload.city, payload.signup_date),
        )
    return {"user_id": cursor.lastrowid}


@app.post("/lab/orders")
def create_order(payload: Annotated[OrderCreate, Body(...)]) -> dict:
    with get_conn() as conn:
        user_exists = conn.execute("SELECT 1 FROM users WHERE user_id=?", (payload.user_id,)).fetchone()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        cursor = conn.execute(
            "INSERT INTO orders(user_id, category, amount, order_date) VALUES (?, ?, ?, ?)",
            (payload.user_id, payload.category, payload.amount, payload.order_date),
        )
    return {"order_id": cursor.lastrowid}


# --------------------------
# SQL concept scenarios
# --------------------------
@app.get("/lab/sql/join")
def sql_join() -> dict:
    """INNER JOIN + aggregate."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.city, COUNT(o.order_id) AS order_count, ROUND(SUM(o.amount), 2) AS revenue
            FROM users u
            JOIN orders o ON o.user_id = u.user_id
            GROUP BY u.city
            ORDER BY revenue DESC
            """
        ).fetchall()
    return {"rows": [dict(row) for row in rows]}


@app.get("/lab/sql/window")
def sql_window_function() -> dict:
    """ROW_NUMBER + running total in SQL."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                o.order_id,
                o.user_id,
                o.amount,
                ROW_NUMBER() OVER (PARTITION BY o.user_id ORDER BY o.order_date, o.order_id) AS rn,
                SUM(o.amount) OVER (PARTITION BY o.user_id ORDER BY o.order_date, o.order_id) AS running_total
            FROM orders o
            ORDER BY o.user_id, rn
            """
        ).fetchall()
    return {"rows": [dict(row) for row in rows]}


# --------------------------
# Pandas concept scenarios
# --------------------------
def load_dataframes() -> tuple[pd.DataFrame, pd.DataFrame]:
    with get_conn() as conn:
        users = pd.read_sql_query("SELECT * FROM users", conn)
        orders = pd.read_sql_query("SELECT * FROM orders", conn)
    return users, orders


@app.get("/lab/pandas/overview")
def pandas_overview() -> dict:
    users, orders = load_dataframes()

    orders["order_date"] = pd.to_datetime(orders["order_date"])
    users["signup_date"] = pd.to_datetime(users["signup_date"])

    merged = orders.merge(users, on="user_id", how="left")
    merged["amount_bucket"] = pd.cut(merged["amount"], bins=[0, 1000, 5000, 10000], labels=["low", "mid", "high"])

    grouped = (
        merged.groupby(["city", "category"], as_index=False)["amount"]
        .agg(["count", "sum", "mean"])
        .round(2)
        .reset_index()
    )

    pivot = pd.pivot_table(
        merged,
        index="city",
        columns="category",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    )

    return {
        "shape": {"users": users.shape, "orders": orders.shape, "merged": merged.shape},
        "groupby": grouped.to_dict(orient="records"),
        "pivot": pivot.reset_index().to_dict(orient="records"),
    }


@app.get("/lab/pandas/timeseries")
def pandas_timeseries(
    freq: Annotated[str, Query(description="Resample frequency. Ex: D, W, M")] = "W",
) -> dict:
    _, orders = load_dataframes()
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    ts = (
        orders.set_index("order_date")
        .resample(freq)["amount"]
        .sum()
        .rename("revenue")
        .reset_index()
    )

    ts["rolling_2_period_avg"] = ts["revenue"].rolling(2, min_periods=1).mean().round(2)

    return {"rows": ts.to_dict(orient="records")}


@app.get("/lab/pandas/filter-sort-page")
def pandas_filter_sort_page(
    city: Annotated[str | None, Query()] = None,
    min_amount: Annotated[float, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    users, orders = load_dataframes()
    merged = orders.merge(users, on="user_id", how="left")

    filtered = merged[merged["amount"] >= min_amount]
    if city:
        filtered = filtered[filtered["city"].str.lower() == city.lower()]

    sorted_df = filtered.sort_values(["amount", "order_date"], ascending=[False, True])
    page = sorted_df.iloc[offset : offset + limit]

    return {
        "total_rows": int(len(sorted_df)),
        "rows": page.to_dict(orient="records"),
    }
