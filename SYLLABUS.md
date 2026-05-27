# Complete Syllabus - AI Engineer Interview Prep

**Target role:** AI Engineer / Applied AI Engineer / Senior IC at scalable-product platform companies  
**Target compensation:** 10+ LPA  
**Source:** Transcribed and expanded from handwritten notes, then prioritized for interview preparation

---

## How to Prioritize

Do not study every topic equally. For most AI Engineer interviews, the strongest return comes from DSA, Python, SQL, Transformers/LLMs, RAG, agents, backend APIs, deployment, and system design.

| Priority | Focus | Goal |
|---|---|---|
| P0 | DSA, Python, SQL, Transformers, RAG, agents, system design | Must be interview-ready |
| P1 | ML/DL fundamentals, Django/DRF, deployment, testing, security | Should be explainable and usable |
| P2 | CNNs, diffusion, RL, frontend depth, crypto math | Study based on company/role |

---

## 01 - CS Fundamentals

Foundational programming and data skills every backend/AI engineer is screened on.

| # | Topic | Why it matters |
|---|---|---|
| 1.1 | **DSA** - arrays, strings, hashmaps, stacks, queues, trees, graphs, heaps, tries, DP, recursion, two-pointer, sliding window, binary search | First round of almost every company. Target LeetCode Medium fluency. |
| 1.2 | **Python nuances** - GIL, mutable defaults, generators, decorators, context managers, `*args/**kwargs`, dunder methods, dataclasses, type hints, asyncio | AI/ML stack is Python-first; tricky behavior is often tested. |
| 1.3 | **OOP principles** - encapsulation, inheritance, polymorphism, abstraction, SOLID, composition vs inheritance, design patterns | Senior IC screens often test design judgment. |
| 1.4 | **SQL** - joins, group-by, window functions, CTEs, indexes, transactions, isolation levels, query optimization | Data work, analytics rounds, and backend interviews. |
| 1.5 | **DBMS** - normalization, ACID vs BASE, B+ tree vs LSM, sharding, replication, CAP theorem | Important for system design and data-heavy products. |
| 1.6 | **Operating Systems** - processes, threads, scheduling, virtual memory, synchronization, deadlocks, filesystems, I/O | Backend, systems, and senior IC interviews often test OS fundamentals. |
| 1.7 | **Computer Networks** - OSI/TCP-IP, DNS, TCP/UDP, HTTP, TLS, load balancing, CORS, debugging | Required for backend, deployment, and system design interviews. |
| 1.8 | **Data-science libraries** - NumPy, Pandas, Matplotlib/Seaborn, scikit-learn | ML interview baseline and take-home tasks. |

## 02 - ML & Deep Learning Foundations

| # | Topic | Why |
|---|---|---|
| 2.1 | **ML algorithms** - linear/logistic regression, decision trees, random forests, XGBoost, k-means, KNN, SVM, Naive Bayes, PCA | Classical ML is still asked, especially for applied roles. |
| 2.2 | **ML evaluation metrics** - precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, calibration, bias/variance, cross-validation | Needed to judge whether a model is actually useful. |
| 2.3 | **DL basics** - neurons, activation functions, backprop, loss functions, regularization, batch norm, dropout | Bedrock of DL interviews. |
| 2.4 | **Gradient descent** - SGD, momentum, Adam, AdamW, learning-rate schedules, vanishing/exploding gradients | Common "walk me through training" topic. |
| 2.5 | **Embeddings** - word2vec, GloVe, FastText, sentence embeddings, vector spaces, cosine similarity | RAG, search, recommendations, and clustering depend on this. |
| 2.6 | **NLP basics** - tokenization history, n-grams, TF-IDF, NER, POS, perplexity | Useful context before modern LLMs. |
| 2.7 | **CNNs** - convolutions, pooling, padding, stride, receptive field, LeNet, AlexNet, VGG | P2 unless the role includes vision. |
| 2.8 | **RNN / LSTM / GRU** - sequence modeling, BPTT, gating mechanisms | Historical context for transformers. |
| 2.9 | **ResNet** - residual connections, skip connections, deep network training | Foundational architecture pattern. |
| 2.10 | **UNet** - encoder-decoder, skip connections, segmentation, diffusion usage | P2 unless vision/diffusion is role-specific. |
| 2.11 | **Reinforcement Learning** - MDP, Q-learning, policy gradients, PPO, RLHF, DPO | Focus mainly on RLHF/DPO for LLM roles. |
| 2.12 | **Diffusion models** - forward/reverse process, DDPM, DDIM, latent diffusion, classifier-free guidance | Useful for generative AI and image/video roles. |

