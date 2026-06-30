# Python Nuances -- Interview Cheatsheet

## The GIL
- **Global Interpreter Lock**: one Python bytecode at a time per process
- **CPU-bound code** doesn't benefit from threads -- use **multiprocessing** or native extensions
- **I/O-bound code** does -- threads release GIL during I/O (sockets, files, subprocess)
- **asyncio** is single-threaded cooperative concurrency -- best for many concurrent I/O ops
- Python 3.13+ has experimental free-threaded (no-GIL) mode

## Mutable default argument trap
```python
def append_to(x, lst=[]):   #  lst created ONCE at function definition
    lst.append(x)
    return lst

append_to(1)  # [1]
append_to(2)  # [1, 2]   surprise!

def append_to(x, lst=None): #  correct pattern
    if lst is None: lst = []
    lst.append(x)
    return lst
```

## `is` vs `==`
- `==` calls `__eq__` (value equality)
- `is` checks identity (same object in memory)
- `a = 256; b = 256; a is b` -> True (small int cache)
- `a = 257; b = 257; a is b` -> False (no cache)
- Always use `is None`, never `== None`

## Decorators
```python
def log(fn):
    def wrapper(*args, **kw):
        print(f"calling {fn.__name__}")
        return fn(*args, **kw)
    return wrapper

@log
def add(a, b): return a + b
```
- Decorator = function that takes a function and returns a function
- `functools.wraps` preserves `__name__`, `__doc__`, signature

## Generators & yield
```python
def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
```
- **Lazy** -- values computed on demand
- Memory-efficient for big sequences
- Generator expressions: `(x*x for x in range(N))`
- `yield from gen2` delegates to another generator

## Context managers
```python
with open("f") as f: ...   # __enter__/__exit__ called automatically

# Custom:
from contextlib import contextmanager

@contextmanager
def timer():
    t = time.time()
    yield
    print(time.time() - t)
```

## Args / kwargs
```python
def f(a, b, *args, c=10, **kwargs): ...
# Calling: f(1, 2, 3, 4, c=5, x=1, y=2)
# a=1, b=2, args=(3,4), c=5, kwargs={'x':1,'y':2}
```

## Dunder (magic) methods
| Method | Triggered by |
|--------|-------------|
| `__init__` | `MyClass()` |
| `__repr__` / `__str__` | `repr(o)` / `str(o)` |
| `__eq__` / `__hash__` | `==`, `hash()` (define both for sets/dicts) |
| `__lt__` etc. | `<`, sorting (use `functools.total_ordering`) |
| `__call__` | `o()` |
| `__enter__` / `__exit__` | `with` |
| `__iter__` / `__next__` | `for x in o` |
| `__getitem__` | `o[k]` |
| `__contains__` | `x in o` |
| `__len__` | `len(o)` |

## Dataclasses
```python
from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float
    label: str = "default"
    tags: list = field(default_factory=list)   # <- mutable default
```
Auto-generated `__init__`, `__repr__`, `__eq__`. `frozen=True` makes it immutable.

## Type hints
```python
from typing import Optional, Union
def fetch(id: int, retries: int = 3) -> Optional[dict]: ...

# Python 3.10+:
def fetch(id: int) -> dict | None: ...
```
Tools: `mypy`, `pyright`. Use Pydantic for runtime validation (covered in agents notes).

## List comprehension & efficiency
- `[x*2 for x in xs if x > 0]` -- readable + fast
- Generator `(...)` for memory; list `[...]` for indexing
- Dict comp: `{k: v for k, v in items}`
- Set comp: `{x for x in xs}`

## asyncio essentials
```python
import asyncio

async def fetch(url):
    async with httpx.AsyncClient() as c:
        return (await c.get(url)).json()

async def main():
    results = await asyncio.gather(*[fetch(u) for u in urls])

asyncio.run(main())
```
- `async def` declares a coroutine
- `await` yields control while waiting
- `gather` runs concurrently
- **Never** call blocking sync code from async -- wraps with `loop.run_in_executor`

## Common gotchas to mention
- **Late binding closures**: `[lambda: i for i in range(3)]` all return 2. Fix: `lambda i=i: i`
- **Modifying list while iterating**: skip indices. Build new list instead.
- **Dict ordered** since 3.7 (CPython 3.6) -- `OrderedDict` rarely needed
- **`==` for floats**: use `math.isclose` (floating-point precision)
- **Shallow vs deep copy**: `copy.copy` vs `copy.deepcopy`
- **`__init__` vs `__new__`**: `__new__` creates the instance, `__init__` initializes it. Override `__new__` for singletons / immutable inheritance.

## Bit tricks & shift-operator gotchas
Two bugs that bite in bit-manipulation problems (e.g. "concatenate the binary of `i`"):

**1. `len(bin(i))` is *not* the bit length.** `bin()` always prepends a `'0b'` prefix (2 chars), then the binary digits.

| `i` | `bin(i)` | `len(bin(i))` | true bit length |
|-----|----------|---------------|-----------------|
| 2 | `'0b10'` | 4 | 2 |
| 3 | `'0b11'` | 4 | 2 |
| 5 | `'0b101'` | 5 | 3 |

- True bit count = `len(bin(i)) - 2`, which is exactly `i.bit_length()`.
- Subtracting `1` instead of `2` gives a value **one too large** -- classic off-by-one. Just use `i.bit_length()`.

**2. `+`/`-` bind tighter than `<<`/`>>`.** Precedence, high -> low:
```
*  /  //  %
+  -            (binary)
<<  >>
&
^
|
```
So `ans + ans << bit_length` parses as `(ans + ans) << bit_length` == `(2 * ans) << bit_length`, **not** `ans + (ans << bit_length)`. Always parenthesize shifts mixed with arithmetic.

**3. The deeper question.** Even correctly parenthesized, `ans + (ans << bit)` doubles `ans` -- it doesn't append anything new. To *concatenate the binary of `i`* onto the running result you shift `ans` left by `i`'s bit-width to make room, then OR/add the value `i` itself:
```python
ans = (ans << i.bit_length()) | i      # append binary of i
```
Appending `ans` to itself answers the wrong question -- the value being concatenated must be `i`, not `ans`.

## Interview one-liners
- *What's the GIL?* Lock that serializes Python bytecode in CPython -> no true parallelism in pure-Python threads. Multiprocessing or async work around it.
- *List vs tuple?* List = mutable, tuple = immutable + hashable (usable as dict keys / set elements).
- *Why mutable default args dangerous?* Default is evaluated once at function-def time and reused -> spooky action between calls.
- *Generator vs list?* Generator is lazy, O(1) memory; list materializes everything.
- *Decorator?* HOF that wraps another function -- used for logging, caching, auth, retries.
- *`is` vs `==`?* `is` = identity (same object); `==` = value equality (`__eq__`). Always `is None`.
- *Why `__slots__`?* Avoids creating `__dict__` per instance -> less memory, faster attribute access. Pay: no dynamic attrs.

## Project anchor
> "In AIAAS, node handlers are classes with `__call__` so the executor can treat them uniformly. State updates go through Pydantic models for validation. We use asyncio throughout the executor -- most node operations are I/O-bound (LLM calls, MCP RPC, DB), so async gives us 100s of concurrent workflows on one process without the GIL biting."
