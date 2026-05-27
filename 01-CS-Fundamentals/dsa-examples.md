# DSA -- Worked Examples by Pattern

> Companion to [dsa-cheatsheet.md](dsa-cheatsheet.md). Each section: **pattern -> 1-3 fully-solved canonical problems** with the dialogue you'd give in the interview.

---

## 1. Two Pointers

### Example 1.1 -- Two Sum II (sorted array) -- LC 167
**Problem**: Given a **sorted** array, return indices of two numbers that sum to target.

**Brute force**: O(n^2) nested loop.

**Optimal -- two pointers, O(n) time, O(1) space**:
```python
def twoSum(nums, target):
    l, r = 0, len(nums) - 1
    while l < r:
        s = nums[l] + nums[r]
        if s == target: return [l + 1, r + 1]   # LC uses 1-indexed
        elif s < target: l += 1                  # need a bigger sum
        else: r -= 1                             # need a smaller sum
    return []
```

**Why it works**: array is sorted. If `nums[l] + nums[r] < target`, increasing `r` only makes it bigger; decreasing `l` makes it smaller -- pointless. So move `l`. Symmetric logic for the other direction.

### Example 1.2 -- Container With Most Water -- LC 11
**Problem**: Heights array; pick two lines that form the largest water container.

**Key insight**: Area = `min(h[l], h[r]) x (r - l)`. Always move the **shorter** pointer inward -- moving the taller one cannot improve area (width drops, min stays the same).

```python
def maxArea(h):
    l, r = 0, len(h) - 1
    best = 0
    while l < r:
        best = max(best, min(h[l], h[r]) * (r - l))
        if h[l] < h[r]: l += 1
        else:           r -= 1
    return best
```

### Example 1.3 -- Remove Duplicates from Sorted Array -- LC 26
**In-place** O(1) extra space:
```python
def removeDuplicates(nums):
    if not nums: return 0
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[read - 1]:
            nums[write] = nums[read]
            write += 1
    return write
```
Pattern: **read pointer scans, write pointer advances only on accept.**

---

## 2. Sliding Window

### Example 2.1 -- Longest Substring Without Repeating Characters -- LC 3
**Problem**: Longest substring with all unique characters.

```python
def lengthOfLongestSubstring(s):
    seen = {}            # char -> last seen index
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1     # jump past the prior occurrence
        seen[ch] = right
        best = max(best, right - left + 1)
    return best
```

**Walk-through** on `"abcabcbb"`:
| right | ch | seen[ch] | left after | window | best |
|-------|----|---------|------------|--------|------|
| 0 | a | -- | 0 | "a" | 1 |
| 1 | b | -- | 0 | "ab" | 2 |
| 2 | c | -- | 0 | "abc" | 3 |
| 3 | a | 0 >= 0 -> left=1 | 1 | "bca" | 3 |
| 4 | b | 1 >= 1 -> left=2 | 2 | "cab" | 3 |
| 5 | c | 2 >= 2 -> left=3 | 3 | "abc" | 3 |
| 6 | b | 4 >= 3 -> left=5 | 5 | "cb" | 3 |
| 7 | b | 6 >= 5 -> left=7 | 7 | "b" | 3 |

### Example 2.2 -- Minimum Window Substring -- LC 76
**Problem**: Smallest window in `s` containing all characters of `t`.

```python
from collections import Counter

def minWindow(s, t):
    need = Counter(t)
    missing = len(t)         # total chars still needed
    l = start = end = 0
    best_len = float('inf')

    for r, ch in enumerate(s):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1

        while missing == 0:                          # valid window
            if r - l + 1 < best_len:
                best_len = r - l + 1
                start, end = l, r
            need[s[l]] += 1
            if need[s[l]] > 0:
                missing += 1
            l += 1

    return s[start:end+1] if best_len != float('inf') else ""
```

**Pattern**: expand right until valid, then shrink left while still valid, tracking best. Standard template for "minimum window with property" problems.

---

## 3. Binary Search

### Example 3.1 -- Classic Binary Search -- LC 704
```python
def search(nums, target):
    l, r = 0, len(nums) - 1
    while l <= r:
        m = l + (r - l) // 2          # avoid overflow (matters in C++/Java)
        if nums[m] == target: return m
        if nums[m] < target: l = m + 1
        else:                r = m - 1
    return -1
```

