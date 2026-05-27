"""Generate SVG diagrams for the remaining 5 folders."""
from pathlib import Path

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")

STYLE = """
<style>
  .title { font: bold 16px sans-serif; fill: #1a1a1a; }
  .label { font: 12px sans-serif; fill: #333; }
  .small { font: 10px sans-serif; fill: #555; }
  .mono  { font: 13px 'Consolas','Courier New',monospace; fill: #111; }
  .box   { fill: #f6f8fa; stroke: #444; stroke-width: 1.2; }
  .box2  { fill: #e6f0ff; stroke: #1f6feb; stroke-width: 1.5; }
  .box3  { fill: #fff3cd; stroke: #b58900; stroke-width: 1.5; }
  .box4  { fill: #d4edda; stroke: #1a7f37; stroke-width: 1.5; }
  .box5  { fill: #fce7f3; stroke: #be185d; stroke-width: 1.5; }
  .arrow { stroke: #444; stroke-width: 1.6; fill: none; marker-end: url(#arr); }
  .arrow2{ stroke: #1f6feb; stroke-width: 2; fill: none; marker-end: url(#arrB); }
  .arrow3{ stroke: #d33; stroke-width: 2; fill: none; marker-end: url(#arrR); }
</style>
<defs>
  <marker id="arr"  viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#444"/></marker>
  <marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1f6feb"/></marker>
  <marker id="arrR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#d33"/></marker>
</defs>
"""

def svg(w,h,body,title=None):
    t = f'<text x="{w//2}" y="22" text-anchor="middle" class="title">{title}</text>' if title else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{t}{body}</svg>'

# ====================== 05 Backend-Django ======================
def d_django_request():
    body = ''
    stages = ["WSGI/ASGI","Middleware","URL resolver","View","Model / ORM","Database"]
    cols = [("box2","box3","box4","box5","box3","box")]
    for i,s in enumerate(stages):
        x = 60 + i*110
        cls = ["box2","box3","box4","box5","box3","box"][i]
        body += f'<rect x="{x}" y="80" width="100" height="60" class="{cls}"/>'
        body += f'<text x="{x+50}" y="115" text-anchor="middle" class="mono">{s}</text>'
        if i < len(stages)-1:
            body += f'<path class="arrow" d="M {x+100} 110 L {x+110} 110"/>'
    body += '<text x="40" y="65" class="label">Request lifecycle:</text>'
    # response back
    body += '<path class="arrow3" d="M 660 170 C 660 200 60 200 60 170"/>'
    body += '<text x="360" y="210" text-anchor="middle" class="small">response (template / JSON)</text>'
    body += '<text x="40" y="260" class="mono">Key files:  settings.py · urls.py · views.py · models.py · serializers.py</text>'
    body += '<text x="40" y="282" class="mono">DRF adds: serializers, viewsets, routers, permissions, throttling</text>'
    body += '<text x="40" y="305" class="small">ASGI for async / websockets (Django channels). WSGI for sync (gunicorn).</text>'
    return svg(780, 340, body, "Django Request Lifecycle")

def d_orm():
    body = ''
    body += '<rect x="60" y="60" width="160" height="200" class="box4"/>'
    body += '<text x="140" y="85" text-anchor="middle" class="label">User (Model)</text>'
    for i,f in enumerate(["id PK","email","password","created_at"]):
        body += f'<text x="80" y="{115+i*22}" class="mono">{f}</text>'
    body += '<rect x="320" y="60" width="160" height="200" class="box2"/>'
    body += '<text x="400" y="85" text-anchor="middle" class="label">Post (Model)</text>'
    for i,f in enumerate(["id PK","title","body","user_id FK"]):
        body += f'<text x="340" y="{115+i*22}" class="mono">{f}</text>'
    body += '<line x1="220" y1="170" x2="320" y2="170" stroke="#1f6feb" stroke-width="2"/>'
    body += '<text x="270" y="160" text-anchor="middle" class="small">1 ─── *</text>'
    body += '<rect x="540" y="60" width="180" height="200" class="box3"/>'
    body += '<text x="630" y="85" text-anchor="middle" class="label">QuerySet (lazy)</text>'
    body += '<text x="560" y="115" class="mono">Post.objects \\</text>'
    body += '<text x="580" y="135" class="mono">  .filter(user=u) \\</text>'
    body += '<text x="580" y="155" class="mono">  .select_related("user") \\</text>'
    body += '<text x="580" y="175" class="mono">  .order_by("-created_at")[:10]</text>'
    body += '<text x="560" y="210" class="small">.select_related → JOIN</text>'
    body += '<text x="560" y="230" class="small">.prefetch_related → 2 queries</text>'
    body += '<text x="40" y="300" class="mono">N+1 problem: looping over qs and lazy-loading FK fields → 1+N queries.</text>'
    body += '<text x="40" y="322" class="mono">Fix: select_related (single JOIN) or prefetch_related (separate query, in-Python join).</text>'
    return svg(760, 350, body, "Django ORM — Models &amp; QuerySets")

