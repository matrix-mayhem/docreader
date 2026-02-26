# 03 - Design Principles (SOLID)

## S - Single Responsibility Principle
A class should have one reason to change.

## O - Open/Closed Principle
Software entities should be open for extension, closed for modification.

## L - Liskov Substitution Principle
Derived classes should be substitutable for base classes.

## I - Interface Segregation Principle
Clients should not depend on methods they do not use.

## D - Dependency Inversion Principle
Depend on abstractions, not concretions.

## Example: Dependency Injection

```python
class EmailService:
    def send(self, message: str) -> None:
        print("Sending email:", message)

class NotificationManager:
    def __init__(self, service):
        self.service = service

    def notify(self, message: str):
        self.service.send(message)
```

`NotificationManager` can work with any service implementing `send`.
