"""Inject diagrams + an appendix of comprehensive supplemental content into dsa-cheatsheet.md."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

CHEAT = ROOT / "dsa-cheatsheet.md"

EXTRA = r"""

---

# 📈 Visual appendix

## Big-O growth curves
![Big-O growth curves](dsa-patterns/diagrams/00-complexity-curves.png)

For n = 10⁵ on a 10⁸-op/s machine: O(n²) ≈ 10¹⁰ ops ≈ 100s ❌. O(n log n) ≈ 1.6·10⁶ ops ≈ 16 ms ✓. Memorise the table.

## Data structure choice matrix
![DS matrix](dsa-patterns/diagrams/00-ds-choice.png)

## Pattern → which file to study
| Problem keyword | Pattern | File |
|-----------------|---------|------|
| "pair sums to target", "complement", "anagram" | Arrays & Hashing | dsa-patterns/01 |
| "sorted array", "two pointers", "in-place dedup" | Two Pointers | 02 |
| "longest/shortest subarray/substring with property" | Sliding Window | 03 |
| "sorted", "find min in rotated", "min capacity such that …" | Binary Search | 04 |
| "balanced parens", "next greater", "histogram rectangle" | Stack | 05 |
| "reverse list", "cycle", "kth from end" | Linked List | 06 |
| "tree traversal", "LCA", "validate BST" | Trees | 07 |
| "autocomplete", "shared prefix" | Tries | 08 |
| "kth largest", "merge K", "running median" | Heap | 09 |
| "all subsets/permutations", "N-queens", "sudoku" | Backtracking | 10 |
| "shortest path on grid/graph", "topo sort", "MST" | Graphs | 11 |
| "fibonacci-like", "house robber", "coin change" | 1-D DP | 12 |
| "LCS", "edit distance", "unique paths" | 2-D DP | 13 |
| "earliest finishing", "jump game", "gas station" | Greedy | 14 |
| "overlap", "merge intervals", "meeting rooms" | Intervals | 15 |
| "XOR", "single number", "bits" | Bit Manipulation | 16 |
| "rotate matrix", "spiral", "pow(x,n)" | Math & Geometry | 17 |

---

# 🧭 30-second decision tree

```
                    Is input SORTED or can you SORT?
                    ┌─────── yes ───────┐         ┌────── no ──────┐
                    ▼                                 ▼
            two-pointer / binary search          hash map / heap
                    │
        ┌── monotone predicate? ──┐
        yes                       no
        ▼                         ▼
    binary search on answer    two-pointer scan

                Need ALL subsets / permutations / paths?  → Backtracking
                Optimal substructure + overlap?           → DP
                Graph / grid traversal?                   → BFS/DFS
                Streaming / "top K" / "k-th"?             → Heap
```

---

# 🧮 Master complexity reference (with derivation)

| Operation | Vec/Array | Linked list | Hashmap | BST balanced | Heap | Trie (len m) |
|-----------|-----------|-------------|---------|--------------|------|--------------|
| Index | O(1) | O(n) | — | — | — | — |
| Search by key | O(n) | O(n) | **O(1) avg** | O(log n) | O(n) | O(m) |
| Insert at end | O(1)* | O(1) | O(1) | O(log n) | O(log n) | O(m) |
| Insert at front | O(n) | O(1) | — | — | — | — |
| Delete | O(n) | O(1) given node | O(1) | O(log n) | O(log n) | O(m) |
| Min / Max | O(n) | O(n) | O(n) | O(log n) | **O(1)** | — |
| Range / sorted scan | O(n log n) | O(n) (after sort) | O(n) | **O(n)** | O(n log n) | — |
| Membership | O(n) | O(n) | **O(1)** | O(log n) | O(n) | O(m) |

*amortised; resize doubles capacity.

---

# 🧠 30 high-frequency micro-snippets

