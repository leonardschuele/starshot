"""Compile Starshot IR AST to Python source code."""
from __future__ import annotations
from starshot.ir.ast_nodes import (
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

_ALL_BUILTINS = {
    'not', 'map', 'filter', 'reduce', 'head', 'tail',
    'cons', 'append', 'nth', 'range', 'empty?',
    'sort-by', 'length', 'concat', 'substr', 'split',
    'join', 'format', 'print', 'read-line',
    'some', 'none', 'some?', 'unwrap', 'map-opt',
    'or-else', 'error', 'try', 'catch', 'set',
    'reverse', 'first', 'second', 'last', 'contains',
    'abs', 'min', 'max', 'to-string', 'to-int', 'to-float',
    'to-lower', 'to-upper', 'string-length', 'char-at',
    'string-starts-with', 'string-ends-with', 'string-contains',
    'string-replace', 'string-trim', 'flat-map', 'zip',
    'take', 'drop', 'slice', 'index-of', 'sum', 'product',
    'any', 'all', 'enumerate', 'dict', 'keys', 'values',
    'has-key', 'get-or', 'int-to-string',
    # Common aliases LLMs use
    'list_get', 'list-get', 'string_trim', 'string_starts_with',
    'string_ends_with', 'string_contains', 'string_replace',
    'int_to_string', 'to_string', 'to_lower', 'to_upper',
    'empty_q', 'some_q', 'sort_by', 'map_opt', 'or_else',
    'read_line', 'flat_map',
}
_ALL_OPERATORS = {'+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not'}


def _sanitize_name(name: str) -> str:
    """Convert Starshot identifiers to valid Python identifiers."""
    name = name.replace('-', '_').replace('?', '_q')
    if name in ('lambda', 'class', 'def', 'return', 'import', 'from', 'as',
                'if', 'else', 'elif', 'while', 'for', 'break', 'continue',
                'pass', 'raise', 'try', 'except', 'finally', 'with', 'yield',
                'assert', 'del', 'in', 'is', 'not', 'and', 'or', 'global',
                'nonlocal', 'True', 'False', 'None', 'match', 'case', 'type'):
        name = name + '_'
    return name


def emit_type_annotation(t: TypeExpr) -> str:
    """Convert a TypeExpr to a Python type annotation string."""
    if isinstance(t, PrimitiveType):
        return {'Int': 'int', 'Float': 'float', 'String': 'str',
                'Bool': 'bool', 'Unit': 'None'}[t.name]
    elif isinstance(t, ListType):
        return f"list[{emit_type_annotation(t.elem)}]"
    elif isinstance(t, OptionType):
        return f"{emit_type_annotation(t.elem)} | None"
    elif isinstance(t, TupleType):
        inner = ', '.join(emit_type_annotation(e) for e in t.elems)
        return f"tuple[{inner}]"
    elif isinstance(t, RecordType):
        return "dict"  # Records become dataclasses, but as annotation use name
    elif isinstance(t, FunctionType):
        # Callable[[param], ret]
        return f"Callable[[{emit_type_annotation(t.param)}], {emit_type_annotation(t.ret)}]"
    elif isinstance(t, EnumType):
        return "object"
    elif isinstance(t, NamedType):
        return _sanitize_name(t.name)
    return "object"


class PythonEmitter:
    def __init__(self):
        self.lines: list[str] = []
        self.indent = 0
        self.needs_functools = False
        self.needs_dataclasses = False
        self.needs_callable = False

    def emit(self, program: Program) -> str:
        """Emit a complete Python program from the AST."""
        # First pass: determine imports
        self._scan_imports(program)

        # Imports
        imports = []
        if self.needs_dataclasses:
            imports.append("from dataclasses import dataclass")
        if self.needs_functools:
            imports.append("import functools")
        if self.needs_callable:
            imports.append("from typing import Callable")
        if imports:
            for imp in imports:
                self._line(imp)
            self._line("")

        # Type definitions
        for defn in program.definitions:
            if isinstance(defn, TypeDef):
                self._emit_type_def(defn)
                self._line("")

        # Graph definitions
        for defn in program.definitions:
            if isinstance(defn, Graph):
                self._emit_graph(defn)
                self._line("")

        # If there's a main graph, call it
        graph_names = [d.name for d in program.definitions if isinstance(d, Graph)]
        if 'main' in graph_names:
            self._line("if __name__ == '__main__':")
            self.indent += 1
            main_graph = next(d for d in program.definitions
                              if isinstance(d, Graph) and d.name == 'main')
            if main_graph.output and not (isinstance(main_graph.output, PrimitiveType)
                                          and main_graph.output.name == 'Unit'):
                self._line("print(main())")
            else:
                self._line("main()")
            self.indent -= 1

        return '\n'.join(self.lines) + '\n'

    def _scan_imports(self, program: Program):
        """Scan AST to determine needed imports."""
        for defn in program.definitions:
            if isinstance(defn, TypeDef):
                if isinstance(defn.type_expr, (RecordType, EnumType)):
                    self.needs_dataclasses = True
            if isinstance(defn, Graph):
                self._scan_expr_imports(defn.body)
                for inp in defn.inputs:
                    self._scan_type_imports(inp[1])
                self._scan_type_imports(defn.output)

    def _scan_type_imports(self, t: TypeExpr):
        if isinstance(t, FunctionType):
            self.needs_callable = True
            self._scan_type_imports(t.param)
            self._scan_type_imports(t.ret)
        elif isinstance(t, ListType):
            self._scan_type_imports(t.elem)
        elif isinstance(t, OptionType):
            self._scan_type_imports(t.elem)
        elif isinstance(t, TupleType):
            for e in t.elems:
                self._scan_type_imports(e)

    def _scan_expr_imports(self, expr: Expr):
        if isinstance(expr, BuiltinExpr) and expr.name == 'reduce':
            self.needs_functools = True
        elif isinstance(expr, LetExpr):
            self._scan_expr_imports(expr.value)
            self._scan_expr_imports(expr.body)
        elif isinstance(expr, IfExpr):
            self._scan_expr_imports(expr.cond)
            self._scan_expr_imports(expr.then_)
            self._scan_expr_imports(expr.else_)
        elif isinstance(expr, MatchExpr):
            self._scan_expr_imports(expr.target)
            for arm in expr.arms:
                self._scan_expr_imports(arm.body)
        elif isinstance(expr, LambdaExpr):
            self._scan_expr_imports(expr.body)
        elif isinstance(expr, PipeExpr):
            self._scan_expr_imports(expr.value)
            for s in expr.steps:
                self._scan_expr_imports(s)
        elif isinstance(expr, DoExpr):
            for e in expr.exprs:
                self._scan_expr_imports(e)
        elif isinstance(expr, OpExpr):
            for a in expr.args:
                self._scan_expr_imports(a)
        elif isinstance(expr, CallExpr):
            for a in expr.args:
                self._scan_expr_imports(a)
        elif isinstance(expr, ListExpr):
            for e in expr.elems:
                self._scan_expr_imports(e)
        elif isinstance(expr, RecordExpr):
            for _, v in expr.fields:
                self._scan_expr_imports(v)
        elif isinstance(expr, GetExpr):
            self._scan_expr_imports(expr.obj)
        elif isinstance(expr, BuiltinExpr):
            for a in expr.args:
                self._scan_expr_imports(a)
        elif isinstance(expr, TryExpr):
            self._scan_expr_imports(expr.body)
            self._scan_expr_imports(expr.catch_body)

    def _line(self, text: str):
        if text == "":
            self.lines.append("")
        else:
            self.lines.append("    " * self.indent + text)

    # === Type Definitions ===

    def _emit_type_def(self, td: TypeDef):
        if isinstance(td.type_expr, RecordType):
            self._emit_record_class(td.name, td.type_expr)
        elif isinstance(td.type_expr, EnumType):
            self._emit_enum_classes(td.name, td.type_expr)
        else:
            # Type alias
            self._line(f"{_sanitize_name(td.name)} = {emit_type_annotation(td.type_expr)}")

    def _emit_record_class(self, name: str, rt: RecordType):
        sname = _sanitize_name(name)
        self._line("@dataclass")
        self._line(f"class {sname}:")
        self.indent += 1
        if not rt.fields:
            self._line("pass")
        else:
            for fname, ftype in rt.fields:
                self._line(f"{_sanitize_name(fname)}: {emit_type_annotation(ftype)}")
        self.indent -= 1

    def _emit_enum_classes(self, name: str, et: EnumType):
        sname = _sanitize_name(name)
        # Base class
        self._line("@dataclass")
        self._line(f"class {sname}:")
        self.indent += 1
        self._line("pass")
        self.indent -= 1
        self._line("")
        # Variant classes
        for vname, vtypes in et.variants:
            svname = _sanitize_name(vname)
            self._line("@dataclass")
            self._line(f"class {svname}({sname}):")
            self.indent += 1
            if not vtypes:
                self._line("pass")
            else:
                for i, vt in enumerate(vtypes):
                    field_name = f"_{i}" if len(vtypes) > 1 else "value"
                    self._line(f"{field_name}: {emit_type_annotation(vt)}")
            self.indent -= 1
            self._line("")

    # === Graph (Function) Definitions ===

    def _emit_graph(self, graph: Graph):
        sname = _sanitize_name(graph.name)
        params = ', '.join(
            f"{_sanitize_name(pname)}: {emit_type_annotation(ptype)}"
            for pname, ptype in graph.inputs
        )
        ret = emit_type_annotation(graph.output)
        self._line(f"def {sname}({params}) -> {ret}:")
        self.indent += 1

        # Preconditions
        if graph.contract:
            for pre in graph.contract.preconditions:
                self._line(f"assert {self._expr(pre)}, \"Precondition failed\"")

        # Body — might need to be a block or an expression
        body = graph.body
        if graph.contract and graph.contract.postconditions:
            # Need to capture result for postcondition check
            self._emit_body_with_postconditions(body, graph.contract.postconditions)
        else:
            self._emit_body(body)

        self.indent -= 1

    def _emit_body_with_postconditions(self, body: Expr, postconditions: list[Expr]):
        stmts = self._flatten_to_statements(body)
        for stmt in stmts[:-1]:
            self._emit_flat_statement(stmt)
        last = stmts[-1]
        self._line(f"result = {self._expr(last)}")
        for post in postconditions:
            self._line(f"assert {self._expr(post)}, \"Postcondition failed\"")
        self._line("return result")

    def _emit_body(self, body: Expr):
        stmts = self._flatten_to_statements(body)
        for stmt in stmts[:-1]:
            self._emit_flat_statement(stmt)
        last = stmts[-1]
        self._line(f"return {self._expr(last)}")

    def _flatten_to_statements(self, expr: Expr) -> list[Expr]:
        """Flatten nested lets and do-blocks into a list of statements.
        The last item is the final expression to be returned."""
        if isinstance(expr, DoExpr):
            result = []
            for e in expr.exprs:
                result.extend(self._flatten_to_statements(e))
            return result
        elif isinstance(expr, LetExpr):
            # Emit the binding as an assignment, then flatten the body
            return [expr] + self._flatten_to_statements(expr.body)
        else:
            return [expr]

    def _emit_flat_statement(self, expr: Expr):
        """Emit a single flattened statement."""
        if isinstance(expr, LetExpr):
            sname = _sanitize_name(expr.name)
            self._line(f"{sname} = {self._expr(expr.value)}")
        elif isinstance(expr, BuiltinExpr) and expr.name == 'print':
            args = ', '.join(self._expr(a) for a in expr.args)
            self._line(f"print({args})")
        else:
            self._line(self._expr(expr))

    def _is_block_if(self, expr: IfExpr) -> bool:
        """Check if an if-expression should be emitted as a block."""
        return isinstance(expr.then_, DoExpr) or isinstance(expr.else_, DoExpr)

    def _emit_if_block(self, expr: IfExpr, is_return: bool = False):
        self._line(f"if {self._expr(expr.cond)}:")
        self.indent += 1
        if is_return:
            self._emit_body(expr.then_)
        else:
            self._line(self._expr(expr.then_))
        self.indent -= 1
        self._line("else:")
        self.indent += 1
        if is_return:
            self._emit_body(expr.else_)
        else:
            self._line(self._expr(expr.else_))
        self.indent -= 1

    # === Expression Emission ===

    def _expr(self, expr: Expr) -> str:
        if isinstance(expr, LitExpr):
            return self._lit(expr)
        elif isinstance(expr, IdentExpr):
            # Handle common LLM-generated identifiers
            if expr.name == 'empty':
                return '[]'
            return _sanitize_name(expr.name)
        elif isinstance(expr, LetExpr):
            return self._let_expr(expr)
        elif isinstance(expr, IfExpr):
            return self._if_expr(expr)
        elif isinstance(expr, MatchExpr):
            return self._match_expr(expr)
        elif isinstance(expr, LambdaExpr):
            return self._lambda_expr(expr)
        elif isinstance(expr, PipeExpr):
            return self._pipe_expr(expr)
        elif isinstance(expr, DoExpr):
            return self._do_expr(expr)
        elif isinstance(expr, OpExpr):
            return self._op_expr(expr)
        elif isinstance(expr, CallExpr):
            return self._call_expr(expr)
        elif isinstance(expr, ListExpr):
            return self._list_expr(expr)
        elif isinstance(expr, RecordExpr):
            return self._record_expr(expr)
        elif isinstance(expr, GetExpr):
            return self._get_expr(expr)
        elif isinstance(expr, SetExpr):
            return self._set_expr(expr)
        elif isinstance(expr, BuiltinExpr):
            return self._builtin_expr(expr)
        elif isinstance(expr, SomeExpr):
            return self._expr(expr.value)
        elif isinstance(expr, NoneExpr):
            return "None"
        elif isinstance(expr, TryExpr):
            return self._try_expr(expr)
        elif isinstance(expr, ErrorExpr):
            return self._error_expr(expr)
        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")

    def _lit(self, expr: LitExpr) -> str:
        if expr.type_hint == "string":
            escaped = expr.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'"{escaped}"'
        elif expr.type_hint == "bool":
            return "True" if expr.value else "False"
        elif expr.type_hint == "unit":
            return "None"
        elif expr.type_hint == "float":
            return repr(expr.value)
        else:
            return repr(expr.value)

    def _let_expr(self, expr: LetExpr) -> str:
        # In expression context, use walrus operator or helper
        sname = _sanitize_name(expr.name)
        val = self._expr(expr.value)
        body = self._expr(expr.body)
        return f"(lambda: (({sname} := {val}), {body})[-1])()"

    def _if_expr(self, expr: IfExpr) -> str:
        cond = self._expr(expr.cond)
        then = self._expr(expr.then_)
        else_ = self._expr(expr.else_)
        return f"({then} if {cond} else {else_})"

    def _match_expr(self, expr: MatchExpr) -> str:
        target = self._expr(expr.target)
        arms_code = []
        for arm in expr.arms:
            cond = self._pattern_condition(arm.pattern, "_mt_")
            bindings = self._pattern_bindings(arm.pattern, "_mt_")
            body = self._expr(arm.body)
            if bindings:
                bound_body = f"(lambda {', '.join(b[0] for b in bindings)}: {body})({', '.join(b[1] for b in bindings)})"
            else:
                bound_body = body
            is_catchall = isinstance(arm.pattern, (WildcardPattern, IdentPattern)) and not isinstance(arm.pattern, ConstructorPattern)
            if is_catchall:
                if isinstance(arm.pattern, IdentPattern):
                    sname = _sanitize_name(arm.pattern.name)
                    arms_code.append(('catchall', f"(lambda {sname}: {body})(_mt_)"))
                else:
                    arms_code.append(('catchall', bound_body))
                break
            else:
                arms_code.append(('cond', (cond, bound_body)))

        # Build chained conditional
        if not arms_code:
            return "None"
        result = self._build_match_chain(arms_code, 0)
        return f"(lambda _mt_: {result})({target})"

    def _build_match_chain(self, arms, idx):
        if idx >= len(arms):
            return "None"
        kind, data = arms[idx]
        if kind == 'catchall':
            return data
        cond, body = data
        rest = self._build_match_chain(arms, idx + 1)
        return f"({body} if {cond} else {rest})"

    def _pattern_condition(self, pat: Pattern, target: str) -> str:
        if isinstance(pat, WildcardPattern):
            return "True"
        elif isinstance(pat, LiteralPattern):
            return f"{target} == {repr(pat.value)}"
        elif isinstance(pat, IdentPattern):
            return "True"
        elif isinstance(pat, ConstructorPattern):
            return f"isinstance({target}, {_sanitize_name(pat.name)})"
        return "True"

    def _pattern_bindings(self, pat: Pattern, target: str) -> list[tuple[str, str]]:
        """Extract variable bindings from a pattern. Returns list of (name, accessor)."""
        if isinstance(pat, ConstructorPattern):
            bindings = []
            for i, arg in enumerate(pat.args):
                if isinstance(arg, IdentPattern):
                    accessor = f"{target}.value" if len(pat.args) == 1 else f"{target}._{i}"
                    bindings.append((_sanitize_name(arg.name), accessor))
                elif isinstance(arg, WildcardPattern):
                    pass  # No binding needed
            return bindings
        return []

    def _lambda_expr(self, expr: LambdaExpr) -> str:
        params = ', '.join(_sanitize_name(p[0]) for p in expr.params)
        body = self._expr(expr.body)
        return f"(lambda {params}: {body})"

    def _order_fn_list_args(self, raw_args: list, compiled_args: list[str]) -> tuple[str, str]:
        """For map/filter, detect whether arg order is (fn, list) or (list, fn)."""
        if len(raw_args) == 2:
            if isinstance(raw_args[0], LambdaExpr):
                return compiled_args[0], compiled_args[1]
            elif isinstance(raw_args[1], LambdaExpr):
                return compiled_args[1], compiled_args[0]
        # Default: first arg is function
        return compiled_args[0], compiled_args[1]

    def _pipe_expr(self, expr: PipeExpr) -> str:
        result = self._expr(expr.value)
        for step in expr.steps:
            if isinstance(step, BuiltinExpr) or isinstance(step, CallExpr):
                # For builtins like (filter ...) and (map ...) in a pipe,
                # the first argument is the function, and the pipe value is threaded in
                result = self._apply_pipe_step(step, result)
            elif isinstance(step, LambdaExpr):
                result = f"({self._expr(step)})({result})"
            else:
                result = f"{self._expr(step)}({result})"
        return result

    def _apply_pipe_step(self, step: Expr, pipe_val: str) -> str:
        if isinstance(step, BuiltinExpr):
            name = step.name
            if name == 'filter':
                fn = self._expr(step.args[0]) if step.args else "None"
                return f"[_x_ for _x_ in {pipe_val} if {fn}(_x_)]"
            elif name == 'map':
                fn = self._expr(step.args[0]) if step.args else "None"
                return f"[{fn}(_x_) for _x_ in {pipe_val}]"
            elif name == 'reduce':
                fn = self._expr(step.args[0])
                init = self._expr(step.args[1]) if len(step.args) > 1 else "None"
                self.needs_functools = True
                return f"functools.reduce({fn}, {pipe_val}, {init})"
            elif name == 'sort-by' or name == 'sort_by':
                fn = self._expr(step.args[0])
                return f"sorted({pipe_val}, key={fn})"
            else:
                # Generic builtin with pipe value as last argument
                args = ', '.join(self._expr(a) for a in step.args)
                if args:
                    return f"{_sanitize_name(name)}({pipe_val}, {args})"
                return f"{_sanitize_name(name)}({pipe_val})"
        elif isinstance(step, CallExpr):
            func = _sanitize_name(step.func)
            args = ', '.join(self._expr(a) for a in step.args)
            if args:
                return f"{func}({pipe_val}, {args})"
            return f"{func}({pipe_val})"
        return f"{self._expr(step)}({pipe_val})"

    def _do_expr(self, expr: DoExpr) -> str:
        # In expression context, wrap in a lambda
        if len(expr.exprs) == 1:
            return self._expr(expr.exprs[0])
        # Multiple expressions — use comma operator in a tuple, return last
        parts = ', '.join(self._expr(e) for e in expr.exprs)
        return f"({parts})[-1]"

    def _op_expr(self, expr: OpExpr) -> str:
        py_ops = {
            '+': '+', '-': '-', '*': '*', '/': '//', '%': '%',
            '==': '==', '!=': '!=', '<': '<', '>': '>', '<=': '<=', '>=': '>=',
            'and': 'and', 'or': 'or',
        }
        op = py_ops.get(expr.op, expr.op)
        if len(expr.args) == 1 and expr.op == '-':
            return f"(-{self._expr(expr.args[0])})"
        elif len(expr.args) == 1 and expr.op == 'not':
            return f"(not {self._expr(expr.args[0])})"
        elif len(expr.args) == 2:
            left = self._expr(expr.args[0])
            right = self._expr(expr.args[1])
            return f"({left} {op} {right})"
        else:
            # Variadic: chain the operator
            parts = [self._expr(a) for a in expr.args]
            return f"({f' {op} '.join(parts)})"

    def _call_expr(self, expr: CallExpr) -> str:
        # If the function name matches a builtin, route through builtin emitter
        if expr.func in _ALL_BUILTINS:
            return self._builtin_expr(BuiltinExpr(name=expr.func, args=expr.args))
        # If the function name matches an operator, route through op emitter
        if expr.func in _ALL_OPERATORS:
            return self._op_expr(OpExpr(op=expr.func, args=expr.args))
        func = _sanitize_name(expr.func)
        args = ', '.join(self._expr(a) for a in expr.args)
        return f"{func}({args})"

    def _list_expr(self, expr: ListExpr) -> str:
        elems = ', '.join(self._expr(e) for e in expr.elems)
        return f"[{elems}]"

    def _record_expr(self, expr: RecordExpr) -> str:
        sname = _sanitize_name(expr.type_name)
        fields = ', '.join(
            f"{_sanitize_name(fname)}={self._expr(fval)}"
            for fname, fval in expr.fields
        )
        return f"{sname}({fields})"

    def _get_expr(self, expr: GetExpr) -> str:
        obj = self._expr(expr.obj)
        field = _sanitize_name(expr.field)
        return f"{obj}.{field}"

    def _set_expr(self, expr: SetExpr) -> str:
        # Functional update — create new instance with one field changed
        # Use dataclasses.replace or manual construction
        obj = self._expr(expr.obj)
        field = _sanitize_name(expr.field)
        val = self._expr(expr.value)
        return f"__import__('dataclasses').replace({obj}, {field}={val})"

    def _builtin_expr(self, expr: BuiltinExpr) -> str:
        name = expr.name
        args = [self._expr(a) for a in expr.args]

        if name == 'not':
            return f"(not {args[0]})"
        elif name == 'map':
            # Support both (map fn list) and (map list fn)
            fn_arg, list_arg = self._order_fn_list_args(expr.args, args)
            return f"[{fn_arg}(_x_) for _x_ in {list_arg}]"
        elif name == 'filter':
            # Support both (filter fn list) and (filter list fn)
            fn_arg, list_arg = self._order_fn_list_args(expr.args, args)
            return f"[_x_ for _x_ in {list_arg} if {fn_arg}(_x_)]"
        elif name == 'reduce':
            # Support (reduce fn init list), (reduce list fn init), and (reduce fn list init)
            self.needs_functools = True
            if len(expr.args) == 3:
                # Detect which arg is the lambda/function
                if isinstance(expr.args[0], LambdaExpr):
                    # (reduce fn init list)
                    return f"functools.reduce({args[0]}, {args[2]}, {args[1]})"
                elif isinstance(expr.args[1], LambdaExpr):
                    # (reduce list fn init)
                    return f"functools.reduce({args[1]}, {args[0]}, {args[2]})"
                elif isinstance(expr.args[2], LambdaExpr):
                    # (reduce list init fn)
                    return f"functools.reduce({args[2]}, {args[0]}, {args[1]})"
                else:
                    # Default: (reduce fn init list)
                    return f"functools.reduce({args[0]}, {args[2]}, {args[1]})"
            elif len(expr.args) == 2:
                # (reduce fn list) — no init
                if isinstance(expr.args[0], LambdaExpr):
                    return f"functools.reduce({args[0]}, {args[1]})"
                else:
                    return f"functools.reduce({args[1]}, {args[0]})"
            return f"functools.reduce({', '.join(args)})"
        elif name == 'head':
            return f"{args[0]}[0]"
        elif name == 'tail':
            return f"{args[0]}[1:]"
        elif name == 'cons':
            return f"[{args[0]}] + {args[1]}"
        elif name == 'append':
            return f"{args[0]} + [{args[1]}]"
        elif name == 'nth':
            return f"{args[0]}[{args[1]}]"
        elif name == 'range':
            if len(args) == 1:
                return f"list(range({args[0]}))"
            elif len(args) == 2:
                return f"list(range({args[0]}, {args[1]}))"
            else:
                return f"list(range({args[0]}, {args[1]}, {args[2]}))"
        elif name == 'empty?' or name == 'empty_q':
            return f"(len({args[0]}) == 0)"
        elif name == 'sort-by' or name == 'sort_by':
            return f"sorted({args[1]}, key={args[0]})"
        elif name == 'length':
            return f"len({args[0]})"
        elif name == 'concat':
            return ' + '.join(f"str({a})" if i > 0 or len(args) > 2 else a
                              for i, a in enumerate(args))
        elif name == 'substr':
            if len(args) == 2:
                return f"{args[0]}[{args[1]}:]"
            return f"{args[0]}[{args[1]}:{args[2]}]"
        elif name == 'split':
            # Handle split with empty string -> list(str)
            if len(expr.args) >= 2 and isinstance(expr.args[1], LitExpr) and expr.args[1].value == "":
                return f"list({args[0]})"
            return f"{args[0]}.split({args[1]})"
        elif name == 'join':
            return f"{args[0]}.join({args[1]})"
        elif name == 'format':
            if len(args) == 1:
                return f"str({args[0]})"
            return f"{args[0]}.format({', '.join(args[1:])})"
        elif name == 'print':
            return f"print({', '.join(args)})"
        elif name == 'read-line' or name == 'read_line':
            return "input()"
        elif name == 'some':
            return args[0]
        elif name == 'none':
            return "None"
        elif name == 'some?' or name == 'some_q':
            return f"({args[0]} is not None)"
        elif name == 'unwrap':
            return args[0]
        elif name == 'map-opt' or name == 'map_opt':
            return f"({args[0]}({args[1]}) if {args[1]} is not None else None)"
        elif name == 'or-else' or name == 'or_else':
            return f"({args[0]} if {args[0]} is not None else {args[1]})"
        elif name == 'error':
            return f"(_ for _ in ()).throw(RuntimeError({args[0]}))"
        elif name == 'set':
            # (set obj field value) -> functional update
            return f"__import__('dataclasses').replace({args[0]}, {args[1]}={args[2]})"
        # Extended builtins
        elif name == 'reverse':
            return f"list(reversed({args[0]}))"
        elif name == 'first':
            return f"{args[0]}[0]"
        elif name == 'second':
            return f"{args[0]}[1]"
        elif name == 'last':
            return f"{args[0]}[-1]"
        elif name == 'contains' or name == 'string-contains' or name == 'string_contains':
            return f"({args[1]} in {args[0]})"
        elif name == 'abs':
            return f"abs({args[0]})"
        elif name == 'min':
            if len(args) == 1:
                return f"min({args[0]})"
            return f"min({args[0]}, {args[1]})"
        elif name == 'max':
            if len(args) == 1:
                return f"max({args[0]})"
            return f"max({args[0]}, {args[1]})"
        elif name in ('to-string', 'to_string', 'int-to-string', 'int_to_string'):
            return f"str({args[0]})"
        elif name in ('to-int', 'to_int'):
            return f"int({args[0]})"
        elif name in ('to-float', 'to_float'):
            return f"float({args[0]})"
        elif name in ('to-lower', 'to_lower'):
            return f"{args[0]}.lower()"
        elif name in ('to-upper', 'to_upper'):
            return f"{args[0]}.upper()"
        elif name in ('string-length', 'string_length'):
            return f"len({args[0]})"
        elif name in ('char-at', 'char_at'):
            return f"{args[0]}[{args[1]}]"
        elif name in ('string-starts-with', 'string_starts_with'):
            return f"{args[0]}.startswith({args[1]})"
        elif name in ('string-ends-with', 'string_ends_with'):
            return f"{args[0]}.endswith({args[1]})"
        elif name in ('string-replace', 'string_replace'):
            return f"{args[0]}.replace({args[1]}, {args[2]})"
        elif name in ('string-trim', 'string_trim'):
            return f"{args[0]}.strip()"
        elif name in ('flat-map', 'flat_map'):
            return f"[_y_ for _x_ in {args[1]} for _y_ in {args[0]}(_x_)]"
        elif name == 'zip':
            return f"list(zip({args[0]}, {args[1]}))"
        elif name == 'take':
            return f"{args[1]}[:{args[0]}]"
        elif name == 'drop':
            return f"{args[1]}[{args[0]}:]"
        elif name == 'slice':
            return f"{args[0]}[{args[1]}:{args[2]}]"
        elif name in ('index-of', 'index_of'):
            return f"({args[0]}.index({args[1]}) if {args[1]} in {args[0]} else -1)"
        elif name == 'sum':
            return f"sum({args[0]})"
        elif name == 'product':
            self.needs_functools = True
            return f"functools.reduce(lambda a, b: a * b, {args[0]}, 1)"
        elif name == 'any':
            return f"any({args[0]}({_x_}) for _x_ in {args[1]})" if len(args) > 1 else f"any({args[0]})"
        elif name == 'all':
            return f"all({args[0]}({_x_}) for _x_ in {args[1]})" if len(args) > 1 else f"all({args[0]})"
        elif name == 'enumerate':
            return f"list(enumerate({args[0]}))"
        elif name == 'dict':
            # (dict (k1 v1) (k2 v2) ...) — but args are already compiled
            return f"{{{', '.join(args)}}}"
        elif name == 'keys':
            return f"list({args[0]}.keys())"
        elif name == 'values':
            return f"list({args[0]}.values())"
        elif name in ('has-key', 'has_key'):
            return f"({args[1]} in {args[0]})"
        elif name in ('get-or', 'get_or'):
            return f"{args[0]}.get({args[1]}, {args[2]})"
        elif name in ('list-get', 'list_get'):
            return f"{args[0]}[{args[1]}]"
        elif name == 'tuple':
            return f"({', '.join(args)},)" if len(args) == 1 else f"({', '.join(args)})"
        else:
            return f"{_sanitize_name(name)}({', '.join(args)})"

    def _try_expr(self, expr: TryExpr) -> str:
        body = self._expr(expr.body)
        catch_var = _sanitize_name(expr.catch_var)
        catch_body = self._expr(expr.catch_body)
        # In expression context, this is tricky. Use a helper.
        return (f"(lambda: (lambda _try_fn_: _try_fn_())"
                f"(lambda: {body}))()"
                f" if True else None")  # Simplified — see block emission for full version

    def _error_expr(self, expr: ErrorExpr) -> str:
        msg = self._expr(expr.message)
        return f"(_ for _ in ()).throw(RuntimeError({msg}))"


def compile_to_python(program: Program) -> str:
    """Compile a Starshot IR Program AST to Python source code."""
    emitter = PythonEmitter()
    return emitter.emit(program)