def d_auth_drf():
    body = ''
    body += '<text x="40" y="60" class="label">JWT auth flow (DRF + SimpleJWT)</text>'
    steps = [
        ("client",        80, 100),
        ("/login",       240, 100),
        ("validate user",400, 100),
        ("issue access + refresh JWT",560, 100),
        ("client stores tokens",80, 200),
        ("/api with Bearer access",240, 200),
        ("middleware validates JWT",400, 200),
        ("view + return data",560, 200),
    ]
    for s,x,y in steps:
        body += f'<rect x="{x-60}" y="{y-22}" width="120" height="44" class="box2"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{s}</text>'
    for a,b in [(0,1),(1,2),(2,3),(4,5),(5,6),(6,7)]:
        x1,y1 = steps[a][1]+60, steps[a][2]
        x2,y2 = steps[b][1]-60, steps[b][2]
        body += f'<path class="arrow" d="M {x1} {y1} L {x2} {y2}"/>'
    # access expires → /refresh
    body += '<text x="40" y="270" class="mono">When access expires: POST /refresh with refresh JWT → new access</text>'
    body += '<text x="40" y="292" class="mono">Logout: blacklist refresh token (DB table)</text>'
    body += '<text x="40" y="315" class="small">Access = short (15 min). Refresh = long (7d). Store refresh in HttpOnly cookie if possible.</text>'
    return svg(780, 345, body, "Django REST + JWT Authentication")

# ====================== 06 Frontend ======================
def d_react_lifecycle():
    body = ''
    body += '<text x="40" y="60" class="label">React component lifecycle (functional + hooks)</text>'
    phases = [
        ("Render",      120, 110, "box2", "compute JSX"),
        ("Commit",      320, 110, "box3", "DOM updated"),
        ("useLayoutEffect", 520, 110, "box5", "sync, before paint"),
        ("useEffect",   520, 200, "box4", "async, after paint"),
        ("Unmount",     320, 290, "box", "cleanup runs"),
    ]
    for label,x,y,cls,sub in phases:
        body += f'<rect x="{x-80}" y="{y-26}" width="160" height="52" class="{cls}"/>'
        body += f'<text x="{x}" y="{y-2}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="{x}" y="{y+15}" text-anchor="middle" class="small">{sub}</text>'
    body += '<path class="arrow" d="M 200 110 L 240 110"/>'
    body += '<path class="arrow" d="M 400 110 L 440 110"/>'
    body += '<path class="arrow" d="M 520 136 L 520 174"/>'
    body += '<path class="arrow" d="M 440 200 C 360 240 360 270 320 290"/>'
    body += '<text x="40" y="370" class="mono">useEffect deps:  [] = once, [x] = on x change, missing = every render</text>'
    body += '<text x="40" y="392" class="mono">return () =&gt; { cleanup }   in effect for unmount / re-effect</text>'
    return svg(760, 420, body, "React Lifecycle &amp; Hooks Timing")

