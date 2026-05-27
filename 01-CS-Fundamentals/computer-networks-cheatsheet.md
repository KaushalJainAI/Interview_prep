# Computer Networks -- Interview Cheatsheet

> Goal: answer CN interview questions clearly: OSI/TCP-IP, DNS, HTTP, TCP vs UDP, TLS, load balancing, latency, caching, and network debugging.

## TL;DR

| Topic | One-line answer |
|-------|-----------------|
| IP | Addressing and routing packets between machines |
| TCP | Reliable, ordered, connection-oriented byte stream |
| UDP | Connectionless datagrams; faster but no delivery guarantee |
| DNS | Converts domain names to IP addresses |
| HTTP | Application protocol for web request/response |
| TLS | Encrypts and authenticates communication |
| CDN | Serves content from edge locations near users |
| Load balancer | Distributes traffic across servers |

---

## 1. OSI and TCP/IP models

### OSI model

| Layer | Name | Example |
|-------|------|---------|
| 7 | Application | HTTP, DNS, SMTP |
| 6 | Presentation | TLS, compression, encoding |
| 5 | Session | session management |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP, ICMP, routing |
| 2 | Data link | Ethernet, Wi-Fi, MAC |
| 1 | Physical | cables, radio, signals |

### TCP/IP model

| Layer | Example |
|-------|---------|
| Application | HTTP, DNS, TLS |
| Transport | TCP, UDP |
| Internet | IP, ICMP |
| Link | Ethernet, Wi-Fi |

Interview tip: OSI is a teaching model; TCP/IP is closer to real internet stacks.

## 2. What happens when you type a URL?

```text
1. Browser parses URL.
2. DNS resolves domain to IP.
3. Browser opens TCP connection to server IP:port.
4. TLS handshake happens for HTTPS.
5. Browser sends HTTP request.
6. Server/app processes request.
7. Response returns through network.
8. Browser parses HTML, fetches CSS/JS/images, renders page.
```

Mention caches: browser cache, DNS cache, CDN, load balancer, reverse proxy, app cache, DB cache.

## 3. DNS

DNS maps names to records.

| Record | Meaning |
|--------|---------|
| A | domain -> IPv4 |
| AAAA | domain -> IPv6 |
| CNAME | alias to another domain |
| MX | mail server |
| TXT | arbitrary text, SPF/DKIM verification |
| NS | authoritative name server |

### Recursive resolution

```text
browser -> OS cache -> recursive resolver -> root -> TLD -> authoritative DNS -> answer
```

Key concept: **TTL** controls how long records are cached. Lower TTL before migration; raise after stable.

## 4. TCP vs UDP

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Yes | No |
| Reliability | Retransmits lost packets | No guarantee |
| Ordering | Preserved | Not guaranteed |
| Flow control | Yes | No |
| Congestion control | Yes | No built-in |
| Overhead | Higher | Lower |
| Use cases | HTTP/1.1, HTTP/2, DB connections | DNS, VoIP, gaming, QUIC |

**Interview answer:** Use TCP when correctness/order matters. Use UDP when latency matters and the application can tolerate or handle loss.

## 5. TCP handshake and teardown

### 3-way handshake

```text
Client -> Server: SYN
Server -> Client: SYN-ACK
Client -> Server: ACK
```

Purpose:
- agree initial sequence numbers
- confirm both sides can send/receive
- establish connection state

### 4-way close

```text
A -> B: FIN
B -> A: ACK
B -> A: FIN
A -> B: ACK
```

`TIME_WAIT`: keeps old delayed packets from corrupting a future connection with same tuple.

## 6. TCP reliability

Mechanisms:
- sequence numbers
- acknowledgements
- retransmission timeout
- sliding window
- flow control
- congestion control

### Flow control vs congestion control

| Concept | Protects | Signal |
|---------|----------|--------|
| Flow control | receiver | receiver window |
| Congestion control | network | packet loss, RTT, ECN |

## 7. HTTP basics

| Method | Meaning | Idempotent? |
|--------|---------|-------------|
| GET | Read resource | Yes |
| POST | Create/action | No by default |
| PUT | Replace resource | Yes |
| PATCH | Partial update | No by default |
| DELETE | Delete resource | Yes |

### Status codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No content |
| 301/302 | Redirect |
| 400 | Bad request |
| 401 | Unauthenticated |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict |
| 429 | Rate limited |
| 500 | Server error |
| 502 | Bad gateway |
| 503 | Service unavailable |
| 504 | Gateway timeout |

## 8. HTTP/1.1 vs HTTP/2 vs HTTP/3

| Version | Transport | Key improvement |
|---------|-----------|-----------------|
| HTTP/1.1 | TCP | persistent connections, chunking |
| HTTP/2 | TCP | multiplexing streams over one connection |
| HTTP/3 | QUIC over UDP | avoids TCP head-of-line blocking, faster handshakes |

Head-of-line blocking: one blocked packet delays later data. HTTP/2 fixes application-level HOL but still has TCP-level HOL. HTTP/3/QUIC improves this.

## 9. HTTPS and TLS

TLS provides:
- encryption: hides content
- authentication: proves server identity via certificate
- integrity: detects tampering

### Simplified TLS handshake

```text
ClientHello: supported versions, ciphers, random
ServerHello: chosen cipher, certificate, key share
Client verifies certificate chain
Both derive shared session keys
Encrypted HTTP begins
```

Certificate chain: server cert -> intermediate CA -> root CA trusted by OS/browser.