```python
# 1. Reverse string
s[::-1]

# 2. Reverse in place
a[i], a[j] = a[j], a[i]   # while i<j

# 3. Defaultdict counter
from collections import defaultdict
d = defaultdict(int); d['x'] += 1

# 4. Sorted with key
sorted(items, key=lambda x: (-x.priority, x.name))

# 5. Bisect insert
from bisect import insort
insort(arr, x)

# 6. Cyclic next index
nxt = (i + 1) % n

# 7. Build adjacency list
g = [[] for _ in range(n)]
for u,v in edges: g[u].append(v); g[v].append(u)

# 8. BFS template
from collections import deque
q = deque([start]); seen={start}
while q:
    u = q.popleft()
    for v in g[u]:
        if v not in seen:
            seen.add(v); q.append(v)

# 9. DFS recursive
def dfs(u):
    if u in seen: return
    seen.add(u)
    for v in g[u]: dfs(v)

# 10. DFS iterative
stk = [start]; seen=set()
while stk:
    u = stk.pop()
    if u in seen: continue
    seen.add(u)
    stk.extend(g[u])

# 11. Topo sort (Kahn)
indeg = [0]*n
for u in range(n):
    for v in g[u]: indeg[v]+=1
q = deque(i for i in range(n) if indeg[i]==0)
order=[]
while q:
    u = q.popleft(); order.append(u)
    for v in g[u]:
        indeg[v]-=1
        if indeg[v]==0: q.append(v)

# 12. Dijkstra
import heapq
def dijkstra(g, src):
    dist=[float('inf')]*len(g); dist[src]=0
    h=[(0,src)]
    while h:
        d,u = heapq.heappop(h)
        if d>dist[u]: continue
        for v,w in g[u]:
            if d+w < dist[v]:
                dist[v]=d+w; heapq.heappush(h,(dist[v],v))
    return dist

# 13. Union-Find
class DSU:
    def __init__(self,n): self.p=list(range(n)); self.r=[0]*n
    def find(self,x):
        while self.p[x]!=x: self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a,b):
        ra,rb=self.find(a),self.find(b)
        if ra==rb: return False
        if self.r[ra]<self.r[rb]: ra,rb=rb,ra
        self.p[rb]=ra
        if self.r[ra]==self.r[rb]: self.r[ra]+=1
        return True

# 14. Heap pattern (top-K)
import heapq
heap=[]
for x in stream:
    heapq.heappush(heap,x)
    if len(heap)>k: heapq.heappop(heap)
# heap[0] = K-th largest

# 15. Binary search "first true"
def first_true(lo, hi, P):
    while lo<hi:
        m=(lo+hi)//2
        if P(m): hi=m
        else: lo=m+1
    return lo

# 16. Sliding window template (longest with predicate)
l=best=0
for r,c in enumerate(s):
    add(c)
    while violates(): drop(s[l]); l+=1
    best=max(best, r-l+1)

# 17. Two-pointer (sorted)
l,r=0,len(a)-1
while l<r:
    if cond(a[l],a[r]): ...
    elif less(): l+=1
    else: r-=1

# 18. Subsets via bit mask
for mask in range(1<<n):
    sub=[a[i] for i in range(n) if mask>>i & 1]

# 19. Memoised recursion
from functools import cache
@cache
def f(i,j): ...

# 20. Iterate two arrays in sync (merge)
i=j=0
while i<len(A) and j<len(B):
    if A[i]<B[j]: out.append(A[i]); i+=1
    else: out.append(B[j]); j+=1

# 21. Detect cycle in list (Floyd)
slow=fast=head
while fast and fast.next:
    slow=slow.next; fast=fast.next.next
    if slow is fast: break

# 22. Reverse linked list
prev=None; cur=head
while cur:
    nxt=cur.next; cur.next=prev
    prev,cur=cur,nxt

# 23. Inorder iterative (BST sorted output)
stk=[]; cur=root
while stk or cur:
    while cur: stk.append(cur); cur=cur.left
    cur=stk.pop(); visit(cur)
    cur=cur.right

# 24. Trie node
class N: __slots__=('child','end'); ...
# or dict children

# 25. Counter sort by frequency
from collections import Counter
top = [k for k,_ in Counter(a).most_common(k)]

# 26. Matrix neighbours
for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
    nr,nc = r+dr, c+dc
    if 0<=nr<R and 0<=nc<C: ...

# 27. Prefix sums
ps=[0]
for x in a: ps.append(ps[-1]+x)
# sum(a[l..r]) = ps[r+1]-ps[l]

# 28. Difference array (range update O(1))
d=[0]*(n+1)
def add(l,r,v): d[l]+=v; d[r+1]-=v
# then prefix-sum d to recover

# 29. Run-length encoding
out=[]
for k,grp in groupby(s): out.append((k, sum(1 for _ in grp)))

# 30. Quickselect (k-th smallest, avg O(n))
import random
def qs(a,k):
    p=random.choice(a)
    lt=[x for x in a if x<p]; eq=[x for x in a if x==p]; gt=[x for x in a if x>p]
    if k<len(lt): return qs(lt,k)
    if k<len(lt)+len(eq): return p
    return qs(gt,k-len(lt)-len(eq))
```

