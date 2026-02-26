# docreader

This repository now includes a **learning lab** that helps you practice core concepts for:

- **Pandas** (cleaning, grouping, pivoting, time-series, pagination-style filtering)
- **SQL (SQLite)** (CRUD, joins, aggregates, indexes, window functions)
- **FastAPI** (path/query/body params, validation, error handling, dependency-style DB access)

---

## Project structure

- `rag/main.py` — original RAG chatbot implementation.
- `rag/fastapi_pandas_sql_lab.py` — dedicated tutorial API with scenario endpoints.
- `rag/docs.txt` — sample text chunks used by other prototypes.

---

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies (minimum):
   - `fastapi`
   - `uvicorn`
   - `pandas`
3. Run the learning API:

```bash
uvicorn rag.fastapi_pandas_sql_lab:app --reload
```

Open interactive docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Scenario map: FastAPI + SQL + Pandas

### 0) Prepare sample data

- **POST** `/lab/seed`
- Resets and inserts sample users + orders.

---

### 1) FastAPI fundamentals (request handling + validation)

- **POST** `/lab/users`
  - JSON body validation with Pydantic model (`UserCreate`)
  - Returns generated `user_id`

- **POST** `/lab/orders`
  - Validates positive order amount
  - Validates user existence and raises `404` if missing

- **GET** `/lab/pandas/filter-sort-page`
  - Query params: `city`, `min_amount`, `limit`, `offset`
  - Example of filtering + sorting + pagination behavior

---

### 2) SQL fundamentals and intermediate patterns

- **GET** `/lab/sql/join`
  - `JOIN` + `GROUP BY` + aggregates
  - Revenue by city

- **GET** `/lab/sql/window`
  - Window functions:
    - `ROW_NUMBER()` partitioned by user
    - running total with `SUM() OVER (...)`

Also included in schema setup:

- primary keys
- foreign key relation (`orders.user_id -> users.user_id`)
- index (`idx_orders_user_date`) for common filter/sort access patterns

---

### 3) Pandas fundamentals and common data workflows

- **GET** `/lab/pandas/overview`
  - Load SQL tables into DataFrames
  - Type conversion to datetime
  - Merge DataFrames
  - Create bins via `pd.cut`
  - Grouping + aggregate stats
  - Pivot table generation

- **GET** `/lab/pandas/timeseries?freq=W`
  - Resample by time (`D`, `W`, `M`, etc.)
  - Rolling average over resampled results

- **GET** `/lab/pandas/filter-sort-page`
  - Data filtering with conditions
  - Multi-column sorting
  - Page slicing with `offset/limit`

---

## Suggested learning sequence

1. Start server and call `/lab/seed`.
2. Add 1-2 users and orders manually via `/lab/users` and `/lab/orders`.
3. Inspect SQL outputs in `/lab/sql/join` and `/lab/sql/window`.
4. Compare SQL aggregates to Pandas outputs in `/lab/pandas/overview`.
5. Explore time-series behavior by changing `freq` in `/lab/pandas/timeseries`.
6. Experiment with API query params in `/lab/pandas/filter-sort-page`.

---

## Example curl commands

```bash
curl -X POST http://127.0.0.1:8000/lab/seed

curl -X POST http://127.0.0.1:8000/lab/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Esha","city":"Pune","signup_date":"2024-06-11"}'

curl -X POST http://127.0.0.1:8000/lab/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"category":"books","amount":1500,"order_date":"2024-06-15"}'

curl "http://127.0.0.1:8000/lab/sql/join"
curl "http://127.0.0.1:8000/lab/sql/window"
curl "http://127.0.0.1:8000/lab/pandas/overview"
curl "http://127.0.0.1:8000/lab/pandas/timeseries?freq=W"
curl "http://127.0.0.1:8000/lab/pandas/filter-sort-page?city=Delhi&min_amount=500&limit=5&offset=0"
```

---

## Notes

- This lab is intentionally focused on concept clarity over production hardening.
- Once you're comfortable, you can refactor this into:
  - layered architecture (router/service/repository)
  - SQLAlchemy ORM models + migrations
  - async DB driver and async FastAPI handlers
  - automated tests (`pytest`) for each endpoint/scenario