def d_state_mgmt():
    body = ''
    body += '<text x="40" y="60" class="label">State management options</text>'
    options = [
        ("useState",    100, 110, "box4", "local, simple, primitive"),
        ("useReducer",  300, 110, "box4", "local, complex transitions"),
        ("Context",     500, 110, "box3", "shared in tree, low-freq"),
        ("Redux/Zustand", 100, 220, "box2", "global, devtools, async"),
        ("React Query", 300, 220, "box2", "server state cache"),
        ("URL state",   500, 220, "box5", "shareable, bookmarkable"),
    ]
    for label,x,y,cls,sub in options:
        body += f'<rect x="{x-80}" y="{y-26}" width="160" height="52" class="{cls}"/>'
        body += f'<text x="{x}" y="{y-2}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="{x}" y="{y+15}" text-anchor="middle" class="small">{sub}</text>'
    body += '<text x="40" y="310" class="mono">Decision: local? → useState. Shared but stable? → Context. Server data? → React Query.</text>'
    body += '<text x="40" y="332" class="mono">Frequent updates across tree → Zustand / Jotai (atoms) avoid context re-render storm.</text>'
    return svg(760, 360, body, "React State Management Choices")

def d_render():
    body = ''
    body += '<text x="40" y="60" class="label">Rendering strategies</text>'
    rows = [
        ("CSR",  "browser fetches JS, renders client-side", "Slow first paint, fast nav, simple",       100, "box2"),
        ("SSR",  "server renders HTML per request",          "Fast first paint, server load",            150, "box3"),
        ("SSG",  "build-time static HTML",                    "Fastest, scales, stale risk",              200, "box4"),
        ("ISR",  "static + revalidate on a schedule",         "Best of SSG + freshness",                  250, "box5"),
        ("RSC",  "React Server Components stream HTML/RSC",   "Less JS to client; modern Next.js",        300, "box"),
    ]
    for tag,desc,trade,y,cls in rows:
        body += f'<rect x="60" y="{y-20}" width="60" height="40" class="{cls}"/>'
        body += f'<text x="90" y="{y+5}" text-anchor="middle" class="mono">{tag}</text>'
        body += f'<text x="130" y="{y+5}" class="mono">{desc}</text>'
        body += f'<text x="450" y="{y+5}" class="small">{trade}</text>'
    body += '<text x="40" y="370" class="small">Next.js app router supports CSR/SSR/SSG/ISR/RSC on a per-route basis.</text>'
    return svg(760, 400, body, "Rendering Strategies")

# ====================== 07 Deployment ======================
def d_docker_layers():
    body = ''
    body += '<text x="40" y="60" class="label">Image layers (top = newest)</text>'
    layers = [
        ("CMD ['python','app.py']",  90, "box5"),
        ("COPY app.py /app",        140, "box4"),
        ("RUN pip install -r req",  190, "box4"),
        ("COPY requirements.txt",   240, "box3"),
        ("WORKDIR /app",            290, "box3"),
        ("FROM python:3.11-slim",   340, "box2"),
    ]
    for label,y,cls in layers:
        body += f'<rect x="80" y="{y-20}" width="280" height="40" class="{cls}"/>'
        body += f'<text x="220" y="{y+5}" text-anchor="middle" class="mono">{label}</text>'
    body += '<text x="40" y="400" class="mono">Each line = layer; cached if unchanged. Order matters: COPY app.py late = pip cache reused.</text>'
    # multi-stage on right
    body += '<text x="430" y="60" class="label">Multi-stage build</text>'
    body += '<rect x="430" y="90" width="280" height="100" class="box3"/>'
    body += '<text x="440" y="115" class="mono">FROM node:20 AS build</text>'
    body += '<text x="440" y="135" class="mono">COPY . . && npm ci && npm run build</text>'
    body += '<text x="440" y="175" class="small">(huge build tools, dev deps)</text>'
    body += '<rect x="430" y="210" width="280" height="100" class="box4"/>'
    body += '<text x="440" y="235" class="mono">FROM nginx:alpine</text>'
    body += '<text x="440" y="255" class="mono">COPY --from=build /app/dist /usr/share/nginx/html</text>'
    body += '<text x="440" y="295" class="small">(small final image)</text>'
    body += '<text x="40" y="425" class="small">.dockerignore reduces context. Healthchecks for orchestrators. Pin tags (not :latest).</text>'
    return svg(760, 450, body, "Docker — Layers &amp; Multi-stage")

