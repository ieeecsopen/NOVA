# NOVA — Governance

## Current state

NOVA is pre-1.0 and small. Governance is deliberately lightweight and will
be replaced when the project has enough contributors to need more.

Today: decisions are made by the maintainers through the RFC process
(RFC 0000). There is no foundation, no steering council, and no voting
body, because there is not yet anything to steer.

## How decisions are made

1. **Non-core changes** — bug fixes, diagnostics, docs, tests,
   performance: normal review, one maintainer approval.
2. **Core changes** — anything in RFC 0000's "RFC required" list: an RFC,
   14 days minimum in Review, and consensus among maintainers. Consensus
   means no sustained objection, not unanimity.
3. **Constitution changes** — an RFC, 30 days in Review, and an entry in
   `docs/constitution-changelog.md` recording what changed and why.

## Sustained objection

An objection is sustained if it identifies a concrete problem — a program
that breaks, a guarantee that is lost, a cost that was not accounted for.
"I prefer the other syntax" is a preference and does not block.

If a sustained objection cannot be resolved, the RFC is Postponed, not
overridden.

## Deadlock

If maintainers deadlock on a core change, the default is **do nothing**.
The Constitution's priority order (Article III) is the tiebreaker where it
applies; where it does not, the status quo wins. A language is harmed more
by a rushed core decision than by a slow one.

## Maintainers

Maintainership is granted for sustained, high-quality contribution and is
not tied to volume. It is removed by request, by inactivity (12 months),
or by conduct.

## Conduct

Be direct about ideas and decent to people. Technical criticism is
expected and should be specific. Personal attacks, harassment, and bad
faith are not tolerated and result in removal.

## Trademark and licensing

To be decided before any public release. Until then, the name and the code
carry no promises.
