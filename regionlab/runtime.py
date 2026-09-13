"""Thread-safe reference handoff model for Region XOR.

RegionLab's language checker is deliberately single-threaded, but a task
runtime must preserve the same invariant while a suspended frame is moved to
another worker.  This module is the small executable model of that boundary:
all lease state and all frame-owner changes are protected by the same
per-frame critical section.  A worker that has lost a stolen frame can no
longer use its exclusive lease.

It is intentionally not a production scheduler.  There is no native task
runtime in NOVA v0.2; this model defines the synchronization a future
work-stealing runtime must implement.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import RLock, Thread
from typing import Callable, Generic, TypeVar


class RegionAccessError(RuntimeError):
    """A task attempted an access it no longer owns."""


@dataclass(frozen=True)
class RegionLease:
    """An opaque-by-identity runtime capability token."""
    region: str
    kind: str  # ``shared`` or ``exclusive``
    serial: int


@dataclass
class _Region:
    shared: dict[int, str] = field(default_factory=dict)
    exclusive: int | None = None


class RegionRuntime:
    """Atomic lease bookkeeping for one or more live regions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._regions: dict[str, _Region] = {}
        self._leases: dict[int, tuple[str, str, str]] = {}
        self._next_serial = 0

    def open(self, region: str) -> None:
        with self._lock:
            if region in self._regions:
                raise RegionAccessError(f"region `{region}` is already open")
            self._regions[region] = _Region()

    def borrow_exclusive(self, region: str, task: str) -> RegionLease:
        with self._lock:
            state = self._region(region)
            if state.exclusive is not None or state.shared:
                raise RegionAccessError(
                    f"cannot exclusively borrow `{region}` while it is live")
            lease = self._new_lease(region, "exclusive", task)
            state.exclusive = lease.serial
            return lease

    def borrow_shared(self, region: str, task: str) -> RegionLease:
        with self._lock:
            state = self._region(region)
            if state.exclusive is not None:
                raise RegionAccessError(
                    f"cannot shared-borrow `{region}` while it is exclusive")
            lease = self._new_lease(region, "shared", task)
            state.shared[lease.serial] = task
            return lease

    def handoff_exclusive(self, lease: RegionLease, donor: str, thief: str) -> None:
        """Atomically move an exclusive lease at a preemption safe point."""
        with self._lock:
            region, kind, owner = self._lease(lease)
            if kind != "exclusive" or owner != donor:
                raise RegionAccessError("exclusive lease is not owned by donor")
            state = self._region(region)
            if state.exclusive != lease.serial or state.shared:
                raise AssertionError("Region XOR invariant violated internally")
            self._leases[lease.serial] = (region, kind, thief)

    def check_read(self, lease: RegionLease, task: str) -> None:
        with self._lock:
            region, kind, owner = self._lease(lease)
            if owner != task or kind not in ("shared", "exclusive"):
                raise RegionAccessError("task does not own a readable region lease")
            self._assert_xor(region)

    def check_write(self, lease: RegionLease, task: str) -> None:
        with self._lock:
            region, kind, owner = self._lease(lease)
            if owner != task or kind != "exclusive":
                raise RegionAccessError("task does not own an exclusive region lease")
            self._assert_xor(region)

    def snapshot(self, region: str) -> tuple[int, bool]:
        """Return a synchronized observation for invariant stress tests."""
        with self._lock:
            state = self._region(region)
            self._assert_xor(region)
            return len(state.shared), state.exclusive is not None

    def _new_lease(self, region: str, kind: str, task: str) -> RegionLease:
        self._next_serial += 1
        lease = RegionLease(region, kind, self._next_serial)
        self._leases[lease.serial] = (region, kind, task)
        return lease

    def _region(self, region: str) -> _Region:
        try:
            return self._regions[region]
        except KeyError:
            raise RegionAccessError(f"region `{region}` is not open") from None

    def _lease(self, lease: RegionLease) -> tuple[str, str, str]:
        value = self._leases.get(lease.serial)
        if value is None or value[:2] != (lease.region, lease.kind):
            raise RegionAccessError("unknown or forged region lease")
        return value

    def _assert_xor(self, region: str) -> None:
        state = self._region(region)
        if state.exclusive is not None and state.shared:
            raise AssertionError("Region XOR invariant violated internally")


T = TypeVar("T")