def d_k8s():
    body = ''
    objs = [
        ("Deployment",  120, 100, "box2", "scales pods, rolling update"),
        ("ReplicaSet",  300, 100, "box3", "ensures N replicas"),
        ("Pod",         480, 100, "box4", "1+ containers, shared net/vol"),
        ("Container",   640, 100, "box5", "Docker image"),
        ("Service",     120, 240, "box2", "stable IP / DNS, load-balance"),
        ("Ingress",     300, 240, "box3", "HTTP routing + TLS"),
        ("ConfigMap",   480, 240, "box4", "non-secret env vars"),
        ("Secret",      640, 240, "box5", "encrypted credentials"),
    ]
    for label,x,y,cls,sub in objs:
        body += f'<rect x="{x-60}" y="{y-22}" width="120" height="44" class="{cls}"/>'
        body += f'<text x="{x}" y="{y-2}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="{x}" y="{y+15}" text-anchor="middle" class="small">{sub}</text>'
    body += '<path class="arrow" d="M 180 100 L 240 100"/>'
    body += '<path class="arrow" d="M 360 100 L 420 100"/>'
    body += '<path class="arrow" d="M 540 100 L 580 100"/>'
    body += '<path class="arrow" d="M 180 240 L 240 240"/>'
    body += '<text x="40" y="320" class="mono">Deployment → ReplicaSet → Pod (× N replicas) → Container</text>'
    body += '<text x="40" y="342" class="mono">Service exposes Pods by label selector. Ingress routes external traffic.</text>'
    body += '<text x="40" y="370" class="small">kubectl rollout undo · kubectl logs · kubectl exec -it &lt;pod&gt; -- sh — top 3 daily commands.</text>'
    return svg(780, 400, body, "Kubernetes Core Objects")

def d_cicd():
    body = ''
    stages = [
        ("commit/PR", 80, "box"),
        ("CI: lint + test", 220, "box2"),
        ("Build image", 360, "box3"),
        ("Push to registry", 500, "box3"),
        ("Deploy staging", 640, "box4"),
        ("E2E tests", 80, "box4", 220),
        ("Approve", 220, "box5", 220),
        ("Deploy prod", 360, "box5", 220),
        ("Smoke + monitor", 500, "box4", 220),
        ("Rollback?", 640, "box", 220),
    ]
    for s in stages:
        if len(s) == 3:
            label,x,cls = s; y = 100
        else:
            label,x,cls,y = s
        body += f'<rect x="{x-60}" y="{y-22}" width="120" height="44" class="{cls}"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{label}</text>'
    for a,b in [(0,1),(1,2),(2,3),(3,4)]:
        x1 = stages[a][1]+60; x2 = stages[b][1]-60
        body += f'<path class="arrow" d="M {x1} 100 L {x2} 100"/>'
    # vertical drop
    body += '<path class="arrow" d="M 640 122 L 640 200"/>'
    # second row backwards
    for a,b in [(5,6),(6,7),(7,8),(8,9)]:
        x1 = stages[a][1]+60 if a!=5 else stages[5][1]+60
        x2 = stages[b][1]-60
        body += f'<path class="arrow" d="M {x1} 220 L {x2} 220"/>'
    body += '<text x="40" y="290" class="mono">Branch protection · required checks · environments + approvals · concurrency locks</text>'
    body += '<text x="40" y="312" class="mono">GitHub Actions / GitLab CI / CircleCI · Argo CD for K8s GitOps</text>'
    return svg(780, 350, body, "CI/CD Pipeline")

