# Deployment -- Worked Examples

> Companion to [deployment-full-cheatsheet.md](deployment-full-cheatsheet.md). Production-shape Dockerfiles, nginx configs, CI yaml, IaC fragments. Anchored to NGU stack.

## 1. Multi-stage Dockerfile -- Django + static files
```dockerfile
# ============================================================
# Stage 1: builder -- install Python deps in a venv
# ============================================================
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# ============================================================
# Stage 2: runtime -- only what we need to RUN
# ============================================================
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos "" appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --chown=appuser:appuser . .

RUN python manage.py collectstatic --noinput

USER appuser
EXPOSE 8000
CMD ["gunicorn", "ngu.wsgi", "-b", "0.0.0.0:8000", "-w", "4", "--access-logfile", "-"]
```

**Talking points**:
- **Multi-stage**: build-time deps (gcc, libpq-dev) gone from final image -> smaller, less attack surface
- **`appuser`**: never run as root in production
- **`PYTHONUNBUFFERED=1`**: logs flush immediately, visible in `docker logs`
- **Layer order**: `requirements.txt` copied before source -> caching wins on code changes
- **`--chown`**: avoids "permission denied" inside container

## 2. docker-compose for local dev with hot-reload

```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: python manage.py runserver 0.0.0.0:8000
    ports: ["8000:8000"]
    volumes:
      - .:/app                          # bind mount for hot reload
      - /app/__pycache__                # exclude from bind mount
    env_file: .env
    depends_on:
      db:    { condition: service_healthy }
      redis: { condition: service_started }

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: ngu
    volumes: [pg_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./nginx.dev.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on: [web]

  worker:
    build: .
    command: celery -A ngu worker -l info
    volumes: [.:/app]
    env_file: .env
    depends_on: [redis]

volumes:
  pg_data:
```

**Notes**:
- `condition: service_healthy` -> wait for Postgres `pg_isready`, not just "container started"
- Separate `Dockerfile.dev` mounts source; production Dockerfile doesn't
- `worker` runs Celery from the same image -- different command

## 3. Nginx production config -- TLS + WS + static

```nginx
upstream django {
    server web:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name nidhimasala.kaushaljain.com;
    return 301 https://$host$request_uri;        # force HTTPS
}

server {
    listen 443 ssl http2;
    server_name nidhimasala.kaushaljain.com;

    ssl_certificate     /etc/letsencrypt/live/nidhimasala.kaushaljain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nidhimasala.kaushaljain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header Referrer-Policy strict-origin-when-cross-origin;

    client_max_body_size 20M;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;        # WebSocket can be long-lived
    }

    location / {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**Talking points** (all interview gold):
- HSTS, X-Frame-Options, X-Content-Type-Options -> minimum security headers
- `upgrade` headers -> required for WebSocket proxy
- `gzip` compression -> smaller responses
- Cache-Control immutable for fingerprinted static assets
- Long `proxy_read_timeout` for WS lifecycle

## 4. GitHub Actions CI -- test + build + deploy

```yaml
# .github/workflows/ci.yml
name: ci

on:
  push:
    branches: [main, dev]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        ports: [5432:5432]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: [6379:6379]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Lint
        run: |
          ruff check .
          black --check .

      - name: Type check
        run: mypy ngu

      - name: Tests
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/postgres
          REDIS_URL: redis://localhost:6379/0
        run: pytest --cov=ngu --cov-report=xml

      - uses: codecov/codecov-action@v4

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & push image
        run: |
          echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u kaushaljain --password-stdin
          docker build -t kaushaljain/ngu:${{ github.sha }} -t kaushaljain/ngu:latest .
          docker push kaushaljain/ngu:${{ github.sha }}
          docker push kaushaljain/ngu:latest
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/ngu
            docker compose pull
            docker compose up -d --no-deps web worker
            docker compose exec -T web python manage.py migrate --noinput
