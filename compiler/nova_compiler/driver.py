"""Compiler pipeline driver for NOVA.

Manages:
- Source Map and multi-file span resolution
- Frontend parsing, type checking, reachability verification
- Incremental caching in `.nova_cache/`
- Execution via the reference interpreter (the authoritative engine)
- Best-effort native C codegen for the supported language subset

Honesty note (v0.2): the reference interpreter in `verifier/refspec/eval.py`
is the *authoritative* execution engine. The C backend
(`codegen_c.py`) covers a subset — top-level functions over Int / Bool /
String / structs with `Runtime` and `Clock` — and is offered as an
optional optimization. Anything it cannot lower (enums, `match`,
closures, generics, traits, `List`, `for`) falls back to the interpreter
with a clear message, never a crash.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional

from verifier.refspec.diagnostics import Diagnostic
from verifier.refspec.driver import (PRELUDE_PATH, CompilationUnit, SourceMap,
                                     compile_source)
from verifier.refspec.eval import Interpreter, NovaRuntimeError
from .codegen_c import CodegenUnsupported, compile_to_native
from .hir import lower_ast_to_hir
from .mir import lower_hir_to_mir


@dataclass
class CompileMetrics:
    source_file: str
    parse_time_ms: float
    typecheck_time_ms: float
    codegen_time_ms: float
    total_time_ms: float
    binary_size_bytes: int
    is_cached: bool
    backend: str            # "native-c" or "interpreter"
    fallback_reason: str = ""   # why the interpreter path was taken, if it was


class NovaCompiler:
    def __init__(self, cache_dir: str = ".nova_cache") -> None:
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def compute_hash(self, source_path: str) -> str:
        h = hashlib.sha256()
        with open(source_path, "rb") as f:
            h.update(f.read())
        if os.path.exists(PRELUDE_PATH):
            with open(PRELUDE_PATH, "rb") as f:
                h.update(f.read())
        return h.hexdigest()

    def check_file(self, path: str) -> tuple[Optional[CompilationUnit], Optional[str]]:
        """Run frontend type and effect checking, returning (unit, rendered_error)."""
        if not os.path.exists(path):
            return None, f"error: file not found: {path}"

        with open(path, "r", encoding="utf-8") as f:
            src_text = f.read()

        try:
            unit = compile_source(src_text, name=path, with_prelude=True)
            return unit, None
        except Diagnostic as diag:
            sm = getattr(diag, "sources", SourceMap())
            return None, sm.render(diag)
        except Exception as ex:  # pragma: no cover - defensive
            return None, f"internal compiler error: {ex}"

    # ---------------------------------------------------------------- build
    def build_file(self, path: str, output_binary: Optional[str] = None,
                   force_clean: bool = False, target: str = "native"
                   ) -> tuple[bool, Optional[str], Optional[CompileMetrics]]:
        """Build an executable artifact for `path`.

        Returns (success, output_path_or_error, metrics). The artifact is
        either a native binary (when the C backend supports the program) or
        a self-contained runner script that invokes the bundled reference
        interpreter.
        """
        t_start = time.perf_counter()

        if output_binary is None:
            base_name = os.path.splitext(os.path.basename(path))[0]
            ext = ".wasm" if target in ("wasm", "wasi") else ""
            output_binary = os.path.join(".", f"{base_name}{ext}")

        src_hash = self.compute_hash(path) + f"_{target}"
        cached_bin = os.path.join(self.cache_dir, f"{src_hash}.bin")
        cached_meta = os.path.join(self.cache_dir, f"{src_hash}.backend")

        if not force_clean and os.path.exists(cached_bin):
            self._install(cached_bin, output_binary)
            backend, reason = "native-c", ""
            if os.path.exists(cached_meta):
                with open(cached_meta) as f:
                    parts = f.read().split("\n", 1)
                backend = parts[0].strip() or backend
                reason = parts[1].strip() if len(parts) > 1 else ""
            t_end = time.perf_counter()
            return True, output_binary, CompileMetrics(
                source_file=path, parse_time_ms=0.0, typecheck_time_ms=0.0,
                codegen_time_ms=0.0, total_time_ms=(t_end - t_start) * 1000.0,
                binary_size_bytes=os.path.getsize(output_binary),
                is_cached=True, backend=backend, fallback_reason=reason)

        t_parse_start = time.perf_counter()
        unit, err = self.check_file(path)
        if err or not unit:
            return False, err, None
        t_typecheck_end = time.perf_counter()

        # Lower AST -> HIR -> MIR (informational; also validates the lowering
        # passes do not choke on the program).
        try:
            hir_mod = lower_ast_to_hir(
                unit.program.decls,
                module_name=os.path.splitext(os.path.basename(path))[0])
            lower_hir_to_mir(hir_mod)
        except Exception:  # pragma: no cover - lowering is advisory
            pass

        t_codegen_start = time.perf_counter()
        backend = "native-c"
        fallback_reason = ""
        try:
            compile_to_native(unit.result, cached_bin, target=target)
        except CodegenUnsupported as reason:
            backend = "interpreter"
            fallback_reason = str(reason)
            self._write_runner_script(path, cached_bin)
        except FileNotFoundError:
            backend = "interpreter"
            fallback_reason = "clang is not installed"
            self._write_runner_script(path, cached_bin)
        except RuntimeError as reason:
            # Backend emitted C that clang rejected — a backend bug. Fall
            # back so the user is never blocked, but surface it loudly.
            backend = "interpreter"
            fallback_reason = "native backend bug (see warning above)"
            print(f"warning: native backend fell back to the interpreter: {reason}",
                  file=sys.stderr)
            self._write_runner_script(path, cached_bin)

        with open(cached_meta, "w") as f:
            f.write(f"{backend}\n{fallback_reason}")

        self._install(cached_bin, output_binary)
        t_end = time.perf_counter()

        return True, output_binary, CompileMetrics(
            source_file=path,
            parse_time_ms=(t_typecheck_end - t_parse_start) * 1000.0,
            typecheck_time_ms=(t_typecheck_end - t_parse_start) * 1000.0,
            codegen_time_ms=(t_end - t_codegen_start) * 1000.0,
            total_time_ms=(t_end - t_start) * 1000.0,
            binary_size_bytes=os.path.getsize(output_binary),
            is_cached=False, backend=backend, fallback_reason=fallback_reason)

    def _install(self, cached_bin: str, output_binary: str) -> None:
        out_dir = os.path.dirname(output_binary)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        shutil.copyfile(cached_bin, output_binary)
        st = os.stat(output_binary)
        os.chmod(output_binary, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _write_runner_script(self, source_path: str, dest: str) -> None:
        """Emit a self-contained runner that executes `source_path` through
        the reference interpreter. This is a real, runnable artifact — it
        just is not a standalone machine binary."""
        repo_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", ".."))
        abs_src = os.path.abspath(source_path)
        py = sys.executable or "python3"
        # Fully self-contained: a shell stub that picks a 3.10+ interpreter
        # and feeds it a bootstrap on stdin. Paths travel through the
        # environment, so nothing needs shell-vs-Python quoting, and there
        # is no sidecar file to lose if `.nova_cache/` is cleaned.
        script = f"""#!/bin/sh
