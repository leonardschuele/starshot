"""Basic type checker for Starshot IR."""
from __future__ import annotations
from starshot.ir.ast_nodes import (
    Program, Graph, TypeDef, Contract,
    PrimitiveType, ListType, OptionType, TupleType, RecordType,
    FunctionType, EnumType, NamedType,
    LitExpr, IdentExpr, LetExpr, IfExpr, MatchExpr,
    LambdaExpr, PipeExpr, DoExpr, OpExpr, CallExpr,
    ListExpr, RecordExpr, GetExpr, SetExpr, BuiltinExpr,
    SomeExpr, NoneExpr, TryExpr, ErrorExpr,
    WildcardPattern, LiteralPattern, IdentPattern, ConstructorPattern,
    TypeExpr, Expr,
)


class TypeEnv:
    """Type environment: maps names to types."""
    def __init__(self, parent: TypeEnv | None = None):
        self.bindings: dict[str, TypeExpr] = {}
        self.parent = parent

    def bind(self, name: str, type_: TypeExpr):
        self.bindings[name] = type_

    def lookup(self, name: str) -> TypeExpr | None:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def child(self) -> TypeEnv:
        return TypeEnv(parent=self)


def _types_equal(a: TypeExpr, b: TypeExpr) -> bool:
    """Check if two types are structurally equal."""
    if type(a) != type(b):
        return False
    if isinstance(a, PrimitiveType):
        return a.name == b.name
    if isinstance(a, NamedType):
        return a.name == b.name
    if isinstance(a, ListType):
        return _types_equal(a.elem, b.elem)
    if isinstance(a, OptionType):
        return _types_equal(a.elem, b.elem)
    if isinstance(a, FunctionType):
        return _types_equal(a.param, b.param) and _types_equal(a.ret, b.ret)
    if isinstance(a, TupleType):
        return len(a.elems) == len(b.elems) and all(
            _types_equal(x, y) for x, y in zip(a.elems, b.elems))
    return True  # For complex types, be lenient in Phase 0


INT = PrimitiveType('Int')
FLOAT = PrimitiveType('Float')
STRING = PrimitiveType('String')
BOOL = PrimitiveType('Bool')
UNIT = PrimitiveType('Unit')


