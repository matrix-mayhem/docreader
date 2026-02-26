# OOPS Learning Hub

Welcome to the **OOPS** folder. This material is designed to help you learn Object-Oriented Programming (OOP) in a structured, deep, and practical way.

## What you'll learn

- Why OOP exists and what problems it solves
- Core pillars: Encapsulation, Abstraction, Inheritance, Polymorphism
- Class design, composition, and relationships
- SOLID principles for maintainable code
- Common design patterns
- Real-world Python examples and mini-project ideas
- Interview-style questions and practice prompts

## Study Path (Recommended)

1. Start with `01_basics.md`
2. Continue to `02_pillars.md`
3. Learn design with `03_design_principles.md`
4. Explore reusable architecture in `04_design_patterns.md`
5. Practice with `05_projects_and_exercises.md`

## Quick Start Example (Python)

```python
class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self.__balance = balance  # encapsulated

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.__balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")
        if amount > self.__balance:
            raise ValueError("Insufficient funds")
        self.__balance -= amount

    def get_balance(self) -> float:
        return self.__balance
```

This small class already demonstrates encapsulation, validation, and behavior-driven design.

---

Keep learning by implementing each concept in code, not just reading theory.
