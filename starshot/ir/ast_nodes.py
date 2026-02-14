"""AST node definitions for the Starshot IR."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union


# === Type Expressions ===

@dataclass
class PrimitiveType:
    name: str  # Int, Float, String, Bool, Unit


@dataclass
class ListType:
    elem: TypeExpr


@dataclass
class OptionType:
    elem: TypeExpr


@dataclass
class TupleType:
    elems: list[TypeExpr]


@dataclass
class RecordType:
    fields: list[tuple[str, TypeExpr]]


@dataclass
class FunctionType:
    param: TypeExpr
    ret: TypeExpr


@dataclass
class EnumType:
    variants: list[tuple[str, list[TypeExpr]]]


@dataclass
class NamedType:
    name: str


TypeExpr = Union[
    PrimitiveType, ListType, OptionType, TupleType,
    RecordType, FunctionType, EnumType, NamedType,
]


# === Patterns ===

@dataclass
class WildcardPattern:
    pass


@dataclass
class LiteralPattern:
    value: object  # int, float, str, bool


@dataclass
class IdentPattern:
    name: str


@dataclass
class ConstructorPattern:
    name: str
    args: list[Pattern]


Pattern = Union[WildcardPattern, LiteralPattern, IdentPattern, ConstructorPattern]


# === Expressions ===

@dataclass
class LitExpr:
    value: object  # int, float, str, bool, None (for unit)
    type_hint: str = ""  # "int", "float", "string", "bool", "unit"


@dataclass
class IdentExpr:
    name: str


@dataclass
class LetExpr:
    name: str
    value: Expr
    body: Expr


@dataclass
class IfExpr:
    cond: Expr
    then_: Expr
    else_: Expr


@dataclass
class MatchArm:
    pattern: Pattern
    body: Expr


@dataclass
class MatchExpr:
    target: Expr
    arms: list[MatchArm]


@dataclass
class LambdaExpr:
    params: list[tuple[str, TypeExpr | None]]
    body: Expr


@dataclass
class PipeExpr:
    value: Expr
    steps: list[Expr]  # Each step is a function call expression


@dataclass
class DoExpr:
    exprs: list[Expr]


@dataclass
class OpExpr:
    op: str  # +, -, *, /, %, ==, !=, <, >, <=, >=, and, or
    args: list[Expr]


@dataclass
class CallExpr:
    func: str
    args: list[Expr]


@dataclass
class ListExpr:
    elems: list[Expr]


@dataclass
class RecordExpr:
    type_name: str
    fields: list[tuple[str, Expr]]


@dataclass
class GetExpr:
    obj: Expr
    field: str


@dataclass
class SetExpr:
    obj: Expr
    field: str
    value: Expr


@dataclass
class BuiltinExpr:
    name: str  # map, filter, reduce, head, tail, etc.
    args: list[Expr]


@dataclass
class SomeExpr:
    value: Expr


@dataclass
class NoneExpr:
    pass


@dataclass
class TryExpr:
    body: Expr
    catch_var: str
    catch_body: Expr


@dataclass
class ErrorExpr:
    message: Expr


Expr = Union[
    LitExpr, IdentExpr, LetExpr, IfExpr, MatchExpr,
    LambdaExpr, PipeExpr, DoExpr, OpExpr, CallExpr,
    ListExpr, RecordExpr, GetExpr, SetExpr, BuiltinExpr,
    SomeExpr, NoneExpr, TryExpr, ErrorExpr,
]


# === Top-Level Definitions ===

@dataclass
class Contract:
    preconditions: list[Expr] = field(default_factory=list)
    postconditions: list[Expr] = field(default_factory=list)


@dataclass
class Graph:
    name: str
    inputs: list[tuple[str, TypeExpr]]
    output: TypeExpr
    effects: list[str]  # ["pure"], ["io"], ["io", "fail"], etc.
    contract: Contract | None
    body: Expr


@dataclass
class TypeDef:
    name: str
    type_expr: TypeExpr


@dataclass
class Program:
    definitions: list[TypeDef | Graph]

    @property
    def types(self) -> list[TypeDef]:
        return [d for d in self.definitions if isinstance(d, TypeDef)]

    @property
    def graphs(self) -> list[Graph]:
        return [d for d in self.definitions if isinstance(d, Graph)]