## 03 - Transformers & LLMs

Highest-priority section for AI Engineer roles.

| # | Topic | Why |
|---|---|---|
| 3.1 | **Transformers + attention** - Q/K/V, scaled dot-product attention, multi-head attention, positional encoding, RoPE, ALiBi, encoder vs decoder | Core architecture. Expect deep questions. |
| 3.2 | **BERT family** - masked LM, NSP, fine-tuning, bidirectional attention, `[CLS]`, `[SEP]`, RoBERTa, DistilBERT | Encoder model foundation. |
| 3.3 | **GPT family** - autoregressive generation, causal masking, decoder-only architecture, pretraining vs instruction tuning | Decoder model foundation. |
| 3.4 | **Tokenizers** - BPE, WordPiece, SentencePiece, Unigram, special tokens, vocab size tradeoffs | Frequently asked in LLM interviews. |
| 3.5 | **MoE** - sparse experts, routing, load balancing, Switch Transformer, Mixtral-style designs | Important for understanding modern frontier models. |
| 3.6 | **RAG + HNSW** - embedding stores, FAISS, Pinecone, Weaviate, pgvector, HNSW vs IVF, chunking, reranking, hybrid search | Most common LLM application pattern. |
| 3.7 | **LLM evaluation** - hallucination checks, faithfulness, context precision/recall, golden datasets, human eval, LLM-as-judge risks | Critical for production AI systems. |
| 3.8 | **KV-cache and inference** - what gets cached, memory math, paged attention, prefix caching, speculative decoding | Important for latency, throughput, and cost. |
| 3.9 | **Fine-tuning** - full fine-tuning, LoRA, QLoRA, PEFT, instruction tuning, RLHF, DPO, data preparation | Most-asked applied LLM skill. |
| 3.10 | **Prompt engineering** - system/developer/user message roles, few-shot prompting, structured outputs, JSON mode, prompt injection risks | Practical skill for LLM app interviews. |
| 3.11 | **Scaling laws** - Kaplan, Chinchilla, compute-optimal training, data quality, model size vs tokens | Useful for whiteboard discussion. |
| 3.12 | **Latest AI models** - OpenAI, Anthropic, Google Gemini, Meta Llama, DeepSeek, Mistral, open-source trends | Verify close to the interview date; do not rely on stale model names. |

## 04 - AI Agents

| # | Topic | Why |
|---|---|---|
| 4.1 | **Agent architecture & design** - ReAct, Plan-and-Execute, Reflexion, single-agent vs multi-agent, graph-based agents | Hot topic in applied AI hiring. |
| 4.2 | **Tools + MCP** - tool calling, schemas, MCP servers/clients, stdio/SSE/HTTP transports | Important for modern tool-using AI systems. |
| 4.3 | **StateGraph / DAG / LangGraph** - nodes, edges, conditional routing, state, checkpointing | Common production agent pattern. |
| 4.4 | **Pydantic schemas** - structured outputs, validation, function-calling schemas, v1 vs v2 | Required for reliable tool use. |
| 4.5 | **Memory management** - context memory, vector memory, episodic vs semantic memory, summarization | Multi-turn agent requirement. |
| 4.6 | **Context window management** - limits, sliding windows, compaction, attention cost, retrieval vs context stuffing | Needed for long-running workflows. |
| 4.7 | **Tool-calling loop** - agent loop, max iterations, retries, early stopping, failure handling | Core implementation detail. |
| 4.8 | **Rate limiting** - token bucket, leaky bucket, per-user/per-tenant quotas, 429 handling, exponential backoff | Production hygiene. |
| 4.9 | **Guardrails** - input/output filters, prompt injection defense, jailbreak resistance, allowlists, policy checks | Safety and security topic. |
| 4.10 | **Sandbox environments + HITL** - code execution sandboxes, approval gates, human review, audit logs | Required for high-risk agent actions. |
| 4.11 | **Agent observability** - traces, tool logs, token usage, latency, cost, failure categories, replay/debug workflows | Often separates prototype answers from production answers. |

