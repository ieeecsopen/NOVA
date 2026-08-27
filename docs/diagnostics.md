# NOVA — Diagnostic index

Constitution Article X treats diagnostics as part of the language. Every
code below is emitted by the reference implementation and is covered by a
conformance test in `tests/conformance/`.

## Lexical and syntactic

| Code | Meaning |
|---|---|
| `E0002` | expected some token; parse failure |
| `E0003` | unexpected character |
| `E0004` | unterminated string literal |

## Names and declarations

| Code | Meaning |
|---|---|
| `E0100` | duplicate declaration |
| `E0101` | name not found in scope |
| `E0102` | unknown type |
| `E0103` | unknown effect label (no capability of that name) |
| `E0104` | unbound row variable |
| `E0105` | value is not callable |
| `E0106` | wrong number of arguments |
| `E0107` | type does not support equality |
| `E0108` | receiver has no method of that name (not a capability, or no matching `impl`) |
| `E0109` | capability has no such operation |
| `E0111` | unknown trait in `impl` |
| `E0112` | `impl` target is not a nominal type (tuples/functions cannot be `impl` targets) |
| `E0113` | trait already implemented for this type |
| `E0114` | not a method of the named trait |
| `E0115` | `impl` missing a required trait method |
| `E0116` | generic struct/enum used without its type arguments |
| `E0117` | struct literal field mismatch (missing or unknown fields) |
| `E0118` | unknown enum variant |
| `E0119` | unknown struct field / tuple index out of range |
| `E0120` | name is private to its declaring module (RFC 0004) |
| `E0121` | name exists but its module is not imported (RFC 0004) |
| `E0122` | `for` target is not a `List[_]` |
| `E0123` | method call on a type not yet resolved |
| `E0124` | pattern does not match the scrutinee's type |
| `E0126` | assignment to a binding not declared `mut` (RFC 0005) |
| `E0127` | `impl` method signature disagrees with its trait's declaration |
| `E0128` | `Self` used outside an `impl` |
| `E0130` | closure captures a `mut` local (RFC 0005 §3.1) |

## Types and effects

| Code | Meaning |
|---|---|
| `E0200` | type mismatch |
| `E0201` | performs an effect it does not declare |
| `E0202` | declares an effect it never performs |
| `E0203` | closure captures a capability its expected type does not declare |
| `E0204` | effect row variables do not match |
| `E0205` | two distinct row variables cannot be combined (v0.1 limit) |
| `E0206` | effect mismatch (general case) |
| `E0210` | `main` has the wrong signature |
| `E0220` | non-exhaustive `match` (RFC 0002 §5.1) |

## Runtime

| Code | Meaning |
|---|---|
| `E0300` | division by zero |
| `E0301` | capability operation has no host implementation |

## The three that matter

`E0201`, `E0202` and `E0203` are the language. Everything else is
ordinary type checking.

- **`E0201`** enforces that a row is not too small — you cannot hide what
  you do.
- **`E0202`** enforces that a row is not too large — you cannot claim
  powers you do not exercise. This is the unusual one; most effect systems
  allow silent widening. See RFC 0001 §4.3 for why NOVA does not.
- **`E0203`** is the reason RFC 0001 exists. It is the case that
  capability-only systems miss and that effect-only systems do not
  control.

## Two more, added in Phase 2

- **`E0127`** closes a soundness hole found during RFC 0003's own
  implementation: a caller's method call is checked against a trait's
  *declared* signature, never against whatever an individual `impl`
  happens to have written — so nothing else stopped an `impl` from
  silently disagreeing with its trait. See RFC 0003 §5.1 for the full
  argument and the incident that motivated it.
- **`E0130`** is to RFC 0005 what `E0203` is to RFC 0001: the one rule
  that makes a safety claim ("`mut` locals cannot alias") actually hold
  instead of merely usually holding. See RFC 0005 §3.1.