### Example 3.2 -- Search in Rotated Sorted Array -- LC 33
**Problem**: Array sorted then rotated. Find target in O(log n).

**Key idea**: at each step, *one half is sorted*. Check which, then test if target is in that sorted half.

```python
def search(nums, target):
    l, r = 0, len(nums) - 1
    while l <= r:
        m = (l + r) // 2
        if nums[m] == target: return m

        if nums[l] <= nums[m]:                # left half sorted
            if nums[l] <= target < nums[m]:
                r = m - 1
            else:
                l = m + 1
        else:                                  # right half sorted
            if nums[m] < target <= nums[r]:
                l = m + 1
            else:
                r = m - 1
    return -1
```

### Example 3.3 -- Binary Search on Answer: Koko Eating Bananas -- LC 875
**Problem**: Min eating speed K such that all bananas eaten within H hours.

**Insight**: Answer K lies in `[1, max(piles)]`. Function `f(K) = hours_needed(K)` is monotonic -- bigger K, fewer hours. Binary search K.

```python
def minEatingSpeed(piles, h):
    def hours(k):
        return sum((p + k - 1) // k for p in piles)   # ceil

    l, r = 1, max(piles)
    while l < r:
        m = (l + r) // 2
        if hours(m) <= h:
            r = m                    # m is feasible, try smaller
        else:
            l = m + 1
    return l
```

**Pattern recognition**: "minimum X such that condition" + monotonic condition -> binary search on X.

---

## 4. BFS -- shortest path / level-order

### Example 4.1 -- Binary Tree Level Order Traversal -- LC 102
```python
from collections import deque

def levelOrder(root):
    if not root: return []
    result, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):           # process exactly one level
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result
```
**Trick**: snapshot `len(q)` to know how many nodes are at the current level.

### Example 4.2 -- Rotting Oranges -- LC 994
**Problem**: Grid; rotten orange (2) rots adjacent fresh (1) in 1 minute. Return minutes until all rotten, or -1 if impossible.

**Multi-source BFS**: start with all initially-rotten oranges in the queue at level 0.

```python
def orangesRotting(grid):
    rows, cols = len(grid), len(grid[0])
    q = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2: q.append((r, c, 0))
            elif grid[r][c] == 1: fresh += 1

    time = 0
    while q:
        r, c, t = q.popleft()
        time = max(time, t)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                q.append((nr, nc, t + 1))

    return time if fresh == 0 else -1
```

---

## 5. DFS -- graph / tree traversal

### Example 5.1 -- Number of Islands -- LC 200
```python
def numIslands(grid):
    if not grid: return 0
    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '0'             # mark visited
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)
    return count
```

### Example 5.2 -- Course Schedule (cycle detection) -- LC 207
**Problem**: Given prerequisites, can you finish all courses? (Detect cycle in directed graph.)

**Kahn's algorithm (topological sort via BFS)**:
```python
from collections import defaultdict, deque

def canFinish(numCourses, prerequisites):
    graph = defaultdict(list)
    indeg = [0] * numCourses
    for a, b in prerequisites:        # b -> a
        graph[b].append(a)
        indeg[a] += 1

    q = deque([i for i in range(numCourses) if indeg[i] == 0])
    done = 0
    while q:
        u = q.popleft()
        done += 1
        for v in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)

    return done == numCourses   # all nodes ordered -> no cycle
```
**This is exactly the AIAAS DAG validator** -- interviewer gold to mention.

---

## 6. Backtracking

### Example 6.1 -- Subsets -- LC 78
```python
def subsets(nums):
    result = []
    def bt(start, path):
        result.append(path[:])             # snapshot
        for i in range(start, len(nums)):
            path.append(nums[i])
            bt(i + 1, path)
            path.pop()                     # undo
    bt(0, [])
    return result
```
**Trace** for `nums=[1,2,3]`:
```
[] -> [1] -> [1,2] -> [1,2,3] -> [1,3] -> [2] -> [2,3] -> [3]
```
Pattern: **choose -> recurse -> un-choose** (the "decision tree" walk).

