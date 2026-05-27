# SQL -- Interview Cheatsheet

## Joins (always asked)
```
A  INNER JOIN B  ON ... -> only matching rows
A  LEFT  JOIN B  ON ... -> all of A + matching B (nulls if none)
A  RIGHT JOIN B  ON ... -> all of B + matching A
A  FULL  JOIN B  ON ... -> all of both
A CROSS  JOIN B       -> Cartesian product
```
Visual mental model: Venn diagrams of which side keeps unmatched rows.

## Aggregations
```sql
SELECT category, COUNT(*) AS n, AVG(price) AS avg_price
FROM products
WHERE active = true
GROUP BY category
HAVING COUNT(*) > 5
ORDER BY avg_price DESC
LIMIT 10;
```

## Order of execution (logical) -- surprising!
```
FROM -> JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT
```
That's why you can't reference a SELECT alias in WHERE but you can in ORDER BY.

## Window functions (senior-IC essential)
```sql
SELECT
  user_id,
  order_total,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn,
  SUM(order_total) OVER (PARTITION BY user_id) AS total_per_user,
  LAG(order_total) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_order,
  AVG(order_total) OVER (ORDER BY created_at ROWS 6 PRECEDING) AS rolling_7
FROM orders;
```
Common window fns: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, `SUM/AVG/COUNT OVER`, `NTILE`.

## CTEs (readable!)
```sql
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '30 days'
),
high_value AS (
  SELECT user_id FROM recent_orders WHERE total > 1000
)
SELECT * FROM users WHERE id IN (SELECT user_id FROM high_value);
```
- Recursive CTE for trees/graphs:
```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id, name, 1 AS depth FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.parent_id, c.name, t.depth + 1
  FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree;
```

## Indexes
- **B-tree** (default): equality, range, ORDER BY
- **Hash** (Postgres): equality only, no range
- **GIN/GiST** (Postgres): JSONB, arrays, full-text, geo
- **Composite** `(a, b, c)`: usable for `WHERE a=`, `WHERE a= AND b=`, etc. (leftmost prefix)
- **Partial**: `CREATE INDEX ... WHERE active = true` (smaller, faster)
- **Covering**: includes all SELECT columns -> index-only scan

### When index doesn't help
- High-cardinality column with low selectivity
- `LIKE '%foo'` (leading wildcard) -- use trigram index instead
- Functions on columns: `WHERE LOWER(email) = ...` -> create functional index
- OR conditions across different columns -- DB may scan instead

## Transactions & isolation levels
| Level | Dirty read | Non-repeatable read | Phantom read |
|-------|-----------|---------------------|--------------|
| Read uncommitted |  allowed |  |  |
| Read committed (Postgres default) |  |  |  |
| Repeatable read (MySQL default) |  |  |  (mostly) |
| Serializable |  |  |  |

- Use `SERIALIZABLE` for money / inventory; expect occasional retries.
- `SELECT ... FOR UPDATE` for row-level pessimistic lock.

## ACID vs BASE
- **ACID** (RDBMS): Atomic, Consistent, Isolated, Durable
- **BASE** (NoSQL): Basically Available, Soft state, Eventual consistency
- CAP theorem: in a partition, choose Consistency or Availability -- can't have both

## Query optimization
- **EXPLAIN ANALYZE** is your friend (Postgres). Look for:
  - Sequential scans on big tables -> missing index
  - Nested loop with high row counts -> consider hash join
  - Slow filter that should be a join condition
- **Don't `SELECT *`** in production -- fetches unused columns
- **Use LIMIT** for pagination; cursor pagination > offset on big tables
- **Batch inserts**: `INSERT INTO t VALUES (...), (...), (...)` >> N single inserts
- **Avoid N+1**: prefetch related (Django: `select_related`, `prefetch_related`)

## Useful patterns

### Top-N per group
```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
) t WHERE rn <= 3;
```

### Upsert (Postgres)
```sql
INSERT INTO products (sku, price) VALUES ('A1', 99)
ON CONFLICT (sku) DO UPDATE SET price = EXCLUDED.price;
```

### Cumulative sum / running total
```sql
SELECT date, amount, SUM(amount) OVER (ORDER BY date) AS running_total FROM ...;
```

### Delete duplicates
```sql
DELETE FROM t WHERE ctid NOT IN (
  SELECT MIN(ctid) FROM t GROUP BY natural_key
);
```

## Interview one-liners
- *Join order matters?* Logically no, but in optimizer planning yes for big tables -- start with the most-selective.
- *Why does adding an index slow writes?* Each insert/update/delete must update the index too.
- *When NOT to index?* Tiny tables, very low cardinality, write-heavy + rarely-queried column.
- *N+1?* Loop fires 1+N queries (1 list, N detail). Fix with JOIN or batched IN clause.
- *Index-only scan?* Query reads only from index, never visits the table -- fastest possible. Need covering index + visibility map up to date.
- *Why CTE > subquery sometimes?* Readability; in Postgres 12+, CTEs are inlined by default (no fence).
- *Isolation level for money transfer?* Serializable, with retry on serialization failure.

## NGU interview anchor
> "On NGU, product listings hit Postgres millions of times. The two wins were: (1) covering indexes on `(category_id, active, sort_order)` for the catalog page so it's an index-only scan, and (2) Redis caching with signal-based invalidation so Postgres only sees uncached requests. EXPLAIN ANALYZE showed the home-page query went from 80ms to 4ms after the covering index, then to <1ms once Redis was in front."
