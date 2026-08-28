# Experiment 001 — Capability manifests

Tests [P14](../../research/PROBLEM-SPACE.md#p14--a-dependency-inherits-all-of-your-authority)
and the cheapest part of thesis T2
([DESIGN-OPPORTUNITIES.md §4](../../research/DESIGN-OPPORTUNITIES.md#4-theme-c--boundaries-and-the-adoption-problem)):
can a dependency's authority requirements be published as data and diffed,
so that authority creep in a "patch" release is a *detectable, checkable*
event rather than something discovered after an incident?

**Implementation:** [`verifier/refspec/manifest.py`](../../verifier/refspec/manifest.py).
**CLI:** `python3 tools/manifest-diff.py <old.nova> <new.nova>`.
**Tests:** [`tests/manifest/`](../../tests/manifest/), run via
`python3 tests/manifest/run.py`.

## Method

RFC 0001 already computes an exact effect row for every function — nothing
new needed there. A "manifest" is just that row, printed, for every
function in a file. A "diff" compares two manifests and classifies each
change:

- a function whose row **gained** a label → **breaking**: the published
  claim about what it may do just widened.
- a function whose row **shrank** → compatible: any caller that tolerated
  the larger row still does.
- a new function → compatible (nothing depended on it before).
- a removed function → breaking (something might have depended on it).

This is deliberately narrower than full semantic-versioning compatibility
(P13, Elm's approach): it says nothing about parameter or return types,
only about capability requirements. That narrowness is the point — it
isolates exactly the question P14 is about.

**Known limitation, stated up front.** NOVA v0.1 has no module or package
system (Milestone 2). The experiment treats one `.nova` file's functions
as a stand-in for a package's public interface. A real manifest needs a
real notion of "public" vs. "private" and of package identity, neither of
which exists yet. This experiment tests whether the *underlying idea*
survives contact with real code, not whether the packaging story is
finished.

## Result: the demo the thesis was built to justify

`tests/manifest/logging-lib/` is deliberately shaped like a real supply-
chain incident (the write-up mentions event-stream, node-ipc, xz): a
logging library's patch release adds a network call for "telemetry",
unreviewed, alongside no other visible change.

```
$ python3 tools/manifest-diff.py \
    tests/manifest/logging-lib/v1.nova tests/manifest/logging-lib/v2.nova
  [BREAKING] log: {Runtime} -> {Clock, Runtime}

VERDICT: authority grew — this is a breaking change, regardless of the
version number attached to it
$ echo $?
1
```

This is the whole point of P14: the check needs **nothing** beyond what
RFC 0001 already computes. There is no new mechanism here, only a new use
of an existing one — which is exactly the kind of finding Theme A
predicted (DESIGN-OPPORTUNITIES §2) and the cheapest of the three
experiments to run.

## Result: it does not cry wolf

Two controls, run as conformance tests
(`tests/manifest/safe-patch`, `tests/manifest/authority-decrease`):

- **Adding a pure helper function** — the kind of genuine patch that
  should never be flagged — is correctly classified `compatible`.
- **A function whose authority *shrinks*** (a fix that removes an
  unnecessary capability) is correctly classified `compatible`, not
  breaking. A detector that flagged every row *change* rather than every
  row *growth* would be unusable — it would fire on the fixes people
  actually want credit for making.

All three cases are conformance tests, not one-off demonstrations; they
run in CI.

## Verdict against the falsification criteria

VISION.md named "capability manifests that churn so much they are
ignored" as a falsifier. This experiment cannot test churn rate on real
code — there is no real NOVA codebase yet — but it establishes the
precondition: the signal is exact (no false positives on either control)
and requires zero new type-system machinery, which means the churn
question is about **ecosystem behaviour**, not about whether the
mechanism works. That question is deferred to Milestone 2, honestly,
rather than answered here.

**Does not falsify T2.** If anything this is the strongest positive
result of the three experiments: an existing, already-checked artifact
(the effect row) directly answers a real, named, high-profile class of
incident, with no new design. The open work is entirely in Milestone 2's
module system — what "public interface" and "package identity" mean —
not in whether the underlying signal is worth publishing.
