# Operating Systems -- Interview Cheatsheet

> Goal: answer OS interview questions clearly: processes, threads, memory, scheduling, synchronization, deadlocks, filesystems, I/O, and Linux debugging.

## TL;DR

| Topic | One-line answer |
|-------|-----------------|
| Process | Running program with its own virtual address space and resources |
| Thread | Execution unit inside a process; shares heap/code/files with sibling threads |
| Context switch | CPU saves current execution state and loads another |
| Virtual memory | Per-process address abstraction backed by RAM + disk |
| Page fault | Accessed virtual page is not in RAM or violates permissions |
| Race condition | Output depends on timing/interleaving of concurrent operations |
| Deadlock | Threads wait forever in a cycle of resource ownership |
| System call | User program asks kernel to perform privileged operation |

---

## 1. Process vs thread

| Feature | Process | Thread |
|---------|---------|--------|
| Address space | Separate | Shared within process |
| Creation cost | Higher | Lower |
| Communication | IPC needed | Shared memory directly |
| Crash isolation | Better | One bad thread can crash process |
| Context switch | Heavier | Lighter |
| Example | Browser tab process | Request worker thread |

**Interview answer:** A process is an isolated running program. A thread is a lighter execution path inside a process. Threads share memory, so communication is easier but synchronization is harder.

## 2. Process memory layout

```text
High address
+------------------+
| Stack            | function calls, local variables
|        down      |
|                  |
|        up        |
| Heap             | malloc/new, Python objects
| BSS              | zero-initialized globals
| Data             | initialized globals
| Text/code        | executable instructions
+------------------+
Low address
```

### Stack vs heap

| Stack | Heap |
|-------|------|
| Function calls, local variables | Dynamic allocation |
| Fast allocation/deallocation | Slower, allocator-managed |
| Limited size | Larger |
| Automatically freed | Must be freed by runtime/program |
| Stack overflow possible | Memory leak/fragmentation possible |

Python note: Python objects usually live on the heap; local variables are references in stack frames.

## 3. User mode vs kernel mode

User mode cannot directly access hardware or arbitrary memory. Kernel mode can.

Common system calls:
- `read`, `write`, `open`, `close`
- `fork`, `exec`, `wait`
- `socket`, `bind`, `listen`, `accept`
- `mmap`, `brk`

**Why system calls are expensive:** mode switch + validation + kernel work + possible blocking.

## 4. Context switching

The OS scheduler pauses one task and resumes another.

What gets saved:
- program counter
- registers
- stack pointer
- memory mapping metadata
- scheduling/accounting info

Too many context switches reduce throughput due to overhead and cache/TLB misses.

## 5. Scheduling

| Algorithm | Idea | Pros | Cons |
|----------|------|------|------|
| FCFS | First come, first served | Simple | Convoy effect |
| SJF | Shortest job first | Low average wait | Needs job length estimate |
| Round Robin | Fixed time quantum | Fair for interactive systems | Too-small quantum causes overhead |
| Priority | Highest priority first | Supports importance | Starvation |
| Multilevel feedback queue | Adjust priority based on behavior | Practical | Complex |

Key terms:
- **Throughput:** jobs completed per unit time
- **Latency:** time for one job/request
- **Waiting time:** time spent ready but not running
- **Turnaround time:** submit to completion
- **Starvation:** task waits indefinitely

## 6. Concurrency and synchronization

### Race condition

```python
# Two threads do this at the same time
counter = counter + 1
```

This is not atomic: read -> add -> write. Interleaving can lose updates.

### Critical section

Part of code that accesses shared mutable state and must not run concurrently.

### Locks, mutexes, semaphores

| Primitive | Use |
|-----------|-----|
| Mutex/lock | Only one thread enters critical section |
| Semaphore | Allow up to N concurrent accesses |
| Binary semaphore | Similar to mutex, but ownership semantics differ |
| Condition variable | Sleep until condition becomes true |
| Read-write lock | Many readers or one writer |
| Spinlock | Busy-wait; useful only for very short waits |

**Mutex vs semaphore:** Mutex protects ownership of a resource, usually unlocked by the same thread that locked it. Semaphore is a counter controlling access to N resources.

## 7. Deadlock

Deadlock requires all four Coffman conditions:

1. **Mutual exclusion:** resource cannot be shared.
2. **Hold and wait:** thread holds one resource while waiting for another.
3. **No preemption:** resources cannot be forcibly taken.
4. **Circular wait:** cycle of waiting threads.

### Prevention strategies

| Strategy | Example |
|----------|---------|
| Break circular wait | Always acquire locks in global order |
| Break hold-and-wait | Acquire all locks upfront |
| Add timeout | Give up and retry |
| Detect and recover | Deadlock detector kills/rolls back one worker |

Interview line: "In production code, I usually enforce lock ordering, keep lock scopes small, and add timeouts around external waits."

## 8. Virtual memory and paging

