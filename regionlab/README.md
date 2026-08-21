# regionlab

A small, standalone prototype validating [OWNERSHIP-MODEL.md](../OWNERSHIP-MODEL.md)'s
region/linearity rules — not merged into `verifier/refspec/` (Phase 2's
shipped v0.2 language and its 45 conformance tests are unmodified by
this phase; "build small compiler prototypes where necessary" was the
brief, not "extend the production checker").

This prototype tracks line numbers only, not full byte-range spans —
ARCHITECTURE.md's "spans everywhere" rule binds the production compiler,
not an experimental prototype whose entire purpose is to be small.

```sh
python3 -m regionlab check regionlab/tests/001-use-after-free-rejected.rlab
python3 tests/run.py     # runs every tests/*.rlab against its `# expect:` header
```

## The tiny language

```
fn f(x: Int) -> Int { x }        -- an ordinary function

region r {                        -- opens a region, binds `r: Region`
    let x = alloc(r, 5);           -- x : InRegion(r, Int)
    let s = shared(r);             -- s : Shared(r) -- freely copyable
    let e = exclusive(r);          -- e : Excl(r) -- LINEAR, moves on use
    write(x, 6);                   -- needs a live Excl(r)
    read(x)                        -- needs a live Shared(r) or Excl(r)
}                                  -- region closes; nothing tagged `r` may
                                   -- be used after this point
```

Every rule this validates is listed, with its test file, in
[SAFETY-GUARANTEES.md](../SAFETY-GUARANTEES.md).
