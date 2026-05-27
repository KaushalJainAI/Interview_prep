"""Inject diagrams and append Deep-Dive / Pitfalls / More Problems / Interview Qs sections to each pattern file."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

# Per-pattern expansion content. Each entry: appended markdown block.
EXPANSIONS = {
"01-arrays-hashing": r"""

---

## 🔬 Deep dive — why hashing works

A hash map stores keys in *buckets* indexed by `hash(key) % capacity`. With a good hash function and load factor <0.75, collisions are rare and amortised cost is **O(1)** for insert/lookup/delete. The cost we pay:
- **Worst case O(n)** if everything collides (adversarial hashing). Python `dict` uses randomised hashing to defend against this.
- **Space O(n)** — we trade memory to flatten the time curve.
- **No order** unless we use `OrderedDict` / `dict` (Python 3.7+ preserves insertion order).

> Mental model: "I'll remember every value I've seen so I can answer membership and complement queries instantly."

## ⚠️ Common pitfalls

| Pitfall | Fix |
|--------|-----|
| Checking `if key in dict.keys()` (Python) | Just `if key in dict` — O(1) instead of O(n) |
| Using a list when you need O(1) membership | Convert to `set` first |
| Forgetting hashing breaks on unhashable types | Use `tuple` not `list` as map key |
| Mutating a key after insertion | Hash becomes stale — value lost |
| Iterating + mutating the same dict | `RuntimeError`; iterate over a snapshot |
| Counting then over-writing in one loop | Use `defaultdict(int)` or `Counter` |

## 🧩 More worked problems

### Subarray Sum Equals K — LC 560
Prefix sum + hashmap. Count how many earlier prefixes equal `prefix - k`.
```python
def subarraySum(nums, k):
    cnt = {0: 1}                    # empty prefix
    psum = ans = 0
    for x in nums:
        psum += x
        ans += cnt.get(psum - k, 0) # answers ending here
        cnt[psum] = cnt.get(psum, 0) + 1
    return ans
```
**Why initial `{0:1}`?** A subarray starting at index 0 has prefix-before equal to 0.

### Encode / Decode Strings — LC 271
Length-prefix each token to handle delimiters inside the data.
```python
def encode(strs):  return "".join(f"{len(s)}#{s}" for s in strs)
def decode(s):
    res = []; i = 0
    while i < len(s):
        j = s.find("#", i)
        ln = int(s[i:j]); i = j + 1
        res.append(s[i:i+ln]); i += ln
    return res
```

