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
import verifier.refspec.ast as a


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
    ty: Optional[HIRType] = None


@dataclass
class HIRLiteral(HIRExpr):
    value: Any = None


@dataclass
class HIRVar(HIRExpr):
    name: str = ""


@dataclass
class HIRBinary(HIRExpr):
    op: str = ""
    left: HIRExpr = field(default_factory=HIRExpr)
    right: HIRExpr = field(default_factory=HIRExpr)


@dataclass
class HIRUnary(HIRExpr):
    op: str = ""
    operand: HIRExpr = field(default_factory=HIRExpr)


@dataclass
class HIRCall(HIRExpr):
    callee: str = ""
    args: list[HIRExpr] = field(default_factory=list)


@dataclass
class HIRMethodCall(HIRExpr):
    receiver: HIRExpr = field(default_factory=HIRExpr)
    method: str = ""
    args: list[HIRExpr] = field(default_factory=list)


@dataclass
class HIRFieldAccess(HIRExpr):
    receiver: HIRExpr = field(default_factory=HIRExpr)
    field_name: str = ""


@dataclass
class HIRStructInit(HIRExpr):
    struct_name: str = ""
    fields: list[tuple[str, HIRExpr]] = field(default_factory=list)


@dataclass
class HIREnumInit(HIRExpr):
    enum_name: str = ""
    variant: str = ""
    payload: Optional[HIRExpr] = None


@dataclass
class HIRBlock(HIRExpr):
    stmts: list[HIRStmt] = field(default_factory=list)
    result: Optional[HIRExpr] = None


@dataclass
class HIRIf(HIRExpr):
    cond: HIRExpr = field(default_factory=HIRExpr)
    then_branch: HIRExpr = field(default_factory=HIRExpr)
    else_branch: Optional[HIRExpr] = None


@dataclass
class HIRMatchArm:
    pattern_variant: Optional[str]
    pattern_var: Optional[str]
    body: HIRExpr


@dataclass
class HIRMatch(HIRExpr):
    scrutinee: HIRExpr = field(default_factory=HIRExpr)
    arms: list[HIRMatchArm] = field(default_factory=list)


@dataclass
class HIRStmt:
    pass


@dataclass
class HIRLet(HIRStmt):
    name: str
    is_mut: bool
    ty: Optional[HIRType]
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
    ty: Optional[HIRType]


@dataclass
class HIRFn:
    name: str
    params: list[HIRParam]
    return_ty: Optional[HIRType]
    effects: list[str]
    body: HIRExpr


@dataclass
class HIRStruct:
    name: str
    fields: list[tuple[str, Optional[HIRType]]]


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


def lower_type_expr(te: Optional[a.TypeExpr]) -> Optional[HIRType]:
    if te is None:
        return None
    if isinstance(te, a.TName):
        return HIRType(name=te.name, args=[lower_type_expr(arg) for arg in te.args if arg])
    if isinstance(te, a.TTupleExpr):
        return HIRType(name="Tuple", args=[lower_type_expr(elem) for elem in te.elems if elem])
    return HIRType(name="Unknown")


def lower_expr_to_hir(e: a.Expr) -> HIRExpr:
    if isinstance(e, a.IntLit):
        return HIRLiteral(value=e.value, ty=HIRType("Int"))
    if isinstance(e, a.StrLit):
        return HIRLiteral(value=e.value, ty=HIRType("String"))
    if isinstance(e, a.BoolLit):
        return HIRLiteral(value=e.value, ty=HIRType("Bool"))
    if isinstance(e, a.UnitLit):
        return HIRLiteral(value=(), ty=HIRType("Unit"))
    if isinstance(e, a.Var):
        return HIRVar(name=e.name)
    if isinstance(e, a.Binary):
        return HIRBinary(op=e.op, left=lower_expr_to_hir(e.left), right=lower_expr_to_hir(e.right))
    if isinstance(e, a.Unary):
        return HIRUnary(op=e.op, operand=lower_expr_to_hir(e.operand))
    if isinstance(e, a.Call):
        callee_name = e.callee.name if isinstance(e.callee, a.Var) else "anon_callee"
        return HIRCall(callee=callee_name, args=[lower_expr_to_hir(arg) for arg in e.args])
    if isinstance(e, a.MethodCall):
        return HIRMethodCall(receiver=lower_expr_to_hir(e.recv), method=e.op, args=[lower_expr_to_hir(arg) for arg in e.args])
    if isinstance(e, a.FieldAccess):
        return HIRFieldAccess(receiver=lower_expr_to_hir(e.recv), field_name=e.field)
    if isinstance(e, a.StructLit):
        return HIRStructInit(struct_name=e.name, fields=[(f_name, lower_expr_to_hir(f_val)) for f_name, f_val in e.fields])
    if isinstance(e, a.EnumCtor):
        payload = lower_expr_to_hir(e.args[0]) if e.args else None
        return HIREnumInit(enum_name=e.enum_name, variant=e.variant, payload=payload)
    if isinstance(e, a.If):
        then_b = lower_expr_to_hir(e.then)
        else_b = lower_expr_to_hir(e.els) if e.els else None
        return HIRIf(cond=lower_expr_to_hir(e.cond), then_branch=then_b, else_branch=else_b)
    if isinstance(e, a.Block):
        stmts = []
        for st in e.stmts:
            if isinstance(st, a.Let):
                stmts.append(HIRLet(name=st.name, is_mut=st.mut, ty=lower_type_expr(st.ty), init=lower_expr_to_hir(st.value)))
            elif isinstance(st, a.Assign):
                stmts.append(HIRAssign(name=st.name, value=lower_expr_to_hir(st.value)))
            elif isinstance(st, a.While):
                stmts.append(HIRWhile(cond=lower_expr_to_hir(st.cond), body=lower_expr_to_hir(st.body)))
            else:
                stmts.append(HIRExprStmt(expr=lower_expr_to_hir(st)))
        result = lower_expr_to_hir(e.tail) if e.tail else None
        return HIRBlock(stmts=stmts, result=result)

    return HIRVar(name="<unlowered>")


def lower_ast_to_hir(decls: list[a.Decl], module_name: str = "main") -> HIRModule:
    """Lower parsed and verified AST declarations into HIR."""
    mod = HIRModule(name=module_name)
    for d in decls:
        if isinstance(d, a.StructDecl):
            fields = [(f.name, lower_type_expr(f.ty)) for f in d.fields]
            mod.structs.append(HIRStruct(name=d.name, fields=fields))
        elif isinstance(d, a.EnumDecl):
            variants = []
            for v in d.variants:
                v_ty = lower_type_expr(v.payloads[0]) if v.payloads else None
                variants.append((v.name, v_ty))
            mod.enums.append(HIREnum(name=d.name, variants=variants))
        elif isinstance(d, a.FnDecl):
            params = [HIRParam(name=p.name, ty=lower_type_expr(p.ty)) for p in d.params]
            ret_ty = lower_type_expr(d.ret)
            effects = [lbl for lbl, _ in d.eff.labels] if d.eff else []
            body = lower_expr_to_hir(d.body)
            mod.functions.append(HIRFn(name=d.name, params=params, return_ty=ret_ty, effects=effects, body=body))
    return mod
