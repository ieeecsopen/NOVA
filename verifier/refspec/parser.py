"""Recursive-descent parser for NOVA v0.2 (RFC 0001-0005)."""
from __future__ import annotations

from .ast import (Assign, Binary, Block, BoolLit, Call, CapabilityDecl,
                  EnumCtor, EnumDecl, Expr, FieldAccess, FnDecl, For, If,
                  ImplDecl, ImportDecl, IntLit, Lambda, Let, Match, MatchArm,
                  MethodCall, Module, Node, OpSig, PBind, PBool, PInt,
                  PString, PTuple, PVariant, PWildcard, Param, Pattern,
                  Program, RowExpr, StrLit, StructDecl, StructField,
                  StructLit, TFunExpr, TName, TTupleExpr, TraitDecl,
                  TraitMethodSig, TupleLit, TypeExpr, TypeParam, Unary,
                  UnitLit, Var, VariantDecl, While)
from .diagnostics import Diagnostic, Label, Span
from .lexer import Token, lex

# (precedence, ...) lowest binds loosest
BIN_LEVELS = [
    ["||"],
    ["&&"],
    ["==", "!=", "<", "<=", ">", ">="],
    ["+", "-"],
    ["*", "/"],
]


class Parser:
    def __init__(self, src: str, base: int = 0, module_path: str = "main") -> None:
        self.toks = lex(src, base)
        self.i = 0
        self.module_path = module_path
        # True inside an `if`/`while`/`for`/`match` scrutinee: bare struct
        # literals are ambiguous with the block that follows (`if X { }` —
        # is `{` the literal's fields or the if-body?), so they are
        # disabled there, exactly as Rust disables them (SYNTAX.md
        # "Struct literals in condition position").
        self._no_struct_lit = 0

    # ------------------------------------------------------- plumbing
    @property
    def cur(self) -> Token:
        return self.toks[self.i]

    def peek(self, k: int) -> Token:
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else self.toks[-1]

    def at(self, kind: str, text: str | None = None) -> bool:
        t = self.cur
        return t.kind == kind and (text is None or t.text == text)

    def bump(self) -> Token:
        t = self.cur
        if t.kind != "eof":
            self.i += 1
        return t

    def eat(self, kind: str, text: str | None = None) -> Token | None:
        if self.at(kind, text):
            return self.bump()
        return None

    def expect(self, kind: str, text: str | None = None) -> Token:
        if self.at(kind, text):
            return self.bump()
        want = text or kind
        raise Diagnostic(
            "E0002", f"expected `{want}`",
            [Label(self.cur.span, f"found `{self.cur.text or 'end of file'}`")])

    # ------------------------------------------------------- program
    def parse_module(self) -> Module:
        decls = []
        start = self.cur.span
        while not self.at("eof"):
            decls.append(self.parse_decl())
        end = self.toks[-1].span
        return Module(start.to(end), self.module_path, decls)

    def parse_decl(self):
        is_pub = bool(self.eat("kw", "pub"))
        if self.at("kw", "capability"):
            if is_pub:
                raise Diagnostic("E0002", "`pub` does not apply to `capability`",
                                 [Label(self.cur.span, "capabilities are "
                                        "declared once, in the prelude")])
            return self.parse_capability()
        if self.at("kw", "fn"):
            return self.parse_fn(is_pub)
        if self.at("kw", "struct"):
            return self.parse_struct(is_pub)
        if self.at("kw", "enum"):
            return self.parse_enum(is_pub)
        if self.at("kw", "trait"):
            return self.parse_trait(is_pub)
        if self.at("kw", "impl"):
            if is_pub:
                raise Diagnostic("E0002", "`pub` does not apply to `impl`",
                                 [Label(self.cur.span, "an impl's visibility "
                                        "follows its trait and target")])
            return self.parse_impl()
        if self.at("kw", "import"):
            if is_pub:
                raise Diagnostic("E0002", "`pub` does not apply to `import`",
                                 [Label(self.cur.span, "re-exports are not "
                                        "supported in v0.2")])
            return self.parse_import()
        raise Diagnostic(
            "E0002", "expected a declaration",
            [Label(self.cur.span, f"found `{self.cur.text}`")],
            notes=["expected one of: capability, fn, struct, enum, trait, "
                   "impl, import"])

    def parse_import(self) -> ImportDecl:
        kw = self.expect("kw", "import")
        path = [self.expect("ident").text]
        while self.eat("."):
            path.append(self.expect("ident").text)
        semi = self.expect(";")
        return ImportDecl(kw.span.to(semi.span), path, kw.span.to(semi.span))

    def parse_capability(self) -> CapabilityDecl:
        kw = self.expect("kw", "capability")
        name_tok = self.expect("ident")
        self.expect("{")
        ops: list[OpSig] = []
        while not self.at("}"):
            op_name = self.expect("ident")
            params = self.parse_params()
            self.expect("->")
            ret = self.parse_type()
            ops.append(OpSig(op_name.span.to(ret.span), op_name.text,
                             params, ret))
        close = self.expect("}")
        return CapabilityDecl(kw.span.to(close.span), name_tok.text,
                              name_tok.span, ops)

    def parse_type_params(self) -> list[TypeParam]:
        out: list[TypeParam] = []
        if not self.eat("["):
            return out
        while not self.at("]"):
            n = self.expect("ident")
            bound = None
            if self.eat(":"):
                bound = self.expect("ident").text
            out.append(TypeParam(n.span, n.text, bound))
            if not self.eat(","):
                break
        self.expect("]")
        return out

    def parse_fn(self, is_pub: bool = False, is_method: bool = False) -> FnDecl:
        kw = self.expect("kw", "fn")
        name_tok = self.expect("ident")
        # One `[...]` binder list for BOTH type and row parameters
        # (SYNTAX.md "Generic and row parameters share one binder"):
        # `fn with_retry[r](f: () -> Int ! r) -> Int ! r` and
        # `fn identity[T](x: T) -> T` use the same syntax, and each name
        # is classified by *how it is used* in the signature — appearing
        # after `!` makes it a row parameter, appearing as an ordinary
        # type makes it a type parameter — rather than forcing the
        # programmer to say which bracket group is which.
        all_params = self.parse_type_params()
        params = self.parse_params(allow_self=is_method)
        self.expect("->")
        ret = self.parse_type()
        eff = eff_span = None
        if self.at("!"):
            bang = self.bump()
            eff = self.parse_row()
            eff_span = bang.span.to(eff.span)
        widen = False
        if self.eat("="):
            self.expect("kw", "widen")
            widen = True
        body = self.parse_block()

        row_names = set()
        for p in params:
            row_names |= _row_tail_names(p.ty)
        row_names |= _row_tail_names(ret)
        if eff is not None and eff.tail is not None:
            row_names.add(eff.tail)
        row_params = [tp.name for tp in all_params if tp.name in row_names]
        type_params = [tp for tp in all_params if tp.name not in row_names]

        return FnDecl(kw.span.to(body.span), name_tok.text, name_tok.span,
                      type_params, row_params, params, ret, eff, eff_span,
                      widen, body, is_pub, is_method)

    def parse_params(self, allow_self: bool = False) -> list[Param]:
        self.expect("(")
        out: list[Param] = []
        if allow_self and self.at("kw", "self"):
            t = self.bump()
            out.append(Param(t.span, "self", TName(t.span, "Self")))
            if not self.eat(","):
                self.expect(")")
                return out
        while not self.at(")"):
            n = self.expect("ident")
            self.expect(":")
            t = self.parse_type()
            out.append(Param(n.span.to(t.span), n.text, t))
            if not self.eat(","):
                break
        self.expect(")")
        return out

    def parse_struct(self, is_pub: bool) -> StructDecl:
        kw = self.expect("kw", "struct")
        name_tok = self.expect("ident")
        type_params = self.parse_type_params()
        self.expect("{")
        fields: list[StructField] = []
        while not self.at("}"):
            n = self.expect("ident")
            self.expect(":")
            t = self.parse_type()
            fields.append(StructField(n.span.to(t.span), n.text, t))
            if not self.eat(","):
                break
        close = self.expect("}")
        return StructDecl(kw.span.to(close.span), name_tok.text,
                          name_tok.span, type_params, fields, is_pub)

    def parse_enum(self, is_pub: bool) -> EnumDecl:
        kw = self.expect("kw", "enum")
        name_tok = self.expect("ident")
        type_params = self.parse_type_params()
        self.expect("{")
        variants: list[VariantDecl] = []
        while not self.at("}"):
            v = self.expect("ident")
            args: list[TypeExpr] = []
            end_span = v.span
            if self.eat("("):
                while not self.at(")"):
                    t = self.parse_type()
                    args.append(t)
                    end_span = t.span
                    if not self.eat(","):
                        break
                end_span = self.expect(")").span
            variants.append(VariantDecl(v.span.to(end_span), v.text,
                                        v.span, args))
            if not self.eat(","):
                break
        close = self.expect("}")
        return EnumDecl(kw.span.to(close.span), name_tok.text,
                        name_tok.span, type_params, variants, is_pub)

    def parse_trait(self, is_pub: bool) -> TraitDecl:
        kw = self.expect("kw", "trait")
        name_tok = self.expect("ident")
        self.expect("{")
        methods: list[TraitMethodSig] = []
        while not self.at("}"):
            self.expect("kw", "fn")
            m = self.expect("ident")
            params = self.parse_params(allow_self=True)
            if params and params[0].name == "self":
                params = params[1:]     # TraitMethodSig excludes `self`
            self.expect("->")
            ret = self.parse_type()
            semi = self.expect(";")
            methods.append(TraitMethodSig(m.span.to(semi.span), m.text,
                                          m.span, params, ret))
        close = self.expect("}")
        return TraitDecl(kw.span.to(close.span), name_tok.text,
                         name_tok.span, methods, is_pub)

    def parse_impl(self) -> ImplDecl:
        kw = self.expect("kw", "impl")
        type_params = self.parse_type_params()
        trait_tok = self.expect("ident")
        self._expect_word("for")
        target = self.parse_type()
        self.expect("{")
        methods: list[FnDecl] = []
        while not self.at("}"):
            methods.append(self.parse_fn(is_method=True))
        close = self.expect("}")
        return ImplDecl(kw.span.to(close.span), trait_tok.text,
                        trait_tok.span, type_params, target, methods)

    def _expect_word(self, word: str) -> Token:
        # `for` is a keyword (shared with the `for` loop), so it is
        # matched as kind "kw", not "ident" — a small helper to keep
        # `parse_impl` readable despite that.
        return self.expect("kw", word)

    # ---------------------------------------------------------- types
    def parse_type(self) -> TypeExpr:
        if self.at("("):
            open_tok = self.bump()
            elems: list[TypeExpr] = []
            trailing_comma = False
            while not self.at(")"):
                elems.append(self.parse_type())
                if not self.eat(","):
                    break
                trailing_comma = True
            close = self.expect(")")
            if self.at("->"):
                self.bump()
                ret = self.parse_type()
                eff = None
                end = ret.span
                if self.at("!"):
                    self.bump()
                    eff = self.parse_row()
                    end = eff.span
                return TFunExpr(open_tok.span.to(end), elems, ret, eff)
            if len(elems) == 1 and not trailing_comma:
                return elems[0]                       # `(T)` is a grouping
            return TTupleExpr(open_tok.span.to(close.span), elems)
        t = self.expect("ident")
        args: list[TypeExpr] = []
        end = t.span
        if self.eat("["):
            while not self.at("]"):
                a = self.parse_type()
                args.append(a)
                end = a.span
                if not self.eat(","):
                    break
            end = self.expect("]").span
        return TName(t.span.to(end), t.text, args)

    def parse_row(self) -> RowExpr:
        if self.at("ident"):
            t = self.bump()
            return RowExpr(t.span, [], t.text)
        open_tok = self.expect("{")
        labels: list[tuple[str, Span]] = []
        tail: str | None = None
        while not self.at("}") and not self.at("|"):
            t = self.expect("ident")
            labels.append((t.text, t.span))
            if not self.eat(","):
                break
        if self.eat("|"):
            tail = self.expect("ident").text
        close = self.expect("}")
        return RowExpr(open_tok.span.to(close.span), labels, tail)

    # ---------------------------------------------------- expressions
    def parse_block(self) -> Block:
        open_tok = self.expect("{")
        stmts: list[Let | Expr] = []
        tail: Expr | None = None
        depth = self._no_struct_lit
        self._no_struct_lit = 0     # inside `{ }`, struct literals are fine
        try:
            while not self.at("}"):
                if self.at("kw", "let"):
                    stmts.append(self.parse_let())
                    continue
                e = self.parse_expr()
                if self.eat(";"):
                    stmts.append(e)
                    continue
                if self.at("}"):
                    tail = e
                    break
                if isinstance(e, (If, While, For, Match, Block)):
                    # A block-like expression (SYNTAX.md "Block-like
                    # expressions as statements") needs no trailing `;`
                    # when it is not the last thing in the block —
                    # exactly Rust's rule, adopted for the same reason:
                    # `if x { f(); } g();` reads naturally with no
                    # semicolon after the `if`'s closing brace.
                    stmts.append(e)
                    continue
                raise Diagnostic(
                    "E0002", "expected `;` after this expression",
                    [Label(e.span, "statement must end with `;`, or be "
                           "the last expression in the block")])
            close = self.expect("}")
        finally:
            self._no_struct_lit = depth
        return Block(open_tok.span.to(close.span), stmts, tail)

    def parse_let(self) -> Let:
        let_kw = self.bump()
        is_mut = bool(self.eat("kw", "mut"))
        n = self.expect("ident")
        ty = None
        if self.eat(":"):
            ty = self.parse_type()
        self.expect("=")
        v = self.parse_expr()
        semi = self.expect(";")
        return Let(let_kw.span.to(semi.span), n.text, n.span, ty, v, is_mut)

    def parse_expr(self) -> Expr:
        return self.parse_assign()

    def parse_assign(self) -> Expr:
        # Only a bare identifier may appear on the left of `=`; this is
        # deliberately not a general lvalue grammar (RFC 0005 §2 — no
        # field or index assignment, since NOVA v0.2 has no mutable
        # fields or aliasing).
        if self.at("ident") and self.peek(1).kind == "=" \
                and self.peek(1).text != "==":
            n = self.bump()
            self.bump()   # '='
            v = self.parse_expr()
            return Assign(n.span.to(v.span), n.text, n.span, v)
        return self.parse_binary(0)

    def parse_binary(self, level: int) -> Expr:
        if level >= len(BIN_LEVELS):
            return self.parse_unary()
        left = self.parse_binary(level + 1)
        while self.cur.kind in BIN_LEVELS[level]:
            op = self.bump()
            right = self.parse_binary(level + 1)
            left = Binary(left.span.to(right.span), op.text, left, right)
        return left

    def parse_unary(self) -> Expr:
        if self.at("-") or self.at("!"):
            op = self.bump()
            operand = self.parse_unary()
            return Unary(op.span.to(operand.span), op.text, operand)
        return self.parse_postfix()

    def parse_postfix(self) -> Expr:
        e = self.parse_primary()
        while True:
            if self.at("("):
                self.bump()
                args = self.parse_args()
                close = self.expect(")")
                e = Call(e.span.to(close.span), e, args)
            elif self.at("."):
                self.bump()
                if self.at("int"):
                    idx = self.bump()
                    e = FieldAccess(e.span.to(idx.span), e, idx.text, idx.span)
                    continue
                op = self.expect("ident")
                if self.at("("):
                    self.bump()
                    args = self.parse_args()
                    close = self.expect(")")
                    e = MethodCall(e.span.to(close.span), e, op.text,
                                   op.span, args)
                else:
                    e = FieldAccess(e.span.to(op.span), e, op.text, op.span)
            else:
                return e

    def parse_args(self) -> list[Expr]:
        args: list[Expr] = []
        while not self.at(")"):
            args.append(self.parse_expr())
            if not self.eat(","):
                break
        return args

    def parse_primary(self) -> Expr:
        t = self.cur
        if t.kind == "int":
            self.bump()
            return IntLit(t.span, int(t.text))
        if t.kind == "string":
            self.bump()
            return StrLit(t.span, t.text)
        if self.at("kw", "true") or self.at("kw", "false"):
            self.bump()
            return BoolLit(t.span, t.text == "true")
        if self.at("kw", "self"):
            self.bump()
            return Var(t.span, "self")
        if t.kind == "ident":
            return self._parse_ident_led()
        if self.at("kw", "if"):
            self.bump()
            cond = self._parse_condition()
            then = self.parse_block()
            self.expect("kw", "else")
            els = self.parse_block() if self.at("{") else self._parse_else()
            return If(t.span.to(els.span), cond, then, els)
        if self.at("kw", "while"):
            self.bump()
            cond = self._parse_condition()
            body = self.parse_block()
            return While(t.span.to(body.span), cond, body)
        if self.at("kw", "for"):
            self.bump()
            var = self.expect("ident")
            self._expect_word("in")
            it = self._parse_condition()
            body = self.parse_block()
            return For(t.span.to(body.span), var.text, var.span, it, body)
        if self.at("kw", "match"):
            self.bump()
            scrut = self._parse_condition()
            self.expect("{")
            arms: list[MatchArm] = []
            while not self.at("}"):
                pat = self.parse_pattern()
                self.expect("=>")
                body = self.parse_expr()
                arm_end = body.span
                if self.eat(","):
                    pass
                arms.append(MatchArm(pat.span.to(arm_end), pat, body))
            close = self.expect("}")
            return Match(t.span.to(close.span), scrut, arms)
        if self.at("{"):
            return self.parse_block()
        if self.at("||"):
            self.bump()
            body = self.parse_expr()
            return Lambda(t.span.to(body.span), [], body)
        if self.at("|"):
            self.bump()
            params: list[Param] = []
            while not self.at("|"):
                n = self.expect("ident")
                self.expect(":")
                ty = self.parse_type()
                params.append(Param(n.span.to(ty.span), n.text, ty))
                if not self.eat(","):
                    break
            self.expect("|")
            body = self.parse_expr()
            return Lambda(t.span.to(body.span), params, body)
        if self.at("("):
            self.bump()
            if self.at(")"):
                close = self.bump()
                return UnitLit(t.span.to(close.span))
            first = self.parse_expr()
            if self.eat(","):
                elems = [first]
                while not self.at(")"):
                    elems.append(self.parse_expr())
                    if not self.eat(","):
                        break
                close = self.expect(")")
                return TupleLit(t.span.to(close.span), elems)
            self.expect(")")
            return first
        raise Diagnostic("E0002", "expected an expression",
                         [Label(t.span, f"found `{t.text or 'end of file'}`")])

    def _parse_condition(self) -> Expr:
        """Parse a scrutinee expression with struct literals suppressed,
        so `if x { ... }` cannot be misread as `if (x { }) { ... }`."""
        self._no_struct_lit += 1
        try:
            return self.parse_expr()
        finally:
            self._no_struct_lit -= 1

    def _parse_else(self) -> Expr:
        if self.at("kw", "if"):
            return self.parse_primary()
        return self.parse_expr()

    def _parse_ident_led(self) -> Expr:
        """Everything that can start with an identifier: a variable, an
        enum constructor `Name::Variant(...)`, or a struct literal
        `Name { field: expr, ... }` (suppressed in condition position)."""
        t = self.bump()
        if self.eat("::"):
            variant = self.expect("ident")
            args: list[Expr] = []
            end = variant.span
            if self.at("("):
                self.bump()
                args = self.parse_args()
                end = self.expect(")").span
            return EnumCtor(t.span.to(end), t.text, variant.text,
                            variant.span, args)
        if self.at("{") and self._no_struct_lit == 0 and self._looks_like_struct_lit():
            self.bump()
            fields: list[tuple[str, Expr]] = []
            while not self.at("}"):
                fname = self.expect("ident")
                self.expect(":")
                fval = self.parse_expr()
                fields.append((fname.text, fval))
                if not self.eat(","):
                    break
            close = self.expect("}")
            return StructLit(t.span.to(close.span), t.text, t.span, fields)
        return Var(t.span, t.text)

    def _looks_like_struct_lit(self) -> bool:
        """Disambiguate `Name { ... }` (struct literal) from `Name` being
        a plain variable immediately followed by an unrelated block —
        the latter cannot occur in an expression position in v0.2 (blocks
        are not juxtaposed with a preceding expression), so seeing `{`
        right after a capitalized-or-not identifier, outside condition
        position, is always a struct literal. Kept as its own method so
        the one heuristic this parser relies on is named and explained
        in one place."""
        return True


