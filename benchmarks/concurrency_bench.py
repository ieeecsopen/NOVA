"""Prototype scheduler benchmark for the RegionLab work-stealing model.

This is not a production NOVA runtime benchmark. It measures the current
prototype scheduler implementation in `regionlab/runtime.py` so that the
repo can report honest numbers for the work-stealing model.
"""

from __future__ import annotations

import os
import sys
import time

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from regionlab.runtime import TaskScheduler


def bench_task_throughput(task_count: int = 200_000, workers: int = 4) -> float:
    scheduler = TaskScheduler(worker_count=workers)
    scheduler.start()
    start = time.perf_counter()

    for i in range(task_count):
        scheduler.spawn(lambda i=i: None, worker_index=i % workers)

    deadline = time.perf_counter() + 5.0
    while True:
        if all(q.is_empty() for q in scheduler.queues):
            break
        if time.perf_counter() >= deadline:
            break
        time.sleep(0.001)

    elapsed = time.perf_counter() - start
    scheduler.shutdown(timeout=1.0)
    return task_count / elapsed if elapsed > 0 else 0.0


def main() -> int:
    workers = 4
    task_count = 200_000
    throughput = bench_task_throughput(task_count=task_count, workers=workers)
    print(f"Prototype task throughput: {throughput:,.0f} tasks/sec")
    print(f"workers={workers} task_count={task_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