### Happy Number — LC 202
Detect cycle in `n → sum(digit²)` chain using a set (or Floyd's tortoise/hare).

## 🎤 Interview-style questions

1. **Why O(1) average for dict lookup, and when does it degrade?**
   Hash distributes keys uniformly → constant probes per lookup. Degrades to O(n) under adversarial hashing or once load factor exceeds threshold and rehashing hasn't run.
2. **Group Anagrams: which key — sorted string or 26-letter count tuple?**
   Sorted string is O(k log k) per word; count tuple is O(k). For long words count wins; for short ones sorted is fine and simpler.
3. **Longest Consecutive — why O(n) and not O(n log n)?**
   We only *start* counting from sequence heads (`x-1` absent). Each element is visited once as part of exactly one streak.
4. **When would you prefer a sorted structure over a hashmap?**
   When you need ordered traversal, range queries, or "smallest key ≥ x". Hashmaps don't support these.
5. **Top-K frequent — bucket sort vs heap?**
   Bucket sort O(n) when freq ≤ n. Heap O(n log k) is better for streaming (don't need all data up front).

## 📚 References
- *Introduction to Algorithms* (CLRS), Ch. 11 — Hash Tables
- LeetCode Explore card: Hash Table
- Python docs: `collections.Counter`, `defaultdict`
""",

"02-two-pointers": r"""

---

## 🔬 Deep dive — why two pointers is O(n)

In a converging two-pointer scan, each iteration advances `L` or `R` by exactly 1, so the loop runs at most `n` times. Compare to the brute force `for i: for j>i:` which is O(n²). The trick: the **sorted order** lets you discard half the search space at each step using a monotone decision rule.

For the "fast/slow" variant (cycle detection, find middle, kth-from-end), the two pointers move at different speeds along the same axis; the **gap** between them encodes the invariant.

## ⚠️ Common pitfalls

| Pitfall | Fix |
|--------|-----|
| Forgetting to sort first | Convergent two-pointer needs monotonicity |
| Off-by-one on `while l < r` vs `l <= r` | `<` for pairs, `<=` when single element is valid |
| Duplicates yielding repeated answers | Skip equal neighbours after recording a hit |
| Mutating in place corrupts the index | Use a write pointer (`k`) distinct from the scan |
| Cycle detection without termination check | If list is finite-non-cyclic, fast hits None |

## 🧩 More problems

### 3Sum — LC 15
Fix `i`, two-pointer the rest. Skip duplicates at all three levels.
```python
def threeSum(nums):
    nums.sort(); res = []
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i-1]: continue
        l, r = i+1, len(nums)-1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if   s < 0: l += 1
            elif s > 0: r -= 1
            else:
                res.append([nums[i], nums[l], nums[r]])
                l += 1; r -= 1
                while l < r and nums[l] == nums[l-1]: l += 1
                while l < r and nums[r] == nums[r+1]: r -= 1
    return res
```

### Container With Most Water — LC 11
Move the *shorter* wall inward; area can only stay or grow.
```python
def maxArea(h):
    l, r, best = 0, len(h)-1, 0
    while l < r:
        best = max(best, (r-l) * min(h[l], h[r]))
        if h[l] < h[r]: l += 1
        else:           r -= 1
    return best
```
**Proof of correctness**: discarding the shorter wall is safe because any pair using it with a closer opposite wall would have ≤ current area.

### Trapping Rain Water — LC 42
Two-pointer with running maxes.
```python
def trap(h):
    l, r, lmax, rmax, ans = 0, len(h)-1, 0, 0, 0
    while l < r:
        if h[l] < h[r]:
            lmax = max(lmax, h[l])
            ans += lmax - h[l]; l += 1
        else:
            rmax = max(rmax, h[r])
            ans += rmax - h[r]; r -= 1
    return ans
```

### Linked-list cycle — LC 141
Floyd's tortoise & hare:
```python
slow = fast = head
while fast and fast.next:
    slow = slow.next; fast = fast.next.next
    if slow is fast: return True
return False
```

## 🎤 Interview questions

1. **Why sort before two-pointer?** Monotone decision rule needs order.
2. **3Sum: why O(n²) and not O(n³)?** Outer loop n, inner two-pointer n → n·n.
3. **Trap rain water — why does the "lower side" rule work?** Water trapped at `i` is bounded by `min(leftmax, rightmax)`; once we *know* one side's running max is lower than the opposite raw height, the lower side determines the trapped amount unambiguously.
4. **Fast/slow why does the hare meet the tortoise inside a cycle?** Relative speed is 1; within the cycle of length C the distance closes by 1 per step.
5. **When two-pointer fails:** array is unsorted AND you can't sort (e.g., need original indices and many duplicates) — fall back to hash or DP.

## 📚 References
- LeetCode Explore: Two Pointers
- *Competitive Programming Handbook* (Laaksonen) — Two-pointer section
""",

"03-sliding-window": r"""

---

## 🔬 Deep dive — fixed vs. variable windows

**Fixed window (size k):** slide one step at a time, add new element, drop old. O(n).

**Variable window (longest/shortest satisfying P):** expand R while OK, shrink L while NOT OK. Each index enters and leaves window at most once → **amortised O(n)** even though the inner `while` looks nested.

**Monotonic-deque variant (max in window):** keep indices in a deque whose values are decreasing. Front is the current max. Pop back smaller values before pushing.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Using `if violates` instead of `while` | One shrink may not be enough |
| Forgetting to update `best` after every R | Move "update best" to a fixed place per iteration |
| Mixing "longest" and "shortest" templates | Longest: update best AFTER shrink stops. Shortest: update while shrinking |
| Counting characters wrong on Unicode | Operate on bytes vs code points consistently |
| Off-by-one on window length `r - l + 1` | Draw it out — closed interval |

## 🧩 More problems

### Longest substring without repeating chars — LC 3
```python
def lengthOfLongestSubstring(s):
    last = {}; l = best = 0
    for r, c in enumerate(s):
        if c in last and last[c] >= l:
            l = last[c] + 1
        last[c] = r
        best = max(best, r - l + 1)
    return best
```

### Minimum window substring — LC 76 (Hard)
```python
from collections import Counter
def minWindow(s, t):
    need = Counter(t); missing = len(t)
    l = start = 0; best = (float('inf'), 0, 0)
    for r, c in enumerate(s):
        if need[c] > 0: missing -= 1
        need[c] -= 1
        if missing == 0:
            while need[s[l]] < 0:
                need[s[l]] += 1; l += 1
            if r - l + 1 < best[0]:
                best = (r - l + 1, l, r)
            need[s[l]] += 1; missing += 1; l += 1
    return "" if best[0] == float('inf') else s[best[1]:best[2]+1]
```

### Sliding window maximum — LC 239 (monotonic deque)
```python
from collections import deque
def maxSlidingWindow(nums, k):
    dq = deque(); out = []
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x: dq.pop()
        dq.append(i)
        if dq[0] <= i - k: dq.popleft()
        if i >= k - 1: out.append(nums[dq[0]])
    return out
```

### Permutation in string — LC 567
Fixed window of length |s1|, compare counter arrays.

## 🎤 Interview questions

1. **Why amortised O(n) for variable window?** Each index moves through L exactly once → at most n shrink steps total.
2. **When fixed vs variable?** Fixed if window size is given. Variable if optimising window size to satisfy a predicate.
3. **Minimum window substring — why use `missing` counter?** Avoids re-scanning entire `need` map each step; O(1) check per move.
4. **Monotonic deque why correct for max?** Smaller older elements can never be max while a larger newer element is in range.
5. **Substring with at most K distinct chars vs exactly K?** Exactly K = atMost(K) − atMost(K−1).

## 📚 References
- NeetCode 150 — Sliding window category
- Codeforces blog: monotonic deque tutorial
""",

"04-binary-search": r"""

---

## 🔬 Deep dive — binary search on the answer

Beyond "find x in sorted array", binary search is really about searching a **monotone predicate**: find smallest/largest `m` for which `P(m)` is true. The array view is one special case.

Generic template ("first true"):
```python
lo, hi = lo0, hi0
while lo < hi:
    m = (lo + hi) // 2
    if P(m): hi = m
    else:    lo = m + 1
return lo
```

This invariant — `P(hi)` is always true (or hi is past end) — avoids most off-by-ones.

**Common monotone domains:**
- Sorted array: classic.
- Answer space: "min capacity to ship in D days", "min eating speed".
- Real numbers: bisect with epsilon tolerance.
- 2D matrix: treat row-major or binary search rows.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| `(lo+hi)//2` overflow in other languages | In Python ints are unbounded; in Java use `lo + (hi-lo)//2` |
| Wrong half discarded on duplicates | Decide explicitly: leftmost vs rightmost occurrence |
| `lo<=hi` with `lo=m+1, hi=m-1` → off-by-one | Pick one template and stick with it |
| Infinite loop with `lo=m` (no shrink) | Use `(lo+hi+1)//2` when assigning lo=m |
| Forgetting predicate monotonicity | Verify P(lo..hi) is sorted False...True |

## 🧩 More problems

### Find Minimum in Rotated Sorted Array — LC 153
Compare `nums[m]` to `nums[hi]`.
```python
def findMin(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        m = (lo + hi) // 2
        if nums[m] > nums[hi]: lo = m + 1
        else:                  hi = m
    return nums[lo]
```

### Koko Eating Bananas — LC 875
Binary search over eating-speed K.
```python
import math
def minEatingSpeed(piles, h):
    lo, hi = 1, max(piles)
    while lo < hi:
        m = (lo + hi) // 2
        if sum(math.ceil(p / m) for p in piles) <= h:
            hi = m
        else:
            lo = m + 1
    return lo
```

### Median of Two Sorted Arrays — LC 4 (Hard)
Binary search the partition position of the shorter array.

### Search a 2D Matrix — LC 74
Treat as 1D of length m·n.

## 🎤 Interview questions

1. **Why must the predicate be monotone?** Bisecting depends on "one side always satisfies, other never does".
2. **Leftmost vs rightmost binary search difference?** Tie-break: leftmost shrinks `hi` on equality; rightmost shrinks `lo`.
3. **Binary-search on real-valued answer — when to stop?** `hi - lo < eps` (e.g. 1e-9) or fixed 100 iterations.
4. **Rotated array — why compare to `nums[hi]` not `nums[lo]`?** Rotation cuts the sorted run; `hi` side is the "lower half" after rotation, which is monotone w.r.t. the answer.
5. **What if you can't find a monotone P?** Try parametric search or switch to BFS/DP.

## 📚 References
- "Powerful Ultimate Binary Search Template" — zhijun_liao on LeetCode
- *Beautiful Code*, Ch. 4 — On binary-search variants
""",

"05-stack": r"""

---

## 🔬 Deep dive — what stacks really compute

Three flavours interviewers love:
1. **Parentheses / bracket matching** — push opens, pop and check on close.
2. **Monotonic stack** — maintain increasing/decreasing run; pop while invariant violated. Each element pushed/popped at most once → O(n).
3. **Expression / parsing** — operands on a stack, evaluate on operator.

**Why monotonic stacks unlock "next greater" problems:** when we see a value greater than the top, we've found the answer for everything below it; pop and record. Anything still on the stack hasn't seen a greater value yet.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Forgetting to drain remaining stack at end | Loop after main scan to handle leftovers |
| Storing values instead of indices | Many problems need *positions* (distance, width) |
| `<` vs `<=` flips inclusive/exclusive | Pick one based on "strictly greater" vs ≥ semantics |
| Using list and `.pop(0)` for queue | That's O(n) — use `collections.deque` |
| Recursion blowing stack on deep input | Convert to iterative with explicit stack |

## 🧩 More problems

### Valid Parentheses — LC 20
```python
def isValid(s):
    pair = {")":"(", "]":"[", "}":"{"}
    st = []
    for c in s:
        if c in "([{": st.append(c)
        elif not st or st.pop() != pair[c]: return False
    return not st
```

### Daily Temperatures — LC 739
```python
def dailyTemperatures(t):
    res = [0]*len(t); st = []   # indices, decreasing temps
    for i, x in enumerate(t):
        while st and t[st[-1]] < x:
            j = st.pop(); res[j] = i - j
        st.append(i)
    return res
```

### Largest Rectangle in Histogram — LC 84 (Hard)
```python
def largestRectangleArea(h):
    h = h + [0]; st = []; best = 0
    for i, x in enumerate(h):
        while st and h[st[-1]] > x:
            top = st.pop()
            width = i if not st else i - st[-1] - 1
            best = max(best, h[top] * width)
        st.append(i)
    return best
```

### Min Stack — LC 155
Maintain a second stack of running minimums (or pair value+min).

### Evaluate RPN — LC 150
```python
def evalRPN(tokens):
    st = []
    for t in tokens:
        if t in "+-*/":
            b, a = st.pop(), st.pop()
            st.append(int(a/b) if t == "/" else eval(f"{a}{t}{b}"))
        else: st.append(int(t))
    return st[0]
```

## 🎤 Interview questions

1. **Why O(n) for monotonic stack despite the inner while?** Amortised: each index pushed once, popped once.
2. **Largest rectangle — why the sentinel `0`?** Forces flush of any remaining increasing run at the end.
3. **Min stack — why pair instead of separate min stack?** Pair is O(1) per op; separate stack can also work but uses more memory if minimum rarely changes.
4. **Implement queue with two stacks** — push on `in`, pop after transferring `in→out` lazily.
5. **Reverse Polish vs infix** — RPN needs only a stack; infix needs Shunting-yard or precedence climbing.

## 📚 References
- Dijkstra's Shunting-yard algorithm (1961)
- *Algorithms* by Sedgewick — Stacks & Queues
""",

"06-linked-list": r"""

---

## 🔬 Deep dive — pointer manipulation principles

Three patterns cover most linked-list problems:
1. **Dummy head** — create a sentinel so you don't special-case head insertions/deletions.
2. **Two pointers (fast/slow or runner)** — middle, cycle, kth-from-end, palindrome.
3. **In-place reversal** — using three pointers `prev / curr / next` to flip links.

When recursion is easier, recall that depth = list length; for very long lists prefer iteration to avoid stack overflow.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Losing the tail / forgetting to null it | Always set `tail.next = None` after detach |
| Off-by-one on "find middle" — slow at ⌊n/2⌋ vs ⌈n/2⌉ | Adjust loop condition `fast.next` vs `fast.next and fast.next.next` |
| Modifying head without dummy | Use dummy = ListNode(0, head); return dummy.next |
| Cycle in input crashes plain traversal | Detect first (slow/fast) or use a seen set |
| Using `==` vs `is` for node equality | `is` for identity (cycle), `==` only if `__eq__` defined |

## 🧩 More problems

### Reverse Linked List — LC 206
```python
def reverseList(head):
    prev, curr = None, head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev, curr = curr, nxt
    return prev
```

### Merge Two Sorted Lists — LC 21
```python
def mergeTwoLists(a, b):
    dummy = tail = ListNode()
    while a and b:
        if a.val <= b.val: tail.next, a = a, a.next
        else:              tail.next, b = b, b.next
        tail = tail.next
    tail.next = a or b
    return dummy.next
```

### Remove Nth From End — LC 19
Gap of n between fast and slow.
```python
def removeNthFromEnd(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n+1): fast = fast.next
    while fast: fast = fast.next; slow = slow.next
    slow.next = slow.next.next
    return dummy.next
```

### Linked List Cycle II (start of cycle) — LC 142
Floyd's: after meeting, reset one pointer to head, move both 1 step; meeting point = cycle start.

### Copy List with Random Pointer — LC 138
Interleave clones, fix random pointers, split.

### Reverse Nodes in K-Group — LC 25 (Hard)
Use dummy + count; reverse each block, splice back.

## 🎤 Interview questions

1. **Why does Floyd's cycle-start work mathematically?** Distance from head to start = distance from meeting point to start (mod cycle length); the maths cancels out.
2. **When to use dummy head?** Whenever head can change (insertion/deletion at position 0).
3. **Reverse k-group — iterative complexity?** O(n) time, O(1) space; recursion is O(n) extra stack.
4. **Compare merging k sorted lists with merging pairwise.** Heap is O(N log k); pairwise is O(N log k) too via tournament — but heap is simpler online.
5. **Why prefer iteration over recursion for linked-list problems?** Stack overflow on long lists.

## 📚 References
- *Cracking the Coding Interview*, Ch. 2
- LeetCode Top Interview 150 — Linked List
""",

"07-trees": r"""

---

## 🔬 Deep dive — three traversal orders

```
       1
      / \
     2   3
    / \   \
   4   5   6

preorder  (Node,L,R) : 1 2 4 5 3 6     ← "copy a tree"
inorder   (L,Node,R) : 4 2 5 1 3 6     ← BST sorted output
postorder (L,R,Node) : 4 5 2 6 3 1     ← "delete a tree", evaluate expression
level    (BFS)       : 1 2 3 4 5 6     ← shortest path / serialization
```

DFS naturally fits recursion; BFS naturally fits a queue. Both are O(n) time, O(h) and O(w) space respectively (h = height, w = max width).

**BST property:** for every node, all left descendants < node < all right descendants. Inorder traversal of a BST yields sorted values.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Recursing on `None` without guard | `if not node: return` at top |
| Mutable default args in helpers | Use `None` sentinel, init inside |
| Comparing to parent only for BST validity | Pass running (min, max) bounds down |
| Mixing global and returned values | Pick one, document it |
| Iterative DFS forgetting to mark visited | For graphs yes; for trees not needed if true tree |

## 🧩 More problems

### Maximum Depth — LC 104
```python
def maxDepth(root):
    return 0 if not root else 1 + max(maxDepth(root.left), maxDepth(root.right))
```

### Validate BST — LC 98 (with bounds)
```python
def isValidBST(root, lo=float("-inf"), hi=float("inf")):
    if not root: return True
    if not (lo < root.val < hi): return False
    return isValidBST(root.left, lo, root.val) and isValidBST(root.right, root.val, hi)
```

### LCA of BST — LC 235
Walk down: if both targets < node go left; both > node go right; else node is LCA.

### LCA of Binary Tree — LC 236
```python
def lowestCommonAncestor(root, p, q):
    if not root or root is p or root is q: return root
    l = lowestCommonAncestor(root.left,  p, q)
    r = lowestCommonAncestor(root.right, p, q)
    return root if l and r else (l or r)
```

### Serialize / Deserialize — LC 297
Preorder with null markers.

### Diameter of Binary Tree — LC 543
DFS returning depth, updating global best with `left + right`.

### Binary Tree Level Order — LC 102
```python
from collections import deque
def levelOrder(root):
    if not root: return []
    q = deque([root]); res = []
    while q:
        level = []
        for _ in range(len(q)):
            n = q.popleft(); level.append(n.val)
            if n.left:  q.append(n.left)
            if n.right: q.append(n.right)
        res.append(level)
    return res
```

## 🎤 Interview questions

1. **Why inorder of a BST is sorted?** L < Node < R applied recursively.
2. **Validate BST — why bounds, not just left/right comparison?** A right grandchild could violate the ancestor's bound while satisfying its parent.
3. **LCA — why does the bubble-up trick work?** Because the LCA is exactly where the left and right recursive results both come back non-null.
4. **Iterative inorder?** Stack: push lefts, pop, output, go right.
5. **Morris traversal?** Threaded pointers for O(1) space inorder.

## 📚 References
- CLRS Ch. 12 (BSTs), Ch. 22 (Tree traversals via DFS)
- "Tree problems are recursion problems" — most LC editorial
""",

"08-tries": r"""

---

## 🔬 Deep dive — trie vs hashmap

A trie shines when you need **prefix queries** or **iteration over keys with a shared prefix**. Hashmap is O(1) per key but doesn't expose prefix structure.

Trade-offs:
- Trie: O(m) per op (m = key length), O(N·m) space, optimal for autocomplete / streaming text.
- Hashmap: O(m) hash + O(1) bucket, slightly faster constants but no prefix iteration.
- Compressed trie (radix) saves nodes on sparse alphabets.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Storing 26 references in every node when alphabet is sparse | Use dict children |
| Forgetting end-of-word marker | Add `is_end` flag |
| Deletion that orphans subtree | Delete only when `is_end` and no children |
| Treating trie as memory-cheap | Each char usually = a node (+pointer overhead) |

## 🧩 More problems

### Implement Trie — LC 208
```python
class Trie:
    def __init__(self):
        self.root = {}
    def insert(self, word):
        node = self.root
        for c in word:
            node = node.setdefault(c, {})
        node["$"] = True
    def search(self, word):
        node = self._walk(word)
        return bool(node and node.get("$"))
    def startsWith(self, prefix):
        return self._walk(prefix) is not None
    def _walk(self, s):
        node = self.root
        for c in s:
            if c not in node: return None
            node = node[c]
        return node
```

### Word Search II — LC 212 (Hard)
DFS on board, prune by trie node. Each DFS step checks whether the current cell's letter is a child of the current trie node; if not, prune.

### Replace Words — LC 648
Build trie of roots; for each word, walk until first end-of-word.

### Design Add and Search Word — LC 211
Trie + `.` wildcard means recurse over all children.

### Longest Common Prefix — LC 14
Build trie, walk until branching.

## 🎤 Interview questions

1. **Why trie for autocomplete?** Prefix walk is O(m); collecting completions is O(suggestions) using subtree DFS.
2. **Space optimisation?** Use dict (sparse), radix tree (path compression), or DAWG (shared suffixes too).
3. **When is hashmap better?** When you only do exact lookup and prefix isn't needed.
4. **How to support fuzzy / edit-distance search?** Trie + dynamic programming row over edit distance (Levenshtein automaton).
5. **Word Search II complexity?** O(R·C·4^L) bound; trie prunes massive subtrees so practical perf is far better.

## 📚 References
- Sedgewick R-way Tries; Ternary Search Tries
- "Levenshtein automata" — Schulz & Mihov
""",

"09-heap": r"""

---

## 🔬 Deep dive — when heap beats sort

If you need ALL elements ordered → sort, O(n log n).
If you need top-K / kth element from a stream → heap, O(n log k).
If you need "next event" in simulation → heap = priority queue.
If you need both ends → two heaps (median maintenance) or balanced BST.

**heapify in O(n):** Bottom-up sift-down has cost ∑ h_i ≤ 2n by a tight telescoping argument; not O(n log n).

Python's `heapq` is a **min-heap**. For max-heap, negate values or use tuples `(-priority, item)`.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Using `heap[0]` after `heappush` without `heapify` | OK as long as you only used heappush/heappop |
| Storing un-comparable items | Add a tiebreaker `(priority, counter, item)` |
| Removing arbitrary element | heapq doesn't support; use lazy deletion (mark stale) |
| Forgetting Python is min-heap | Negate, or use SortedList |
| Updating priority in place | Heap invariant breaks; reinsert and lazy-delete old |

## 🧩 More problems

### Kth Largest in Array — LC 215
```python
import heapq
def findKthLargest(nums, k):
    h = []
    for x in nums:
        heapq.heappush(h, x)
        if len(h) > k: heapq.heappop(h)
    return h[0]
```

### Top K Frequent — LC 347
Counter + heap of size k.

### Merge K Sorted Lists — LC 23
```python
import heapq
def mergeKLists(lists):
    h = []
    for i, node in enumerate(lists):
        if node: heapq.heappush(h, (node.val, i, node))
    dummy = tail = ListNode()
    while h:
        v, i, n = heapq.heappop(h)
        tail.next = n; tail = n
        if n.next: heapq.heappush(h, (n.next.val, i, n.next))
    return dummy.next
```

### Find Median from Data Stream — LC 295 (Hard)
Two heaps: max-heap for lower half, min-heap for upper. Rebalance after each insert.

### Task Scheduler — LC 621
Greedy + heap by remaining counts.

### Reorganize String — LC 767
Heap by frequency; always pick top two distinct.

## 🎤 Interview questions

1. **Why is `heapify` O(n)?** Cost dominated by bottom levels which have many cheap operations.
2. **Median of stream — why two heaps?** O(log n) insert, O(1) median. Self-balancing BST also works.
3. **Top K via heap vs quickselect?** Heap O(n log k), quickselect avg O(n) but worst O(n²). Heap is online.
4. **Why include a counter in tuples pushed to heap?** Tiebreaker for unhashable / equal-priority items.
5. **When prefer sorted list over heap?** When you need k-th smallest at arbitrary k, or range queries.

## 📚 References
- CLRS Ch. 6 — Heapsort
- Python docs: `heapq` priority-queue patterns
""",

"10-backtracking": r"""

---

## 🔬 Deep dive — backtracking template

```python
def backtrack(state, choices):
    if is_solution(state):
        record(state); return
    for c in choices:
        if not valid(state, c): continue
        apply(state, c)
        backtrack(state, next_choices)
        undo(state, c)            # ← the "back" in backtracking
```

Three knobs:
- **Choices set** at each level (subset, permutation, branching factor)
- **Validity check** (pruning — the difference between O(2ⁿ) brute force and a fast solver)
- **Solution test** (record full state, or count, or first found)

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Mutating a list then appending to results | Append a *copy* (`state[:]`) |
| Skipping the "undo" step | State leaks across branches |
| Duplicates from sorted inputs | Skip equal siblings: `if i > start and a[i]==a[i-1]: continue` |
| Re-computing validity from scratch each call | Cache / track incremental state (sums, used set) |
| Recursion depth on N≈10⁴ | Use iterative explicit stack |

## 🧩 More problems

### Subsets — LC 78
```python
def subsets(nums):
    res = []
    def bt(i, cur):
        if i == len(nums):
            res.append(cur[:]); return
        cur.append(nums[i]); bt(i+1, cur); cur.pop()  # include
        bt(i+1, cur)                                  # skip
    bt(0, [])
    return res
```

### Permutations — LC 46
```python
def permute(nums):
    res = []; used = [False]*len(nums)
    def bt(cur):
        if len(cur) == len(nums):
            res.append(cur[:]); return
        for i in range(len(nums)):
            if used[i]: continue
            used[i] = True; cur.append(nums[i])
            bt(cur)
            cur.pop(); used[i] = False
    bt([])
    return res
```

### Combination Sum — LC 39
Sorted; reuse same index for repetition.

### Word Search — LC 79
DFS on grid, mark cell as `#` temporarily.

### N-Queens — LC 51 (Hard)
Place row by row; check three sets (cols, diag1, diag2).

### Sudoku Solver — LC 37 (Hard)
Find next empty, try 1–9, validate, recurse, undo.

### Palindrome Partitioning — LC 131

## 🎤 Interview questions

1. **Difference between DFS, recursion, and backtracking?** Backtracking = DFS over choice space + undo on return.
2. **Subset vs permutation branching factor?** Subset: include/exclude → 2ⁿ leaves. Permutation: n! leaves.
3. **N-Queens — why diag set indexed by `r-c` and `r+c`?** Same anti-diag has constant `r+c`; same diag has constant `r-c`.
4. **How do you prune?** Bound check (feasibility), order choices best-first, memoise (overlaps with DP).
5. **When does backtracking degenerate to brute force?** No pruning — i.e. validity rarely fails. Then it really is exponential.

## 📚 References
- "Backtracking" entry, *Algorithm Design Manual* (Skiena)
- DonaldKnuth's Algorithm X (Dancing Links) for exact cover
""",

"11-graphs": r"""

---

## 🔬 Deep dive — graph algorithm cheat matrix

| Task | Best fit | Complexity |
|------|----------|-----------|
| Shortest path, unweighted | BFS | O(V+E) |
| Shortest path, non-negative weights | Dijkstra (heap) | O((V+E) log V) |
| Shortest path, negative weights | Bellman-Ford | O(V·E) |
| All-pairs shortest path | Floyd-Warshall | O(V³) |
| Topological order (DAG) | DFS post-order reverse / Kahn | O(V+E) |
| Strongly Connected Components | Kosaraju / Tarjan | O(V+E) |
| Minimum Spanning Tree | Kruskal (DSU) / Prim (heap) | O(E log E) |
| Connected components | Union-Find or BFS/DFS | ~O(V+E) |
| Cycle detection (undirected) | DFS + parent / Union-Find | O(V+E) |
| Cycle detection (directed)   | DFS w/ 3-colour | O(V+E) |
| Bipartite check | BFS 2-colour | O(V+E) |

**Representation:** adjacency list for sparse, matrix for dense (V ≤ ~500).

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Forgetting visited set on cyclic graphs | Always track visited |
| BFS using list and pop(0) | Use `deque` |
| Dijkstra with negative weights | Switch to Bellman-Ford |
| Re-pushing stale entries to heap | Skip when popped with stale distance |
| Recursive DFS overflow on V=10⁴ | Iterative stack |
| Topo sort returning fewer than V nodes | Cycle exists |

## 🧩 More problems

### BFS — Shortest path in grid (LC 1091)
```python
from collections import deque
def shortestPathBinaryMatrix(grid):
    n = len(grid)
    if grid[0][0] or grid[-1][-1]: return -1
    q = deque([(0,0,1)]); grid[0][0] = 1
    DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    while q:
        r,c,d = q.popleft()
        if (r,c)==(n-1,n-1): return d
        for dr,dc in DIRS:
            nr,nc = r+dr, c+dc
            if 0<=nr<n and 0<=nc<n and grid[nr][nc]==0:
                grid[nr][nc]=1; q.append((nr,nc,d+1))
    return -1
```

### Dijkstra — Network Delay Time (LC 743)
```python
import heapq
def networkDelayTime(times, n, k):
    g = [[] for _ in range(n+1)]
    for u,v,w in times: g[u].append((v,w))
    dist = [float('inf')]*(n+1); dist[k] = 0
    h = [(0,k)]
    while h:
        d, u = heapq.heappop(h)
        if d > dist[u]: continue
        for v,w in g[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd; heapq.heappush(h, (nd, v))
    ans = max(dist[1:])
    return -1 if ans == float('inf') else ans
```

### Topological sort — Course Schedule II (LC 210)
Kahn's algorithm with in-degrees.

### Union-Find — Number of Connected Components
```python
class DSU:
    def __init__(self, n):
        self.p = list(range(n)); self.r = [0]*n
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False
        if self.r[ra] < self.r[rb]: ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]: self.r[ra] += 1
        return True
```

### Word Ladder — LC 127 (BFS over implicit graph)
### Pacific Atlantic Water Flow — LC 417 (multi-source BFS)
### Alien Dictionary — LC 269 (topo on inferred edges)

## 🎤 Interview questions

1. **Why does Dijkstra fail on negative edges?** A node popped with distance d may later be reachable via a lower-cost path through a negative edge.
2. **Topo sort on a cyclic graph?** No valid order; Kahn ends with fewer than V nodes, DFS detects via grey (in-progress) nodes.
3. **BFS vs Dijkstra on unit weights?** Same answer; BFS is simpler & faster (no heap).
4. **Union-Find amortised complexity?** ~O(α(n)) ≈ O(1) with both path compression + union-by-rank.
5. **When matrix > list?** Dense graph, V small, O(1) edge query.
6. **A* vs Dijkstra?** A* is Dijkstra + heuristic; equally optimal when heuristic is admissible & consistent.

## 📚 References
- CLRS Ch. 22–26
- "Competitive Programmer's Handbook" — Antti Laaksonen — chapters 11–15
""",

"12-dp-1d": r"""

---

## 🔬 Deep dive — recognising DP

Three signs you're looking at DP:
1. Optimal substructure (answer to size n depends on answers to smaller sizes)
2. Overlapping subproblems (naive recursion recomputes)
3. Decision at each step (take / skip / pick best)

**Top-down (memoised recursion) vs bottom-up (table):**
- Top-down is closer to the recurrence; easier to derive.
- Bottom-up avoids recursion stack, allows space optimisation by dropping older rows.

Identify the *state*: what minimal info captures "where I am" so the optimal future is determined?

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Wrong base case | Derive from "smallest meaningful subproblem" |
| Forgetting to clamp negative indices | Guard in recurrence or pad table with offset |
| Mutable default arg in memoised recursion | `@functools.cache` is cleaner |
| Wrong order of fills | Topological order on the dependency DAG |
| Counting paths vs values | Different recurrence; read problem carefully |
| Space O(n²) when O(n) suffices | Rolling array |

## 🧩 More problems

### Climbing Stairs — LC 70
```python
def climbStairs(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a + b
    return a
```

### House Robber — LC 198
```python
def rob(nums):
    take = skip = 0
    for x in nums:
        take, skip = skip + x, max(take, skip)
    return max(take, skip)
```

### House Robber II — LC 213
Run rob on `nums[:-1]` and `nums[1:]`, return max — first and last can't both be picked.

### Coin Change — LC 322
```python
def coinChange(coins, amount):
    dp = [0] + [float('inf')]*amount
    for a in range(1, amount+1):
        for c in coins:
            if c <= a: dp[a] = min(dp[a], dp[a-c] + 1)
    return -1 if dp[amount] == float('inf') else dp[amount]
```

### Longest Increasing Subsequence — LC 300
Patience-sorting O(n log n):
```python
from bisect import bisect_left
def lengthOfLIS(nums):
    tails = []
    for x in nums:
        i = bisect_left(tails, x)
        if i == len(tails): tails.append(x)
        else: tails[i] = x
    return len(tails)
```

### Word Break — LC 139
```python
def wordBreak(s, wordDict):
    words = set(wordDict)
    dp = [True] + [False]*len(s)
    for i in range(1, len(s)+1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True; break
    return dp[-1]
```

### Maximum Subarray (Kadane) — LC 53
Running prefix; reset to current when prefix < 0.

## 🎤 Interview questions

1. **Memoisation vs tabulation differences?** Same complexity; tab avoids recursion overhead but requires fill-order analysis.
2. **LIS — why does the patience-sort tails array work?** `tails[i]` = smallest tail of any increasing subseq of length i+1; binary-search lets us extend or replace in O(log n).
3. **Coin change — why bottom-up?** Smaller amounts are dependencies; build up.
4. **When DP doesn't apply?** No overlapping subproblems (→ divide & conquer) or no optimal substructure (→ search).
5. **State representation example?** Robber: `(i, last_taken_bool)`; with rolling vars we collapse to two scalars.

## 📚 References
- "DP for Dummies" — Bill Cook, MIT 6.006
- *Algorithms* (Cormen et al.) Ch. 15
""",

"13-dp-2d": r"""

---

## 🔬 Deep dive — when state is two-dimensional

Common signals: two interacting sequences (LCS, edit distance), two endpoints (palindrome ranges), two coordinates (grid path), or one sequence + an integer budget (knapsack).

**Standard recurrence shapes:**
- LCS: `dp[i][j] = dp[i-1][j-1] + 1` if match, else `max(dp[i-1][j], dp[i][j-1])`
- Edit distance: `min(insert, delete, replace)` + 1
- Knapsack: `dp[i][w] = max(dp[i-1][w], dp[i-1][w-wi] + vi)`
- Palindrome: `dp[i][j] = dp[i+1][j-1] if s[i]==s[j] else False`

**Space optimisation:** if `dp[i][.]` depends only on `dp[i-1][.]`, keep two rows (or one row + careful order).

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Mixing up indices (i for s1 vs s2) | Comment dimensions explicitly |
| Filling in wrong order with rolling array | When updating dp[w] in-place for 0/1 knapsack, iterate w from high to low |
| Forgetting base row/column (empty string) | Initialise dp[0][.] and dp[.][0] |
| Confusing subseq vs substring | Substring must be contiguous; reset on mismatch |
| Edit-distance with extra ops (transpose) | Use Damerau-Levenshtein variant |

## 🧩 More problems

### Longest Common Subsequence — LC 1143
```python
def longestCommonSubsequence(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            dp[i][j] = dp[i-1][j-1]+1 if a[i-1]==b[j-1] else max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

### Edit Distance — LC 72
```python
def minDistance(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]
```

### Unique Paths — LC 62
`dp[i][j] = dp[i-1][j] + dp[i][j-1]`; or closed form `C(m+n-2, m-1)`.

### 0/1 Knapsack
```python
def knapsack(values, weights, W):
    dp = [0]*(W+1)
    for v, w in zip(values, weights):
        for cap in range(W, w-1, -1):       # backward to enforce 0/1
            dp[cap] = max(dp[cap], dp[cap-w] + v)
    return dp[W]
```

### Longest Palindromic Substring — LC 5
Expand around centers (O(n²)) or DP on `dp[i][j]`.

### Distinct Subsequences — LC 115 (Hard)

### Interleaving String — LC 97

## 🎤 Interview questions

1. **0/1 vs unbounded knapsack — loop direction difference?** Backward for 0/1 (each item once), forward for unbounded.
2. **LCS vs Edit Distance — relationship?** EditDistance = m + n − 2·LCS *only* when ops are (insert, delete); with replace it's a different recurrence.
3. **Why does palindrome DP go from inside out?** `dp[i][j]` depends on `dp[i+1][j-1]`, so fill by increasing length.
4. **Memory optimisation example?** LCS: keep two rows. Knapsack: one row, backward.
5. **Where does DP fail?** When state space is exponential (e.g., TSP for large n).

## 📚 References
- Erik Demaine MIT 6.046 — DP lectures
- "Dynamic Programming Patterns" — aatalyk on LeetCode
""",

"14-greedy": r"""

---

## 🔬 Deep dive — when greedy is correct

Greedy is correct when:
- **Greedy choice property:** a locally optimal choice leads to a globally optimal solution.
- **Optimal substructure:** an optimal solution to the problem contains optimal solutions to its subproblems.

You prove correctness via:
1. **Exchange argument** — show that any optimal solution can be transformed into the greedy one without worsening it.
2. **Matroid theory** — when the problem fits a matroid, greedy by weight works (e.g., MST).
3. **Cut property** — for MST, the lightest edge crossing any cut is in some MST.

If you can't construct an exchange argument, suspect DP.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Greedy on the wrong sort key | Try both: "by start", "by end", "by ratio" |
| Greedy works on examples but not in general | Look for a counterexample before coding |
| Ties not broken consistently | Add tiebreaker to sort |
| Greedy stuck because choice depended on future | Need DP / search |

## 🧩 More problems

### Jump Game — LC 55
```python
def canJump(nums):
    reach = 0
    for i, x in enumerate(nums):
        if i > reach: return False
        reach = max(reach, i + x)
    return True
```

### Jump Game II — LC 45
BFS-like: track current furthest and steps.
```python
def jump(nums):
    jumps = end = farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == end:
            jumps += 1; end = farthest
    return jumps
```

### Gas Station — LC 134
```python
def canCompleteCircuit(gas, cost):
    if sum(gas) < sum(cost): return -1
    tank = start = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0: start = i + 1; tank = 0
    return start
```

### Hand of Straights — LC 846
Sort + Counter; for smallest available, greedily form a group.

### Task Scheduler — LC 621 (heap-greedy)

### Partition Labels — LC 763
Compute last index of each char; sweep, extend partition end.

### Minimum Number of Arrows — LC 452
Sort by end; new arrow when start > current end.

## 🎤 Interview questions

1. **Activity selection — why sort by END and not start?** Earliest finishing leaves maximal room for the rest; exchange argument proves optimality.
2. **Greedy vs DP — what's the difference?** Greedy commits a choice without revisiting; DP explores all relevant choices.
3. **Gas station — why does the "reset to next" trick work?** If sum is non-negative, starting from the city right after the lowest cumulative deficit always works.
4. **Huffman coding — why greedy?** Optimal prefix code has structure where two smallest weights are siblings (proved by swap argument).
5. **When greedy is approximate, not exact?** Set cover, TSP (greedy gives log n / 1.5 approximation).

## 📚 References
- CLRS Ch. 16 — Greedy Algorithms
- Kleinberg & Tardos — proofs via exchange arguments
""",

"15-intervals": r"""

---

## 🔬 Deep dive — sort + sweep

Three skeletons:
1. **Merge:** sort by start, sweep, extend last if overlap.
2. **Insert / non-overlap count:** sort by end; pick if start ≥ last end.
3. **Min resources (rooms / arrows):** count concurrent intervals via sweep-line events `(time, +1/−1)` or two-heap.

A sweep-line replaces the interval with two events; processing events in time order solves many "max overlap" or "first conflict" problems.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Inclusive vs exclusive endpoints | Decide once; e.g., [start, end) avoids ties |
| Sorting by start when problem needs end | Pick by problem: count non-overlap → end; merge → start |
| Events processed in wrong tie order | End events before start events when intervals share a boundary (or vice versa per spec) |
| Forgetting to advance "last picked end" | Track explicitly |
| Off-by-one when comparing `a.start` vs `b.end` | Test boundary cases: `[1,2]` and `[2,3]` |

## 🧩 More problems

### Merge Intervals — LC 56
```python
def merge(intervals):
    intervals.sort()
    out = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
```

### Insert Interval — LC 57
Three phases: before, overlap (merge), after.

### Non-overlapping Intervals — LC 435
```python
def eraseOverlapIntervals(intervals):
    intervals.sort(key=lambda x: x[1])
    end = float('-inf'); removed = 0
    for s, e in intervals:
        if s >= end: end = e
        else: removed += 1
    return removed
```

### Meeting Rooms II — LC 253
```python
import heapq
def minMeetingRooms(meetings):
    meetings.sort()
    heap = []  # earliest ending
    for s, e in meetings:
        if heap and heap[0] <= s:
            heapq.heappop(heap)
        heapq.heappush(heap, e)
    return len(heap)
```

Or sweep-line:
```python
def minMeetingRooms2(meetings):
    starts = sorted(m[0] for m in meetings)
    ends   = sorted(m[1] for m in meetings)
    rooms = i = 0
    for s in starts:
        if s >= ends[i]: i += 1
        else:            rooms += 1
    return rooms
```

### Car Pooling — LC 1094 (event sweep)
### Minimum Number of Arrows — LC 452

## 🎤 Interview questions

1. **Why sort by end for non-overlap counting?** Picking earliest-ending leaves more room — exchange argument.
2. **Sweep-line max concurrent — why O(n log n)?** Dominated by sort; sweep is O(n).
3. **Closed vs open intervals — when matters?** Tiebreaking events; e.g., a meeting ending at 10 and another starting at 10 may or may not need a new room.
4. **Insert interval complexity?** O(n) if list is already sorted; O(log n) to find boundary + O(n) to merge.
5. **Range-tree alternative?** Interval tree gives O(log n + k) queries; overkill for one-shot batch problems.

## 📚 References
- de Berg et al., *Computational Geometry* — Ch. 2 sweep line
- LeetCode "Interval" tag
""",

"16-bit-manipulation": r"""

---

## 🔬 Deep dive — bit tricks worth memorising

| Trick | Effect |
|-------|-------|
| `x & 1` | parity (lowest bit) |
| `x >> 1` | divide by 2 (signed: rounds toward -∞ in Python) |
| `x & (x - 1)` | clears lowest set bit |
| `x & -x` | isolates lowest set bit |
| `x | (1 << i)` | set bit i |
| `x & ~(1 << i)` | clear bit i |
| `x ^ (1 << i)` | flip bit i |
| `(x >> i) & 1` | read bit i |
| `bin(x).count('1')` / `x.bit_count()` | popcount |
| `x ^ y` | bits where x and y differ |

XOR is **abelian, self-inverse**: `a ^ a = 0`, `a ^ 0 = a`, `(a^b)^a = b`. That makes it the king of "find the odd one" and "swap without temp".

**Subset enumeration:**
```python
sub = mask
while sub:
    process(sub)
    sub = (sub - 1) & mask
```

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Operator precedence (`&` < `==`) | Parenthesise: `(x & 1) == 0` |
| Negative numbers in two's-complement vs Python's unbounded ints | Mask with `& 0xFFFFFFFF` for 32-bit semantics |
| Signed shift in Python | `>>` arithmetic shift; not the same as JVM |
| Confusing XOR sum with arithmetic sum | "missing number 0..n" uses XOR or sum |

## 🧩 More problems

### Single Number — LC 136
```python
def singleNumber(nums):
    x = 0
    for v in nums: x ^= v
    return x
```

### Number of 1 Bits — LC 191
```python
def hammingWeight(n):
    c = 0
    while n:
        n &= n - 1; c += 1
    return c
```

### Counting Bits — LC 338
`dp[i] = dp[i >> 1] + (i & 1)`.

### Missing Number — LC 268
XOR all with `0..n`.

### Sum of Two Integers (no `+`) — LC 371
Loop with carry via XOR / AND-shift.

### Reverse Bits — LC 190
Build result bit by bit.

### Single Number II (every num thrice except one) — LC 137
Two-bit state machine: `ones, twos = (ones ^ x) & ~twos, (twos ^ x) & ~ones`.

## 🎤 Interview questions

1. **Why XOR for "single number"?** Pairs cancel.
2. **`x & (x-1)` why does it clear lowest set bit?** `x-1` flips trailing zeros and the lowest 1; AND keeps higher bits unchanged.
3. **Popcount in O(1)?** Hardware instruction (`popcnt`); in Python `int.bit_count()`.
4. **How to detect overflow when adding without `+`?** Carry stays non-zero after the loop bounded by word width.
5. **Subset enumeration runtime?** Σ over masks of size k = 2^k subsets → total 3^n across all masks.

## 📚 References
- "Bit Twiddling Hacks" — Sean Eron Anderson
- *Hacker's Delight* — Henry S. Warren Jr.
""",

"17-math-geometry": r"""

---

## 🔬 Deep dive — geometry essentials

- **Cross product** of 2D vectors (a, b): `a.x*b.y − a.y*b.x`. Sign tells orientation (CCW positive, CW negative, 0 collinear).
- **Distance squared** avoids `sqrt` when only comparing.
- **Polygon area** via shoelace: `½ |Σ (x_i·y_{i+1} − x_{i+1}·y_i)|`.
- **Convex hull**: Andrew monotone chain, O(n log n).
- **Line-segment intersection**: orientation test on the four endpoints.
- **Inside polygon**: ray-casting (parity of crossings) or winding number.

For math:
- `gcd(a,b) = gcd(b, a % b)`; `lcm = a*b // gcd`.
- Modular exponent: fast power.
- Sieve of Eratosthenes: O(n log log n) primes up to n.

## ⚠️ Pitfalls

| Pitfall | Fix |
|--------|-----|
| Floating-point comparison | Use epsilon, or work with integers when possible |
| Rotation off by 90° | Verify direction: `(x,y) → (y,-x)` is clockwise |
| Integer overflow on products | Python: fine; other languages: use 64-bit |
| Mixing radians and degrees | Be explicit; `math.radians/degrees` |
| Random `random.randint(a,b)` inclusivity | Inclusive on both ends in Python; `range` is exclusive |

## 🧩 More problems

### Rotate Image — LC 48
```python
def rotate(M):
    n = len(M)
    for i in range(n):
        for j in range(i+1, n):
            M[i][j], M[j][i] = M[j][i], M[i][j]      # transpose
    for row in M: row.reverse()                       # reverse each row
```

### Spiral Matrix — LC 54
Maintain four boundaries top/bottom/left/right; peel layers.

### Set Matrix Zeroes — LC 73
Use first row / first column as markers; O(1) extra space.

### Pow(x, n) — LC 50 (fast exponent)
```python
def myPow(x, n):
    if n < 0: x, n = 1/x, -n
    res = 1
    while n:
        if n & 1: res *= x
        x *= x; n >>= 1
    return res
```

### Happy Number — LC 202

### Plus One — LC 66

### Multiply Strings — LC 43

### Sqrt(x) — LC 69 (binary search on int)

## 🎤 Interview questions

1. **Rotate 90° — why transpose then reverse rows?** Transpose maps `(i,j) → (j,i)`, then reversing each row maps `(j,i) → (j, n-1-i)` = rotation.
2. **Convex hull complexity?** O(n log n) due to sorting.
3. **Why does fast exponentiation work?** `x^n = (x^(n/2))^2 · x^(n mod 2)`.
4. **Sieve memory optimisation?** Bitset; skip evens after marking 2.
5. **When use modular arithmetic?** Counting modulo a prime to avoid overflow.

## 📚 References
- "Computational Geometry" — Mark de Berg et al.
- CP-Algorithms.com — number-theory pages
""",
}

def insert_image(path: Path, img_rel: str):
    text = path.read_text(encoding="utf-8")
    if f"![Diagram]({img_rel})" in text:
        return
    # insert after the first top-level heading line
    lines = text.split("\n")
    out = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("# "):
            out.append("")
            out.append(f"![Diagram]({img_rel})")
            inserted = True
    path.write_text("\n".join(out), encoding="utf-8")

def append_expansion(path: Path, content: str):
    text = path.read_text(encoding="utf-8")
    if "## 🔬 Deep dive" in text or "## Deep dive" in text:
        return  # already expanded
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + content, encoding="utf-8")

for stem, expansion in EXPANSIONS.items():
    md = ROOT / f"{stem}.md"
    if not md.exists():
        print("MISSING:", md); continue
    insert_image(md, f"diagrams/{stem}.png")
    append_expansion(md, expansion)
    print("expanded:", stem)
