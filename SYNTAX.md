# NOVA — Syntax

Phase 2 output. Syntax principles first, then the grammar, for v0.2 (RFC
0001–0005). Surface syntax remains provisional
([CONTRIBUTING.md](CONTRIBUTING.md) already declines syntax-preference
feedback); what is fixed by this document is the set of *principles* the
syntax must satisfy, which will outlast any particular spelling.

`docs/grammar.md` used to hold the full grammar for v0.1; it now points
here, so the grammar has one home.

---

## 1. Principles

The brief for this phase set eight bars. Each is restated as a concrete
design decision below, not just aspired to.

**Readable.** No sigils invented where a keyword already says the same
thing (`mut`, not `&mut` for a feature that has no references to
distinguish from — RFC 0005 §3.3). No line-noise operators for common
cases.

**Tool-friendly / easy to autocomplete.** Every declaration starts with
an unambiguous keyword (`fn`, `struct`, `enum`, `trait`, `impl`, `import`,
`capability`) — an editor can complete "what comes next" from the first
token alone, without parsing ahead. Field access (no parens) and method
call (always parens, even empty `()`) are the *same* two-character
lookahead Rust already made editor-friendly.

**Unambiguous.** Every genuine ambiguity in the grammar is named,
resolved, and justified in §5, not left for the parser to guess at
silently.

**Formatter-friendly.** Statements end in `;`; block-like expressions
(`if`, `while`, `for`, `match`, `{ }`) need no trailing `;` when they are
not a block's tail (§5.4) — both facts a formatter can apply
mechanically, without semantic analysis.

**Easy to parse.** The whole grammar is recursive-descent with one token
of lookahead almost everywhere; the two exceptions (§5.1, §5.2) are
named explicitly, because a language that hides its lookahead
requirements from its own spec is not, in the sense that matters, easy
to parse.

**Easy for humans to learn.** Method-call syntax is reused for
capability operations *and* trait methods (RFC 0002 §6) rather than
inventing a second call form — one thing to learn, not two that happen
to look similar. Generic and row parameters share one `[...]` binder
(RFC 0003 §3), classified by usage rather than requiring the learner to
know in advance which bracket group is which.

**Suitable for AI-assisted development.** Every diagnostic names an
exact code (`E0201`, ...), every node carries a span
([ARCHITECTURE.md](ARCHITECTURE.md)), and the grammar has no
context-sensitive keywords (a token is always a keyword or always an
identifier, never both depending on position) — all three make the
language easy for a tool, human or model, to point at precisely and
reason about locally, without holding the whole file in mind.

**Not "looking futuristic."** No unicode operators, no invented
punctuation beyond what C-family languages already use (`->`, `::`,
`=>`, `!`). The one syntax that is NOVA-specific — `! {Row}` for an
effect row — is specific because the *concept* is specific (RFC 0001),
not for visual distinctiveness.

---

## 2. Lexical structure

- **Identifiers:** `[a-zA-Z_][a-zA-Z0-9_]*`. No unicode identifiers in
  v0.2 (a scope decision, not a principle — revisit if requested).
- **Keywords** (context-free — always keywords, never usable as plain
  identifiers): `capability fn let mut if else true false widen struct
  enum trait impl for in while match pub import self`.
- **Literals:** integers (`42`, `1_000`, underscores as digit
  separators), strings (`"..."`, with `\n \t \" \\` escapes), booleans
  (`true`, `false`), unit (`()`).
- **Comments:** `// to end of line`. No block comments in v0.2.
- **Whitespace:** not significant. No indentation-sensitivity — a
  deliberate simplicity choice; braces alone delimit blocks.

## 3. Declarations

```nova
capability Name { op(params) -> Type ... }
fn name[params](params) -> Type [! Row] [= widen] { body }
struct Name[params] { field: Type, ... }
enum Name[params] { Variant[(Type, ...)], ... }
trait Name { fn method(self, params) -> Type; ... }
impl[params] Trait for Type { fn method(self, params) -> Type { body } ... }
import a.b.c;
```

`pub` may prefix `fn`, `struct`, `enum`, `trait` (RFC 0004 §3.4).

