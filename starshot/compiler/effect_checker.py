"""Effect checker for Starshot IR.

Rules:
- A 'pure' graph can only call other 'pure' graphs.
- An 'io' graph can call 'pure' or 'io' graphs.
- A 'fail' graph can call 'pure' or 'fail' graphs.
- Combined effects (e.g. 'io fail') allow calling graphs with any subset of those effects.
"""
from __future__ import annotations
from starshot.ir.ast_nodes import (
    Program, Graph,
    CallExpr, LetExpr, IfExpr, MatchExpr, LambdaExpr,
    PipeExpr, DoExpr, OpExpr, ListExpr, RecordExpr,
    GetExpr, BuiltinExpr, TryExpr,
    Expr,
)

# Builtins that require specific effects
IO_BUILTINS = {'print', 'read-line'}
FAIL_BUILTINS = {'error'}


class EffectChecker:
    def __init__(self, program: Program):
        self.program = program
        self.errors: list[str] = []
        self.graph_effects: dict[str, set[str]] = {}

    def check(self) -> list[str]:
        # Register graph effects
        for defn in self.program.definitions:
            if isinstance(defn, Graph):
                self.graph_effects[defn.name] = set(defn.effects)

        # Check each graph
        for defn in self.program.definitions:
            if isinstance(defn, Graph):
                self._check_graph(defn)

        return self.errors

    def _check_graph(self, graph: Graph):
        declared = set(graph.effects)
        required = self._collect_effects(graph.body)
        # Check that declared effects cover required effects
        if 'pure' in declared and declared == {'pure'}:
            # Pure graphs must not require any effects
            if required - {'pure'}:
                self.errors.append(
                    f"Graph '{graph.name}' is declared pure but requires effects: "
                    f"{', '.join(sorted(required - {'pure'}))}")
        else:
            missing = required - declared - {'pure'}
            if missing:
                self.errors.append(
                    f"Graph '{graph.name}' uses effects {', '.join(sorted(missing))} "
                    f"not in its declaration [{', '.join(sorted(declared))}]")

    def _collect_effects(self, expr: Expr) -> set[str]:
        """Collect all effects required by an expression."""
        effects: set[str] = set()

        if isinstance(expr, CallExpr):
            if expr.func in self.graph_effects:
                callee_effects = self.graph_effects[expr.func]
                effects.update(callee_effects - {'pure'})
            for arg in expr.args:
                effects.update(self._collect_effects(arg))
        elif isinstance(expr, BuiltinExpr):
            if expr.name in IO_BUILTINS:
                effects.add('io')
            if expr.name in FAIL_BUILTINS:
                effects.add('fail')
            for arg in expr.args:
                effects.update(self._collect_effects(arg))
        elif isinstance(expr, LetExpr):
            effects.update(self._collect_effects(expr.value))
            effects.update(self._collect_effects(expr.body))
        elif isinstance(expr, IfExpr):
            effects.update(self._collect_effects(expr.cond))
            effects.update(self._collect_effects(expr.then_))
            effects.update(self._collect_effects(expr.else_))
        elif isinstance(expr, MatchExpr):
            effects.update(self._collect_effects(expr.target))
            for arm in expr.arms:
                effects.update(self._collect_effects(arm.body))
        elif isinstance(expr, LambdaExpr):
            effects.update(self._collect_effects(expr.body))
        elif isinstance(expr, PipeExpr):
            effects.update(self._collect_effects(expr.value))
            for step in expr.steps:
                effects.update(self._collect_effects(step))
        elif isinstance(expr, DoExpr):
            for e in expr.exprs:
                effects.update(self._collect_effects(e))
        elif isinstance(expr, OpExpr):
            for arg in expr.args:
                effects.update(self._collect_effects(arg))
        elif isinstance(expr, ListExpr):
            for elem in expr.elems:
                effects.update(self._collect_effects(elem))
        elif isinstance(expr, RecordExpr):
            for _, val in expr.fields:
                effects.update(self._collect_effects(val))
        elif isinstance(expr, GetExpr):
            effects.update(self._collect_effects(expr.obj))
        elif isinstance(expr, TryExpr):
            effects.update(self._collect_effects(expr.body))
            effects.update(self._collect_effects(expr.catch_body))

        return effects


def check_effects(program: Program) -> list[str]:
    """Run effect checking on a program. Returns list of error messages."""
    checker = EffectChecker(program)
    return checker.check()