# ====================== 08 VCS-Testing ======================
def d_git_branching():
    body = ''
    body += '<text x="40" y="55" class="label">Git Flow vs Trunk-based</text>'
    # branches drawn as horizontal lines
    body += '<line x1="80" y1="120" x2="700" y2="120" stroke="#1f6feb" stroke-width="2"/>'
    body += '<text x="60" y="124" text-anchor="end" class="mono">main</text>'
    body += '<line x1="80" y1="180" x2="700" y2="180" stroke="#b58900" stroke-width="2"/>'
    body += '<text x="60" y="184" text-anchor="end" class="mono">develop</text>'
    # feature branches off develop
    for fx in (200, 320, 440):
        body += f'<path d="M {fx} 180 C {fx+10} 230 {fx+30} 230 {fx+50} 180" fill="none" stroke="#1a7f37" stroke-width="2"/>'
        body += f'<circle cx="{fx+25}" cy="225" r="5" fill="#1a7f37"/>'
        body += f'<text x="{fx+25}" y="248" text-anchor="middle" class="small">feature</text>'
    # release branch
    body += '<path d="M 540 180 C 540 150 600 130 660 120" fill="none" stroke="#d33" stroke-width="2"/>'
    body += '<circle cx="600" cy="148" r="5" fill="#d33"/>'
    body += '<text x="600" y="142" text-anchor="middle" class="small">release</text>'
    # trunk based right side
    body += '<text x="40" y="300" class="label">Trunk-based:</text>'
    body += '<line x1="80" y1="320" x2="700" y2="320" stroke="#1f6feb" stroke-width="2"/>'
    body += '<text x="60" y="324" text-anchor="end" class="mono">main</text>'
    for fx in (160, 260, 360, 460, 560):
        body += f'<path d="M {fx} 320 C {fx} 350 {fx+30} 350 {fx+30} 320" fill="none" stroke="#1a7f37" stroke-width="2"/>'
        body += f'<circle cx="{fx+15}" cy="345" r="3" fill="#1a7f37"/>'
    body += '<text x="40" y="385" class="small">Trunk: short-lived feature branches, merged to main daily. Behind feature flags.</text>'
    return svg(760, 410, body, "Git Branching Models")

def d_testing_pyramid():
    body = ''
    # pyramid
    pts = [(380, 80), (190, 320), (570, 320)]
    body += f'<polygon points="{pts[0][0]},{pts[0][1]} {pts[1][0]},{pts[1][1]} {pts[2][0]},{pts[2][1]}" fill="#e6f0ff" stroke="#1f6feb" stroke-width="2"/>'
    # horizontal dividers
    body += '<line x1="280" y1="180" x2="480" y2="180" stroke="#1f6feb"/>'
    body += '<line x1="230" y1="240" x2="530" y2="240" stroke="#1f6feb"/>'
    body += '<text x="380" y="140" text-anchor="middle" class="mono">E2E</text>'
    body += '<text x="380" y="155" text-anchor="middle" class="small">few, slow, brittle</text>'
    body += '<text x="380" y="215" text-anchor="middle" class="mono">Integration</text>'
    body += '<text x="380" y="230" text-anchor="middle" class="small">DB / API / service boundary</text>'
    body += '<text x="380" y="280" text-anchor="middle" class="mono">Unit</text>'
    body += '<text x="380" y="295" text-anchor="middle" class="small">many, fast, narrow scope</text>'
    body += '<text x="40" y="365" class="mono">Pareto: 80% unit, 15% integration, 5% E2E.</text>'
    body += '<text x="40" y="387" class="small">Anti-pattern (ice-cream cone): too many slow E2E, too few unit. Common in legacy.</text>'
    return svg(760, 410, body, "Testing Pyramid")

# ====================== 09 System Design + Security ======================
def d_sd_caching():
    body = ''
    # 4 cache patterns
    body += '<text x="40" y="60" class="label">Cache patterns</text>'
    patterns = [
        ("Cache-aside",      120, "App checks cache; on miss, query DB + populate cache"),
        ("Read-through",     180, "Cache layer queries DB itself on miss"),
        ("Write-through",    240, "Writes hit cache + DB synchronously"),
        ("Write-behind",     300, "Writes hit cache; flushed to DB async (risk of loss)"),
        ("Refresh-ahead",    360, "Proactively refresh hot keys before expiry"),
    ]
    for name,y,desc in patterns:
        body += f'<rect x="80" y="{y-20}" width="160" height="40" class="box2"/>'
        body += f'<text x="160" y="{y+5}" text-anchor="middle" class="mono">{name}</text>'
        body += f'<text x="260" y="{y+5}" class="small">{desc}</text>'
    body += '<text x="40" y="420" class="mono">Eviction: LRU, LFU, ARC, TTL. Memcached vs Redis (richer types, persistence).</text>'
    body += '<text x="40" y="442" class="mono">Cache stampede: lock+single-flight, request coalescing, jittered TTL.</text>'
    return svg(760, 470, body, "System Design — Caching Patterns")