class TypeChecker:
    def __init__(self, program: Program):
        self.program = program
        self.errors: list[str] = []
        self.type_defs: dict[str, TypeExpr] = {}
        self.graph_sigs: dict[str, tuple[list[tuple[str, TypeExpr]], TypeExpr]] = {}

    def check(self) -> list[str]:
        # Register type definitions
        for defn in self.program.definitions:
            if isinstance(defn, TypeDef):
                self.type_defs[defn.name] = defn.type_expr

        # Register graph signatures
        for defn in self.program.definitions:
            if isinstance(defn, Graph):
                self.graph_sigs[defn.name] = (defn.inputs, defn.output)

        # Check each graph
        for defn in self.program.definitions:
            if isinstance(defn, Graph):
                self._check_graph(defn)

        return self.errors

    def _check_graph(self, graph: Graph):
        env = TypeEnv()
        # Bind input parameters
        for name, type_ in graph.inputs:
            env.bind(name, type_)
        # Infer body type
        body_type = self._infer(graph.body, env)
        # Check against declared output
        if body_type and not self._compatible(body_type, graph.output):
            self.errors.append(
                f"Graph '{graph.name}': body type {self._type_str(body_type)} "
                f"doesn't match declared output {self._type_str(graph.output)}")

    def _resolve(self, t: TypeExpr) -> TypeExpr:
        """Resolve named types to their definitions."""
        if isinstance(t, NamedType) and t.name in self.type_defs:
            return self.type_defs[t.name]
        return t

    def _compatible(self, actual: TypeExpr, expected: TypeExpr) -> bool:
        """Check if actual type is compatible with expected type."""
        actual = self._resolve(actual)
        expected = self._resolve(expected)
        # Allow numeric coercion Int -> Float
        if isinstance(actual, PrimitiveType) and isinstance(expected, PrimitiveType):
            if actual.name == 'Int' and expected.name == 'Float':
                return True
        return _types_equal(actual, expected)

    def _infer(self, expr: Expr, env: TypeEnv) -> TypeExpr | None:
        """Infer the type of an expression. Returns None if unknown."""
        if isinstance(expr, LitExpr):
            return self._infer_literal(expr)
        elif isinstance(expr, IdentExpr):
            t = env.lookup(expr.name)
            if t is None and expr.name != 'result':
                self.errors.append(f"Undefined variable: '{expr.name}'")
            return t
        elif isinstance(expr, LetExpr):
            val_type = self._infer(expr.value, env)
            child = env.child()
            if val_type:
                child.bind(expr.name, val_type)
            return self._infer(expr.body, child)
        elif isinstance(expr, IfExpr):
            cond_type = self._infer(expr.cond, env)
            if cond_type and not self._compatible(cond_type, BOOL):
                self.errors.append(f"If condition must be Bool, got {self._type_str(cond_type)}")
            then_type = self._infer(expr.then_, env)
            else_type = self._infer(expr.else_, env)
            return then_type  # Assume branches have same type
        elif isinstance(expr, OpExpr):
            return self._infer_op(expr, env)
        elif isinstance(expr, CallExpr):
            return self._infer_call(expr, env)
        elif isinstance(expr, ListExpr):
            if expr.elems:
                elem_type = self._infer(expr.elems[0], env)
                return ListType(elem=elem_type) if elem_type else None
            return ListType(elem=UNIT)
        elif isinstance(expr, RecordExpr):
            return NamedType(name=expr.type_name)
        elif isinstance(expr, GetExpr):
            return self._infer_get(expr, env)
        elif isinstance(expr, LambdaExpr):
            return None  # Lambda type inference is complex, skip in Phase 0
        elif isinstance(expr, PipeExpr):
            return None  # Would need full type propagation
        elif isinstance(expr, DoExpr):
            if expr.exprs:
                for e in expr.exprs[:-1]:
                    self._infer(e, env)
                return self._infer(expr.exprs[-1], env)
            return UNIT
        elif isinstance(expr, MatchExpr):
            self._infer(expr.target, env)
            if expr.arms:
                return self._infer(expr.arms[0].body, env)
            return None
        elif isinstance(expr, BuiltinExpr):
            return self._infer_builtin(expr, env)
        elif isinstance(expr, SomeExpr):
            inner = self._infer(expr.value, env)
            return OptionType(elem=inner) if inner else None
        elif isinstance(expr, NoneExpr):
            return OptionType(elem=UNIT)
        elif isinstance(expr, TryExpr):
            return self._infer(expr.body, env)
        elif isinstance(expr, ErrorExpr):
            return None
        return None

    def _infer_literal(self, expr: LitExpr) -> TypeExpr:
        if expr.type_hint == 'int':
            return INT
        elif expr.type_hint == 'float':
            return FLOAT
        elif expr.type_hint == 'string':
            return STRING
        elif expr.type_hint == 'bool':
            return BOOL
        return UNIT

    def _infer_op(self, expr: OpExpr, env: TypeEnv) -> TypeExpr | None:
        arg_types = [self._infer(a, env) for a in expr.args]
        if expr.op in ('+', '-', '*', '/', '%'):
            # Numeric operations
            has_float = any(isinstance(t, PrimitiveType) and t.name == 'Float'
                           for t in arg_types if t)
            for t in arg_types:
                if t and isinstance(t, PrimitiveType) and t.name not in ('Int', 'Float'):
                    self.errors.append(
                        f"Arithmetic operator '{expr.op}' requires numeric types, got {self._type_str(t)}")
            return FLOAT if has_float else INT
        elif expr.op in ('==', '!=', '<', '>', '<=', '>='):
            return BOOL
        elif expr.op in ('and', 'or'):
            for t in arg_types:
                if t and not self._compatible(t, BOOL):
                    self.errors.append(
                        f"Boolean operator '{expr.op}' requires Bool, got {self._type_str(t)}")
            return BOOL
        return None

    def _infer_call(self, expr: CallExpr, env: TypeEnv) -> TypeExpr | None:
        if expr.func in self.graph_sigs:
            params, ret = self.graph_sigs[expr.func]
            if len(expr.args) != len(params):
                self.errors.append(
                    f"Graph '{expr.func}' expects {len(params)} args, got {len(expr.args)}")
            for i, (arg, (pname, ptype)) in enumerate(zip(expr.args, params)):
                arg_type = self._infer(arg, env)
                if arg_type and not self._compatible(arg_type, ptype):
                    self.errors.append(
                        f"Graph '{expr.func}' arg '{pname}': expected {self._type_str(ptype)}, "
                        f"got {self._type_str(arg_type)}")
            return ret
        # Could be a constructor call
        if expr.func in self.type_defs:
            return NamedType(name=expr.func)
        # Check enum variants
        for tname, tdef in self.type_defs.items():
            if isinstance(tdef, EnumType):
                for vname, vtypes in tdef.variants:
                    if vname == expr.func:
                        return NamedType(name=tname)
        # Unknown function — might be a lambda or builtin
        return None

    def _infer_get(self, expr: GetExpr, env: TypeEnv) -> TypeExpr | None:
        obj_type = self._infer(expr.obj, env)
        if obj_type:
            resolved = self._resolve(obj_type)
            if isinstance(resolved, RecordType):
                for fname, ftype in resolved.fields:
                    if fname == expr.field:
                        return ftype
                self.errors.append(
                    f"Record type has no field '{expr.field}'")
        return None

    def _infer_builtin(self, expr: BuiltinExpr, env: TypeEnv) -> TypeExpr | None:
        name = expr.name
        if name == 'not':
            return BOOL
        elif name in ('map', 'filter'):
            if len(expr.args) >= 2:
                list_type = self._infer(expr.args[1], env)
                if name == 'filter':
                    return list_type
                # map changes element type, but we can't easily infer lambda return
            return None
        elif name == 'reduce':
            return None  # Complex type
        elif name in ('head', 'nth'):
            if expr.args:
                list_type = self._infer(expr.args[0], env)
                if isinstance(list_type, ListType):
                    return list_type.elem
            return None
        elif name == 'tail':
            if expr.args:
                return self._infer(expr.args[0], env)
            return None
        elif name in ('cons', 'append'):
            if len(expr.args) >= 2:
                return self._infer(expr.args[1] if name == 'cons' else expr.args[0], env)
            return None
        elif name == 'length':
            return INT
        elif name in ('empty?', 'some?'):
            return BOOL
        elif name in ('concat', 'format', 'substr', 'join'):
            return STRING
        elif name == 'split':
            return ListType(elem=STRING)
        elif name in ('range',):
            return ListType(elem=INT)
        elif name in ('print', 'read-line'):
            return STRING if name == 'read-line' else UNIT
        elif name in ('unwrap', 'or-else'):
            if expr.args:
                t = self._infer(expr.args[0], env)
                if isinstance(t, OptionType):
                    return t.elem
                return t
            return None
        elif name == 'sort-by':
            if len(expr.args) >= 2:
                return self._infer(expr.args[1], env)
            return None
        elif name == 'error':
            return None
        return None

    def _type_str(self, t: TypeExpr) -> str:
        if isinstance(t, PrimitiveType):
            return t.name
        elif isinstance(t, NamedType):
            return t.name
        elif isinstance(t, ListType):
            return f"(List {self._type_str(t.elem)})"
        elif isinstance(t, OptionType):
            return f"(Option {self._type_str(t.elem)})"
        elif isinstance(t, FunctionType):
            return f"(-> {self._type_str(t.param)} {self._type_str(t.ret)})"
        elif isinstance(t, RecordType):
            fields = ' '.join(f"({f} {self._type_str(ft)})" for f, ft in t.fields)
            return f"(Record {fields})"
        elif isinstance(t, EnumType):
            return "(Enum ...)"
        elif isinstance(t, TupleType):
            return f"(Tuple {' '.join(self._type_str(e) for e in t.elems)})"
        return "?"


def check_types(program: Program) -> list[str]:
    """Run type checking on a program. Returns list of error messages."""
    checker = TypeChecker(program)
    return checker.check()
