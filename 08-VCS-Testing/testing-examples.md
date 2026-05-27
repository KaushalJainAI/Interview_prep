# Testing -- Worked Examples

> Companion to [git-testing-cheatsheet.md](git-testing-cheatsheet.md). Production-shape pytest / Django / Playwright code.

## 1. pytest fixtures -- composing test setup

```python
# conftest.py -- fixtures auto-discovered for the whole test tree
import pytest
from django.contrib.auth import get_user_model

@pytest.fixture
def user(db):                                # db fixture wraps test in transaction
    return get_user_model().objects.create_user(
        email="t@t.com", password="pw", is_active=True
    )

@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        email="staff@t.com", password="pw", is_staff=True
    )

@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client

@pytest.fixture
def product(db):
    from catalog.models import Category, Product
    cat = Category.objects.create(name="Spices", slug="spices")
    return Product.objects.create(
        name="Turmeric", slug="turmeric", category=cat, price=99, stock=100
    )
```

**Fixture scopes**:
- `function` (default) -- runs once per test
- `class` -- once per test class
- `module` -- once per file
- `session` -- once for the whole pytest run

```python
@pytest.fixture(scope="session")
def slow_resource():
    # e.g. a Docker container started by testcontainers
    resource = start_resource()
    yield resource
    resource.stop()
```

## 2. Parametrized tests -- table-driven testing

```python
@pytest.mark.parametrize("a,b,want", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0),
    (-5, -5, -10),
])
def test_add(a, b, want):
    assert add(a, b) == want
```
**Why**: one function, many cases, named in output (`test_add[1-2-3]`).

### Parametrize a fixture
```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def backend(request):
    return request.param

def test_backend_works(backend):
    # runs 3 times with backend = each value
    assert query_backend(backend) is not None
```

## 3. Mocking external calls

```python
from unittest.mock import patch, MagicMock

def test_llm_extraction(monkeypatch):
    # Patch the Anthropic SDK so no real API call
    fake = MagicMock()
    fake.messages.create.return_value.content = [
        MagicMock(type="tool_use", input={"items":["haldi"], "total":100})
    ]
    with patch("agents.client", fake):
        result = run_extraction("Customer ordered 1 haldi for ₹100")
    assert result.items == ["haldi"]
    fake.messages.create.assert_called_once()
```

### When to use monkeypatch vs patch decorator
- `monkeypatch` -- function-scoped, automatic teardown, simple attribute swaps
- `@patch("module.path")` -- decorator/contextmgr, more explicit, often nicer for class-method patches
- **Patch where it's USED, not where it's defined**: `patch("agents.client")` not `patch("anthropic.Client")`

## 4. Testing Django views -- REST API

```python
from rest_framework.test import APIClient
from rest_framework import status

class TestProductAPI:
    def test_list_anonymous(self, client, product):
        r = client.get("/api/products/")
        assert r.status_code == status.HTTP_200_OK
        assert r.json()["results"][0]["slug"] == "turmeric"

    def test_create_requires_auth(self, client):
        r = client.post("/api/products/", {"name":"x"})
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_as_staff(self, auth_client, staff_user, db):
        auth_client.force_login(staff_user)
        r = auth_client.post("/api/products/",
            {"name":"Cumin", "slug":"cumin", "price":50, "category":1, "stock":10},
            content_type="application/json")
        assert r.status_code == status.HTTP_201_CREATED

    def test_user_cannot_create(self, auth_client):
        r = auth_client.post("/api/products/", {"name":"x"})
        assert r.status_code == status.HTTP_403_FORBIDDEN
```

## 5. Testing with database -- TransactionTestCase pitfalls

```python
@pytest.mark.django_db                              # short for db fixture
def test_signal_invalidates_cache(product):
    from django.core.cache import cache
    cache.set(f"product:{product.slug}", {"name": product.name})

    product.name = "Updated"
    product.save()                                   # fires signal

    assert cache.get(f"product:{product.slug}") is None
```

**Gotcha**: `@pytest.mark.django_db(transaction=True)` runs each test in real txn + rollback (slower). Needed if you test `on_commit` callbacks or db locks.

## 6. Testing async code

```python
import pytest

@pytest.mark.asyncio
async def test_async_view():
    from httpx import AsyncClient
    async with AsyncClient(base_url="http://test") as client:
        r = await client.get("/api/async/")
        assert r.status_code == 200
```

Pytest needs `pytest-asyncio` plugin. Mark tests or set `asyncio_mode = "auto"` in `pyproject.toml`.

## 7. Hypothesis -- property-based testing

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)

