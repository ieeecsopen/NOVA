"""NOVA Documentation Generator (`nova doc`).

Generates structured API reference documentation from NOVA source files,
including function signatures, capability effect rows, structs, enums, and traits.
"""
from __future__ import annotations

import os
from typing import Optional

from .driver import NovaCompiler


def generate_docs_for_file(path: str) -> str:
    compiler = NovaCompiler()
    unit, err = compiler.check_file(path)

    base_name = os.path.basename(path)
    lines = [
        f"# Module `{base_name}`",
        "",
        f"*Source file: `{path}`*",
        "",
        "---",
        "",
    ]

    if not unit or not unit.result:
        lines.append(f"> *Warning: Could not extract full type information: {err}*")
        return "\n".join(lines)

    # Structs
    if unit.result.structs:
        lines.append("## Structs")
        lines.append("")
        for name, struct_info in unit.result.structs.items():
            lines.append(f"### `struct {name}`")
            lines.append("```nova")
            lines.append(f"struct {name} {{")
            for fld_name, fld_ty in struct_info.fields.items():
                lines.append(f"    {fld_name}: {fld_ty},")
            lines.append("}")
            lines.append("```")
            lines.append("")

    # Enums
    if unit.result.enums:
        lines.append("## Enums")
        lines.append("")
        for name, enum_info in unit.result.enums.items():
            lines.append(f"### `enum {name}`")
            lines.append("```nova")
            lines.append(f"enum {name} {{")
            for var_name, payload in enum_info.variants.items():
                if payload:
                    args = ", ".join(str(p) for p in payload)
                    lines.append(f"    {var_name}({args}),")
                else:
                    lines.append(f"    {var_name},")
            lines.append("}")
            lines.append("```")
            lines.append("")

    # Traits
    if unit.result.traits:
        lines.append("## Traits")
        lines.append("")
        for name, trait_info in unit.result.traits.items():
            lines.append(f"### `trait {name}`")
            lines.append("```nova")
            lines.append(f"trait {name} {{")
            for m_name, m_ty in trait_info.methods.items():
                lines.append(f"    fn {m_name}(self) -> {m_ty.ret};")
            lines.append("}")
            lines.append("```")
            lines.append("")

    # Functions
    if unit.result.fns:
        lines.append("## Functions")
        lines.append("")
        for name, fn_info in unit.result.fns.items():
            decl = fn_info.decl
            params_str = ", ".join(f"{p.name}: {p.ty.name if hasattr(p.ty, 'name') else p.ty}" for p in decl.params)
            ret_str = f" -> {decl.ret.name if decl.ret and hasattr(decl.ret, 'name') else 'Int'}" if decl.ret else ""
            eff_labels = [lbl[0] if isinstance(lbl, tuple) else str(lbl) for lbl in decl.eff.labels] if decl.eff and hasattr(decl.eff, 'labels') and decl.eff.labels else []
            eff_str = f" ! {{{', '.join(eff_labels)}}}" if eff_labels else ""
            lines.append(f"### `fn {name}`")
            lines.append("```nova")
            lines.append(f"fn {name}({params_str}){ret_str}{eff_str}")
            lines.append("```")
            lines.append("")

    return "\n".join(lines)


def generate_docs(input_path: str, output_dir: str = "docs/api") -> None:
    os.makedirs(output_dir, exist_ok=True)
    if os.path.isfile(input_path):
        doc = generate_docs_for_file(input_path)
        out_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".md")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"Generated documentation: \033[1m{out_file}\033[0m")
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith(".nova"):
                    fpath = os.path.join(root, file)
                    doc = generate_docs_for_file(fpath)
                    out_file = os.path.join(output_dir, os.path.splitext(file)[0] + ".md")
                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write(doc)
                    print(f"Generated documentation: \033[1m{out_file}\033[0m")
