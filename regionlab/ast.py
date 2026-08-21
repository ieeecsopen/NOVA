"""AST for the regionlab prototype. See regionlab/README.md."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Node:
    line: int


# ------------------------------------------------------------ expressions

@dataclass
class IntLit(Node):
    value: int


@dataclass
class Var(Node):
    name: str


@dataclass
class Alloc(Node):
    region: str
    value: "Node"


@dataclass
class Read(Node):
    name: str


@dataclass
class Shared(Node):
    region: str


@dataclass
class Exclusive(Node):
    region: str


@dataclass
class Copy(Node):
    name: str


@dataclass
class Call(Node):
    fn: str
    args: list


@dataclass
class RegionBlock(Node):
    name: str
    body: "Block"


# ------------------------------------------------------------- statements

@dataclass
class Let(Node):
    name: str
    value: Node


@dataclass
class Close(Node):
    region: str


@dataclass
class Write(Node):
    name: str
    value: Node


@dataclass
class ExprStmt(Node):
    value: Node


@dataclass
class Block(Node):
    stmts: list
    tail: Node | None


# ---------------------------------------------------------- declarations

@dataclass
class Param(Node):
    name: str
    ty: str


@dataclass
class FnDecl(Node):
    name: str
    params: list[Param]
    ret: str
    body: Block


@dataclass
class Program(Node):
    fns: dict[str, FnDecl]
    main: Block