## 05 - Backend (Django)

| # | Topic | Why |
|---|---|---|
| 5.1 | **Django basics** - MVT pattern, settings, apps, URL routing, `manage.py` | Resume and project discussion baseline. |
| 5.2 | **HTTP request/response** - methods, status codes, headers, REST principles | Universal backend knowledge. |
| 5.3 | **WebSockets** - Django Channels, ASGI, pub/sub, real-time events | Useful for chat, streaming, and live updates. |
| 5.4 | **Middleware** - request/response processing, custom middleware, ordering | Auth, logging, and CORS often live here. |
| 5.5 | **Models & schemas** - ORM, Meta, managers, migrations, relations | Data layer. |
| 5.6 | **Views** - FBV vs CBV, DRF generic views, viewsets | API implementation. |
| 5.7 | **Permissions & JWT** - DRF permissions, SimpleJWT, refresh tokens, blacklisting | Auth interviews. |
| 5.8 | **Serializers** - DRF serializers, ModelSerializer, validation, nested serializers | API contracts and validation. |
| 5.9 | **Async/await in ASGI** - async views, `sync_to_async`, when to use, gotchas | Performance topic. |
| 5.10 | **Rate limiting** - DRF throttling, django-ratelimit, Redis-backed throttles | Production hygiene. |
| 5.11 | **django-admin** - registering models, custom admin, `list_display`, filters, inlines | Common practical demo. |
| 5.12 | **Backend observability** - logs, metrics, traces, error tracking, request IDs | Important for production debugging. |

## 06 - Frontend

| # | Topic | Why |
|---|---|---|
| 6.1 | **HTML/CSS/JS basics + Tailwind** - semantic HTML, flex/grid, ES6, fetch, promises, async/await | Full-stack screening baseline. |
| 6.2 | **DOM** - selectors, events, event delegation, bubbling vs capturing | Vanilla JS basics. |
| 6.3 | **React basics** - SPA, JSX, components, props, virtual DOM, reconciliation | Default framework knowledge. |
| 6.4 | **Hooks & state** - useState, useEffect, useMemo, useCallback, useRef, useContext, useReducer, custom hooks | React interview core. |
| 6.5 | **React Router** - routes, dynamic params, nested routes, loaders | Routing. |
| 6.6 | **React Query / caching** - TanStack Query, stale-while-revalidate, mutations, optimistic updates | API integration. |
| 6.7 | **Local/session storage** - when to use, XSS/security implications | Persistence and security. |
| 6.8 | **Partial loading** - lazy loading, code splitting, Suspense, skeleton UIs | Performance round. |
| 6.9 | **Streaming AI UX** - token streaming, cancel/retry, loading states, partial responses, error recovery | Useful for AI product roles. |

## 07 - Deployment, Cloud & MLOps

| # | Topic | Why |
|---|---|---|
| 7.1 | **AWS core** - EC2, S3, RDS, Lambda, IAM | Universal cloud baseline. |
| 7.2 | **Load balancing / nginx / reverse proxy** - ALB vs NLB, nginx, TLS termination | System design and deployment. |
| 7.3 | **IAM and network security** - IAM users/roles, security groups, inbound/outbound rules, least privilege | Cloud security baseline. |
| 7.4 | **CDN** - CloudFront, edge caching, cache invalidation | Performance and cost. |
| 7.5 | **Docker** - images vs containers, Dockerfile, layers, registry, `.dockerignore` | Mandatory practical skill. |
| 7.6 | **docker-compose / YAML** - multi-service local dev, volumes, networks | Local workflow and demos. |
| 7.7 | **SSH/Linux commands** - file transfer, key-based auth, permissions, env vars, process management | Practical deployment work. |
| 7.8 | **Networking basics** - OSI, TCP/UDP, DNS, latency, SSL/TLS, certificates | Always asked in backend/system design. |
| 7.9 | **MLOps basics** - experiment tracking, model registry, model serving, data drift, feature stores, rollback | Useful for ML and AI platform roles. |
| 7.10 | **LLM production operations** - prompt/version tracking, caching, retries, fallback models, token/cost monitoring | Required for production GenAI systems. |

## 08 - Version Control & Testing

