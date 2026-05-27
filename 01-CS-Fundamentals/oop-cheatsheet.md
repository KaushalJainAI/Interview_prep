# OOP Principles -- Interview Cheatsheet

## The four pillars

### 1. Encapsulation
Bundle data + methods; hide internals. Python convention: `_private`, `__name_mangled`.
```python
class Account:
    def __init__(self, bal): self._balance = bal
    def deposit(self, x): self._balance += x
    @property
    def balance(self): return self._balance   # read-only access
```

### 2. Inheritance
Child class reuses parent's behavior.
```python
class Animal:
    def speak(self): raise NotImplementedError

class Dog(Animal):
    def speak(self): return "woof"
```

### 3. Polymorphism
Same interface, different behavior.
```python
for a in [Dog(), Cat(), Cow()]:
    a.speak()   # each does its own thing
```
- **Duck typing** (Python): "if it walks like a duck..." -- interface inferred, not declared

### 4. Abstraction
Expose what something *does*, hide *how*.
```python
from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def save(self, key, val): ...
    @abstractmethod
    def load(self, key): ...

class RedisStorage(Storage): ...
class S3Storage(Storage): ...
```

## SOLID (memorize names)

| Letter | Principle | Plain English |
|--------|-----------|---------------|
| **S** | Single Responsibility | One class = one reason to change |
| **O** | Open / Closed | Open for extension, closed for modification |
| **L** | Liskov Substitution | Subtypes must work wherever base type works |
| **I** | Interface Segregation | Many small interfaces > one fat one |
| **D** | Dependency Inversion | Depend on abstractions, not concretions |

## Composition vs Inheritance
**Favor composition.**
- Inheritance creates tight coupling and fragile hierarchies
- Composition: hold instances of collaborators, delegate work
```python
# Inheritance (fragile)
class Logger(File): ...

# Composition (better)
class Logger:
    def __init__(self, sink): self.sink = sink
    def log(self, msg): self.sink.write(msg)
```

## Python-specific OOP

### MRO (Method Resolution Order) -- multiple inheritance
```python
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass

D.__mro__   # (D, B, C, A, object)  -- C3 linearization
```
- `super().__init__()` follows MRO, not just parent
- Diamond inheritance: each method called once (no duplicate calls)

### Mixins
Tiny classes providing a single capability, combined via multiple inheritance.
```python
class TimestampMixin:
    created_at = datetime.now()

class JSONSerializableMixin:
    def to_json(self): return json.dumps(self.__dict__)

class User(TimestampMixin, JSONSerializableMixin, Base): ...
```

### Class vs static vs instance methods
```python
class C:
    def instance_m(self): ...        # uses self
    @classmethod
    def class_m(cls): ...            # uses cls; alt constructors
    @staticmethod
    def static_m(): ...              # no self/cls; utility
```

### Properties + setters
```python
class Temp:
    def __init__(self, c): self._c = c
    @property
    def f(self): return self._c * 9/5 + 32
    @f.setter
    def f(self, v): self._c = (v - 32) * 5/9
```

## Design patterns to know names of

| Pattern | When |
|---------|------|
| **Singleton** | One instance only (config, logger) |
| **Factory** | Centralize object creation |
| **Strategy** | Swap algorithms at runtime |
| **Observer** | Pub/sub (Django signals) |
| **Decorator** | Wrap an object to add behavior |
| **Adapter** | Convert one interface to another |
| **Repository** | Abstract data access |
| **Command** | Encapsulate a request as object (undo/redo) |
| **Builder** | Step-by-step construction of complex objects |

## Interview one-liners
- *Composition vs inheritance?* Prefer composition -- looser coupling, swappable parts. Use inheritance only for true is-a relationships.
- *Why ABCs?* Force concrete subclasses to implement methods; documents intent; works with `isinstance`.
- *Liskov?* Subclass must honor base class's contract. Famous violation: `Square` extending `Rectangle` and breaking width/height invariants.
- *Diamond inheritance in Python?* Resolved by C3 linearization (MRO) -- `super()` walks it correctly.
- *Open-closed principle?* Add a new class to extend; don't modify existing class. Strategy pattern is the canonical example.
- *Mixins vs multiple inheritance?* Mixins are intentionally small (one capability), don't have state of their own, designed to combine.

## Project anchor
> "In AIAAS, every node-handler implements a `NodeHandler` ABC with `validate()` and `execute()`. New node types are just new classes (open-closed). The executor depends only on the ABC, not concrete handlers (dependency inversion). MCP tool nodes vs LLM nodes vs code-exec nodes share zero implementation -- they just satisfy the same interface."
