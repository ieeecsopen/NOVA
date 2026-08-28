# RFC 0004 — Modules and Imports

- **Status:** Implemented
- **Created:** 2026-08-28
- **Depends on:** RFC 0001
- **Tier:** Optional language feature ([DESIGN-PRINCIPLES.md](../docs/foundation/DESIGN-PRINCIPLES.md))

## 1. Summary

A NOVA program becomes a set of `.nova` files (modules) rather than one.
`import a.b;` transitively loads the file at `a/b.nova` (searched under
the repository root and the importing file's own directory) and brings
its `pub`-marked declarations into scope. **Modules provide organization
and visibility control, not namespacing**: there is no qualified-name
syntax (`a.b.name`); every declaration lives in one flat, globally
unique name space, and `pub` is the only thing `import` changes access
to. §2 argues this narrower scope directly.

This RFC also closes a gap [DESIGN-PRINCIPLES.md](../docs/foundation/DESIGN-PRINCIPLES.md)
and [P14](../research/PROBLEM-SPACE.md#p14--a-dependency-inherits-all-of-your-authority)
both named as open: [Experiment 001](../docs/experiments/001-capability-manifests.md)'s
capability manifest used "every function in a file" as a stand-in for "a
package's public interface," because there was no real notion of public
yet. There now is.

## 2. Problem, and the scope decision

The obvious design is qualified paths: `import a.b; a.b.helper()`. NOVA
v0.2 does **not** do this, for a reason worth stating rather than
assuming: a real qualified-namespace system needs to answer what happens
when two *packages* (not yet a NOVA concept — no package manager exists,
per [NON-GOALS.md §2.6](../docs/foundation/NON-GOALS.md#26-a-package-registry)) define
the same path, how aliasing (`import a.b as x;`) interacts with it, and
how it composes with generics' own `[...]` syntax. None of that can be
answered honestly before a package manager exists.

What v0.2 *can* answer now, and what actually blocks
[Experiment 001](../docs/experiments/001-capability-manifests.md)'s
next step, is narrower: **can code be organized into files with real
public/private boundaries, checked, today?** That is this RFC's entire
scope. Qualified paths are deferred to whatever RFC introduces the
package manager, where the question can be answered once, correctly,
rather than twice.

## 3. Design

### 3.1 A module is a file

```nova
// mathutil.nova
pub fn square(x: Int) -> Int { x * x }
fn secret() -> Int { 42 }              // not `pub`: invisible to importers
```

```nova
// main.nova
import mathutil;

fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("ok");
    square(6)      // visible: `square` is `pub` and `mathutil` is imported
}
```

`secret()` from another module would be `E0120` ("private to module
`mathutil`"); `square()` without the `import` line would be `E0121`
("not imported").

### 3.2 Resolution

`import a.b.c;` searches, in order: the repository root (so
`import std.list;` finds `std/list.nova`), then the importing file's own
directory (so sibling files can `import` each other without a `std.`
prefix). Transitive imports are followed to a fixpoint; a module is
loaded at most once (`driver.py`'s `compile_source`).

### 3.3 Visibility, not namespacing

> **Rule (Visibility).** A name declared in module `M` is visible in
> module `M` itself unconditionally. It is visible in a different module
> `N` only if it is `pub` **and** `N` imports `M` (directly — imports are
> not transitive for visibility purposes, only for module *loading*).

Names remain **globally unique** — `Checker.collect`'s existing
duplicate-declaration check (RFC 0001's `E0100`) now spans every loaded
module, not just one file. Two independently-organized modules cannot
declare a function of the same name, even if neither imports the other.
This is the concrete cost of choosing flat visibility over qualified
namespacing (§2); it is a real cost, and it is why a package manager
(which must eventually mediate collisions between code nobody wrote
together) is a separate, harder RFC.

### 3.4 What `pub` applies to

`fn`, `struct`, `enum`, `trait`. Not `capability` (there is exactly one
place capabilities are declared — the prelude — and RFC 0001 §4.1's
"no ambient authority" is a property of the *language*, not something a
module boundary should be able to relax). Not `impl` (an impl's
visibility follows its trait and target, not a declaration of its own).

## 4. Examples

### 4.1 Accepted

```nova
// std/list.nova
pub enum List[T] { Cons(T, List[T]), Nil }
pub fn prepend[T](x: T, xs: List[T]) -> List[T] { List::Cons(x, xs) }
```
```nova
import std.list;
fn main(rt: Runtime) -> Int ! {Runtime} {
    let xs = prepend(1, prepend(2, prepend(3, empty())));
    ...
}
```

### 4.2 Rejected — private item

```nova
import mathutil;
fn main(rt: Runtime) -> Int ! {Runtime} { secret() }
```
```
error[E0120]: `secret` is private to module `mathutil`
```

### 4.3 Rejected — unimported module

Calling a `pub` function from a module that exists on disk but was never
`import`ed:
```
error[E0121]: `helper` is not imported
```

## 5. Alternatives

**A. Qualified paths from the start.** Rejected in §2: cannot be
answered honestly before a package manager exists to define what a
"package" even is.

**B. No visibility at all — every declaration globally visible once
loaded.** Rejected: this is what Experiment 001 already worked around by
treating "every function in a file" as the public interface, and it is
exactly the gap this RFC exists to close. A capability manifest with no
notion of "public" cannot distinguish an intentional interface from an
internal helper.

**C. File-per-module with directory = package hierarchy (Java/Go-style)
enforced now.** Rejected as premature: directory structure as package
identity is a decision that belongs with the package manager, not with
visibility.

## 6. Tradeoffs

- **Global name uniqueness** is a real constraint that will not survive
  contact with a package ecosystem of any size; it is acceptable now
  precisely because there is no ecosystem yet.
- **Imports are not transitive for visibility.** Module `A` importing
  `B` importing `C` does not give `A` access to `C`'s `pub` items unless
  `A` also imports `C` directly. This matches Rust's and Go's choice and
  avoids accidental wide-open transitive access.

## 7. What this forecloses

Nothing yet designed depends on qualified paths, so this RFC forecloses
nothing beyond deferring §2's decision — which was the intent.

## 8. Costs

Visibility checking is a single dictionary lookup per name reference
(`Checker.check_visible`); module loading is one file read per distinct
transitive import, cached by module path so a diamond-shaped import
graph is not re-read.

## 9. Staging

Implemented: file-as-module, `pub`, transitive loading, flat-namespace
visibility checking. Not implemented, not designed: qualified paths,
aliasing (`import x as y`), re-exports, package versioning.

## 10. Success criteria

- [x] `tests/manifest`'s stand-in ("every function in a file is public")
      can now be replaced with real `pub` checking in a future revision
      of that experiment — the mechanism exists; the experiment itself
      is unchanged in this RFC, per its own "known limitation" note.
- [x] Conformance test 043 and the module examples under `examples/`
      exercise cross-file `pub`/`import` end to end.
- [x] `std/list.nova`, `std/option.nova`, `std/result.nova` are ordinary
      importable modules, proving the mechanism serves the standard
      library, not just user code.
