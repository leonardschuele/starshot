"""Recursive descent parser for Starshot IR S-expressions."""
from __future__ import annotations
from .lexer import Token, TokenType, tokenize
from .ast_nodes import (
    Program, Graph, TypeDef, Contract,
    PrimitiveType, ListType, OptionType, TupleType, RecordType,
    FunctionType, EnumType, NamedType,
    LitExpr, IdentExpr, LetExpr, IfExpr, MatchArm, MatchExpr,
    LambdaExpr, PipeExpr, DoExpr, OpExpr, CallExpr,
    ListExpr, RecordExpr, GetExpr, SetExpr, BuiltinExpr,
    SomeExpr, NoneExpr, TryExpr, ErrorExpr,
    WildcardPattern, LiteralPattern, IdentPattern, ConstructorPattern,
    TypeExpr, Expr, Pattern,
)


OPERATORS = {'+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', 'and', 'or'}
BUILTINS = {
    'not', 'map', 'filter', 'reduce', 'head', 'tail',
    'cons', 'append', 'nth', 'range', 'empty?',
    'sort-by', 'length', 'concat', 'substr', 'split',
    'join', 'format', 'print', 'read-line',
    'some', 'none', 'some?', 'unwrap', 'map-opt',
    'or-else', 'error', 'try', 'catch', 'set',
}
PRIMITIVE_TYPES = {'Int', 'Float', 'String', 'Bool', 'Unit'}
COMPOUND_TYPE_KEYWORDS = {'List', 'Option', 'Tuple', 'Record', '->', 'Enum'}