Virtual memory gives each process the illusion of a large private address space.

Components:
- **Virtual address:** address used by process
- **Physical address:** actual RAM location
- **Page:** fixed-size block, often 4 KB
- **Page table:** maps virtual pages to physical frames
- **TLB:** CPU cache of page-table translations

### Page fault

Occurs when a page is not present or permission check fails.

Types:
- valid but not loaded -> OS loads from disk or swap
- invalid address -> segmentation fault
- write to read-only page -> protection fault

## 9. Paging vs segmentation

| Paging | Segmentation |
|--------|--------------|
| Fixed-size pages | Variable-size logical segments |
| Reduces external fragmentation | Matches program structure |
| Page table maps pages to frames | Segment table stores base + limit |
| Common in modern OSes | Mostly historical / combined conceptually |

## 10. Cache, buffers, and memory-mapped files

| Concept | Meaning |
|---------|---------|
| Buffer | Temporary memory used while moving data |
| Cache | Stores data likely to be reused |
| Page cache | OS caches file blocks in RAM |
| `mmap` | Maps file contents into process address space |

Why file reads get faster the second time: OS page cache.

## 11. File systems

Core concepts:
- file metadata: inode, size, permissions, timestamps
- directory: mapping from name to inode
- hard link: another name for same inode
- symbolic link: special file pointing to path
- journaling: log metadata changes to recover after crash

### Hard link vs symlink

| Hard link | Symlink |
|-----------|---------|
| Same inode | Separate inode |
| Cannot usually cross filesystems | Can cross filesystems |
| Still works if original name deleted | Breaks if target path deleted |
| Not allowed for directories in most systems | Can point to directories |

## 12. I/O models

| Model | Meaning |
|-------|---------|
| Blocking I/O | Thread waits until operation completes |
| Non-blocking I/O | Call returns immediately if not ready |
| Multiplexing | `select`/`poll`/`epoll` waits for many fds |
| Async I/O | Kernel/runtime notifies when operation completes |

For high-concurrency servers, event loops avoid one thread per connection.

## 13. Linux commands for interviews/debugging

| Task | Command |
|------|---------|
| List processes | `ps aux`, `top`, `htop` |
| Find process using port | `lsof -i :8000`, `netstat -ano` on Windows |
| Kill process | `kill PID`, `kill -9 PID` only as last resort |
| Disk usage | `df -h`, `du -sh *` |
| Memory | `free -h`, `vmstat` |
| Open files | `lsof -p PID` |
| System calls | `strace -p PID` |
| Logs | `journalctl -u service`, `tail -f app.log` |
| Permissions | `chmod`, `chown`, `ls -l` |

## 14. Common production failure patterns

| Symptom | Likely OS-level cause |
|---------|-----------------------|
| App slow under load | CPU saturation, lock contention, too many context switches |
| Random `OOMKilled` | memory leak, high heap, container memory limit |
| `Too many open files` | fd leak, low `ulimit` |
| High disk latency | swap, bad disk, noisy neighbor, logging overload |
| Server accepts no new connections | backlog full, fd limit, event loop blocked |
| CPU high but throughput low | busy-wait, spinlock, GC, context-switch overhead |

## 15. Interview questions

1. **Process vs thread?** Process has isolated address space; threads share process memory and are cheaper but need synchronization.
2. **What happens during a context switch?** Kernel saves CPU state of current task, updates scheduler state, restores another task, causing overhead and cache/TLB disruption.
3. **What is a deadlock?** A cycle of threads waiting for resources. Requires mutual exclusion, hold-and-wait, no preemption, and circular wait.
4. **Mutex vs semaphore?** Mutex is ownership lock for one critical section; semaphore is a counter allowing N concurrent accesses.
5. **What is virtual memory?** Per-process address abstraction mapped to physical memory by page tables; enables isolation, paging, and large address spaces.
6. **What is a page fault?** CPU accessed a virtual page not currently mapped/present or with invalid permissions; kernel handles it or kills the process.
7. **Stack vs heap?** Stack stores call frames/local references and is automatically managed; heap stores dynamically allocated objects.
8. **Why is `mmap` useful?** Lets file contents be accessed like memory; OS loads pages on demand and can share pages between processes.
9. **What causes `Too many open files`?** File descriptor leak or low process/system fd limit; inspect with `lsof`, fix close logic or raise limit.
10. **How do event loops scale?** One thread multiplexes many I/O operations using non-blocking sockets and readiness notifications like `epoll`.

## 16. Quick revision checklist

- [ ] Explain process vs thread.
- [ ] Draw process memory layout.
- [ ] Explain context switching.
- [ ] Explain deadlock and prevention.
- [ ] Explain virtual memory, paging, TLB, page fault.
- [ ] Explain mutex, semaphore, condition variable.
- [ ] Explain blocking vs non-blocking vs async I/O.
- [ ] Know Linux debugging commands.

