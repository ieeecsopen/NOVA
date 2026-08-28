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
echo "== regionlab (Milestone 1 prototype, docs/regionlab) =="
"$PYTHON" regionlab/tests/run.py