def d_sd_dbreplication():
    body = ''
    body += '<rect x="80" y="100" width="160" height="80" class="box2"/>'
    body += '<text x="160" y="135" text-anchor="middle" class="mono">Primary</text>'
    body += '<text x="160" y="155" text-anchor="middle" class="small">writes + reads</text>'
    for i,y in enumerate([60, 180, 300]):
        body += f'<rect x="400" y="{y+30}" width="160" height="60" class="box4"/>'
        body += f'<text x="480" y="{y+60}" text-anchor="middle" class="mono">Replica {i+1}</text>'
        body += f'<text x="480" y="{y+80}" text-anchor="middle" class="small">read-only</text>'
        body += f'<path class="arrow2" d="M 240 140 L 400 {y+60}"/>'
    body += '<text x="40" y="420" class="mono">Replication: sync (slow, consistent) vs async (fast, lag → stale reads).</text>'
    body += '<text x="40" y="442" class="mono">Failover: promote replica, redirect writes. Watch split-brain via fencing/quorum.</text>'
    body += '<text x="40" y="470" class="small">Sharding (horizontal partitioning) when one primary can\'t hold the data.</text>'
    return svg(760, 500, body, "DB Replication &amp; Read Scaling")

def d_sec_owasp():
    body = ''
    top10 = [
        ("A01 Broken access control",      90, "vertical privilege check missing"),
        ("A02 Cryptographic failures",    130, "plaintext, weak ciphers, mis-config TLS"),
        ("A03 Injection",                 170, "SQL/CMD/LDAP via untrusted input"),
        ("A04 Insecure design",           210, "missing threat modelling"),
        ("A05 Security mis-config",       250, "defaults, verbose errors, open S3"),
        ("A06 Vulnerable components",     290, "outdated libs, log4shell-style"),
        ("A07 Identification failures",   330, "weak passwords, broken session"),
        ("A08 Software/data integrity",   370, "unsigned updates, supply chain"),
        ("A09 Logging/monitoring failures",410, "missed breaches, no audit"),
        ("A10 SSRF",                      450, "fetch internal URLs via user input"),
    ]
    for label,y,desc in top10:
        body += f'<rect x="60" y="{y-16}" width="230" height="30" class="box5"/>'
        body += f'<text x="70" y="{y+5}" class="mono">{label}</text>'
        body += f'<text x="310" y="{y+5}" class="small">{desc}</text>'
    body += '<text x="40" y="490" class="label">Defence: principle of least privilege, parameterised queries, secrets manager,</text>'
    body += '<text x="40" y="510" class="label">security scanners (CodeQL, Snyk), SBOM, audit logs, MFA.</text>'
    return svg(760, 540, body, "OWASP Top 10 (2021)")

DIAGRAMS = {
    "05-Backend-Django": {
        "02-django-lifecycle":  d_django_request(),
        "03-orm":               d_orm(),
        "04-drf-jwt":           d_auth_drf(),
    },
    "06-Frontend": {
        "01-react-lifecycle":   d_react_lifecycle(),
        "02-state-management":  d_state_mgmt(),
        "03-rendering":         d_render(),
    },
    "07-Deployment": {
        "02-docker-layers":     d_docker_layers(),
        "03-k8s-core":          d_k8s(),
        "04-cicd":              d_cicd(),
    },
    "08-VCS-Testing": {
        "01-git-branching":     d_git_branching(),
        "02-test-pyramid":      d_testing_pyramid(),
    },
    "09-System-Design-Security": {
        "06-caching":           d_sd_caching(),
        "07-db-replication":    d_sd_dbreplication(),
        "08-owasp-top10":       d_sec_owasp(),
    },
}

for folder, items in DIAGRAMS.items():
    outdir = ROOT / folder / "diagrams"
    outdir.mkdir(parents=True, exist_ok=True)
    for n, body in items.items():
        (outdir / f"{n}.svg").write_text(body, encoding="utf-8")
        print("wrote", folder, n)