# NOVA executable artifact (interpreter-backed).
# The native C backend does not yet lower every construct this program
# uses; execution goes through the authoritative reference interpreter.
NOVA_REPO_ROOT="{repo_root}"
NOVA_SOURCE="{abs_src}"
export NOVA_REPO_ROOT NOVA_SOURCE
PYTHON="${{NOVA_PYTHON:-{py}}}"
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    for cand in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PYTHON="$cand"; break
        fi
    done
fi
exec "$PYTHON" - "$@" <<'NOVA_BOOTSTRAP'
import os, sys
sys.path.insert(0, os.environ["NOVA_REPO_ROOT"])
from verifier.refspec.__main__ import main
sys.exit(main(["", "run", os.environ["NOVA_SOURCE"]]))
NOVA_BOOTSTRAP
"""
        with open(dest, "w") as f:
            f.write(script)

    # ------------------------------------------------------------------ run
    def run_file(self, path: str, args: list[str] = None) -> int:
        """Check and execute a NOVA program via the reference interpreter.

        The interpreter is the authoritative execution engine (RFC 0001
        §9: types and effects are erased at run time). `nova build`
        produces the optimized artifact; `nova run` is for the inner loop.
        """
        unit, err = self.check_file(path)
        if err or not unit:
            print(err, file=sys.stderr)
            return 1

        interp = Interpreter(unit.result)
        try:
            value = interp.run_main()
        except Diagnostic as diag:
            for line in interp.out:
                print(line)
            sm = getattr(diag, "sources", unit.sources)
            print(sm.render(diag), file=sys.stderr)
            return 1
        except NovaRuntimeError as ex:
            for line in interp.out:
                print(line)
            print(f"runtime error: {ex}", file=sys.stderr)
            return 1

        for line in interp.out:
            print(line)
        return int(value) if isinstance(value, int) else 0