## 10. Load balancing

| Type | Layer | Example |
|------|-------|---------|
| L4 | TCP/UDP | AWS NLB |
| L7 | HTTP | AWS ALB, nginx |

Algorithms:
- round robin
- least connections
- weighted round robin
- IP hash / sticky sessions
- latency-based routing

Health checks remove unhealthy backends from rotation.

## 11. Reverse proxy vs forward proxy

| Proxy | Sits near | Purpose |
|-------|-----------|---------|
| Forward proxy | client | hides/controls client access |
| Reverse proxy | server | routes/protects backend services |

nginx is commonly used as a reverse proxy for TLS termination, static files, compression, and routing.

## 12. NAT, private IPs, ports

Private IP ranges:
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

NAT maps private internal addresses to public external addresses.

Socket tuple:
```text
(source IP, source port, destination IP, destination port, protocol)
```

## 13. Latency and throughput

| Term | Meaning |
|------|---------|
| Latency | Time for one request |
| Throughput | Work completed per second |
| Bandwidth | Max data rate |
| RTT | Round-trip time |
| Jitter | Variation in latency |

Latency budget for web request:
```text
DNS + TCP + TLS + request transfer + server processing + response transfer + rendering
```

Ways to reduce latency:
- cache at browser/CDN/app
- keep connections alive
- compress responses
- reduce payload size
- move compute/data closer to user
- use async/background jobs
- optimize DB queries

## 14. Caching headers

| Header | Meaning |
|--------|---------|
| `Cache-Control` | main caching policy |
| `ETag` | content version identifier |
| `If-None-Match` | client asks if ETag changed |
| `Last-Modified` | timestamp |
| `Expires` | legacy expiry time |

`304 Not Modified` means client can use cached copy.

## 15. CORS

Same-origin policy blocks browser JS from reading responses from another origin unless server allows it.

Preflight occurs for non-simple requests:
```text
OPTIONS /api
Origin: https://app.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Authorization
```

Server responds with allowed origins/methods/headers.

Common bug: using `Access-Control-Allow-Origin: *` with credentials. Browsers reject this.

## 16. WebSockets, SSE, long polling

| Technique | Direction | Use |
|-----------|-----------|-----|
| Long polling | client repeatedly asks | fallback |
| SSE | server -> client | LLM token streaming, notifications |
| WebSocket | bidirectional | chat, multiplayer, live collaboration |

For LLM text streaming, SSE is usually simpler than WebSocket.

## 17. Network debugging commands

| Task | Command |
|------|---------|
| DNS lookup | `nslookup domain`, `dig domain` |
| Ping host | `ping host` |
| Trace route | `tracert host` on Windows, `traceroute host` on Linux |
| Test HTTP | `curl -v https://site.com` |
| Test port | `Test-NetConnection host -Port 443` on PowerShell |
| Show connections | `netstat -ano`, `ss -tulpen` |
| Find process on port | `netstat -ano | findstr :8000` |
| Packet capture | Wireshark, `tcpdump` |
| TLS check | `openssl s_client -connect host:443` |

## 18. Common production network failures

| Symptom | Likely cause |
|---------|--------------|
| DNS works locally but not for users | DNS propagation, resolver cache, wrong TTL |
| 502 Bad Gateway | reverse proxy cannot reach upstream |
| 503 Service Unavailable | backend overloaded/down or no healthy targets |
| 504 Gateway Timeout | upstream too slow or network timeout |
| TLS certificate error | expired cert, wrong hostname, missing intermediate |
| CORS error in browser only | missing/incorrect CORS headers |
| Intermittent timeout | packet loss, overloaded backend, connection pool exhaustion |
| High latency for distant users | no CDN/edge, region too far |

## 19. Interview questions

1. **What happens when you type google.com?** DNS -> TCP -> TLS -> HTTP request -> server response -> browser renders and fetches subresources.
2. **TCP vs UDP?** TCP is reliable, ordered, connection-oriented. UDP is connectionless, lower overhead, no delivery guarantee.
3. **Explain TCP 3-way handshake.** SYN, SYN-ACK, ACK establish connection and sequence numbers.
4. **HTTP vs HTTPS?** HTTPS is HTTP over TLS, adding encryption, integrity, and server authentication.
5. **What is DNS TTL?** How long resolvers cache a DNS record; lower before migrations.
6. **What is a load balancer?** Distributes traffic across healthy backend servers; L4 works at transport, L7 understands HTTP.
7. **HTTP/2 vs HTTP/3?** HTTP/2 multiplexes over TCP; HTTP/3 uses QUIC over UDP to reduce head-of-line blocking and speed handshakes.
8. **What is CORS?** Browser security mechanism where server opts into cross-origin access using headers.
9. **502 vs 504?** 502 means bad gateway/upstream error; 504 means gateway timed out waiting for upstream.
10. **How do you debug "site is down"?** Check DNS, ping/traceroute, TCP port, TLS cert, HTTP status, load balancer health, app logs, DB dependency.

## 20. Quick revision checklist

- [ ] Explain OSI and TCP/IP models.
- [ ] Explain what happens when a URL loads.
- [ ] Explain DNS records and TTL.
- [ ] Explain TCP vs UDP.
- [ ] Explain TCP handshake.
- [ ] Explain HTTP methods and status codes.
- [ ] Explain TLS certificate chain.
- [ ] Explain load balancer L4 vs L7.
- [ ] Explain CORS and preflight.
- [ ] Know network debugging commands.