class ParseError(Exception):
    def __init__(self, msg: str, token: Token | None = None):
        loc = f" at {token.line}:{token.col}" if token else ""
        super().__init__(f"Parse error{loc}: {msg}")
        self.token = token


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, ttype: TokenType, value: str | None = None) -> Token:
        tok = self.advance()
        if tok.type != ttype:
            raise ParseError(f"Expected {ttype.name}, got {tok.type.name} ({tok.value!r})", tok)
        if value is not None and tok.value != value:
            raise ParseError(f"Expected {value!r}, got {tok.value!r}", tok)
        return tok

    def expect_ident(self, value: str | None = None) -> Token:
        return self.expect(TokenType.IDENT, value)

    def at_lparen(self) -> bool:
        return self.peek().type == TokenType.LPAREN

    def at_rparen(self) -> bool:
        return self.peek().type == TokenType.RPAREN

    def at_eof(self) -> bool:
        return self.peek().type == TokenType.EOF

    # === Program ===

    def parse_program(self) -> Program:
        self.expect(TokenType.LPAREN)
        self.expect_ident('program')
        defs = []
        while not self.at_rparen():
            defs.append(self.parse_definition())
        self.expect(TokenType.RPAREN)
        return Program(definitions=defs)

    def parse_definition(self):
        self.expect(TokenType.LPAREN)
        kw = self.advance()
        if kw.value == 'type':
            result = self.parse_type_def()
        elif kw.value == 'graph':
            result = self.parse_graph_def()
        else:
            raise ParseError(f"Expected 'type' or 'graph', got {kw.value!r}", kw)
        return result

    # === Type Definition ===

    def parse_type_def(self) -> TypeDef:
        name = self.expect(TokenType.IDENT).value
        type_expr = self.parse_type_expr()
        self.expect(TokenType.RPAREN)
        return TypeDef(name=name, type_expr=type_expr)

    # === Graph Definition ===

    def parse_graph_def(self) -> Graph:
        name = self.expect(TokenType.IDENT).value
        inputs = self.parse_input_decl()
        output = self.parse_output_decl()
        effects = self.parse_effect_decl()
        contract = None
        if self.at_lparen() and self._lookahead_keyword('contract'):
            contract = self.parse_contract_decl()
        body = self.parse_body_decl()
        self.expect(TokenType.RPAREN)
        return Graph(name=name, inputs=inputs, output=output,
                     effects=effects, contract=contract, body=body)

    def _lookahead_keyword(self, keyword: str) -> bool:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].value == keyword
        return False

    def parse_input_decl(self) -> list[tuple[str, TypeExpr]]:
        self.expect(TokenType.LPAREN)
        self.expect_ident('input')
        params = []
        while not self.at_rparen():
            params.append(self.parse_param())
        self.expect(TokenType.RPAREN)
        return params

    def parse_param(self) -> tuple[str, TypeExpr]:
        self.expect(TokenType.LPAREN)
        name = self.expect(TokenType.IDENT).value
        type_expr = self.parse_type_expr()
        self.expect(TokenType.RPAREN)
        return (name, type_expr)

    def parse_output_decl(self) -> TypeExpr:
        self.expect(TokenType.LPAREN)
        self.expect_ident('output')
        type_expr = self.parse_type_expr()
        self.expect(TokenType.RPAREN)
        return type_expr

    def parse_effect_decl(self) -> list[str]:
        self.expect(TokenType.LPAREN)
        self.expect_ident('effect')
        effects = []
        while not self.at_rparen():
            effects.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        return effects

    def parse_contract_decl(self) -> Contract:
        self.expect(TokenType.LPAREN)
        self.expect_ident('contract')
        pres = []
        posts = []
        while not self.at_rparen():
            self.expect(TokenType.LPAREN)
            kind = self.expect(TokenType.IDENT).value
            if kind == 'pre':
                pres.append(self.parse_expr())
            elif kind == 'post':
                posts.append(self.parse_expr())
            else:
                raise ParseError(f"Expected 'pre' or 'post', got {kind!r}")
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.RPAREN)
        return Contract(preconditions=pres, postconditions=posts)

    def parse_body_decl(self) -> Expr:
        self.expect(TokenType.LPAREN)
        self.expect_ident('body')
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return expr

    # === Type Expressions ===

    def parse_type_expr(self) -> TypeExpr:
        tok = self.peek()
        if tok.type == TokenType.IDENT:
            if tok.value in PRIMITIVE_TYPES:
                self.advance()
                return PrimitiveType(name=tok.value)
            else:
                self.advance()
                return NamedType(name=tok.value)
        elif tok.type == TokenType.LPAREN:
            self.advance()
            kw = self.peek()
            if kw.value == 'List':
                self.advance()
                elem = self.parse_type_expr()
                self.expect(TokenType.RPAREN)
                return ListType(elem=elem)
            elif kw.value == 'Option':
                self.advance()
                elem = self.parse_type_expr()
                self.expect(TokenType.RPAREN)
                return OptionType(elem=elem)
            elif kw.value == 'Tuple':
                self.advance()
                elems = []
                while not self.at_rparen():
                    elems.append(self.parse_type_expr())
                self.expect(TokenType.RPAREN)
                return TupleType(elems=elems)
            elif kw.value == 'Record':
                self.advance()
                fields = []
                while not self.at_rparen():
                    self.expect(TokenType.LPAREN)
                    fname = self.expect(TokenType.IDENT).value
                    ftype = self.parse_type_expr()
                    self.expect(TokenType.RPAREN)
                    fields.append((fname, ftype))
                self.expect(TokenType.RPAREN)
                return RecordType(fields=fields)
            elif kw.value == '->':
                self.advance()
                param = self.parse_type_expr()
                ret = self.parse_type_expr()
                self.expect(TokenType.RPAREN)
                return FunctionType(param=param, ret=ret)
            elif kw.value == 'Enum':
                self.advance()
                variants = []
                while not self.at_rparen():
                    self.expect(TokenType.LPAREN)
                    vname = self.expect(TokenType.IDENT).value
                    vtypes = []
                    while not self.at_rparen():
                        vtypes.append(self.parse_type_expr())
                    self.expect(TokenType.RPAREN)
                    variants.append((vname, vtypes))
                self.expect(TokenType.RPAREN)
                return EnumType(variants=variants)
            else:
                raise ParseError(f"Unknown compound type: {kw.value!r}", kw)
        else:
            raise ParseError(f"Expected type expression, got {tok.value!r}", tok)

    # === Expressions ===

    def parse_expr(self) -> Expr:
        tok = self.peek()

        # Literals
        if tok.type == TokenType.INT:
            self.advance()
            return LitExpr(value=int(tok.value), type_hint="int")
        if tok.type == TokenType.FLOAT:
            self.advance()
            return LitExpr(value=float(tok.value), type_hint="float")
        if tok.type == TokenType.STRING:
            self.advance()
            return LitExpr(value=tok.value, type_hint="string")

        # Identifier or keyword literal
        if tok.type == TokenType.IDENT:
            if tok.value == 'true':
                self.advance()
                return LitExpr(value=True, type_hint="bool")
            elif tok.value == 'false':
                self.advance()
                return LitExpr(value=False, type_hint="bool")
            elif tok.value == 'unit':
                self.advance()
                return LitExpr(value=None, type_hint="unit")
            elif tok.value == 'none':
                self.advance()
                return NoneExpr()
            elif tok.value == 'result':
                self.advance()
                return IdentExpr(name='result')
            else:
                self.advance()
                return IdentExpr(name=tok.value)

        # S-expression
        if tok.type == TokenType.LPAREN:
            return self.parse_sexpr()

        raise ParseError(f"Unexpected token: {tok.value!r}", tok)

    def parse_sexpr(self) -> Expr:
        self.expect(TokenType.LPAREN)
        head = self.peek()

        if head.type != TokenType.IDENT:
            raise ParseError(f"Expected identifier at head of s-expression, got {head.value!r}", head)

        keyword = head.value

        if keyword == 'let':
            return self._parse_let()
        elif keyword == 'if':
            return self._parse_if()
        elif keyword == 'match':
            return self._parse_match()
        elif keyword == 'lambda':
            return self._parse_lambda()
        elif keyword == 'pipe':
            return self._parse_pipe()
        elif keyword == 'do':
            return self._parse_do()
        elif keyword == 'call':
            return self._parse_call()
        elif keyword == 'list':
            return self._parse_list()
        elif keyword == 'record':
            return self._parse_record()
        elif keyword == 'get':
            return self._parse_get()
        elif keyword == 'some':
            return self._parse_some()
        elif keyword == 'try':
            return self._parse_try()
        elif keyword == 'error':
            return self._parse_error()
        elif keyword in OPERATORS:
            return self._parse_op()
        elif keyword in BUILTINS:
            return self._parse_builtin()
        else:
            # Treat as a function call: (name args...)
            return self._parse_implicit_call()

    def _parse_let(self) -> LetExpr:
        self.expect_ident('let')
        name = self.expect(TokenType.IDENT).value
        value = self.parse_expr()
        # Body is optional — in a do-block, let can be (let name value)
        if self.at_rparen():
            self.expect(TokenType.RPAREN)
            return LetExpr(name=name, value=value, body=LitExpr(value=None, type_hint="unit"))
        body = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return LetExpr(name=name, value=value, body=body)

    def _parse_if(self) -> IfExpr:
        self.expect_ident('if')
        cond = self.parse_expr()
        then_ = self.parse_expr()
        else_ = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return IfExpr(cond=cond, then_=then_, else_=else_)

    def _parse_match(self) -> MatchExpr:
        self.expect_ident('match')
        target = self.parse_expr()
        arms = []
        while not self.at_rparen():
            arms.append(self.parse_match_arm())
        self.expect(TokenType.RPAREN)
        return MatchExpr(target=target, arms=arms)

    def parse_match_arm(self) -> MatchArm:
        self.expect(TokenType.LPAREN)
        pattern = self.parse_pattern()
        body = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return MatchArm(pattern=pattern, body=body)

    def parse_pattern(self) -> Pattern:
        tok = self.peek()
        if tok.type == TokenType.IDENT:
            if tok.value == '_':
                self.advance()
                return WildcardPattern()
            elif tok.value in ('true', 'false'):
                self.advance()
                return LiteralPattern(value=tok.value == 'true')
            else:
                self.advance()
                return IdentPattern(name=tok.value)
        elif tok.type == TokenType.INT:
            self.advance()
            return LiteralPattern(value=int(tok.value))
        elif tok.type == TokenType.FLOAT:
            self.advance()
            return LiteralPattern(value=float(tok.value))
        elif tok.type == TokenType.STRING:
            self.advance()
            return LiteralPattern(value=tok.value)
        elif tok.type == TokenType.LPAREN:
            self.advance()
            name = self.expect(TokenType.IDENT).value
            args = []
            while not self.at_rparen():
                args.append(self.parse_pattern())
            self.expect(TokenType.RPAREN)
            return ConstructorPattern(name=name, args=args)
        else:
            raise ParseError(f"Expected pattern, got {tok.value!r}", tok)

    def _parse_lambda(self) -> LambdaExpr:
        self.expect_ident('lambda')
        self.expect(TokenType.LPAREN)
        params = []
        while not self.at_rparen():
            # Lambda params can be bare idents or (name type)
            if self.at_lparen():
                p = self.parse_param()
                params.append(p)
            else:
                name = self.expect(TokenType.IDENT).value
                params.append((name, None))
        self.expect(TokenType.RPAREN)
        body = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return LambdaExpr(params=params, body=body)

    def _parse_pipe(self) -> PipeExpr:
        self.expect_ident('pipe')
        value = self.parse_expr()
        steps = []
        while not self.at_rparen():
            step = self.parse_expr()
            steps.append(step)
        self.expect(TokenType.RPAREN)
        return PipeExpr(value=value, steps=steps)

    def _parse_do(self) -> DoExpr:
        self.expect_ident('do')
        exprs = []
        while not self.at_rparen():
            exprs.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        # Chain body-less lets: each let's body becomes the rest of the do-block
        return DoExpr(exprs=self._chain_lets(exprs))

    def _chain_lets(self, exprs: list[Expr]) -> list[Expr]:
        """Chain body-less let expressions so scope carries forward."""
        if not exprs:
            return exprs
        result = []
        i = 0
        while i < len(exprs):
            expr = exprs[i]
            if (isinstance(expr, LetExpr) and
                    isinstance(expr.body, LitExpr) and
                    expr.body.type_hint == "unit" and
                    expr.body.value is None and
                    i + 1 < len(exprs)):
                # This let has no body — chain remaining exprs as the body
                remaining = self._chain_lets(exprs[i + 1:])
                if len(remaining) == 1:
                    body = remaining[0]
                else:
                    body = DoExpr(exprs=remaining)
                result.append(LetExpr(name=expr.name, value=expr.value, body=body))
                return result
            else:
                result.append(expr)
                i += 1
        return result

    def _parse_op(self) -> OpExpr:
        op = self.advance().value
        args = []
        while not self.at_rparen():
            args.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return OpExpr(op=op, args=args)

    def _parse_call(self) -> CallExpr:
        self.expect_ident('call')
        func = self.expect(TokenType.IDENT).value
        args = []
        while not self.at_rparen():
            args.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return CallExpr(func=func, args=args)

    def _parse_implicit_call(self) -> CallExpr:
        func = self.advance().value
        args = []
        while not self.at_rparen():
            args.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return CallExpr(func=func, args=args)

    def _parse_list(self) -> ListExpr:
        self.expect_ident('list')
        elems = []
        while not self.at_rparen():
            elems.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return ListExpr(elems=elems)

    def _parse_record(self) -> RecordExpr:
        self.expect_ident('record')
        type_name = self.expect(TokenType.IDENT).value
        fields = []
        while not self.at_rparen():
            self.expect(TokenType.LPAREN)
            fname = self.expect(TokenType.IDENT).value
            fval = self.parse_expr()
            self.expect(TokenType.RPAREN)
            fields.append((fname, fval))
        self.expect(TokenType.RPAREN)
        return RecordExpr(type_name=type_name, fields=fields)

    def _parse_get(self) -> GetExpr:
        self.expect_ident('get')
        obj = self.parse_expr()
        field = self.expect(TokenType.IDENT).value
        self.expect(TokenType.RPAREN)
        return GetExpr(obj=obj, field=field)

    def _parse_some(self) -> SomeExpr:
        self.expect_ident('some')
        value = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return SomeExpr(value=value)

    def _parse_try(self) -> TryExpr:
        self.expect_ident('try')
        body = self.parse_expr()
        self.expect(TokenType.LPAREN)
        self.expect_ident('catch')
        catch_var = self.expect(TokenType.IDENT).value
        catch_body = self.parse_expr()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.RPAREN)
        return TryExpr(body=body, catch_var=catch_var, catch_body=catch_body)

    def _parse_error(self) -> ErrorExpr:
        self.expect_ident('error')
        msg = self.parse_expr()
        self.expect(TokenType.RPAREN)
        return ErrorExpr(message=msg)

    def _parse_builtin(self) -> BuiltinExpr:
        name = self.advance().value
        args = []
        while not self.at_rparen():
            args.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return BuiltinExpr(name=name, args=args)


def parse(source: str) -> Program:
    """Parse a Starshot IR source string into a Program AST."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    program = parser.parse_program()
    if not parser.at_eof():
        raise ParseError("Unexpected tokens after program", parser.peek())
    return program
