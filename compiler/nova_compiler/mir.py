"""Mid-Level Intermediate Representation (MIR) for NOVA.

MIR properties:
- Basic Blocks with single entry, single exit
- Explicit Control Flow Graph (CFG)
- Explicit linear region allocation and drop elaboration
- Direct mapping to LLVM IR / C native backend
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from .hir import HIRModule, HIRFn, HIRExpr, HIRLiteral, HIRVar, HIRBinary, HIRUnary, HIRCall, HIRBlock, HIRIf, HIRLet, HIRAssign, HIRWhile, HIRExprStmt


@dataclass
class MIRLocal:
    id: int
    name: Optional[str]
    ty_name: str


@dataclass
class MIROperand:
    pass


@dataclass
class MIRConstant(MIROperand):
    value: Any
    ty_name: str


@dataclass
class MIRUse(MIROperand):
    local_id: int


@dataclass
class MIRRvalue:
    pass


@dataclass
class MIRUseRvalue(MIRRvalue):
    operand: MIROperand


@dataclass
class MIRBinaryRvalue(MIRRvalue):
    op: str
    left: MIROperand
    right: MIROperand


@dataclass
class MIRUnaryRvalue(MIRRvalue):
    op: str
    operand: MIROperand


@dataclass
class MIRCallRvalue(MIRRvalue):
    callee: str
    args: list[MIROperand]


@dataclass
class MIRStructRvalue(MIRRvalue):
    struct_name: str
    field_operands: list[MIROperand]


@dataclass
class MIRFieldAccessRvalue(MIRRvalue):
    base: MIROperand
    field_idx: int


@dataclass
class MIRStatement:
    pass


@dataclass
class MIRAssign(MIRStatement):
    dest_id: int
    rvalue: MIRRvalue


@dataclass
class MIRDrop(MIRStatement):
    local_id: int


@dataclass
class MIRTerminator:
    pass


@dataclass
class MIRGoto(MIRTerminator):
    target_block: int


@dataclass
class MIRBranch(MIRTerminator):
    cond: MIROperand
    then_block: int
    else_block: int


@dataclass
class MIRReturn(MIRTerminator):
    value: Optional[MIROperand]


@dataclass
class MIRSwitch(MIRTerminator):
    discriminant: MIROperand
    targets: list[tuple[int, int]]  # (variant_tag, target_block_id)
    otherwise: int


@dataclass
class MIRBasicBlock:
    id: int
    statements: list[MIRStatement] = field(default_factory=list)
    terminator: Optional[MIRTerminator] = None


@dataclass
class MIRFunction:
    name: str
    params: list[MIRLocal]
    return_ty: str
    locals: list[MIRLocal] = field(default_factory=list)
    blocks: list[MIRBasicBlock] = field(default_factory=list)

    def add_local(self, name: Optional[str], ty_name: str) -> int:
        local_id = len(self.locals)
        self.locals.append(MIRLocal(local_id, name, ty_name))
        return local_id

    def add_block(self) -> MIRBasicBlock:
        block_id = len(self.blocks)
        bb = MIRBasicBlock(block_id)
        self.blocks.append(bb)
        return bb


@dataclass
class MIRModule:
    name: str
    functions: list[MIRFunction] = field(default_factory=list)


def lower_hir_to_mir(hir_mod: HIRModule) -> MIRModule:
    """Lower high-level intermediate representation into basic-block CFG MIR."""
    mir_mod = MIRModule(name=hir_mod.name)

    for h_fn in hir_mod.functions:
        fn_params = []
        fn_locals = []
        for i, p in enumerate(h_fn.params):
            loc = MIRLocal(id=i, name=p.name, ty_name=str(p.ty) if p.ty else "Int")
            fn_params.append(loc)
            fn_locals.append(loc)

        ret_ty_str = str(h_fn.return_ty) if h_fn.return_ty else "Int"
        mir_fn = MIRFunction(name=h_fn.name, params=fn_params, return_ty=ret_ty_str, locals=fn_locals)
        entry_bb = mir_fn.add_block()

        # Lower body
        if isinstance(h_fn.body, HIRBlock):
            for st in h_fn.body.stmts:
                if isinstance(st, HIRLet):
                    loc_id = mir_fn.add_local(st.name, str(st.ty) if st.ty else "Int")
                    if isinstance(st.init, HIRLiteral):
                        op = MIRConstant(st.init.value, str(st.ty) if st.ty else "Int")
                        entry_bb.statements.append(MIRAssign(loc_id, MIRUseRvalue(op)))
                elif isinstance(st, HIRExprStmt) and isinstance(st.expr, HIRCall):
                    args_op = [MIRConstant(a.value, "Any") if isinstance(a, HIRLiteral) else MIRUse(0) for a in st.expr.args]
                    entry_bb.statements.append(MIRAssign(mir_fn.add_local(None, "Unit"), MIRCallRvalue(st.expr.callee, args_op)))

            if h_fn.body.result and isinstance(h_fn.body.result, HIRLiteral):
                entry_bb.terminator = MIRReturn(MIRConstant(h_fn.body.result.value, ret_ty_str))
            else:
                entry_bb.terminator = MIRReturn(MIRConstant(0, ret_ty_str))
        else:
            entry_bb.terminator = MIRReturn(MIRConstant(0, ret_ty_str))

        mir_mod.functions.append(mir_fn)

    return mir_mod
