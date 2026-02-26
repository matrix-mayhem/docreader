# 04 - Design Patterns (Senior-Level + System Design Focus)

Design patterns are proven templates for solving recurring design problems. At senior level, the goal is not to memorize names, but to choose the right trade-offs for **scalability, reliability, changeability, and team velocity**.

---

## 1) Pattern Thinking at Senior Level

Before selecting a pattern, ask:

1. **What will change most often?** (business rules, integrations, data model, UI flow)
2. **Where is coupling too high?**
3. **What failure modes exist?** (timeouts, partial writes, duplicate events, race conditions)
4. **What scale target matters?** (QPS, data volume, number of teams, release frequency)
5. **What should be optimized?** (latency, cost, consistency, throughput)

A good pattern fit should reduce risk and increase clarity, not add unnecessary abstraction.

---

## 2) Core OOP Design Patterns (Refresher)

## Creational

- **Singleton**: ensure one instance (use carefully in tests and concurrent systems)
- **Factory Method**: delegate object creation to subclasses/methods
- **Abstract Factory**: create related object families (e.g., cloud provider adapters)
- **Builder**: construct complex objects step-by-step with validation

## Structural

- **Adapter**: wrap incompatible interfaces
- **Decorator**: add behavior dynamically without subclass explosion
- **Facade**: provide a simplified, stable API over complex subsystems
- **Proxy**: control access (caching, lazy loading, authorization, remote calls)

## Behavioral

- **Strategy**: switch algorithms/policies at runtime
- **Observer**: event-driven one-to-many notification
- **Command**: encapsulate actions as objects (supports queues/retries/undo)
- **State**: behavior changes based on internal state
- **Template Method**: common workflow skeleton with overridable steps

---

## 3) System Design Patterns Every Senior Engineer Should Know

These are architecture-level patterns often implemented using OOP principles.

### A) Layered Architecture (Presentation → Application → Domain → Infrastructure)

**Use when:** building business applications with clear separation of concerns.
**Benefits:** maintainability, testability, team ownership boundaries.
**Trade-off:** can become rigid if over-layered.

### B) Hexagonal / Ports-and-Adapters

Core domain depends on abstractions (ports), external services plug via adapters.

**Use when:** domain logic should be independent of DB/framework/vendors.
**Benefits:** easy testing, vendor portability, cleaner boundaries.
**Trade-off:** more interfaces/boilerplate.

### C) CQRS (Command Query Responsibility Segregation)

Separate write and read models for different scalability/performance needs.

**Use when:** read and write workloads differ significantly.
**Benefits:** optimized models, independent scaling.
**Trade-off:** eventual consistency and higher complexity.

### D) Event-Driven Architecture

Services communicate through events (pub/sub, message brokers, streams).

**Use when:** asynchronous workflows and loose coupling are needed.
**Benefits:** resilience, decoupling, extensibility.
**Trade-off:** tracing/debugging complexity, ordering/idempotency challenges.

### E) Saga Pattern (Distributed Transactions)

Coordinate multi-service business transactions using compensating actions.

- **Choreography Saga**: services react to events.
- **Orchestration Saga**: central orchestrator controls steps.

**Use when:** ACID across services is impractical.
**Benefits:** consistency at workflow level.
**Trade-off:** compensation complexity and edge cases.

### F) Outbox Pattern

Write business state + event record in the same local transaction; publish later.

**Use when:** avoiding dual-write inconsistency between DB and broker.
**Benefits:** reliable event publication.
**Trade-off:** requires relay process and monitoring.

### G) Circuit Breaker + Retry + Timeout + Bulkhead

Reliability patterns for external calls.

- **Timeout**: fail fast.
- **Retry (with backoff + jitter)**: recover transient failures.
- **Circuit Breaker**: stop hammering failing dependency.
- **Bulkhead**: isolate resources so one failure doesn't sink all traffic.

**Use when:** downstream dependency reliability is variable.
**Benefits:** graceful degradation and protection.
**Trade-off:** tuning thresholds can be hard.

### H) Cache-Aside / Read-Through / Write-Through

**Use when:** read latency and DB load need improvement.
**Benefits:** lower latency, reduced backend load.
**Trade-off:** cache invalidation and staleness.

### I) API Gateway + Backend for Frontend (BFF)

Centralized cross-cutting concerns and client-specific APIs.

**Use when:** many clients/services, auth/rate-limit/aggregation requirements.
**Benefits:** simplified clients, governance.
**Trade-off:** gateway can become bottleneck or monolith.

### J) Strangler Fig Pattern

Incrementally replace a legacy monolith by routing selected functionality to new services.

**Use when:** gradual modernization with low risk.
**Benefits:** safer migration, continuous delivery.
**Trade-off:** temporary duplication and integration complexity.

---

## 4) Mapping OOP Patterns to System Design

- **Strategy** → dynamic routing, pricing engines, fraud rule evaluation.
- **Factory/Abstract Factory** → cloud/vendor-specific adapter creation.
- **Observer** → internal domain events before moving to broker-based EDA.
- **Facade** → anti-corruption layer for legacy integrations.
- **Command** → queued job execution, retries, audit trail.
- **State** → workflow engines (order states, payment states).

This mapping helps teams evolve from code-level design to distributed architecture.

---

## 5) Senior Interview Scenarios and Pattern Choice

1. **"Need reliable order placement across inventory, payment, shipping"**
   - Choose: **Saga + Outbox + Idempotency keys**
2. **"Reads are 50x writes and need low latency"**
   - Choose: **CQRS + Cache-Aside + Read replicas**
3. **"Third-party API frequently fails"**
   - Choose: **Timeout + Retry + Circuit Breaker + Fallback**
4. **"Monolith migration with minimal downtime"**
   - Choose: **Strangler Fig + API Gateway**
5. **"Business rules change weekly"**
   - Choose: **Strategy + Specification pattern + Rule configuration**

---

## 6) Python Example: Strategy + Factory + Circuit Breaker Skeleton

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> str:
        ...


class CardPayment(PaymentStrategy):
    def pay(self, amount: float) -> str:
        return f"Paid {amount:.2f} via Card"


class UPIPayment(PaymentStrategy):
    def pay(self, amount: float) -> str:
        return f"Paid {amount:.2f} via UPI"


class PaymentFactory:
    @staticmethod
    def create(method: str) -> PaymentStrategy:
        if method == "card":
            return CardPayment()
        if method == "upi":
            return UPIPayment()
        raise ValueError(f"Unsupported payment method: {method}")


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    failures: int = 0
    open: bool = False

    def call(self, fn, *args, **kwargs):
        if self.open:
            raise RuntimeError("Circuit is open")
        try:
            result = fn(*args, **kwargs)
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.open = True
            raise


class CheckoutService:
    def __init__(self, breaker: CircuitBreaker):
        self.breaker = breaker

    def process_payment(self, method: str, amount: float) -> str:
        strategy = PaymentFactory.create(method)
        return self.breaker.call(strategy.pay, amount)
```

In production, pair this with timeout, retry policy, metrics, and tracing.

---

## 7) Practical Guidance

- Prefer **composition over inheritance** for evolving business domains.
- Keep domain model free from framework-specific concerns.
- Avoid "pattern-for-pattern's-sake"; justify by measurable constraints.
- Add observability (logs, metrics, traces) whenever introducing asynchronous patterns.
- Define explicit consistency model: strong vs eventual, and document user impact.

A senior engineer uses patterns as a communication and risk-management tool, not just a coding trick.
