"""Concurrent work-stealing regression tests for the Region XOR model."""
from __future__ import annotations

import threading

from regionlab.runtime import (ChaseLevDeque, RegionAccessError, RegionFrame,
                               RegionRuntime, TaskScheduler, WorkStealingScheduler)


def test_stolen_frame_revokes_donor_before_thief_can_write() -> None:
    regions = RegionRuntime()
    regions.open("r")
    lease = regions.borrow_exclusive("r", "worker-a")
    frame = RegionFrame("worker-a", lease)
    scheduler = WorkStealingScheduler(regions)
    entered = threading.Event()
    release = threading.Event()
    failures: list[BaseException] = []

    def donor() -> None:
        try:
            def action() -> None:
                entered.set()
                release.wait(timeout=2)
            scheduler.run(frame, "worker-a", action)
        except BaseException as ex:  # recorded for the harness assertion
            failures.append(ex)

    worker = threading.Thread(target=donor)
    worker.start()
    assert entered.wait(timeout=2), "donor never entered its safe-point section"

    # A thief cannot migrate an executing frame: it blocks on ``frame._lock``.
    thief_done = threading.Event()
    thief = threading.Thread(
        target=lambda: (scheduler.steal(frame, "worker-a", "worker-b"),
                        thief_done.set()))
    thief.start()
    assert not thief_done.wait(timeout=0.05), "frame migrated while donor ran"
    release.set()
    worker.join(timeout=2)
    thief.join(timeout=2)
    assert not worker.is_alive() and not thief.is_alive()
    assert not failures, failures

    try:
        scheduler.run(frame, "worker-a", lambda: None)
    except RegionAccessError:
        pass
    else:
        raise AssertionError("donor retained write access after frame theft")
    assert scheduler.run(frame, "worker-b", lambda: 7) == 7


def test_repeated_concurrent_steals_preserve_xor() -> None:
    regions = RegionRuntime()
    regions.open("r")
    lease = regions.borrow_exclusive("r", "worker-a")
    frame = RegionFrame("worker-a", lease)
    scheduler = WorkStealingScheduler(regions)
    failures: list[BaseException] = []
    start = threading.Barrier(3)

    def migrate(donor: str, thief: str) -> None:
        try:
            start.wait()
            for _ in range(500):
                try:
                    scheduler.steal(frame, donor, thief)
                except RegionAccessError:
                    # The competing worker won this round; that is a normal
                    # work-stealing race, not an XOR violation.
                    continue
                donor, thief = thief, donor
        except BaseException as ex:
            failures.append(ex)

    a = threading.Thread(target=migrate, args=("worker-a", "worker-b"))
    b = threading.Thread(target=migrate, args=("worker-a", "worker-b"))
    a.start()
    b.start()
    start.wait()
    for _ in range(500):
        shared, exclusive = regions.snapshot("r")
        assert not (shared and exclusive), (shared, exclusive)
    a.join(timeout=2)
    b.join(timeout=2)
    assert not a.is_alive() and not b.is_alive()
    assert not failures, failures


def test_preemption_races_with_writes() -> None:
    regions = RegionRuntime()
    regions.open("r")
    lease = regions.borrow_exclusive("r", "worker-a")
    frame = RegionFrame("worker-a", lease)
    scheduler = WorkStealingScheduler(regions)
    failures: list[BaseException] = []
    start = threading.Barrier(3)
    writes = 0
    writes_lock = threading.Lock()

    def worker(name: str, other: str) -> None:
        nonlocal writes
        try:
            start.wait()
            for _ in range(1000):
                try:
                    def write() -> None:
                        nonlocal writes
                        with writes_lock:
                            writes += 1

                    scheduler.run(frame, name, write)
                except RegionAccessError:
                    pass
                try:
                    scheduler.steal(frame, other, name)
                except RegionAccessError:
                    pass
        except BaseException as ex:
            failures.append(ex)

    a = threading.Thread(target=worker, args=("worker-a", "worker-b"))
    b = threading.Thread(target=worker, args=("worker-b", "worker-a"))
    a.start()
    b.start()
    start.wait()
    for _ in range(1000):
        shared, exclusive = regions.snapshot("r")
        assert not (shared and exclusive), (shared, exclusive)
    a.join(timeout=5)
    b.join(timeout=5)
    assert not a.is_alive() and not b.is_alive()
    assert not failures, failures
    assert writes > 0


def test_chase_lev_deque_work_stealing_round_trip() -> None:
    deque = ChaseLevDeque[int]()
    deque.push_bottom(1)
    deque.push_bottom(2)
    assert deque.pop_bottom() == 2
    assert deque.steal_top() == 1
    assert deque.is_empty()


def test_chase_lev_deque_resizes_cleanly_after_steal() -> None:
    deque = ChaseLevDeque[int](initial_capacity=4)
    deque.push_bottom(1)
    deque.push_bottom(2)
    assert deque.steal_top() == 1
    deque.push_bottom(3)
    deque.push_bottom(4)
    deque.push_bottom(5)
    popped = [deque.pop_bottom() for _ in range(4)]
    assert popped == [5, 4, 3, 2], f"unexpected pop sequence: {popped}"
    assert deque.is_empty()


def test_task_scheduler_steals_work_from_other_worker() -> None:
    scheduler = TaskScheduler(worker_count=2)
    seen: list[int] = []
    scheduler.start()
    scheduler.spawn(lambda: seen.append(1), worker_index=0)
    scheduler.spawn(lambda: seen.append(2), worker_index=1)
    for _ in range(200):
        if len(seen) >= 2:
            break
        import time
        time.sleep(0.01)
    scheduler.shutdown(timeout=0.5)
    assert len(seen) >= 2, seen


def run() -> None:
    test_stolen_frame_revokes_donor_before_thief_can_write()
    test_repeated_concurrent_steals_preserve_xor()
    test_preemption_races_with_writes()
    test_chase_lev_deque_work_stealing_round_trip()
    test_chase_lev_deque_resizes_cleanly_after_steal()
    test_task_scheduler_steals_work_from_other_worker()
