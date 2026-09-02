# experiments

Reserved for controlled experiments that test a design hypothesis and
either falsify it or promote it into an RFC.

**Status: empty.** The experiments that have actually been run are
written up in [`docs/experiments/`](../docs/experiments/) and have
executable checks under [`tests/`](../tests/):

| Experiment | Write-up | Check |
| :--- | :--- | :--- |
| Capability manifests | `docs/experiments/001-capability-manifests.md` | `tests/manifest/run.py` |
| Rows → trace spans | `docs/experiments/002-rows-to-spans.md` | `tests/tracing/run.py` |
| Graded effect rows | `docs/experiments/003-graded-rows.md` | `tests/grading/run.py` |

New experiment code, when there is any, lands here with its own runner.