```

**Talking points**:
- **Services**: Postgres + Redis spun up as side containers
- **Health checks**: prevent races
- **Cache pip**: faster CI runs
- **Image tagged with `github.sha`** -> reproducible rollback
- **Deploy only on `main`** push
- **`--no-deps`**: don't restart DB/Redis just because app changed

## 5. systemd unit for a non-docker deployment

```ini
# /etc/systemd/system/ngu-web.service
[Unit]
Description=NGU Django app
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=ngu
Group=ngu
WorkingDirectory=/opt/ngu
EnvironmentFile=/opt/ngu/.env
ExecStart=/opt/ngu/venv/bin/gunicorn ngu.wsgi -b 127.0.0.1:8000 -w 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Useful systemd commands:
```bash
sudo systemctl enable ngu-web
sudo systemctl start ngu-web
sudo systemctl status ngu-web
sudo journalctl -u ngu-web -f          # follow logs
```

## 6. Let's Encrypt cert renewal (cron)

```bash
# Initial cert
sudo certbot --nginx -d nidhimasala.kaushaljain.com

# Auto-renewal cron (most distros do this automatically; otherwise):
0 3 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```
Certs are valid 90 days; certbot renews when <30 days remain.

## 7. AWS IAM policy -- least-privilege for S3 uploads

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BucketRead",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:HeadObject"],
      "Resource": "arn:aws:s3:::ngu-media/*"
    },
    {
      "Sid": "BucketWrite",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::ngu-media/uploads/*"
    },
    {
      "Sid": "BucketList",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::ngu-media",
      "Condition": {
        "StringLike": { "s3:prefix": ["uploads/*"] }
      }
    }
  ]
}
```
**Talking points**:
- Read everything, but write only under `uploads/`
- `ListBucket` scoped to a prefix
- Attach to an EC2 instance role -- never bake keys into images

## 8. Zero-downtime deploy strategy (rolling)

```
1. New version image pushed (tag: v2.3.1)
2. Bring up new container (web-v2.3.1) on a different port
3. Health-check it directly (curl localhost:8001/healthz)
4. Reload nginx with both upstreams; new = primary, old = backup
5. Drain old (let in-flight requests finish; ~60s)
6. Stop old container
```

Implementation snippet (nginx with two upstreams):
```nginx
upstream django {
    server web_new:8000;
    server web_old:8000 backup;
}
```
Or use Docker swarm / Kubernetes `kubectl rollout` which automates this.

## 9. PostgreSQL backup + restore

```bash
# Backup (daily cron, encrypted, uploaded to S3)
PGPASSWORD=$DB_PASS pg_dump -h db -U postgres ngu \
  | gzip \
  | openssl enc -aes-256-cbc -salt -pass file:/etc/ngu/backup.key \
  | aws s3 cp - s3://ngu-backups/$(date +%Y%m%d).sql.gz.enc

# Restore
aws s3 cp s3://ngu-backups/20260520.sql.gz.enc - \
  | openssl enc -d -aes-256-cbc -pass file:/etc/ngu/backup.key \
  | gunzip \
  | PGPASSWORD=$DB_PASS psql -h db -U postgres ngu
```

## 10. Health-check endpoint (Django)

```python
# urls.py
path('healthz/', health_view)

# views.py
from django.db import connection
from django.core.cache import cache

def health_view(request):
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        cache.set("health", "ok", timeout=10)
        cache.get("health")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=503)
```
ALB/nginx/k8s probes hit `/healthz/` -- only marks instance healthy on 200.

## Interview-quick answers
- *EC2 vs Lambda vs Fargate?* EC2 = managed VM; Lambda = stateless function <=15min; Fargate = container w/o managing VM.
- *Why nginx in front of Gunicorn?* Static file serving, TLS termination, buffering slow clients, request limits, gzip.
- *Reverse proxy vs forward proxy?* Reverse = front of your servers; forward = front of clients.
- *Zero-downtime deploy?* Rolling: spin new, health-check, switch traffic, drain old.
- *Docker COPY vs ADD?* COPY is plain; ADD also handles URLs + tar extraction. Prefer COPY for clarity.
- *Build cache invalidation?* Every Dockerfile instruction creates a layer. Change -> invalidates all subsequent layers. Order rarely-changing things first.
- *S3 storage classes?* Standard (hot), Standard-IA (warm), Glacier (cold archive); lifecycle rules transition automatically.
- *DNS TTL?* How long resolvers cache. Lower before changes, raise after.
