"""NOVA Package Manager (`nova add`, `nova remove`).

Manages dependency declaration, capability boundaries, and package manifests.
"""
from __future__ import annotations

import os
from typing import Optional


MANIFEST_FILE = "nova.toml"


def init_manifest_if_missing() -> None:
    if not os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            f.write("""[package]
name = "nova-project"
version = "0.1.0"
edition = "2026"

[dependencies]
# Example:
# analytics = { version = "1.0.0", capabilities = ["Network"] }

[capabilities]
allowed = ["Runtime", "Clock", "Filesystem", "Network"]
""")


def add_dependency(pkg_name: str, version: str = "latest", capabilities: list[str] = None) -> bool:
    init_manifest_if_missing()
    caps_str = ", ".join(f'"{c}"' for c in (capabilities or []))

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    dep_line = f'{pkg_name} = {{ version = "{version}", capabilities = [{caps_str}] }}\n'
    if "[dependencies]" in content:
        content = content.replace("[dependencies]\n", f"[dependencies]\n{dep_line}")
    else:
        content += f"\n[dependencies]\n{dep_line}"

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\033[32m✓\033[0m Added dependency \033[1m{pkg_name}\033[0m (capabilities: {capabilities or 'none'})")
    return True


def remove_dependency(pkg_name: str) -> bool:
    if not os.path.exists(MANIFEST_FILE):
        print("error: nova.toml not found", file=sys.stderr)
        return False

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [l for l in lines if not l.strip().startswith(pkg_name)]

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"\033[32m✓\033[0m Removed dependency \033[1m{pkg_name}\033[0m from nova.toml")
    return True
