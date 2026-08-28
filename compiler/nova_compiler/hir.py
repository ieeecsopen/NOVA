"""High-Level Intermediate Representation (HIR) for NOVA.

HIR desugars high-level syntactic sugar:
- De-sugars pattern matches into decision trees
- Monomorphizes generic function calls
- Normalizes closure captures into explicit environment structures
- Resolves trait dispatch to concrete monomorphic functions
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class HIRType:
    name: str
    args: list[HIRType] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.args:
            return self.name
        return f"{self.name}[{', '.join(str(a) for a in self.args)}]"


@dataclass
class HIRExpr:
    ty: HIRType


@dataclass
class HIRLiteral(HIRExpr):
    value: Any


@dataclass
class HIRVar(HIRExpr):
    name: str


@dataclass
class HIRBinary(HIRExpr):
    op: str
    left: HIRExpr
    right: HIRExpr


@dataclass
class HIRUnary(HIRExpr):
    op: str
    operand: HIRExpr


@dataclass
class HIRCall(HIRExpr):
    callee: str
    args: list[HIRExpr]


@dataclass
class HIRMethodCall(HIRExpr):
    receiver: HIRExpr
    method: str
    args: list[HIRExpr]


@dataclass
class HIRFieldAccess(HIRExpr):
    receiver: HIRExpr
    field_name: str


@dataclass
class HIRStructInit(HIRExpr):
    struct_name: str
    fields: list[tuple[str, HIRExpr]]


@dataclass
class HIREnumInit(HIRExpr):
    enum_name: str
    variant: str
    payload: Optional[HIRExpr]


@dataclass
class HIRBlock(HIRExpr):
    stmts: list[HIRStmt]
    result: Optional[HIRExpr]


@dataclass
class HIRIf(HIRExpr):
    cond: HIRExpr
    then_branch: HIRExpr
    else_branch: Optional[HIRExpr]


@dataclass
class HIRMatchArm:
    pattern_variant: Optional[str]
    pattern_var: Optional[str]
    body: HIRExpr


@dataclass
class HIRMatch(HIRExpr):
    scrutinee: HIRExpr
    arms: list[HIRMatchArm]


@dataclass
class HIRStmt:
    pass


@dataclass
class HIRLet(HIRStmt):
    name: str
    is_mut: bool
    ty: HIRType
    init: HIRExpr


@dataclass
class HIRAssign(HIRStmt):
    name: str
    value: HIRExpr


@dataclass
class HIRWhile(HIRStmt):
    cond: HIRExpr
    body: HIRExpr


@dataclass
class HIRExprStmt(HIRStmt):
    expr: HIRExpr


@dataclass
class HIRParam:
    name: str
    ty: HIRType


@dataclass
class HIRFn:
    name: str
    params: list[HIRParam]
    return_ty: HIRType
    effects: list[str]
    body: HIRExpr


@dataclass
class HIRStruct:
    name: str
    fields: list[tuple[str, HIRType]]


@dataclass
class HIREnum:
    name: str
    variants: list[tuple[str, Optional[HIRType]]]


@dataclass
class HIRModule:
    name: str
    structs: list[HIRStruct] = field(default_factory=list)
    enums: list[HIREnum] = field(default_factory=list)
    functions: list[HIRFn] = field(default_factory=list)
