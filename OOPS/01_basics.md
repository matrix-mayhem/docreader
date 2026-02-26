# 01 - OOP Basics

## 1) What is OOP?

Object-Oriented Programming is a style where software is modeled as **objects** that combine:

- **State** (data/attributes)
- **Behavior** (methods/functions)

### Why OOP?

- Better organization for complex systems
- Easier reuse via classes and composition
- Improved maintainability and testing

## 2) Key Terms

- **Class**: Blueprint for objects
- **Object**: Instance of a class
- **Attribute**: Data stored in object
- **Method**: Function defined inside class
- **Constructor**: Initialization method (`__init__` in Python)

## 3) Class vs Object

```python
class Car:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

    def start(self):
        return f"{self.brand} {self.model} is starting"

car1 = Car("Toyota", "Corolla")
print(car1.start())
```

## 4) Instance vs Class Attributes

```python
class Student:
    school = "Central High"  # class attribute

    def __init__(self, name):
        self.name = name  # instance attribute
```

## 5) Practice

- Create a `Book` class with title, author, and year
- Add a method to return formatted details
- Instantiate 3 books and print summaries
