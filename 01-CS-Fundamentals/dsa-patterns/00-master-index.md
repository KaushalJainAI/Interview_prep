# DSA Patterns -- Master Index

Curriculum source: **Striver's A2Z Sheet** (takeuforward.org) + **NeetCode 150** (neetcode.io). Both converge on the same ~18 patterns; this folder covers every one.

**Format of each pattern file** (the format you asked for):
1. **The pattern** -- when to apply, complexity
2. **Master template code** -- the canonical implementation you should know cold
3. **Diagram / mental model**
4. **Variations** -- for each "similar" problem: *what changes from the template* + logic + diagram + code

## How to use this folder
- **First pass**: read each pattern file end-to-end (~20-30 min each)
- **Practice pass**: take the variations, hide the code, try to write it from the template
- **Pre-interview**: re-read just the templates + variation summaries (~5 min per pattern)

## Pattern files
| # | Pattern | Striver step | NeetCode category | Problems covered |
|---|---------|--------------|--------------------|------------------|
| 01 | [Arrays & Hashing](01-arrays-hashing.md) | 3 | Arrays & Hashing | 8 |
| 02 | [Two Pointers](02-two-pointers.md) | 3, 10 | Two Pointers | 6 |
| 03 | [Sliding Window](03-sliding-window.md) | 10 | Sliding Window | 7 |
| 04 | [Binary Search](04-binary-search.md) | 4 | Binary Search | 8 |
| 05 | [Stack & Monotonic Stack](05-stack.md) | 9 | Stack | 7 |
| 06 | [Linked List](06-linked-list.md) | 6 | Linked List | 8 |
| 07 | [Trees](07-trees.md) | 13, 14 | Trees | 10 |
| 08 | [Tries](08-tries.md) | 17 | Tries | 4 |
| 09 | [Heap / Priority Queue](09-heap.md) | 11 | Heap / PQ | 6 |
| 10 | [Backtracking & Recursion](10-backtracking.md) | 7 | Backtracking | 8 |
| 11 | [Graphs](11-graphs.md) | 15 | Graphs / Advanced Graphs | 10 |
| 12 | [Dynamic Programming 1D](12-dp-1d.md) | 16 | 1-D DP | 8 |
| 13 | [Dynamic Programming 2D](13-dp-2d.md) | 16 | 2-D DP | 7 |
| 14 | [Greedy](14-greedy.md) | 12 | Greedy | 6 |
| 15 | [Intervals](15-intervals.md) | 12 | Intervals | 6 |
| 16 | [Bit Manipulation](16-bit-manipulation.md) | 8 | Bit Manipulation | 6 |
| 17 | [Math & Geometry](17-math-geometry.md) | -- | Math & Geometry | 5 |

## Striver-specific (covered in mapped pattern files)
- **Sorting** (step 2) -> integrated into Arrays (merge sort) + DP (recursion patterns)
- **Strings basic/medium** (steps 5, 18) -> covered in Two Pointers, Sliding Window, Tries, DP

## Interview strategy (universal)
1. **Restate the problem** -> catch ambiguity
2. **Edge cases out loud** -> empty, single, all-same, max-size, duplicates, negatives
3. **State brute force + complexity** -> "let's optimize"
4. **Name the pattern** -> "looks like sliding window because..."
5. **Trace one example by hand**
6. **Code while narrating** -> variable purpose, invariant
7. **Test mentally** on example + edge case
8. **Final time + space complexity**

## Time complexity cheat-sheet
| Big-O | Acceptable input size |
|-------|------------------------|
| O(log n) | n up to 1018 |
| O(n) | n up to 108 |
| O(n log n) | n up to 106 |
| O(n sqrtn) | n up to 105 |
| O(n^2) | n up to 104 |
| O(n^3) | n up to 500 |
| O(2ⁿ) | n up to 20 |
| O(n!) | n up to 11 |

Match input size to the algorithm -- if `n <= 20`, brute-force/backtracking is fine; if `n = 105`, you need O(n log n) or better.