def _row_tail_names(t: TypeExpr) -> set[str]:
    """Every row-variable name mentioned anywhere inside a type
    expression, at any nesting depth — used to classify a `[...]`
    binder name as a row parameter (RFC 0003 §1)."""
    out: set[str] = set()
    if isinstance(t, TFunExpr):
        for p in t.params:
            out |= _row_tail_names(p)
        out |= _row_tail_names(t.ret)
        if t.eff is not None and t.eff.tail is not None:
            out.add(t.eff.tail)
    elif isinstance(t, TName):
        for arg in t.args:
            out |= _row_tail_names(arg)
    elif isinstance(t, TTupleExpr):
        for el in t.elems:
            out |= _row_tail_names(el)
    return out


def parse_module(src: str, base: int = 0, module_path: str = "main") -> Module:
    return Parser(src, base, module_path).parse_module()


def parse(src: str, base: int = 0) -> Module:
    """Back-compat entry point: parse a single module, used by every
    caller that predates RFC 0004's multi-module `Program`."""
    return parse_module(src, base)


def parse_pattern(p: "Parser") -> Pattern:
    return p.parse_pattern()


def _install_pattern_parser() -> None:
    def parse_pattern(self: Parser) -> Pattern:
        t = self.cur
        if self.at("ident", "_"):
            self.bump()
            return PWildcard(t.span)
        if t.kind == "int":
            self.bump()
            return PInt(t.span, int(t.text))
        if t.kind == "string":
            self.bump()
            return PString(t.span, t.text)
        if self.at("kw", "true") or self.at("kw", "false"):
            self.bump()
            return PBool(t.span, t.text == "true")
        if self.at("("):
            self.bump()
            elems = []
            while not self.at(")"):
                elems.append(self.parse_pattern())
                if not self.eat(","):
                    break
            close = self.expect(")")
            return PTuple(t.span.to(close.span), elems)
        if t.kind == "ident":
            self.bump()
            if self.eat("::"):
                variant = self.expect("ident")
                args = []
                end = variant.span
                if self.at("("):
                    self.bump()
                    while not self.at(")"):
                        args.append(self.parse_pattern())
                        if not self.eat(","):
                            break
                    end = self.expect(")").span
                return PVariant(t.span.to(end), t.text, variant.text,
                                variant.span, args)
            return PBind(t.span, t.text)
        raise Diagnostic("E0002", "expected a pattern",
                         [Label(t.span, f"found `{t.text or 'end of file'}`")])
    Parser.parse_pattern = parse_pattern


_install_pattern_parser()
