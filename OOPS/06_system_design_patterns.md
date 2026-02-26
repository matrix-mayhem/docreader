# 06 - System Design Patterns (Extensive Senior-Level Guide)

This guide focuses on architecture patterns used in production-grade distributed systems. The intent is to help you make senior-level trade-offs, not just list definitions.

## 1) How Seniors Choose Patterns

Use this decision frame:

- **Scale shape**: read-heavy, write-heavy, bursty, globally distributed?
- **Consistency needs**: strict correctness vs eventual consistency tolerance?
- **Failure budget**: what can fail, for how long, and with what blast radius?
- **Change frequency**: how often will rules/integrations evolve?
- **Team topology**: can teams own services independently?

A pattern is good only when it solves today's constraint without creating unpayable complexity tomorrow.

---

## 2) Data & Transaction Patterns

### 2.1 Database per Service

Each service owns its data store schema and lifecycle.

- **Why**: independent deployment and ownership
- **Watch out**: cross-service joins become API/event orchestration

### 2.2 Saga Pattern

Distributed transaction via local transactions + compensation.

- **Orchestration**: central workflow manager (clear control, single coordination point)
- **Choreography**: event reactions (loosely coupled, but emergent complexity)
- **Key needs**: idempotency, dead-letter handling, timeout compensation

### 2.3 Outbox + Inbox

- **Outbox** ensures atomicity between DB write and event publication.
- **Inbox** ensures consumer-side deduplication/exactly-once effect semantics.

### 2.4 Event Sourcing (selectively)

Persist state as immutable event log; rebuild state by replay.

- **Use when**: auditability/time-travel/history are core requirements
- **Trade-off**: projection maintenance and operational complexity

---

## 3) Read/Write Scaling Patterns

### 3.1 CQRS

Separate command model (writes) and query model (reads).

- **Use when**: read and write concerns diverge in shape and scale
- **Add-ons**: materialized views, denormalized projections

### 3.2 Caching Patterns

- **Cache-aside**: app controls cache population (most common)
- **Read-through**: cache layer fetches from DB when missing
- **Write-through/write-behind**: trade durability vs latency

Important senior concerns:

- TTL strategy per entity type
- stampede control (request coalescing, soft TTL)
- invalidation by versioning/event triggers

### 3.3 Sharding

Horizontal partitioning by shard key.

- **Choose key carefully**: cardinality, hotspot risk, query patterns
- **Plan early**: rebalancing/migration strategy

---

## 4) Reliability & Resilience Patterns

### 4.1 Timeout + Retry + Backoff + Jitter

- Retry only transient failures.
- Use exponential backoff + jitter to avoid synchronized retry storms.
- Respect idempotency before retrying writes.

### 4.2 Circuit Breaker

Protects dependencies by opening circuit after threshold failures.

States typically: `closed -> open -> half-open -> closed/open`.

### 4.3 Bulkhead

Isolate resources (thread pools/connections/queues) per dependency path.

### 4.4 Rate Limiting & Load Shedding

- Token bucket/leaky bucket for fairness.
- Shed non-critical traffic to preserve core flows.

### 4.5 Fallback & Graceful Degradation

Define degraded behavior explicitly (cached defaults, partial response, async confirmation).

---

## 5) Integration & API Patterns

### 5.1 API Gateway

Central point for auth, routing, throttling, observability, and policy.

### 5.2 Backend for Frontend (BFF)

Dedicated backend per client type (web/mobile/partner) to avoid over-fetching and coupling.

### 5.3 Anti-Corruption Layer (ACL)

Facade/adapter boundary around legacy or third-party models to protect your domain language.

### 5.4 Idempotency Keys

Mandatory for payment/order-style APIs where duplicate submission is common.

---

## 6) Messaging & Event Patterns

### 6.1 Competing Consumers

Scale consumer throughput horizontally with shared subscription.

### 6.2 Dead Letter Queue (DLQ)

Route poison messages for diagnosis/replay.

### 6.3 Exactly-Once Myth

In practice, design for **at-least-once delivery** and **idempotent processing**.

### 6.4 Ordering Guarantees

Per-key ordering is often feasible; global ordering rarely scales affordably.

---

## 7) Migration & Evolution Patterns

### 7.1 Strangler Fig

Replace legacy capabilities incrementally behind routing boundary.

### 7.2 Branch by Abstraction

Introduce abstraction first, then swap implementation gradually.

### 7.3 Parallel Run / Shadow Traffic

Validate new path correctness and performance before cutover.

---

## 8) Observability Patterns (Non-Optional at Senior Level)

- **Structured logs** with correlation IDs
- **Metrics**: RED/USE plus business KPIs
- **Tracing**: distributed traces across service boundaries
- **SLO-driven alerts**: alert on user impact, not internal noise

Pattern adoption without observability is operational risk.

---

## 9) Pattern Compositions You’ll Use Often

1. **Reliable order workflow**
   - API Gateway + Idempotency Key + Saga + Outbox/Inbox + DLQ
2. **Low-latency product catalog**
   - CQRS + Materialized views + Cache-aside + Event invalidation
3. **Unstable third-party provider**
   - Adapter + Timeout/Retry/Jitter + Circuit Breaker + Fallback
4. **Legacy modernization**
   - Strangler Fig + ACL + Branch by Abstraction + Shadow traffic

---

## 10) Senior-Level Design Review Checklist

- What are explicit **invariants** and where are they enforced?
- Which operations are **idempotent**?
- What are the **failure domains** and **blast radius controls**?
- What is the **consistency model** per user journey?
- How do we detect and recover from **partial failures**?
- What is the **backpressure strategy** under overload?
- How is data **replayed/reconciled** after outages?
- Which metrics prove this design works in production?

---

## 11) Common Anti-Patterns

- Distributed monolith (many services, synchronized deployments)
- Shared database across service boundaries
- Synchronous call chains with no timeout budgets
- Blind retries causing retry storms
- Event-driven design without schema governance/versioning
- "Microservices first" before modular monolith maturity

---

## 12) Final Advice

Senior engineering is about controlled trade-offs. Start simple, instrument deeply, and evolve architecture only when real constraints demand it.
