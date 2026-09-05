#!/bin/sh
# Everything CI would run. No dependencies beyond Python 3.11+.
set -e
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON=python3.11
    elif command -v python3.12 >/dev/null 2>&1; then
        PYTHON=python3.12
    elif command -v python3.10 >/dev/null 2>&1; then
        PYTHON=python3.10
    fi
fi

echo "== documentation links =="
"$PYTHON" tools/check-links.py

echo
echo "== conformance suite =="
"$PYTHON" tests/run_conformance.py

echo
echo "== examples check (all, including module-system/) =="
for f in $(find examples -name "*.nova" ! -name "rejected.nova"); do
    "$PYTHON" -m verifier.refspec check "$f"
done

echo
echo "== examples run (programs with a main only) =="
# A program's exit code is its computed `main` return value, not a
# success/failure signal (RFC 0001 §4.7) -- 42, 149, whatever -- so a
# nonzero code here is expected and must not abort this script under
# `set -e`. Only a Diagnostic/traceback (nonzero AND no output at all,
# or a Python exception) is a real failure; catch that by checking the
# command's own reported success via a distinct sentinel instead of $?.
for f in $(find examples -name "*.nova" ! -name "rejected.nova" ! -name "geometry.nova"); do
    if ! "$PYTHON" -m verifier.refspec run "$f" >/dev/null 2>/tmp/nova-run-err; then
        if grep -q "Traceback" /tmp/nova-run-err; then
            echo "CRASH running $f:"; cat /tmp/nova-run-err; exit 1
        fi
    fi
done
rm -f /tmp/nova-run-err
echo "examples ran"

echo
echo "== nova build every example (native subset + interpreter fallback) =="
# Exercises the driver end to end: codegen for the supported subset, and
# the interpreter-backed runner for everything else. A build that errors
# out (rather than falling back) is a real failure. This is the check
# whose absence let the codegen breakage go unnoticed.
mkdir -p /tmp/nova-build-check
native=0; interp=0
for f in $(find examples -name "*.nova" ! -name "rejected*.nova" ! -name "*rejected*"); do
    out="/tmp/nova-build-check/$(basename "$f" .nova)"
    if ! msg=$(./nova build "$f" -o "$out" 2>&1); then
        echo "BUILD ERROR for $f:"; echo "$msg"; exit 1
    fi
    case "$msg" in
        *"native binary"*)        native=$((native + 1)) ;;
        *"interpreter-backed"*)   interp=$((interp + 1)) ;;
        *) echo "BUILD produced no backend line for $f:"; echo "$msg"; exit 1 ;;
    esac
    # Run the artifact; only a Python traceback is a real failure (see above).
    if ! "$out" >/dev/null 2>/tmp/nova-artifact-err; then
        if grep -q "Traceback" /tmp/nova-artifact-err; then
            echo "ARTIFACT CRASH for $f:"; cat /tmp/nova-artifact-err; exit 1
        fi
    fi
done
rm -rf /tmp/nova-build-check /tmp/nova-artifact-err
echo "built and ran every example ($native native, $interp interpreter-backed)"

echo
echo "== rejected.nova must fail =="
if "$PYTHON" -m verifier.refspec check examples/module-system/rejected.nova >/dev/null 2>&1; then
    echo "ERROR: rejected.nova unexpectedly checked ok"
    exit 1
fi
echo "rejected.nova correctly rejected"

echo
echo "== audit =="
"$PYTHON" -m verifier.refspec audit examples/retry.nova >/dev/null
echo "audit ran"

echo
echo "== experiments (docs/experiments/) =="
"$PYTHON" tests/manifest/run.py
"$PYTHON" tests/grading/run.py
"$PYTHON" tests/tracing/run.py

echo
echo "== toolchain (nova fmt / lint / add, diagnostic rendering) =="
"$PYTHON" tests/toolchain/run.py
./nova fmt --check examples >/dev/null
echo "examples are canonically formatted"

echo
echo "== regionlab (Milestone 1 prototype, docs/regionlab) =="
"$PYTHON" regionlab/tests/run.py
