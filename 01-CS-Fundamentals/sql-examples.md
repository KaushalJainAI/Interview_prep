# SQL -- Worked Query Examples

> Companion to [sql-cheatsheet.md](sql-cheatsheet.md). Realistic schemas + queries with explanations.

## Schema for these examples
```sql
users(id PK, email, name, country, signup_date)
products(id PK, name, category_id FK, price, stock, active)
categories(id PK, name, slug)
orders(id PK, user_id FK, total, status, created_at)
order_items(id PK, order_id FK, product_id FK, qty, unit_price)
```

## 1. Multi-join with aggregation
**Q**: Top 5 categories by revenue last 30 days.

```sql
SELECT  c.name,
        SUM(oi.qty * oi.unit_price) AS revenue
FROM    order_items oi
JOIN    products  p ON p.id = oi.product_id
JOIN    categories c ON c.id = p.category_id
JOIN    orders o ON o.id = oi.order_id
WHERE   o.created_at >= NOW() - INTERVAL '30 days'
  AND   o.status = 'completed'
GROUP BY c.id, c.name
ORDER BY revenue DESC
LIMIT 5;
```

**Explanation**: `WHERE` filters orders by date+status; `GROUP BY` aggregates per category; `ORDER BY ... LIMIT` ranks. Note `c.id` in GROUP BY (safer than name alone in case of duplicates).

## 2. Window function -- running total
**Q**: For each user, list orders with running total spend.

```sql
SELECT  user_id,
        created_at,
        total,
        SUM(total) OVER (
            PARTITION BY user_id
            ORDER BY created_at
        ) AS running_total
FROM    orders
WHERE   status = 'completed';
```

**Explanation**: `OVER (PARTITION BY user_id ORDER BY created_at)` says "compute the sum per user, ordered by time, including the current row". No GROUP BY collapse -- each row stays.

## 3. RANK / ROW_NUMBER -- top N per group
**Q**: 3 highest-spend orders per user.

```sql
WITH ranked AS (
    SELECT  *,
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total DESC) AS rn
    FROM    orders
)
SELECT user_id, total, created_at
FROM   ranked
WHERE  rn <= 3;
```

**Why ROW_NUMBER over RANK?**
- `ROW_NUMBER`: 1, 2, 3, 4 (always distinct)
- `RANK`: 1, 2, 2, 4 (ties get same rank, then skip)
- `DENSE_RANK`: 1, 2, 2, 3 (ties get same rank, no skip)

## 4. LAG/LEAD -- period-over-period change
**Q**: For each month, total revenue + change vs prior month.

```sql
WITH monthly AS (
    SELECT  date_trunc('month', created_at) AS month,
            SUM(total) AS revenue
    FROM    orders
    WHERE   status = 'completed'
    GROUP BY month
)
SELECT  month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS prev,
        revenue - LAG(revenue) OVER (ORDER BY month) AS delta,
        ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
              / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS pct_change
FROM    monthly
ORDER BY month;
```

`NULLIF(x, 0)` returns NULL when x = 0, preventing divide-by-zero.

## 5. Self-join -- find users who placed orders within 1 hour of each other
```sql
SELECT  a.user_id AS u1, b.user_id AS u2,
        a.created_at, b.created_at
FROM    orders a
JOIN    orders b
  ON    a.id < b.id                              -- avoid duplicate pairs
 AND    b.created_at BETWEEN a.created_at AND a.created_at + INTERVAL '1 hour'
WHERE   a.user_id <> b.user_id;
```

## 6. Recursive CTE -- category tree
**Schema**: `categories(id, parent_id, name)`. Get the full path from root to each category.

```sql
WITH RECURSIVE tree AS (
    -- anchor: roots
    SELECT id, parent_id, name, name::text AS path, 1 AS depth
    FROM   categories
    WHERE  parent_id IS NULL

    UNION ALL

    -- recursive step
    SELECT c.id, c.parent_id, c.name,
           t.path || ' > ' || c.name,
           t.depth + 1
    FROM   categories c
    JOIN   tree t ON c.parent_id = t.id
)
SELECT path, depth FROM tree ORDER BY path;
```

Output:
```
Spices                          1
Spices > Whole                  2
Spices > Whole > Black Pepper   3
Spices > Ground                 2
```

## 7. Upsert (Postgres)
**Q**: Insert a product; if SKU already exists, update the price + stock.
```sql
INSERT INTO products (sku, name, price, stock)
VALUES ('HALDI-100', 'Turmeric 100g', 99.0, 250)
ON CONFLICT (sku) DO UPDATE
SET price = EXCLUDED.price,
    stock = EXCLUDED.stock + products.stock,    -- add to existing stock
    updated_at = NOW();
```

