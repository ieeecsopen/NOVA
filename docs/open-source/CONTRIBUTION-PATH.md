# NOVA — Contributor Growth & Onboarding Path

**Status:** Official Onboarding Guide  
**Cross-References:** [CONTRIBUTING.md](../../CONTRIBUTING.md), [ISSUE-TAXONOMY.md](ISSUE-TAXONOMY.md)

---

## 1. The Contributor Growth Ladder

NOVA is designed to welcome contributors at all experience levels, providing a structured progression path:

```
[Level 1: Novice / Explorer]
   • Fix doc typos, broken links, add simple examples.
   • Label: `status:good-first-issue` | `size:small`
   ▼
[Level 2: Unit Contributor]
   • Add conformance tests for edge cases, improve error diagnostics.
   • Label: `type:test` | `type:bug` | `size:small`
   ▼
[Level 3: Feature Contributor]
   • Implement AST/HIR passes, standard library functions, LSP features.
   • Label: `type:feature` | `size:medium`
   ▼
[Level 4: Subsystem Maintainer]
   • Lead an IR lowering pass, work-stealing scheduler component, or WASM bridge.
   • Label: `type:feature` | `size:large`
   ▼
[Level 5: Core Architect]
   • Author RFCs, participate in language governance, review security audits.
   • Label: `type:rfc` | `area:language`
```

---

## 2. First PR Step-by-Step Checklist

1. Clone repository: `git clone https://github.com/ieeecsopen/NOVA.git && cd NOVA`
2. Run baseline verification suite: `./tools/check-all.sh`
3. Pick an unassigned issue tagged with [`status:good-first-issue`](https://github.com/ieeecsopen/NOVA/labels/status%3Agood-first-issue).
4. Create feature branch: `git checkout -b fix/issue-123-description`
5. Implement change and verify locally: `./nova test`
6. Commit using Conventional Commits: `git commit -m "fix(compiler): improve span tracking on match expressions"`
7. Push and open Pull Request against `origin/main`.