@given(st.lists(st.integers(), min_size=1))
def test_max_is_in_list(xs):
    m = max(xs)
    assert m in xs
    assert all(x <= m for x in xs)
```
**Hypothesis generates random inputs satisfying constraints** -- finds edge cases that hand-written tests miss (empty, single element, very large, negative).

## 8. Coverage -- what really matters

```bash
pytest --cov=ngu --cov-report=term --cov-report=html
open htmlcov/index.html
```

**Don't chase 100%**. Aim for ~80% on business logic, less on glue code. Coverage tells you *what's executed*, not *what's correctly tested*.

```toml
# pyproject.toml -- exclude lines that are hard to test
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

## 9. Playwright E2E test -- your NGU example

```python
# tests/e2e/test_checkout.py
from playwright.sync_api import sync_playwright, expect

def test_full_checkout_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Open storefront
        page.goto("https://nidhimasala.kaushaljain.com/")

        # 2. Search for "haldi"
        page.fill('input[placeholder="Search"]', "haldi")
        page.press('input[placeholder="Search"]', "Enter")
        page.wait_for_selector("text=Turmeric")

        # 3. Add to cart
        page.click('text=Add to cart')
        expect(page.locator('[data-testid="cart-count"]')).to_have_text("1")

        # 4. Go to checkout
        page.click('[aria-label="Cart"]')
        page.click('text=Checkout')

        # 5. Fill address
        page.fill('input[name="name"]', "Test User")
        page.fill('input[name="email"]', "t@t.com")
        page.fill('input[name="address"]', "PEC, Chandigarh")
        page.fill('input[name="zip"]', "160012")

        # 6. Submit
        page.click('button:has-text("Place Order")')
        expect(page.locator('h1')).to_contain_text("Thank you")

        browser.close()
```

**Why Playwright > Selenium**: auto-wait removes flaky `sleep()`s. The `expect(...).to_have_text` polls automatically until it succeeds or times out.

### Playwright fixture for reuse
```python
@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()

def test_homepage_loads(page):
    page.goto("https://nidhimasala.kaushaljain.com/")
    expect(page).to_have_title("NGU Spices")
```

## 10. Postman / Newman in CI

```json
// postman_collection.json (excerpt)
{
  "info": {"name": "NGU API"},
  "item": [
    {
      "name": "Login + Get me",
      "event": [{
        "listen": "test",
        "script": {"exec": [
          "pm.test('login returns access token', () => {",
          "  pm.expect(pm.response.json()).to.have.property('access');",
          "  pm.environment.set('access_token', pm.response.json().access);",
          "});"
        ]}
      }],
      "request": {
        "method": "POST",
        "url": {"raw": "{{baseUrl}}/api/auth/login/"},
        "body": {"mode":"raw", "raw":"{\"email\":\"t@t.com\",\"password\":\"pw\"}"}
      }
    }
  ]
}
```

CI step:
```bash
npx newman run postman_collection.json -e staging.env.json --reporters cli,junit
```

## Interview-quick answers
- *Unit vs integration vs E2E?* Unit isolates a function (mocks deps). Integration tests multiple components together (real DB). E2E exercises the whole system through the UI.
- *Mock vs stub vs spy?* Mock = also verifies how it was called. Stub = canned return values. Spy = real object recording calls.
- *Why TestCase rolls back automatically?* Each test wraps in a txn, rolled back at teardown -> fast + isolated.
- *Why Playwright over Selenium?* Auto-wait kills flakiness. Better debug tools (trace viewer, video). Native parallel. Cleaner API.
- *Coverage = quality?* No. 100% can still be buggy with weak assertions. Coverage is a floor.
- *Flaky test?* Inconsistent pass/fail. Causes: timing, ordering, network, shared state. Quarantine -> root-cause.
- *Property-based vs example-based testing?* Property-based generates inputs satisfying invariants -- finds edge cases humans miss.
- *Snapshot test?* Compares output to stored reference. Useful for serialized JSON / rendered HTML, dangerous if devs blindly update snapshots.

## AIAAS interview anchor (testing)
> "AIAAS tests are layered: **unit tests** for the compiler -- graph validation, expression resolution, schema checks -- fully isolated. **Integration tests** for the executor with real Redis/Postgres but a mocked MCP server using `pytest-httpserver`. **E2E tests** with Playwright: drag a node, save, run, watch live status flow through WebSocket. LLM/MCP calls in CI are recorded via `vcrpy` so we test deterministic behavior; a separate nightly suite hits real providers to catch upstream regressions."
