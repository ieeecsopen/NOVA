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
