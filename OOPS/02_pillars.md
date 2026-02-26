# 02 - Four Pillars of OOP

## 1) Encapsulation

Encapsulation means bundling data + methods and restricting direct access to internal state.

```python
class Temperature:
    def __init__(self, celsius: float):
        self.__celsius = celsius

    def set_celsius(self, value: float):
        if value < -273.15:
            raise ValueError("Below absolute zero")
        self.__celsius = value

    def get_celsius(self) -> float:
        return self.__celsius
```

## 2) Abstraction

Expose only necessary details, hide implementation complexity.

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass
```

## 3) Inheritance

A class can derive from another class and reuse/extend behavior.

```python
class Animal:
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "Woof"
```

## 4) Polymorphism

Different objects respond to the same method call in their own way.

```python
def make_sound(animal):
    print(animal.speak())
```

## 5) Important Note

Prefer **composition over inheritance** when inheritance relationships become fragile or unnatural.