### 3.1 The `[...]` binder

One bracket list per `fn`/`struct`/`enum`, holding **both** generic type
parameters and row parameters, each optionally bounded
(`T: TraitName`, type parameters only):

```nova
fn with_retry[r](attempts: Int, f: () -> Int ! r) -> Int ! r { ... }
fn identity[T](x: T) -> T { x }
fn describe[T: Show](x: T) -> String { x.show() }
```

A name is classified as a **row** parameter if it appears in an effect
position (after `!`) anywhere in the signature, and as a **type**
parameter otherwise (RFC 0003 §3). This is a parse-time classification —
no separate declaration syntax exists for the two kinds.

## 4. Types

```nova
Int  Bool  String  Unit                 -- primitives
Name                                     -- a capability, struct, or enum
Name[Type, ...]                          -- a generic struct/enum, instantiated
(Type, Type, ...)                        -- a tuple
(Type, ...) -> Type [! Row]              -- a function type
```

Effect rows: `{}` (pure), `{A, B}` (closed), `{A | r}` (open, tail `r`),
or a bare row variable `r`.

## 5. Named ambiguities and their resolutions

A syntax that hides its ambiguities is not, whatever else it is, "easy to
parse" — so every one this grammar has is named here rather than left
implicit in the parser's control flow.

### 5.1 `(T)` — grouping vs. one-parameter function type

`(Int)` is the type `Int`, parenthesized; `(Int) -> Int` is a function
type. The parser commits to "function type" only on seeing `->`
immediately after the closing `)`. A single-element tuple *type* has no
literal syntax in v0.2 for this reason (write a one-field struct
instead) — a real, minor gap, not hidden.

### 5.2 Struct literals in condition position

```nova
if Point { x: 1, y: 2 }.x > 0 { ... }
```

is genuinely ambiguous: is `{` the struct literal's fields, or the `if`
body, with `Point` a bare (nonsensical, but syntactically valid until
type-checked) condition? **Resolution, identical to Rust's:** a bare
struct literal is not permitted directly as the scrutinee of `if`,
`while`, `for`, or `match`; wrap it in parentheses if one is genuinely
needed there. Implemented as a suppression flag the parser carries
through `_parse_condition` (`parser.py`).

### 5.3 Field access vs. method call vs. capability operation

`p.x` (field access, no parens) vs. `p.show()` (method call) vs.
`c.now()` (capability operation) are the same two-token lookahead
(`.` then identifier, then check for `(`) and the same AST node
(`MethodCall` when parens follow, `FieldAccess` when they don't); which
of "method" or "capability operation" applies is resolved by the
receiver's *type*, not by anything the parser needs to know (RFC 0002
§6). The parser's job ends at "is there a paren"; the checker's job is
everything after.

### 5.4 Block-like expressions as statements

```nova
if flag { do_a(); } do_b();
```

needs no `;` after the `if`'s closing `}` when another statement
follows — otherwise every `if`/`while`/`for`/`match` used for effect
(not for its value) would need an awkward trailing semicolon. Rule: a
block-like expression (`If`, `While`, `For`, `Match`, a bare `{ }`) may
be followed directly by the next statement; it needs `;` only when some
other expression form is used as a statement (`f();`). Exactly Rust's
rule (`parser.py`'s `parse_block`).

### 5.5 `!` is two things

Effect-row marker (`Int ! {Clock}`, type position) and logical negation
(`!flag`, expression position) share one token. They never occur in the
same *position*, so no lookahead is needed to disambiguate — the parser
simply expects different things depending on whether it is parsing a
type or an expression.

### 5.6 `||` is two things

Zero-parameter lambda introducer (`|| expr`) in expression-start
position, logical-or operator (`a || b`) in infix position. Resolved
purely by parser position, not by lookahead.

## 6. What is deliberately absent

No operator overloading, no implicit conversions (TYPE-SYSTEM.md,
"Coercion"), no macros, no string interpolation, no indentation-sensitive
blocks, no semicolon-insertion beyond §5.4's narrow rule, no
single-element tuple type literal (§5.1). Each is a scope decision for
v0.2, not a gap being hidden; several are plausible future RFCs.
