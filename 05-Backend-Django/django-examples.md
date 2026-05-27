# Django -- Worked Examples

> Companion to [django-full-cheatsheet.md](django-full-cheatsheet.md). Real code patterns from NGU + AIAAS.

## 1. Full DRF endpoint -- products list with pagination, filter, cache

```python
# models.py
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "active"]),
            models.Index(fields=["-created"]),
        ]

# serializers.py
class ProductSerializer(serializers.ModelSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id","slug","name","price","stock","in_stock",
                  "category_slug","created"]

    def get_in_stock(self, obj): return obj.stock > 0

# views.py
from django.core.cache import cache
from rest_framework import viewsets, filters
from rest_framework.pagination import CursorPagination

class ProductCursorPagination(CursorPagination):
    page_size = 24
    ordering = "-created"

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = ProductCursorPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "slug"]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Product.objects.filter(active=True).select_related("category")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def list(self, request, *args, **kwargs):
        # cache the listing for anonymous users (cheap win)
        if request.user.is_anonymous:
            cache_key = f"products:list:v3:{request.GET.urlencode()}"
            cached = cache.get(cache_key)
            if cached: return Response(cached)
            response = super().list(request, *args, **kwargs)
            cache.set(cache_key, response.data, timeout=300)
            return response
        return super().list(request, *args, **kwargs)

# signals.py -- invalidate cache on writes
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=Product)
def bump_products_cache(sender, instance, **kwargs):
    cache.delete_pattern("products:list:v3:*")
    cache.delete(f"product:detail:{instance.slug}")
```

**Key things to talk about in interviews:**
- `select_related("category")` -> JOIN, no N+1
- **Namespaced cache key** with version `v3` -> bump version = mass invalidation
- **Cursor pagination** -> safe on big tables (no OFFSET cliff)
- **Anonymous-only caching** -> user-specific data never leaks via cache
- **Signal-based invalidation** -> write triggers cache delete

## 2. Custom permission

```python
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = OrderSerializer

    def get_queryset(self):
        # Users see only their orders; staff see all
        qs = Order.objects.select_related("user")
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs
```

## 3. JWT auth flow (SimpleJWT)

```python
# settings.py
INSTALLED_APPS += ["rest_framework_simplejwt", "rest_framework_simplejwt.token_blacklist"]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

urlpatterns += [
    path("api/auth/login/",   TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/logout/",  TokenBlacklistView.as_view()),
]

# Custom claims:
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtain(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["is_staff"] = user.is_staff
        return token
```

## 4. Custom middleware -- per-request timing + correlation ID

```python
import time, uuid, logging

logger = logging.getLogger("requests")

class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.META.get("HTTP_X_REQUEST_ID") or uuid.uuid4().hex
        t0 = time.time()
        response = self.get_response(request)
        duration_ms = int((time.time() - t0) * 1000)

        response["X-Request-Id"] = request.request_id
        response["X-Took-Ms"] = duration_ms

        logger.info("", extra={
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "user_id": getattr(request.user, "id", None),
        })
        return response
```

Hook up in `settings.MIDDLEWARE` near the top.

## 5. Async view + sync ORM (the right pattern)

```python
from asgiref.sync import sync_to_async
from django.http import JsonResponse
import httpx

async def llm_search(request):
    query = request.GET.get("q","")
    # parallel: hit DB and LLM API concurrently
    async with httpx.AsyncClient() as client:
        db_task   = sync_to_async(list)(Product.objects.filter(name__icontains=query)[:5])
        llm_task  = client.post("https://api.anthropic.com/...", json={...})
        products, llm_resp = await asyncio.gather(db_task, llm_task)

    return JsonResponse({"products": [p.name for p in products],
                          "ai_suggestion": llm_resp.json()["completion"]})
```

`sync_to_async(list)(qs)` is the bridge -- async views require `await` for any sync work.

## 6. Django Channels WebSocket consumer (AIAAS pattern)

