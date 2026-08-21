"""Recursive-descent parser for regionlab. See regionlab/README.md."""
from __future__ import annotations

from .ast import (Alloc, Block, Call, Close, Copy, Exclusive, ExprStmt,
                  FnDecl, IntLit, Let, Param, Program, Read, RegionBlock,
                  Shared, Var, Write)
from .lexer import Token, lex


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, src: str) -> None:
        self.toks = lex(src)
        self.i = 0

    @property
    def cur(self) -> Token:
        return self.toks[self.i]

    def at(self, kind: str, text: str | None = None) -> bool:
        t = self.cur
        return t.kind == kind and (text is None or t.text == text)

    def bump(self) -> Token:
        t = self.cur
        if t.kind != "eof":
            self.i += 1
        return t

    def eat(self, kind: str, text: str | None = None) -> Token | None:
        return self.bump() if self.at(kind, text) else None

    def expect(self, kind: str, text: str | None = None) -> Token:
        if self.at(kind, text):
            return self.bump()
        raise ParseError(f"line {self.cur.line}: expected `{text or kind}`, "
                         f"found `{self.cur.text or 'eof'}`")

    def parse_program(self) -> Program:
        fns: dict[str, FnDecl] = {}
        while self.at("kw", "fn"):
            f = self.parse_fn()
            fns[f.name] = f
        main = self.parse_stmts_until("eof")
        self.expect("eof")
        return Program(1, fns, main)

    def parse_stmts_until(self, end_kind: str) -> Block:
        """Like `parse_block`, but for the implicit top-level block,
        which has no surrounding `{ }` -- there is exactly one such
        block per program, so no ambiguity is introduced by omitting
        the braces there specifically."""
        line = self.cur.line
        stmts = []
        tail = None
        while not self.at(end_kind):
            if self.at("kw", "let"):
                stmts.append(self.parse_let())
                continue
            if self.at("kw", "close"):
                stmts.append(self.parse_close())
                continue
            if self.at("kw", "write"):
                stmts.append(self.parse_write())
                continue
            e = self.parse_expr()
            if self.eat(";"):
                stmts.append(ExprStmt(line, e))
                continue
            tail = e
            break
        return Block(line, stmts, tail)

    def parse_fn(self) -> FnDecl:
        line = self.cur.line
        self.expect("kw", "fn")
        name = self.expect("ident").text
        self.expect("(")
        params = []
        while not self.at(")"):
            pname = self.expect("ident").text
            self.expect(":")
            pty = self.expect("ident").text
            params.append(Param(line, pname, pty))
            if not self.eat(","):
                break
        self.expect(")")
        self.expect("->")
        ret = self.expect("ident").text
        body = self.parse_block()
        return FnDecl(line, name, params, ret, body)

    def parse_block(self) -> Block:
        line = self.cur.line
        self.expect("{")
        stmts = []
        tail = None
        while not self.at("}"):
            if self.at("kw", "let"):
                stmts.append(self.parse_let())
                continue
            if self.at("kw", "close"):
                stmts.append(self.parse_close())
                continue
            if self.at("kw", "write"):
                stmts.append(self.parse_write())
                continue
            e = self.parse_expr()
            if self.eat(";"):
                stmts.append(ExprStmt(line, e))
                continue
            tail = e
            break
        self.expect("}")
        return Block(line, stmts, tail)

    def parse_let(self) -> Let:
        line = self.cur.line
        self.expect("kw", "let")
        name = self.expect("ident").text
        self.expect("=")
        v = self.parse_expr()
        self.expect(";")
        return Let(line, name, v)

    def parse_close(self) -> Close:
        line = self.cur.line
        self.expect("kw", "close")
        self.expect("(")
        name = self.expect("ident").text
        self.expect(")")
        self.expect(";")
        return Close(line, name)

    def parse_write(self) -> Write:
        line = self.cur.line
        self.expect("kw", "write")
        self.expect("(")
        name = self.expect("ident").text
        self.expect(",")
        v = self.parse_expr()
        self.expect(")")
        self.expect(";")
        return Write(line, name, v)

    def parse_expr(self):
        line = self.cur.line
        if self.at("int"):
            return IntLit(line, int(self.bump().text))
        if self.at("kw", "alloc"):
            self.bump()
            self.expect("(")
            r = self.expect("ident").text
            self.expect(",")
            v = self.parse_expr()
            self.expect(")")
            return Alloc(line, r, v)
        if self.at("kw", "read"):
            self.bump()
            self.expect("(")
            n = self.expect("ident").text
            self.expect(")")
            return Read(line, n)
        if self.at("kw", "shared"):
            self.bump()
            self.expect("(")
            r = self.expect("ident").text
            self.expect(")")
            return Shared(line, r)
        if self.at("kw", "exclusive"):
            self.bump()
            self.expect("(")
            r = self.expect("ident").text
            self.expect(")")
            return Exclusive(line, r)
        if self.at("kw", "copy"):
            self.bump()
            self.expect("(")
            n = self.expect("ident").text
            self.expect(")")
            return Copy(line, n)
        if self.at("kw", "region"):
            self.bump()
            name = self.expect("ident").text
            body = self.parse_block()
            return RegionBlock(line, name, body)
        if self.at("ident"):
            name = self.bump().text
            if self.at("("):
                self.bump()
                args = []
                while not self.at(")"):
                    args.append(self.parse_expr())
                    if not self.eat(","):
                        break
                self.expect(")")
                return Call(line, name, args)
            return Var(line, name)
        raise ParseError(f"line {line}: expected an expression, "
                         f"found `{self.cur.text or 'eof'}`")


def parse(src: str) -> Program:
    return Parser(src).parse_program()
