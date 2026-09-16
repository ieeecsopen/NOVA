## Summary of Changes & Fixes

### 1. Overview
This PR addresses Windows UTF-8 text encoding compatibility issues across the NOVA toolchain and test scripts, ensuring cross-platform stability without changing language core semantics.

---

### 2. Detailed Bug Fixes
- **`tools/check-links.py`**: Specified `encoding="utf-8"` in `read_text()` calls to prevent `UnicodeDecodeError` when processing Markdown documentation on Windows systems.
- **`verifier/refspec/__main__.py`**: Reconfigured `sys.stdout` and `sys.stderr` streams to `utf-8` to prevent `UnicodeEncodeError` when rendering checkmark symbols (`✓`) in Windows consoles.
- **`compiler/nova_compiler/cli.py`**: Reconfigured standard output streams to `utf-8` to handle terminal output formatting during `nova check` and CLI operations cleanly on Windows.
- **`nova.bat`**: Added native Windows batch launcher script to allow running `nova check`, `nova run`, and `nova build` seamlessly in CMD / PowerShell.

---

### 3. Verification Suite Results
All verification suites pass cleanly with **0 errors / 0 failures**:
- **Conformance Suite:** 53/53 Passed (100%)
- **Internal Link Checker:** 959/959 Links Resolved
- **Toolchain Suite:** 18/18 Passed
- **Interpreter Suite:** 4/4 Passed
- **Regionlab Memory Suite:** 15/15 Passed
- **WASI Preview2 Bridge:** 7/7 Passed
- **LSP Server Smoke Test:** PASS
- **Examples Execution:** All `.nova` example scripts run without errors.
