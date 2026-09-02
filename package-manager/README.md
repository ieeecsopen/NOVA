# Package manager

**Status: manifest helpers only. There is no registry, no dependency
resolver, and no way to actually fetch a package.**

## What exists

`compiler/nova_compiler/pkg.py` (invoked as `nova add` / `remove` /
`update` / `publish` / `deploy`) does local manifest bookkeeping:

| Command | What it does today |
| :--- | :--- |
| `nova add <pkg> --caps ...` | writes a `[dependencies]` entry into `nova.toml` with a capability bound |
| `nova remove <pkg>` | deletes that entry |
| `nova update` | rewrites `nova.lock` with a manifest hash (no packages are fetched — the lock's `packages` map is always empty) |
| `nova publish` | tars the working tree and prints a SHA-256 |
| `nova deploy --target ...` | emits a `Dockerfile` / systemd unit / edge manifest template |

`tools/manifest-diff.py` compares two manifests and flags a dependency
that asks for *new* capabilities between versions — that part is a real,
tested idea (`tests/manifest/`).

## What does not exist

- A package registry or index.
- Fetching, version resolution, semver ranges.
- Lockfile verification against downloaded tarballs (SEC-02 in the
  backlog).
- Qualified import paths — names are globally unique across a program
  ([docs/known-issues.md](../docs/known-issues.md) P3). A real
  package system has to define what a "package" is first; that is
  Milestone 2.

## Design intent (not yet built)

* **Explicit authority boundaries** — a dependency must declare every
  capability it needs in `nova.toml`; the consumer passes tokens in.
* **Zero ambient access** — importing a library grants it nothing.
* **Semantic manifest diffing** — a version bump that requests a new
  capability is a reviewable security event.