### Example 6.2 -- Permutations -- LC 46
```python
def permute(nums):
    result, used = [], [False]*len(nums)
    def bt(path):
        if len(path) == len(nums):
            result.append(path[:]); return
        for i in range(len(nums)):
            if used[i]: continue
            used[i] = True
            path.append(nums[i])
            bt(path)
            path.pop()
            used[i] = False
    bt([])
    return result
```

### Example 6.3 -- N-Queens -- LC 51
```python
def solveNQueens(n):
    result = []
    cols, diag1, diag2 = set(), set(), set()    # col, r-c, r+c

    def bt(r, board):
        if r == n:
            result.append(["." * c + "Q" + "." * (n - c - 1) for c in board])
            return
        for c in range(n):
            if c in cols or (r-c) in diag1 or (r+c) in diag2: continue
            cols.add(c); diag1.add(r-c); diag2.add(r+c)
            board.append(c)
            bt(r+1, board)
            board.pop()
            cols.remove(c); diag1.remove(r-c); diag2.remove(r+c)

    bt(0, [])
    return result
```

---

## 7. Dynamic Programming

### Example 7.1 -- House Robber -- LC 198
**Problem**: Can't rob two adjacent houses. Max money.

**Recurrence**: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`

```python
def rob(nums):
    prev2, prev1 = 0, 0
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1
```
O(n) time, **O(1) space** -- interviewer loves the rolling-variable optimization.

### Example 7.2 -- Coin Change -- LC 322
**Problem**: Fewest coins to make `amount`. Return -1 if impossible.

```python
def coinChange(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1
```
**dp[a] = min coins to make amount a.** Transition: try each coin, look up `dp[a-c]`.

### Example 7.3 -- Longest Common Subsequence -- LC 1143
**Problem**: LCS of two strings.

```python
def longestCommonSubsequence(s, t):
    m, n = len(s), len(t)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```
2D DP. Same shape as edit distance.

### Example 7.4 -- 0/1 Knapsack
```python
def knapsack(weights, values, W):
    n = len(weights)
    dp = [[0]*(W+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for w in range(W+1):
            dp[i][w] = dp[i-1][w]                       # skip item i
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w],
                               dp[i-1][w-weights[i-1]] + values[i-1])
    return dp[n][W]
```

---

## 8. Heap / Priority Queue

### Example 8.1 -- Kth Largest Element -- LC 215
**O(n log k)** using min-heap of size k:
```python
import heapq
def findKthLargest(nums, k):
    h = []
    for x in nums:
        heapq.heappush(h, x)
        if len(h) > k: heapq.heappop(h)
    return h[0]
```
At the end, the heap contains the k largest, smallest at top -> answer.

### Example 8.2 -- Top K Frequent Elements -- LC 347
```python
from collections import Counter
def topKFrequent(nums, k):
    return [x for x, _ in Counter(nums).most_common(k)]
# OR
def topKFrequent2(nums, k):
    freq = Counter(nums)
    return heapq.nlargest(k, freq.keys(), key=freq.get)
```

### Example 8.3 -- Find Median from Data Stream -- LC 295
**Two heaps**: max-heap for lower half, min-heap for upper half.
```python
class MedianFinder:
    def __init__(self):
        self.low = []     # max-heap (negate)
        self.high = []    # min-heap

    def addNum(self, num):
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def findMedian(self):
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2
```

---

## 9. Prefix Sum

### Example 9.1 -- Subarray Sum Equals K -- LC 560
**Problem**: # subarrays with sum K.

**Brute** O(n^2). **Trick**: `sum(arr[i..j]) = prefix[j+1] - prefix[i]`. So count pairs `(i, j)` where `prefix[j+1] - prefix[i] = K` ⇔ `prefix[i] = prefix[j+1] - K`.

Hash count of prefix sums seen so far:
```python
def subarraySum(nums, k):
    count = 0
    cur = 0
    seen = {0: 1}                  # empty prefix
    for x in nums:
        cur += x
        count += seen.get(cur - k, 0)
        seen[cur] = seen.get(cur, 0) + 1
    return count
```

---

## 10. Linked List

### Example 10.1 -- Reverse Linked List -- LC 206
```python
def reverseList(head):
    prev, cur = None, head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev
```
Three pointers. **Always practice writing this without bugs.**

### Example 10.2 -- Detect Cycle (Floyd's tortoise & hare) -- LC 141
```python
def hasCycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast: return True
    return False
```
O(n) time, O(1) space. If there's a cycle, fast catches slow.

### Example 10.3 -- Merge Two Sorted Lists -- LC 21
```python
def mergeTwoLists(a, b):
    dummy = tail = ListNode()
    while a and b:
        if a.val <= b.val:
            tail.next = a; a = a.next
        else:
            tail.next = b; b = b.next
        tail = tail.next
    tail.next = a or b
    return dummy.next
```
**Dummy node** simplifies edge cases -- recurring pattern in LL problems.

---

## 11. Trie

### Example 11.1 -- Implement Trie -- LC 208
```python
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for c in word:
            node = node.setdefault(c, {})
        node['$'] = True

    def search(self, word):
        node = self._walk(word)
        return node is not None and '$' in node

    def startsWith(self, prefix):
        return self._walk(prefix) is not None

    def _walk(self, s):
        node = self.root
        for c in s:
            if c not in node: return None
            node = node[c]
        return node
```

---

## 12. Union-Find

### Example 12.1 -- Number of Connected Components -- LC 323
```python
class DSU:
    def __init__(self, n):
        self.p = list(range(n))
        self.r = [0]*n
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]      # path compression
            x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False              # already connected
        if self.r[ra] < self.r[rb]: ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]: self.r[ra] += 1
        return True