`EXCLUDED.col` refers to the row that would have been inserted; `products.col` refers to the existing row.

## 8. Pagination -- cursor over offset
**Bad** (slow on large tables):
```sql
SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 100000;
-- Postgres must scan 100020 rows to discard 100000
```

**Good** (cursor -- uses index):
```sql
SELECT * FROM products
WHERE  id > :last_seen_id
ORDER BY id
LIMIT 20;
```

`:last_seen_id` = the last `id` from the previous page. Index seek, O(log n) per page.

## 9. Find duplicates
```sql
SELECT email, COUNT(*) AS n
FROM   users
GROUP BY email
HAVING COUNT(*) > 1;
```

To find specific duplicate rows:
```sql
SELECT *
FROM   users
WHERE  email IN (
    SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
)
ORDER BY email, id;
```

## 10. Delete duplicates (keep oldest)
```sql
DELETE FROM users a
USING  users b
WHERE  a.email = b.email
  AND  a.id   >  b.id;          -- a is the newer duplicate; b is the original
```

## 11. Conditional aggregation (pivot)
**Q**: Number of completed vs pending orders per user.

```sql
SELECT  user_id,
        COUNT(*) FILTER (WHERE status = 'completed') AS completed,
        COUNT(*) FILTER (WHERE status = 'pending')   AS pending,
        SUM(total) FILTER (WHERE status = 'completed') AS revenue
FROM    orders
GROUP BY user_id;
```

`FILTER (WHERE ...)` is the cleanest pivot syntax in Postgres. MySQL: use `SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)`.

## 12. NULL handling -- gotcha
```sql
SELECT * FROM users WHERE country = 'India';
-- Does NOT return rows where country IS NULL, even though NULL != 'India' is "true" intuitively
```

NULL comparisons return UNKNOWN, never TRUE. Use:
```sql
WHERE country IS NULL
WHERE country IS NOT DISTINCT FROM 'India'      -- treats NULL = NULL as true
```

## 13. EXPLAIN ANALYZE walkthrough
```sql
EXPLAIN ANALYZE
SELECT * FROM products WHERE category_id = 5 ORDER BY price LIMIT 20;
```

Output (simplified):
```
Limit (cost=... rows=20 actual time=0.05..0.07 rows=20)
  -> Index Scan using idx_products_category_price on products
    (cost=... rows=1500 actual time=0.04..0.06)
    Index Cond: (category_id = 5)
Planning Time: 0.1ms
Execution Time: 0.08ms
```

**What to look for**:
- **Seq Scan** on a big table -> missing index
- `actual rows` vs `estimated rows` differ wildly -> ANALYZE the table, stats are stale
- **Nested Loop** with high outer/inner rows -> consider hash join (raise `work_mem`)
- **Sort** in memory vs disk (`Disk: 100MB`) -> raise `work_mem` or add an index that pre-orders

## 14. Index design
**Q**: Best index for the listing query in §1?

Query needs `o.status='completed'`, `o.created_at >= X`, joined to items. The hot filter is `(status, created_at)`:
```sql
CREATE INDEX idx_orders_status_created ON orders (status, created_at);
-- partial index -- even better if most rows aren't 'completed':
CREATE INDEX idx_orders_completed_created
ON orders (created_at) WHERE status = 'completed';
```

**Composite index leftmost-prefix rule**: index `(a, b, c)` supports queries filtering on `a`, `(a, b)`, `(a, b, c)` -- NOT `b` alone or `(b, c)` alone.

## 15. Transactions -- money transfer
```sql
BEGIN;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- consistency check (race-condition-safe under SERIALIZABLE)
SELECT 1 FROM accounts WHERE id = 1 AND balance < 0;
-- if this returns a row, ROLLBACK
COMMIT;
```

For high concurrency, prefer:
```sql
SELECT id, balance FROM accounts WHERE id IN (1, 2) FOR UPDATE;
-- explicit row lock; both rows locked in consistent order
```

**Always lock rows in a deterministic order** (e.g. by ascending id) to avoid deadlocks.

## NGU interview anchor
> "On NGU's home page, the product listing query joins products + categories + reviews with filters on `active=true` and category. I added a covering index `(active, category_id) INCLUDE (id, name, price, slug)` -- Postgres index-only scan, p99 dropped from ~80ms to ~3ms. EXPLAIN ANALYZE was my best friend. After that, Redis caches the response so most requests don't even hit Postgres."
