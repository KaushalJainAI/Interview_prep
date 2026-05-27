# Pydantic -- Worked-Example Cheatsheet

> Why dedicated: Pydantic is the runtime-validation backbone of every modern Python AI/web stack -- DRF serializers' younger cousin, FastAPI's foundation, LangChain/LangGraph state schemas, OpenAI/Anthropic structured outputs, MCP tool schemas. **You'll touch it in every AIAAS interview question.**

## What it is (one-liner)
Pydantic = **dataclass + runtime type validation + JSON Schema generation** in one. You declare types; Pydantic enforces them when objects are created, with auto-coercion and rich errors.

## Pydantic v1 vs v2 (you'll be asked)
| | v1 | v2 |
|--|----|----|
| Released | 2017 | 2023 |
| Backend | Pure Python | **Rust core (pydantic-core)** -- 5-50x faster |
| Method names | `.dict()`, `.json()`, `.parse_obj()` | `.model_dump()`, `.model_dump_json()`, `.model_validate()` |
| Validators | `@validator` | `@field_validator`, `@model_validator` |
| Strict mode | Loose by default | Configurable strict mode |
| Schema | `.schema()` | `.model_json_schema()` |

**LangChain/LangGraph, FastAPI, OpenAI SDK, Anthropic SDK** -- all migrated to v2. Use v2 syntax in interviews.

## Example 1 -- basic model
```python
from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int = Field(ge=0, le=150)              # ge / le constraints
    is_active: bool = True                       # default
    tags: list[str] = []
    created: datetime = Field(default_factory=datetime.utcnow)

u = User(id="42", name="Kaushal", email="k@p.com", age="25")
# ^ str                              ^ str
# Pydantic auto-coerces "42" -> 42, "25" -> 25 (default loose mode)
print(u.id, type(u.id))     # 42 <class 'int'>
```

### Validation errors
```python
try:
    User(id="abc", name="x", email="x", age=-1)
except ValidationError as e:
    print(e.json())
# [
# {"loc":["id"], "msg":"Input should be a valid integer", ...},
# {"loc":["age"],"msg":"Input should be greater than or equal to 0", ...}
# ]
```
Pydantic collects **all** errors, not just the first -- great for API responses.

## Example 2 -- nested models
```python
class Address(BaseModel):
    street: str
    city: str
    zip: str = Field(pattern=r"^\d{6}$")          # Indian PIN code

class User(BaseModel):
    name: str
    addresses: list[Address]

u = User(name="K", addresses=[
    {"street":"PEC", "city":"Chandigarh", "zip":"160012"},
    {"street":"Sector 22", "city":"Chandigarh", "zip":"160022"},
])
```
Nested validation is automatic -- `addresses[0]` is parsed into an `Address`.

## Example 3 -- field validator
```python
from pydantic import field_validator

class Product(BaseModel):
    sku: str
    price: float

    @field_validator("sku")
    @classmethod
    def upper_sku(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("SKU too short")
        return v.upper()

    @field_validator("price")
    @classmethod
    def positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be non-negative")
        return v

p = Product(sku="haldi-100g", price=100.0)
print(p.sku)   # HALDI-100G
```

## Example 4 -- model-level validator
Cross-field validation runs *after* all fields are validated.
```python
from pydantic import model_validator

class Range(BaseModel):
    low: int
    high: int

    @model_validator(mode="after")
    def low_lt_high(self):
        if self.low >= self.high:
            raise ValueError("low must be < high")
        return self
```

## Example 5 -- JSON Schema for LLM tool calling
This is the **agent/MCP integration** point -- Pydantic produces the schema you pass to LLM APIs.
```python
class SearchTool(BaseModel):
    """Search internal documentation."""
    query: str = Field(..., description="What to search for")
    top_k: int = Field(5, ge=1, le=20, description="How many results")

schema = SearchTool.model_json_schema()
# {
# "type": "object",
# "properties": {
# "query": {"type":"string", "description":"What to search for"},
# "top_k": {"type":"integer", "minimum":1, "maximum":20, "default":5, ...}
# },
# "required": ["query"],
# "title": "SearchTool",
# "description": "Search internal documentation."
# }
```

Pass this directly to Anthropic / OpenAI tool-calling:
```python
tools = [{"name":"search_docs", "input_schema": SearchTool.model_json_schema(), ...}]
```

## Example 6 -- parsing LLM structured output
**Anthropic & OpenAI** support "JSON mode" + tool calls that return structured args. Parse safely:
```python
class OrderSummary(BaseModel):
    items: list[str]
    total: float
    currency: str = "INR"

raw = llm.invoke("Extract order: 2 turmeric, 1 garam masala, total ₹450")
# raw.content is JSON: {"items": ["turmeric", "turmeric", "garam masala"], "total": 450}

parsed = OrderSummary.model_validate_json(raw.content)
# OR if raw is already a dict:
parsed = OrderSummary.model_validate(raw)
```
If the model returns malformed JSON, you get a clean ValidationError to log and retry.

## Example 7 -- discriminated union (polymorphism)
Agent tool outputs are heterogeneous. Tag them and Pydantic dispatches.
```python
from typing import Annotated, Literal, Union
from pydantic import Discriminator, Tag

class TextResult(BaseModel):
    kind: Literal["text"]
    text: str

class ImageResult(BaseModel):
    kind: Literal["image"]
    url: str
    width: int

ToolResult = Annotated[
    Union[TextResult, ImageResult],
    Discriminator("kind"),
]

class Step(BaseModel):
    result: ToolResult

Step.model_validate({"result": {"kind": "image", "url": "x", "width": 10}})
# -> Step(result=ImageResult(...))
```
This is the **AIAAS node-result type system** in miniature.

