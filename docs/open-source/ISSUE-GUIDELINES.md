# NOVA — Issue Writing & Contribution Guidelines

**Status:** Official Guidelines  
**Cross-References:** [ISSUE-TAXONOMY.md](ISSUE-TAXONOMY.md), [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## 1. The Contributor Dependency Safety Checklist

Before filing or claiming an issue, verify that the following 5 questions can be answered affirmatively:

1. **Can a contributor understand the goal without prior repo context?**
2. **Is there a direct link to the authoritative specification or RFC?**
3. **Is there a concrete test command to run locally (e.g. `./nova test`)?**
4. **Is there an unambiguous Definition of Done?**
5. **Can the work proceed without refactoring unrelated subsystems?**

---

## 2. Standard Implementation Issue Structure

```markdown
# [Component] Title

## Summary
Brief explanation of what needs to be implemented.

## Problem
What currently fails, diverges, or is missing.

## Why
Why this capability is essential to NOVA.

## Specification References
- `docs/language/...`
- `RFC/...`

## Current State
`IMPLEMENTED` | `PARTIALLY IMPLEMENTED` | `PROTOTYPE` | `MISSING`

## Proposed Work
Clear technical direction without micromanaging the contributor.

## Acceptance Criteria
- [ ] Feature implemented matching specification
- [ ] Unit & integration tests added in `tests/`
- [ ] Conformance runner (`./tools/check-all.sh`) passes with 0 errors
- [ ] Documentation updated

## Dependencies
- Pre-requisite issues or RFCs

## Out of Scope
Explicitly declare what this issue should NOT modify.
```

---

## 3. Standard Research Issue Structure

```markdown
# [Research] Question Title

## Question
What empirical or theoretical question needs an answer?

## Context
Why NOVA requires a decision now.

## Existing Approaches
Survey of prior art (Rust, OCaml, Koka, Haskell, etc.).

## Evaluation Criteria
Metrics for comparison (memory overhead, syntax ergonomics, type soundness).

## Expected Output
A markdown research report, benchmark data, prototype, or draft RFC.

## Non-Goals
What this research should NOT implement.
```