def countComponents(n, edges):
    dsu = DSU(n)
    components = n
    for a, b in edges:
        if dsu.union(a, b):
            components -= 1
    return components
```

---

## 13. Bit Manipulation

### Example 13.1 -- Single Number -- LC 136
**Every number appears twice except one.** XOR cancels duplicates.
```python
def singleNumber(nums):
    x = 0
    for n in nums: x ^= n
    return x
```

### Example 13.2 -- Number of 1 Bits -- LC 191
```python
def hammingWeight(n):
    count = 0
    while n:
        n &= n - 1                # drops lowest set bit
        count += 1
    return count
```

---

## 14. Greedy

### Example 14.1 -- Jump Game -- LC 55
**Can you reach the last index?** Greedy on max reachable.
```python
def canJump(nums):
    reach = 0
    for i, jump in enumerate(nums):
        if i > reach: return False
        reach = max(reach, i + jump)
    return True
```

### Example 14.2 -- Meeting Rooms II -- LC 253
**Min meeting rooms** = max simultaneous meetings.
```python
import heapq
def minMeetingRooms(intervals):
    intervals.sort(key=lambda x: x[0])
    rooms = []                  # heap of end times
    for s, e in intervals:
        if rooms and rooms[0] <= s:
            heapq.heappop(rooms)
        heapq.heappush(rooms, e)
    return len(rooms)
```

---

## Interview tactics -- what to say while solving
1. **Restate** the problem in your own words (catch ambiguity)
2. **Edge cases out loud**: empty, single element, all-same, max-size
3. **State brute force first** with its complexity -> "let's optimize"
4. **Name the pattern** ("this looks like sliding-window because...")
5. **Walk through one example by hand** on paper before coding
6. **Talk while coding** -- narrate variable purpose, invariant
7. **Test mentally** on the example you walked through, plus an edge case
8. **State final time + space**

**If stuck**: ask for a hint after stating what you've tried. Better than silence.

## Pattern -> Problem cheat-sheet (top 30 to be fluent in)
| Pattern | Must-know problems |
|---------|--------------------|
| Two pointers | 167, 11, 26, 15 (3Sum) |
| Sliding window | 3, 76, 209, 424 |
| Binary search | 704, 33, 875, 410 |
| BFS | 102, 994, 127 (Word Ladder) |
| DFS | 200, 207, 695 |
| Backtracking | 78, 46, 51, 39 (Combination Sum) |
| DP 1D | 198, 322, 300 (LIS), 139 (Word Break) |
| DP 2D | 1143, 72 (Edit Distance), 64 (Min Path Sum) |
| Heap | 215, 347, 295, 23 (Merge K) |
| Prefix sum | 560, 238, 53 (Max Subarray) |
| Linked list | 206, 141, 21, 19 (Remove Nth from End) |
| Trie | 208, 212 (Word Search II) |
| Union-Find | 323, 547, 684 (Redundant Connection) |
| Bit | 136, 191, 338 (Counting Bits) |
| Greedy | 55, 45, 253, 435 |