```python
# consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class WorkflowConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.run_id = self.scope["url_route"]["kwargs"]["run_id"]
        # auth
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close(); return
        # validate ownership
        run = await sync_to_async(WorkflowRun.objects.get)(id=self.run_id)
        if run.user_id != user.id:
            await self.close(); return

        # join the group for this run
        await self.channel_layer.group_add(f"run-{self.run_id}", self.channel_name)
        await self.accept()
        await self.send_json({"type":"connected"})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"run-{self.run_id}", self.channel_name)

    async def workflow_event(self, event):
        # called when executor sends to group
        await self.send_json(event["payload"])

# routing.py
websocket_urlpatterns = [
    re_path(r"ws/runs/(?P<run_id>\w+)/$", WorkflowConsumer.as_asgi()),
]

# from executor:
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def emit(run_id, payload):
    async_to_sync(get_channel_layer().group_send)(
        f"run-{run_id}",
        {"type": "workflow.event", "payload": payload},
    )
```

The executor doesn't need its own WebSocket connection -- it just publishes to the channel group via Redis, and any connected consumer receives it.

## 7. Rate limiting -- DRF + Redis (production-grade)

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "1000/hour",
        "login": "5/min",
    },
}

# views.py
class LoginView(TokenObtainPairView):
    throttle_classes = [throttling.ScopedRateThrottle]
    throttle_scope = "login"
```

For per-IP and per-endpoint fine control, `django-ratelimit`:
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def expensive_search(request): ...
```

## 8. Migration with backfill (zero-downtime schema change)

```python
# Step 1: add nullable column
class Migration(migrations.Migration):
    dependencies = [...]
    operations = [
        migrations.AddField("Product", "vector",
                            models.JSONField(null=True, blank=True)),
    ]

# Step 2 (separate migration, after deploy): backfill in batches
def backfill_vectors(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    batch = []
    for p in Product.objects.filter(vector__isnull=True).iterator(chunk_size=500):
        p.vector = compute_embedding(p.name).tolist()
        batch.append(p)
        if len(batch) >= 500:
            Product.objects.bulk_update(batch, ["vector"])
            batch = []
    if batch:
        Product.objects.bulk_update(batch, ["vector"])

class Migration(migrations.Migration):
    operations = [migrations.RunPython(backfill_vectors, migrations.RunPython.noop)]

# Step 3 (after backfill complete): make non-null
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField("Product", "vector",
                              models.JSONField(null=False)),
    ]
```

The 3-step pattern (add nullable -> backfill -> enforce non-null) prevents downtime on big tables.

## 9. Custom Manager -- soft-delete pattern

```python
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Order(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)
    # ... other fields

    objects = SoftDeleteManager()          # default: hides deleted
    all_objects = models.Manager()          # for admin

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save()
```

Now `Order.objects.all()` excludes deleted; `Order.all_objects.all()` includes them.

## 10. Custom admin for AIAAS workflow runs

```python
@admin.register(WorkflowRun)
class WorkflowRunAdmin(admin.ModelAdmin):
    list_display = ["id", "workflow", "user", "status", "created",
                    "duration_ms", "approval_status_badge"]
    list_filter = ["status", "workflow", "created"]
    search_fields = ["id", "workflow__name", "user__email"]
    readonly_fields = ["state_snapshot", "trace"]
    actions = ["cancel_runs", "retry_failed"]

    def duration_ms(self, obj):
        if obj.completed_at:
            return int((obj.completed_at - obj.created).total_seconds() * 1000)
        return None

    def approval_status_badge(self, obj):
        if obj.status == "waiting_approval":
            return format_html('<span style="color:orange">⏸ waiting</span>')
        return obj.status

    def cancel_runs(self, request, queryset):
        for run in queryset.filter(status__in=["running","waiting_approval"]):
            cancel_workflow(run.id)
        self.message_user(request, f"Cancelled {queryset.count()} runs.")
```

## Interview anchor lines (memorize one per area)
- **N+1 fix**: "`select_related` for FK (single JOIN); `prefetch_related` for M2M (second query + Python merge)"
- **Caching**: "Namespaced versioned keys for class-level invalidation; signal-based delete for per-row freshness"
- **Pagination**: "Cursor pagination on big tables -- OFFSET is O(N) skipped rows in Postgres"
- **Async**: "Async views work with httpx and async DBs; for sync ORM use `sync_to_async`"
- **Migrations**: "Three-step pattern for non-null columns on big tables -- add nullable, backfill, enforce"
- **WebSockets**: "Channels uses Redis as a pub/sub channel layer so any worker can broadcast to any connected client"
