# NOVA — Security

## Reporting a vulnerability

Do not open a public issue. Report privately; a maintainer will
acknowledge within 72 hours and agree a disclosure timeline (default 90
days).

Until a security contact address is published, this file is a placeholder
and NOVA should not be used for anything where a vulnerability matters —
which is currently true for many other reasons.

## Security model

NOVA's security posture is a *language* property, not a runtime add-on.
The core claim (RFC 0001):

> Code that was never handed a capability value cannot perform the
> corresponding effect, and the type system makes this checkable.

### What NOVA intends to guarantee

- **No ambient authority.** There is no free function that performs IO.
  All authority descends from the `Runtime` value passed to `main`.
- **Authority is visible.** A function's effect row states every
  capability reachable from its body, including through closure captures
  (RFC 0001 §4.3). A dependency cannot silently acquire authority.
- **Attenuation is auditable.** `attenuate` is the only construct that
  drops an effect from a row. Every use is reported by `nova check`.

### What NOVA does not guarantee

Stated plainly, because a security document that only lists guarantees is
a marketing document:

- **Nothing yet.** No implementation is complete. None of the above is
  enforced end to end today.
- **Not against the trusted computing base.** The compiler, the runtime's
  root capability, and every `attenuate` body are trusted. A bug there
  defeats everything above.
- **Not against covert channels.** Timing, cache, and resource-exhaustion
  channels are out of scope for the capability model.
- **Not against unsafe FFI.** Any C interop escapes the model. FFI will be
  a capability, but a capability that can do anything is not a
  restriction — it is a labelled hole.
- **Not confidentiality or integrity of data.** Information-flow control
  (taint, declassification) is a *different* system from authority
  control. NOVA has none. Do not read "no ambient authority" as "no data
  leaks."
- **Not availability.** Nothing bounds infinite loops or memory growth
  until Milestone 5.

### Threat model

Assumed adversary: a malicious or compromised **dependency** inside the
program, and a **caller** attempting to obtain more authority than it was
granted.

Not assumed: a hostile compiler, a hostile OS, a hostile CPU, or physical
access.

## Supply chain

The package manager does not exist. When it does, its RFC must address
signing, reproducible builds, and — specifically for NOVA — whether a
package's declared capability requirements can be checked at install time
rather than at first run. That is the interesting question and it is not
yet answered.
