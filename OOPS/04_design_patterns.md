# 04 - Useful OOP Design Patterns

## Creational

- **Singleton**: one instance for shared resource
- **Factory Method**: object creation via a method
- **Builder**: step-wise object construction

## Structural

- **Adapter**: bridge incompatible interfaces
- **Decorator**: add behavior dynamically
- **Facade**: simplified high-level interface

## Behavioral

- **Strategy**: interchangeable algorithms
- **Observer**: publish/subscribe updates
- **Command**: encapsulate actions as objects

## Strategy Example

```python
class PaymentStrategy:
    def pay(self, amount: float):
        raise NotImplementedError

class CardPayment(PaymentStrategy):
    def pay(self, amount: float):
        print(f"Paid {amount} via card")

class UPIPayment(PaymentStrategy):
    def pay(self, amount: float):
        print(f"Paid {amount} via UPI")

class Checkout:
    def __init__(self, strategy: PaymentStrategy):
        self.strategy = strategy

    def process(self, amount: float):
        self.strategy.pay(amount)
```