class ChaseLevDeque(Generic[T]):
    """Prototype Chase-Lev work-stealing deque.

    The deque is intentionally simple: it uses a lock for the prototype, but it
    preserves the same bottom-push / top-steal geometry that a full runtime
    would use when work is stolen across worker threads.
    """

    def __init__(self, initial_capacity: int = 64) -> None:
        self._array: list[T | None] = [None] * max(2, initial_capacity)
        self._top = 0
        self._bottom = 0
        self._lock = RLock()

    def push_bottom(self, value: T) -> None:
        with self._lock:
            b = self._bottom
            t = self._top
            if b - t >= len(self._array) - 1:
                self._resize()
                b = self._bottom
            self._array[b % len(self._array)] = value
            self._bottom = b + 1

    def pop_bottom(self) -> T | None:
        with self._lock:
            b = self._bottom - 1
            self._bottom = b
            t = self._top
            if b < t:
                self._bottom = t
                return None
            value = self._array[b % len(self._array)]
            self._array[b % len(self._array)] = None
            return value

    def steal_top(self) -> T | None:
        with self._lock:
            t = self._top
            b = self._bottom
            if t >= b:
                return None
            value = self._array[t % len(self._array)]
            self._array[t % len(self._array)] = None
            self._top = t + 1
            return value

    def is_empty(self) -> bool:
        with self._lock:
            return self._top >= self._bottom

    def _resize(self) -> None:
        old = self._array
        new_cap = len(old) * 2
        new_arr: list[T | None] = [None] * new_cap
        size = self._bottom - self._top
        for i in range(size):
            new_arr[i] = old[(self._top + i) % len(old)]
        self._array = new_arr
        self._top = 0
        self._bottom = size


@dataclass
class RegionFrame:
    """A suspended task frame carrying one exclusive region lease."""
    task: str
    lease: RegionLease
    _lock: RLock = field(default_factory=RLock, repr=False)


class WorkStealingScheduler:
    """Reference safe-point protocol for a frame carrying ``Excl(Region)``."""

    def __init__(self, regions: RegionRuntime) -> None:
        self.regions = regions

    def run(self, frame: RegionFrame, worker: str, action: Callable[[], T]) -> T:
        # A migration takes this same lock.  The scheduler must not move a
        # frame while its old worker is inside guest code using the lease.
        with frame._lock:
            with self.regions._lock:
                if frame.task != worker:
                    raise RegionAccessError("worker no longer owns this frame")
                self.regions.check_write(frame.lease, worker)
            return action()

    def steal(self, frame: RegionFrame, donor: str, thief: str) -> None:
        # Owner update and capability handoff are one critical section; there
        # is no interval in which both workers can pass ``check_write``. The
        # runtime lock also prevents raw lease checks from observing the
        # transfer halfway through owner publication.
        with frame._lock:
            with self.regions._lock:
                if frame.task != donor:
                    raise RegionAccessError("frame is not owned by donor")
                self.regions.handoff_exclusive(frame.lease, donor, thief)
                frame.task = thief


@dataclass
class Task:
    """A scheduled unit of work for the prototype runtime."""
    id: int
    fn: Callable[[], object]


class TaskScheduler:
    """Prototype M:N scheduler with local-deque execution and work stealing."""

    def __init__(self, worker_count: int = 4) -> None:
        self.worker_count = max(1, worker_count)
        self.queues = [ChaseLevDeque[Task]() for _ in range(self.worker_count)]
        self._next_id = 0
        self._lock = RLock()
        self._shutdown = False
        self._threads: list[Thread] = []

    def spawn(self, fn: Callable[[], object], worker_index: int | None = None) -> Task:
        with self._lock:
            if self._shutdown:
                raise RuntimeError("scheduler is shut down")
            task = Task(self._next_id, fn)
            self._next_id += 1
            idx = worker_index if worker_index is not None else 0
            idx = max(0, min(idx, self.worker_count - 1))
            self.queues[idx].push_bottom(task)
            return task

    def start(self) -> None:
        if self._threads:
            return
        for i in range(self.worker_count):
            thread = Thread(target=self._worker_loop, args=(i,), daemon=True)
            thread.start()
            self._threads.append(thread)

    def shutdown(self, timeout: float = 1.0) -> None:
        self._shutdown = True
        for thread in self._threads:
            thread.join(timeout=timeout)

    def _worker_loop(self, worker_index: int) -> None:
        while not self._shutdown:
            task = self._pop_local(worker_index)
            if task is None:
                task = self._steal_from_other_workers(worker_index)
            if task is None:
                time.sleep(0.0005)
                continue
            task.fn()

    def _pop_local(self, worker_index: int) -> Task | None:
        return self.queues[worker_index].pop_bottom()

    def _steal_from_other_workers(self, worker_index: int) -> Task | None:
        for i in range(self.worker_count):
            if i == worker_index:
                continue
            task = self.queues[i].steal_top()
            if task is not None:
                return task
        return None