| # | Topic | Why |
|---|---|---|
| 8.1 | **Git + GitHub** - commit, branch, merge, rebase, cherry-pick, stash, reset vs revert | Daily engineering tool. |
| 8.2 | **.gitignore + workflows** - patterns, GitHub Actions basics | Repo hygiene and CI. |
| 8.3 | **Merge conflicts** - resolution strategies, ours/theirs, three-way merge | Live coding and team workflow. |
| 8.4 | **Unit testing** - pytest, unittest, mocking, fixtures, parametrize | Quality round. |
| 8.5 | **Integration testing + Postman** - happy/sad paths, environments, collections | API testing. |
| 8.6 | **E2E + browser automation** - Selenium, Cypress, Playwright | Senior engineering signal. |
| 8.7 | **Django tests** - TestCase, Client, factory_boy, fixtures | Backend role baseline. |
| 8.8 | **AI system testing** - golden test sets, regression evals, prompt tests, RAG evals, toxicity/safety tests | Critical for LLM applications. |

## 09 - System Design & Security

| # | Topic | Why |
|---|---|---|
| 9.1 | **System design / API design** - REST vs GraphQL vs gRPC, idempotency, versioning, pagination, caching layers | Senior IC round. |
| 9.2 | **AI system design** - chat app, RAG service, agent platform, document QA, embedding pipeline, async workers | Directly relevant to AI Engineer interviews. |
| 9.3 | **Scalability patterns** - queues, workers, fanout, backpressure, caching, horizontal scaling, database partitioning | Needed for realistic architecture answers. |
| 9.4 | **HLD** - requirements, capacity estimates, APIs, data model, cache/queue/DB choices, bottlenecks, tradeoffs | Required for system design rounds. |
| 9.5 | **LLD** - classes, interfaces, SOLID, design patterns, object relationships, edge cases, code skeletons | Required for OOP/design rounds. |
| 9.6 | **Inheritance** - single vs multiple inheritance, MRO in Python, mixins, when to compose instead | OOP deep dive. |
| 9.7 | **Encryption** - symmetric vs asymmetric encryption, TLS handshake, key exchange | Security round. |
| 9.8 | **Hashing** - MD5/SHA family, password hashing, bcrypt/scrypt/argon2, salt, HMAC | Auth and security round. |
| 9.9 | **CORS** - same-origin policy, preflight requests, headers, common pitfalls | Frontend/backend integration. |
| 9.10 | **SSL/TLS** - versions, certificate chain, mTLS, certificate authorities | Networking and security. |
| 9.11 | **RSA** - intuition for `n`, `e`, `d`, phi(n), key generation, signing vs encryption | Classic crypto question; keep practical. |
| 9.12 | **LLM security** - prompt injection, data exfiltration, unsafe tool calls, secrets handling, tenant isolation | Required for production AI systems. |

## 10 - Behavioral, Projects & Job Search

| # | Topic | Why |
|---|---|---|
| 10.1 | **Project storytelling** - problem, constraints, architecture, tradeoffs, metrics, failures, impact | Most interviews include project deep dives. |
| 10.2 | **Behavioral questions** - conflict, ownership, ambiguity, missed deadline, hard bug, leadership, feedback | Needed for HR and senior IC rounds. |
| 10.3 | **Resume alignment** - map every resume bullet to a technical explanation, metric, and follow-up question | Prevents shallow project answers. |
| 10.4 | **Mock interviews** - DSA, ML/LLM, system design, behavioral | Converts passive revision into interview performance. |
| 10.5 | **Job-search playbook** - cold emails, LinkedIn, referrals, startup leads | See [JOB-SEARCH/playbook.md](JOB-SEARCH/playbook.md). |

---

## Suggested 6-Week Revision Plan

| Week | Focus |
|---|---|
| Week 1 | DSA patterns, Python nuances, SQL |
| Week 2 | ML basics, evaluation metrics, embeddings, DL basics |
| Week 3 | Transformers, tokenizers, fine-tuning, LLM evaluation |
| Week 4 | RAG, agents, tool calling, guardrails, AI system testing |
| Week 5 | Django/DRF, deployment, Docker, testing, observability |
| Week 6 | System design, AI architecture case studies, behavioral/project mocks |

DSA should run in parallel throughout: target 1-2 LeetCode Medium problems per day, with emphasis on patterns rather than random problem solving.

