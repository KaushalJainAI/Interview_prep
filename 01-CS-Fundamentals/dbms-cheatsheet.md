# DBMS -- Interview Cheatsheet

## Normalization (memorize the forms)

| Form | Rule | Example violation |
|------|------|-------------------|
| **1NF** | Atomic columns, no repeating groups | `tags = "red,blue,green"` in one cell |
| **2NF** | 1NF + no partial dep on composite key | Order_items table: product_name depends on product_id, not the composite (order_id, product_id) |
| **3NF** | 2NF + no transitive deps | `user.zip_code -> user.city` -> move city to a Zip table |
| **BCNF** | Stronger 3NF -- every determinant is a candidate key | Rare violations in practice |

**When to denormalize**: read-heavy hot paths, write-once analytics tables. Caching reduces the need.

## ACID
- **Atomicity** -- all-or-nothing transactions
- **Consistency** -- transitions from valid state to valid state (constraints, FK, triggers)
- **Isolation** -- concurrent txns don't see each other's intermediate state
- **Durability** -- committed data survives crashes

## Isolation levels (recap from SQL sheet)
| Level | Dirty | Non-repeat | Phantom |
|-------|-------|------------|---------|
| Read Uncommitted |  |  |  |
| Read Committed (PG default) |  |  |  |
| Repeatable Read (MySQL default) |  |  | ~ |
| Serializable |  |  |  |

## CAP theorem
In a network partition, you can have **only two of three**:
- **C**onsistency (linearizable reads/writes)
- **A**vailability (every request gets a response)
- **P**artition tolerance (system survives network splits)

Real systems: partitions are unavoidable -> pick **CP** (HBase, MongoDB) or **AP** (Cassandra, DynamoDB).

### PACELC (refinement)
- During Partition: choose A or C
- Else (normal): choose Latency or Consistency
- e.g. Cassandra = PA/EL, Postgres = PC/EC

## BASE (NoSQL philosophy)
- **B**asically Available
- **S**oft state (data may change without input)
- **E**ventual consistency

## Indexes -- deep dive

### B-tree (most common)
- Self-balancing, multi-way search tree
- Postgres / MySQL default
- Good for: equality, range, ORDER BY, prefix matches on composite
- Bad for: leading wildcard LIKE, function on column

### B+ tree (variant)
- All values in leaf nodes, internal nodes have only keys
- Leaves linked -> fast range scans
- Postgres + MySQL InnoDB use B+ trees

### Hash index
- O(1) equality lookup, no range
- Postgres has `USING hash`, less commonly used

### LSM tree (log-structured merge)
- Write-optimized: append to memtable, flush to sorted runs, merge in background
- Used by: Cassandra, RocksDB, LevelDB, ScyllaDB, BigTable
- Trade: writes very fast, reads slower (must check multiple levels), needs compaction

### B-tree vs LSM (the comparison)
| Aspect | B-tree | LSM |
|--------|--------|-----|
| Reads | Fast (1 seek to leaf) | Slower (check memtable + multiple SSTables) |
| Writes | In-place, slower | Append-only, very fast |
| Space | Pages may have holes | Compaction needed; can have write amplification |
| Best for | OLTP, mixed workloads | Write-heavy (logs, time-series, metrics) |

### Other index types (Postgres)
- **GIN** -- inverted index for JSONB, arrays, full-text
- **GiST** -- generalized search tree for geo, ranges
- **BRIN** -- block-range index; tiny, good for naturally-ordered data
- **Hash** -- equality only

## Sharding (horizontal partitioning)
- **Range** -- keys 0-1M on shard A, 1M-2M on shard B. Risk: hot spots
- **Hash** -- `hash(key) % N` -> uniform, but resharding hurts
- **Consistent hashing** -- ring; adding nodes re-shards only ~1/N keys. Used in DynamoDB, Cassandra, Redis Cluster
- **Directory-based** -- lookup table; flexible, central SPOF

## Replication
- **Synchronous** -- primary waits for replicas before ack -> strong consistency, higher latency
- **Asynchronous** -- primary acks immediately, replicates in background -> eventual consistency, low latency, replicas may lag
- **Quorum (Cassandra, Dynamo)** -- write W replicas, read R replicas; if W+R > N -> strong consistency
- **Multi-primary** -- anywhere writes; conflicts resolved via CRDTs or last-write-wins

## NoSQL families
| Type | Examples | Best for |
|------|----------|----------|
| **Document** | MongoDB, DynamoDB doc, Postgres JSONB | Flexible schema, nested data |
| **Key-value** | Redis, DynamoDB, Memcached | Cache, simple lookups |
| **Wide-column** | Cassandra, ScyllaDB, BigTable, HBase | Time-series, massive write throughput |
| **Graph** | Neo4j, Memgraph, Neptune | Relationships, recommendations, fraud |
| **Search** | Elasticsearch, OpenSearch | Full-text, faceted search, logs |
| **Vector** | pgvector, Qdrant, Pinecone, Weaviate | Embeddings, semantic search |
| **Time-series** | TimescaleDB, Influx, Prometheus | Metrics, IoT, financial |

## Transactions in distributed systems
- **2PC (two-phase commit)** -- coordinator asks all participants to prepare, then commits. Blocks if coordinator crashes.
- **Saga** -- break transaction into smaller local transactions with compensating actions on failure. Used in microservices.
- **Outbox pattern** -- write event + business data in the same DB transaction; publisher reads outbox table -> events to message bus. Solves "DB committed but message not sent" problem.

## Common pitfalls / interview material
- **N+1 query** -- fix with joins / batch fetch (`select_related`, `prefetch_related`)
- **Missing index** -- `EXPLAIN ANALYZE` to detect
- **Index bloat in Postgres** -- periodic `REINDEX` / `pg_repack`
- **VACUUM** in Postgres -- reclaims dead tuples; tune autovacuum or it lags behind on write-heavy tables
- **Deadlocks** -- lock acquisition order matters; always order consistently
- **Long-running txns** hold locks + bloat -- keep short
- **Schema migrations on big tables** -- add column NULL -> backfill in batches -> set NOT NULL; never block writes

## Interview one-liners
- *ACID?* Atomic, Consistent, Isolated, Durable. RDBMS guarantees for txns.
- *CAP?* In a partition, choose C or A. Modern systems all are P; the real choice is A vs C.
- *3NF in plain English?* No column depends on a non-key column.
- *B-tree vs LSM?* B-tree = fast reads, slower writes (OLTP). LSM = fast writes, slower reads (logs / time-series).
- *Why is Cassandra eventually consistent?* AP system -- prioritizes availability under partitions. Reads at QUORUM trade some availability for consistency.
- *Sharding strategy?* Hash for even distribution; range for ordered access; consistent hashing if you'll add nodes. Best: keep all related data on one shard (single-tenant or single-user queries don't need cross-shard joins).
- *Read replicas -- when not?* Reads needing strong consistency must hit primary (account balance after a deposit).
- *Outbox pattern?* Atomic insert of business row + event row -> background publisher -> message bus. Solves dual-write inconsistency.

## NGU + AIAAS interview anchors
- **NGU**: Postgres (RDS) for OLTP, Redis for cache, S3 for media. Possible read replicas for product catalog at scale. Cache invalidation via Django signals = pragmatic eventual consistency (within ~ms).
- **AIAAS**: Postgres stores plans + workflow runs + state snapshots -- durable, transactional. Redis = ephemeral queue + heartbeats + WebSocket pub/sub. Versioned plans = no migration risk for in-flight runs.