## Example 8 -- settings from env vars (pydantic-settings)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AIAAS_")

    db_url: str
    openai_api_key: str
    redis_url: str = "redis://localhost:6379"
    max_workers: int = 8

settings = Settings()                  # reads from .env + os.environ
```
Replaces `os.getenv` boilerplate; gives you typed config with validation.

## Example 9 -- Pydantic + Django (alongside DRF serializers)
DRF serializers and Pydantic both validate. Use DRF for HTTP boundary, Pydantic for **internal type-safe interfaces** between services / for LLM I/O.

```python
# Django view receives JSON via DRF serializer (HTTP edge)
# Then converts to typed Pydantic model for the executor:
from drf_serializers import WorkflowRequestSerializer

class WorkflowInput(BaseModel):
    workflow_id: str
    inputs: dict[str, str]

def run_view(request):
    ser = WorkflowRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    typed = WorkflowInput.model_validate(ser.validated_data)
    return enqueue_workflow(typed)
```

## Example 10 -- partial updates with model_copy
```python
class Profile(BaseModel):
    name: str
    bio: str
    avatar_url: str | None = None

p = Profile(name="K", bio="...", avatar_url=None)
updated = p.model_copy(update={"bio": "new bio"})
```

## Common pitfalls
- **Forgetting `@classmethod`** on field_validator -> silent breakage in v2.
- **Strict vs loose**: `model_validate(d, strict=True)` to disable `"42"`->`42` coercion when you need precision.
- **Mutating model after construction**: by default models are *not* frozen; set `model_config = ConfigDict(frozen=True)` to make them immutable + hashable.
- **`Optional[T]` vs `T | None` vs `T = None`**: `Optional[T]` means `T | None`. A *default* of `None` makes the field optional **at construction**. They are independent.
- **Forward references**: `model_rebuild()` after self-referential types.
- **Performance**: v1 was slow; v2 is fast. If you're on v1, plan migration.
- **`Field(...)`** (Ellipsis) = required; `Field(default)` = optional with default.

## Interview one-liners
- *Why Pydantic over `@dataclass`?* Dataclasses don't validate at runtime; Pydantic does, and emits JSON Schema for free.
- *Why v2 is faster?* Validation core rewritten in Rust (pydantic-core); ~5-50x faster than v1.
- *Pydantic vs DRF serializers?* DRF for HTTP request/response with Django ORM integration; Pydantic for general-purpose typed data anywhere (internal services, LLM I/O, settings, schemas).
- *Field vs field_validator vs model_validator?* `Field` declares constraints (min, max, regex). `field_validator` runs custom logic on one field. `model_validator` runs after all fields validated -- for cross-field checks.
- *How does it interact with LLM function calling?* `model_json_schema()` produces the schema you pass to the model. Model returns args as JSON; you `model_validate_json(args)` to get a typed object.
- *What's a discriminated union?* Union of types with a "kind"-like tag field; Pydantic dispatches to the right model based on the tag. Used for heterogeneous tool results.

## AIAAS interview anchor
> "In AIAAS, every node has a Pydantic input schema and output schema. The compiler uses `model_json_schema()` to emit schemas for the visual editor (so users see the right form fields) and to validate edges between nodes -- `node_A.output_schema` must satisfy `node_B.input_schema`. The executor wraps every LLM tool-call response in `model_validate_json` so a malformed structured output becomes a typed validation error we can retry on. We also use pydantic-settings to load multi-provider LLM credentials from a single config object -- no scattered `os.getenv`."


---

## Deep dive -- why structured outputs

LLMs return strings; we want **typed objects** to chain them into reliable software. Pydantic gives:
- Schema-as-Python-class (readable, IDE-friendly).
- Validation with clear error messages.
- JSON Schema export -> goes straight to function-calling tools.
- Coercion (`"3" -> 3`) where safe; refusal where not.

Pair with **Instructor** / **outlines** / **JSON-mode** to constrain the LLM's output to the schema.

## Patterns

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Citation(BaseModel):
    url: str
    quote: str = Field(..., min_length=10)

class Answer(BaseModel):
    text: str
    confidence: Literal["low","medium","high"]
    citations: list[Citation]

    @field_validator("citations")
    @classmethod
    def at_least_one(cls, v):
        if not v: raise ValueError("need at least one citation")
        return v
```

Schema-driven prompting:
```
schema = Answer.model_json_schema()
prompt = f"Reply with JSON matching this schema:\n{json.dumps(schema)}"
raw = llm(prompt)
answer = Answer.model_validate_json(raw)   # raises on bad output
```

##  Pitfalls

| Pitfall | Fix |
|---------|-----|
| Free-form prompts then hope for JSON | Force JSON mode + schema |
| Allowing too many optional fields | Model fills them sloppily; constrain |
| Long descriptions on every field | Tokens cost money; keep descriptions short |
| No retry on validation failure | Pass error back to LLM with original output |
| Pydantic v1 vs v2 confusion | `model_validate` is v2; `parse_obj` is v1 |

## Interview questions

1. **Why Pydantic over `json.loads`?** Validation + types + helpful error messages.
2. **What if the LLM refuses to obey the schema?** Use JSON mode (OpenAI), tool-calling, or grammar-constrained decoding (outlines / vllm guided).
3. **How to handle partial / streaming structured output?** Use `instructor` partial parsing; emit fields as they arrive.
4. **Pydantic vs dataclasses?** Pydantic adds validation + JSON Schema + serialisation; dataclasses are zero-runtime.
5. **Forward references in models?** `from __future__ import annotations` + `model_rebuild()`.

## References
- Pydantic v2 docs
- `instructor` library -- JSON-mode + retries
- "Constrained Decoding" -- outlines library