---

# 🎯 50-question interview drill list (organised by pattern)

| # | Pattern | Problem | LC |
|---|---------|---------|----|
| 1 | Hash | Two Sum | 1 |
| 2 | Hash | Group Anagrams | 49 |
| 3 | Hash | Top K Frequent | 347 |
| 4 | Hash | Longest Consecutive | 128 |
| 5 | Two-pt | 3Sum | 15 |
| 6 | Two-pt | Container w/ Water | 11 |
| 7 | Two-pt | Trapping Rain Water | 42 |
| 8 | Window | Longest Substring w/o repeat | 3 |
| 9 | Window | Min Window Substring | 76 |
| 10 | Window | Sliding Window Maximum | 239 |
| 11 | BSearch | Find Min in Rotated | 153 |
| 12 | BSearch | Koko Eating Bananas | 875 |
| 13 | BSearch | Median of Two Sorted | 4 |
| 14 | Stack | Valid Parens | 20 |
| 15 | Stack | Daily Temperatures | 739 |
| 16 | Stack | Largest Rect in Histogram | 84 |
| 17 | List | Reverse Linked List | 206 |
| 18 | List | LL Cycle II | 142 |
| 19 | List | Merge K Sorted Lists | 23 |
| 20 | Tree | Max Depth | 104 |
| 21 | Tree | Validate BST | 98 |
| 22 | Tree | LCA Binary Tree | 236 |
| 23 | Tree | Serialize/Deserialize | 297 |
| 24 | Trie | Implement Trie | 208 |
| 25 | Trie | Word Search II | 212 |
| 26 | Heap | Kth Largest | 215 |
| 27 | Heap | Find Median Stream | 295 |
| 28 | Backtrack | Subsets | 78 |
| 29 | Backtrack | Permutations | 46 |
| 30 | Backtrack | Word Search | 79 |
| 31 | Backtrack | N-Queens | 51 |
| 32 | Graph | Number of Islands | 200 |
| 33 | Graph | Course Schedule | 207 |
| 34 | Graph | Network Delay | 743 |
| 35 | Graph | Word Ladder | 127 |
| 36 | DP1D | Climbing Stairs | 70 |
| 37 | DP1D | House Robber | 198 |
| 38 | DP1D | Coin Change | 322 |
| 39 | DP1D | LIS | 300 |
| 40 | DP1D | Word Break | 139 |
| 41 | DP2D | LCS | 1143 |
| 42 | DP2D | Edit Distance | 72 |
| 43 | DP2D | Unique Paths | 62 |
| 44 | Greedy | Jump Game | 55 |
| 45 | Greedy | Gas Station | 134 |
| 46 | Intervals | Merge Intervals | 56 |
| 47 | Intervals | Meeting Rooms II | 253 |
| 48 | Bits | Single Number | 136 |
| 49 | Math | Pow(x,n) | 50 |
| 50 | Math | Rotate Image | 48 |

---

# 🧪 Mock interview rubric (what they grade)

| Dimension | Weak (1) | OK (3) | Strong (5) |
|-----------|----------|--------|------------|
| Clarifying questions | none | a few | edge cases, types, scale all surfaced |
| Brute force first | jumps to optimal | mentions vaguely | states and analyses O(...) |
| Approach communication | silent | thinking out loud | structured: state → idea → algo → trace |
| Code quality | spaghetti | passes | clean names, small helpers, no dead code |
| Test cases | skipped | one happy path | empty, single, dup, max, adversarial |
| Complexity analysis | guesses | states big-O | derives, mentions amortised, space |
| Debugging | random changes | prints | hypothesis-driven |
| Bonus | — | — | proposes follow-up improvements |

---

# 🔗 Cross-references
- Deep dives per pattern: see `dsa-patterns/01-…` through `17-…`
- Worked problem walk-throughs: `dsa-examples.md`
- SQL DB algorithms: `sql-cheatsheet.md`
- OO design (LRU cache, observer, etc.): `oop-cheatsheet.md`
"""

def main():
    txt = CHEAT.read_text(encoding="utf-8")
    if "# 📈 Visual appendix" in txt:
        print("already expanded"); return
    if not txt.endswith("\n"):
        txt += "\n"
    CHEAT.write_text(txt + EXTRA, encoding="utf-8")
    print("expanded", CHEAT.name)

main()
