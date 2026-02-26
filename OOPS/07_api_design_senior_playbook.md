# Senior API Design Playbook (with Code)

This guide is for learning API design the way senior engineers think: **requirements first, contract-first design, scalability, backward compatibility, observability, and operations**.

---

## 1) Start with product requirements, not endpoints

Before writing routes, capture:

- Actors (who calls the API)
- Capabilities (what they need)
- SLA/SLO targets (latency, uptime)
- Data sensitivity (PII, PCI, compliance)
- Volume assumptions (RPS, payload size, burst)
- Consistency needs (strong/eventual)

### Example requirement card

```text
Feature: Submit transaction
Actors: Internal service, finance admin UI
SLO: p95 < 300ms, 99.9% availability
Traffic: 500 RPS baseline, 2k RPS burst
Consistency: write-after-read for single account
Security: OAuth2 JWT, audit trail required
```

---

## 2) API style choices and when to use each

## REST (resource-oriented)
Use when you want broad compatibility and cache-friendly HTTP semantics.

```http
POST /v1/transactions
GET /v1/transactions/{id}
GET /v1/accounts/{account_id}/transactions?from=2026-01-01&to=2026-01-31
```

**Strengths:** simple, ubiquitous, tooling-rich.  
**Tradeoffs:** over-fetching/under-fetching for complex clients.

## GraphQL (query-oriented)
Use when clients need flexible field selection and aggregation across entities.

```graphql
query {
  account(id: "acct-1") {
    id
    transactions(limit: 5) {
      id
      amount
      category
    }
  }
}
```

**Strengths:** client flexibility, fewer round trips.  
**Tradeoffs:** complexity in caching, cost control, authorization.

## gRPC (contract + performance)
Use for service-to-service low-latency typed communication.

```proto
service TransactionService {
  rpc CreateTransaction(CreateTransactionRequest) returns (TransactionResponse);
}
```

**Strengths:** strict contracts, strong performance, streaming.  
**Tradeoffs:** browser support needs proxies, more operational complexity.

## Event-driven API (async contracts)
Use for workflows that don't need immediate response and require loose coupling.

```json
{
  "event_type": "transaction.created",
  "event_id": "evt_123",
  "occurred_at": "2026-02-01T10:00:00Z",
  "payload": {
    "transaction_id": "tx_42",
    "account_id": "acct_1",
    "amount": 120.5
  }
}
```

**Strengths:** decoupled scaling, replay, eventual consistency patterns.  
**Tradeoffs:** harder debugging, idempotency + ordering challenges.

---

## 3) Contract-first REST design in FastAPI

### 3.1 Resource model and naming

- Nouns, not verbs: `/transactions`, `/accounts/{id}`
- Consistent pluralization
- Avoid deep nesting unless ownership is strict (`/accounts/{id}/transactions` is acceptable)

### 3.2 Request/response schemas

```python
from datetime import datetime
from pydantic import BaseModel, Field, condecimal

class CreateTransactionRequest(BaseModel):
    account_id: str = Field(min_length=3, max_length=64)
    category: str = Field(min_length=2, max_length=64)
    amount: condecimal(gt=0, max_digits=12, decimal_places=2)
    transaction_date: datetime

class TransactionResponse(BaseModel):
    id: str
    account_id: str
    category: str
    amount: float
    transaction_date: datetime
    created_at: datetime
```

### 3.3 Endpoint contract with status codes

```python
from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(payload: CreateTransactionRequest, response: Response):
    created = await service.create_transaction(payload)
    response.headers["Location"] = f"/v1/transactions/{created.id}"
    return created
```

Use semantic statuses:

- `201 Created` on successful creation
- `400 Bad Request` for malformed payload
- `401/403` for authn/authz
- `404` resource absent
- `409` conflict (duplicate/idempotency violation)
- `422` validation error
- `429` rate limited
- `5xx` server/internal/dependency failures

---

## 4) Cross-cutting concerns seniors always design

## 4.1 Idempotency for create/write endpoints

```python
@router.post("", status_code=201)
async def create_transaction(payload: CreateTransactionRequest, idempotency_key: str = Header(...)):
    existing = await idempotency_store.get(idempotency_key)
    if existing:
        return existing
    created = await service.create_transaction(payload)
    await idempotency_store.save(idempotency_key, created)
    return created
```

## 4.2 Pagination patterns

Offset pagination (simple):

```http
GET /v1/transactions?limit=50&offset=100
```

Cursor pagination (recommended at scale):

```http
GET /v1/transactions?limit=50&cursor=eyJjcmVhdGVkX2F0Ijoi..."
```

Response shape:

```json
{
  "items": [ ... ],
  "page": {
    "next_cursor": "abc",
    "has_more": true
  }
}
```

## 4.3 Filtering/sorting conventions

```http
GET /v1/transactions?account_id=acct-1&category=cloud&sort=-transaction_date,amount
```

Rules:
- Prefix descending with `-`
- Reject unknown filter fields
- Publish allowed operators (`eq`, `gte`, `lte`, `in`)

## 4.4 Error envelope standardization

```json
{
  "error": {
    "code": "INVALID_CATEGORY",
    "message": "Category must be one of payroll, cloud, rent",
    "details": {"field": "category"},
    "trace_id": "d5f9..."
  }
}
```

## 4.5 Rate limiting + quotas

- Token bucket per API key/user
- Return `429` + `Retry-After`
- Expose usage headers if product requires it

---

## 5) Versioning and compatibility strategy

Common strategies:

- URI versioning: `/v1/...` (clear and explicit)
- Header versioning: `Accept: application/vnd.company.v2+json`

Senior rule: **avoid breaking changes when possible**.

Examples:

- Safe: add optional field `merchant_name`
- Risky: change field type `amount: string -> number`
- Breaking: rename required field `account_id -> account`

Deprecation playbook:

1. Mark field/endpoint deprecated in OpenAPI docs
2. Emit warning header and telemetry
3. Communicate migration timeline
4. Remove after adoption threshold and sunset date

---

## 6) Security design checklist

- OAuth2/JWT for user APIs, mTLS/API keys for internal APIs
- RBAC/ABAC authorization at endpoint and record level
- Input validation + output encoding
- Secrets via vault/KMS, never hardcoded
- Audit logs for sensitive actions
- Threat model: replay, injection, privilege escalation, data exfiltration

FastAPI dependency example:

```python
from fastapi import Depends, HTTPException, status

async def require_scope(user=Depends(get_current_user)):
    if "transactions:write" not in user.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
    return user
```

---

## 7) Reliability patterns

- Timeouts on all downstream calls
- Retries with exponential backoff + jitter (only for safe/idempotent operations)
- Circuit breakers for flaky dependencies
- Bulkheads (thread/connection pool isolation)
- Graceful degradation (partial response with warnings)

Pseudo-policy:

```python
retry_policy = {
    "max_attempts": 3,
    "base_delay_ms": 50,
    "jitter": True,
    "retry_on": ["timeout", "503"]
}
```

---

## 8) Observability and operational excellence

Emit:

- Structured logs (`trace_id`, `user_id`, `endpoint`, `latency_ms`)
- Metrics (RPS, p95/p99, error rate, saturation)
- Traces (distributed spans across dependencies)

Example middleware idea:

```python
@app.middleware("http")
async def telemetry(request, call_next):
    trace_id = request.headers.get("x-trace-id", uuid4().hex)
    start = perf_counter()
    response = await call_next(request)
    duration_ms = (perf_counter() - start) * 1000
    logger.info("request_done", extra={"trace_id": trace_id, "path": request.url.path, "latency_ms": duration_ms})
    response.headers["x-trace-id"] = trace_id
    return response
```

---

## 9) Testing matrix for API contracts

- Unit tests for business rules and validators
- Integration tests for DB + service boundaries
- Contract tests against OpenAPI schema
- Load tests for SLO validation
- Chaos/failure tests for retry/circuit behavior

Example `pytest` contract assertion:

```python
def test_create_transaction_returns_201(client):
    payload = {
        "account_id": "acct-1",
        "category": "cloud",
        "amount": 100.00,
        "transaction_date": "2026-01-01T10:00:00Z"
    }
    r = client.post("/v1/transactions", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
```

---

## 10) How seniors review API designs

Use this scorecard (0-2 each):

1. Clear resource boundaries
2. Error model consistency
3. Backward compatibility plan
4. Security model (authn/authz + audit)
5. SLO-aware performance strategy
6. Idempotency/retry safety
7. Pagination/filter/sort conventions
8. Observability completeness
9. Operational runbooks and alerting
10. Migration/deprecation readiness

A design scoring `< 14/20` usually needs redesign before production.

---

## 11) End-to-end mini blueprint (recommended learning sequence)

1. Design OpenAPI spec for `transactions` domain.
2. Implement `POST /v1/transactions` with idempotency key.
3. Add `GET /v1/transactions` with cursor pagination.
4. Standardize error envelope + trace ID.
5. Add scope-based authorization.
6. Add metrics/logging middleware.
7. Validate with unit + integration + load tests.
8. Publish migration notes for v2 additions.

If you can do all 8 steps with clean code and measurable SLOs, you're operating at strong senior API design level.
