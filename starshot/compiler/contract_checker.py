"""Contract checker for Starshot IR.

Validates that contracts are well-formed and generates runtime assertions.
In Phase 0, contracts compile to Python assert statements.
"""
from __future__ import annotations
from starshot.ir.ast_nodes import (
    Program, Graph, Contract,
    IdentExpr, OpExpr, BuiltinExpr, CallExpr,
    Expr,
)


class ContractChecker:
    def __init__(self, program: Program):
        self.program = program
        self.errors: list[str] = []

    def check(self) -> list[str]:
        for defn in self.program.definitions:
            if isinstance(defn, Graph) and defn.contract:
                self._check_contract(defn)
        return self.errors

    def _check_contract(self, graph: Graph):
        contract = graph.contract
        param_names = {name for name, _ in graph.inputs}

        # Check preconditions only reference input parameters
        for i, pre in enumerate(contract.preconditions):
            free = self._free_vars(pre)
            invalid = free - param_names
            if invalid:
                self.errors.append(
                    f"Graph '{graph.name}' precondition {i+1} references "
                    f"undefined variables: {', '.join(sorted(invalid))}")

        # Check postconditions can reference 'result' and input parameters
        for i, post in enumerate(contract.postconditions):
            free = self._free_vars(post)
            valid = param_names | {'result'}
            invalid = free - valid
            if invalid:
                self.errors.append(
                    f"Graph '{graph.name}' postcondition {i+1} references "
                    f"undefined variables: {', '.join(sorted(invalid))}")

    def _free_vars(self, expr: Expr) -> set[str]:
        """Collect free variable names in an expression."""
        if isinstance(expr, IdentExpr):
            return {expr.name}
        elif isinstance(expr, OpExpr):
            result = set()
            for arg in expr.args:
                result.update(self._free_vars(arg))
            return result
        elif isinstance(expr, BuiltinExpr):
            result = set()
            for arg in expr.args:
                result.update(self._free_vars(arg))
            return result
        elif isinstance(expr, CallExpr):
            result = set()
            for arg in expr.args:
                result.update(self._free_vars(arg))
            return result
        return set()


def check_contracts(program: Program) -> list[str]:
    """Validate contracts in a program. Returns list of error messages."""
    checker = ContractChecker(program)
    return checker.check()
