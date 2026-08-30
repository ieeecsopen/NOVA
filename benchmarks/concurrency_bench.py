"""NOT a NOVA benchmark.

NOVA has no concurrency runtime (see ROADMAP.md Milestone 4). This file
previously measured Python's `concurrent.futures.ThreadPoolExecutor` and
`queue.Queue` and reported the numbers as if they were NOVA's — they were
not. It has been reduced to this notice to avoid that.

When NOVA has a scheduler, its benchmark will live here and will run
compiled NOVA programs.
"""
import sys

if __name__ == "__main__":
    sys.stderr.write(__doc__)
    sys.exit(1)
