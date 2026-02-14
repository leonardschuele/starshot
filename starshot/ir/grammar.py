"""Formal CFG for Starshot IR.

This module defines the context-free grammar for the Starshot IR in a format
suitable for grammar-constrained decoding with tools like SynCode or Outlines.
"""

# EBNF grammar for Starshot IR (compatible with Lark, Outlines, SynCode)
STARSHOT_GRAMMAR_EBNF = r"""
?start: program

program: "(" "program" definition* ")"

definition: type_def | graph_def

type_def: "(" "type" IDENT type_expr ")"

graph_def: "(" "graph" IDENT input_decl output_decl effect_decl contract_decl? body_decl ")"

input_decl: "(" "input" param* ")"
param: "(" IDENT type_expr ")"
output_decl: "(" "output" type_expr ")"
effect_decl: "(" "effect" EFFECT_KIND+ ")"
EFFECT_KIND: "pure" | "io" | "fail"
contract_decl: "(" "contract" contract_clause+ ")"
contract_clause: "(" "pre" expr ")" | "(" "post" expr ")"
body_decl: "(" "body" expr ")"

// Types
?type_expr: prim_type | compound_type | IDENT
prim_type: PRIM_TYPE
PRIM_TYPE: "Int" | "Float" | "String" | "Bool" | "Unit"
compound_type: list_type | option_type | tuple_type | record_type | func_type | enum_type
list_type: "(" "List" type_expr ")"
option_type: "(" "Option" type_expr ")"
tuple_type: "(" "Tuple" type_expr type_expr+ ")"
record_type: "(" "Record" field_def+ ")"
func_type: "(" "->" type_expr type_expr ")"
enum_type: "(" "Enum" variant_def+ ")"
field_def: "(" IDENT type_expr ")"
variant_def: "(" IDENT type_expr* ")"

// Expressions
?expr: literal
     | IDENT
     | let_expr
     | if_expr
     | match_expr
     | lambda_expr
     | pipe_expr
     | do_expr
     | op_expr
     | call_expr
     | list_expr
     | record_expr
     | get_expr
     | builtin_expr
     | implicit_call

literal: INT | FLOAT | STRING | BOOL | "unit"
BOOL: "true" | "false"

let_expr: "(" "let" IDENT expr expr? ")"
if_expr: "(" "if" expr expr expr ")"
match_expr: "(" "match" expr match_arm+ ")"
match_arm: "(" pattern expr ")"
?pattern: "_" | literal | IDENT | "(" IDENT pattern* ")"
lambda_expr: "(" "lambda" "(" lambda_param* ")" expr ")"
lambda_param: IDENT | param
pipe_expr: "(" "pipe" expr expr+ ")"
do_expr: "(" "do" expr+ ")"
op_expr: "(" OPERATOR expr+ ")"
OPERATOR: "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "and" | "or"
call_expr: "(" "call" IDENT expr* ")"
implicit_call: "(" IDENT expr* ")"
list_expr: "(" "list" expr* ")"
record_expr: "(" "record" IDENT field_val* ")"
field_val: "(" IDENT expr ")"
get_expr: "(" "get" expr IDENT ")"
builtin_expr: "(" BUILTIN expr* ")"
BUILTIN: "not" | "map" | "filter" | "reduce" | "head" | "tail"
       | "cons" | "append" | "nth" | "range" | "empty?"
       | "sort-by" | "length" | "concat" | "substr" | "split"
       | "join" | "format" | "print" | "read-line"
       | "some" | "none" | "some?" | "unwrap" | "map-opt"
       | "or-else" | "error" | "try" | "catch" | "set"

// Tokens
IDENT: /[a-zA-Z_][a-zA-Z0-9_?-]*/
INT: /\-?[0-9]+/
FLOAT: /\-?[0-9]+\.[0-9]+/
STRING: /\"[^\"]*\"/

%ignore /[ \t\n\r]+/
%ignore /;[^\n]*/
"""

# BNF grammar (pure BNF, no regex — for tools that need strict BNF)
STARSHOT_GRAMMAR_BNF = r"""
<program>       ::= '(' 'program' <definitions> ')'
<definitions>   ::= <definition> <definitions> | ''
<definition>    ::= <type_def> | <graph_def>
<type_def>      ::= '(' 'type' <ident> <type_expr> ')'
<graph_def>     ::= '(' 'graph' <ident> <input_decl> <output_decl> <effect_decl> <contract_decl> <body_decl> ')'
                  | '(' 'graph' <ident> <input_decl> <output_decl> <effect_decl> <body_decl> ')'
<input_decl>    ::= '(' 'input' <params> ')'
<params>        ::= <param> <params> | ''
<param>         ::= '(' <ident> <type_expr> ')'
<output_decl>   ::= '(' 'output' <type_expr> ')'
<effect_decl>   ::= '(' 'effect' <effects> ')'
<effects>       ::= <effect_kind> <effects> | <effect_kind>
<effect_kind>   ::= 'pure' | 'io' | 'fail'
<contract_decl> ::= '(' 'contract' <contract_clauses> ')'
<contract_clauses> ::= <contract_clause> <contract_clauses> | <contract_clause>
<contract_clause> ::= '(' 'pre' <expr> ')' | '(' 'post' <expr> ')'
<body_decl>     ::= '(' 'body' <expr> ')'

<type_expr>     ::= <prim_type> | <compound_type> | <ident>
<prim_type>     ::= 'Int' | 'Float' | 'String' | 'Bool' | 'Unit'
<compound_type> ::= '(' 'List' <type_expr> ')'
                  | '(' 'Option' <type_expr> ')'
                  | '(' 'Tuple' <type_exprs2> ')'
                  | '(' 'Record' <field_defs> ')'
                  | '(' '->' <type_expr> <type_expr> ')'
                  | '(' 'Enum' <variant_defs> ')'
<type_exprs2>   ::= <type_expr> <type_expr> <type_exprs_rest>
<type_exprs_rest> ::= <type_expr> <type_exprs_rest> | ''
<field_defs>    ::= <field_def> <field_defs> | <field_def>
<field_def>     ::= '(' <ident> <type_expr> ')'
<variant_defs>  ::= <variant_def> <variant_defs> | <variant_def>
<variant_def>   ::= '(' <ident> <type_exprs> ')'
<type_exprs>    ::= <type_expr> <type_exprs> | ''

<expr>          ::= <literal> | <ident> | <let_expr> | <if_expr> | <match_expr>
                  | <lambda_expr> | <pipe_expr> | <do_expr> | <op_expr>
                  | <call_expr> | <list_expr> | <record_expr> | <get_expr>
                  | <builtin_expr>

<literal>       ::= <int> | <float> | <string> | 'true' | 'false' | 'unit'
<let_expr>      ::= '(' 'let' <ident> <expr> <expr> ')' | '(' 'let' <ident> <expr> ')'
<if_expr>       ::= '(' 'if' <expr> <expr> <expr> ')'
<match_expr>    ::= '(' 'match' <expr> <match_arms> ')'
<match_arms>    ::= <match_arm> <match_arms> | <match_arm>
<match_arm>     ::= '(' <pattern> <expr> ')'
<pattern>       ::= '_' | <literal> | <ident> | '(' <ident> <patterns> ')'
<patterns>      ::= <pattern> <patterns> | ''
<lambda_expr>   ::= '(' 'lambda' '(' <lambda_params> ')' <expr> ')'
<lambda_params> ::= <ident> <lambda_params> | <param> <lambda_params> | ''
<pipe_expr>     ::= '(' 'pipe' <expr> <exprs1> ')'
<do_expr>       ::= '(' 'do' <exprs1> ')'
<exprs1>        ::= <expr> <exprs_rest>
<exprs_rest>    ::= <expr> <exprs_rest> | ''
<op_expr>       ::= '(' <operator> <exprs1> ')'
<operator>      ::= '+' | '-' | '*' | '/' | '%' | '==' | '!=' | '<' | '>' | '<=' | '>=' | 'and' | 'or'
<call_expr>     ::= '(' 'call' <ident> <exprs> ')'
<exprs>         ::= <expr> <exprs> | ''
<list_expr>     ::= '(' 'list' <exprs> ')'
<record_expr>   ::= '(' 'record' <ident> <field_vals> ')'
<field_vals>    ::= <field_val> <field_vals> | ''
<field_val>     ::= '(' <ident> <expr> ')'
<get_expr>      ::= '(' 'get' <expr> <ident> ')'
<builtin_expr>  ::= '(' <builtin> <exprs> ')'
<builtin>       ::= 'not' | 'map' | 'filter' | 'reduce' | 'head' | 'tail'
                  | 'cons' | 'append' | 'nth' | 'range' | 'empty?'
                  | 'sort-by' | 'length' | 'concat' | 'substr' | 'split'
                  | 'join' | 'format' | 'print' | 'read-line'
                  | 'some' | 'none' | 'some?' | 'unwrap' | 'map-opt'
                  | 'or-else' | 'error' | 'try' | 'catch' | 'set'

<ident>         ::= [a-zA-Z_][a-zA-Z0-9_?-]*
<int>           ::= '-'? [0-9]+
<float>         ::= '-'? [0-9]+ '.' [0-9]+
<string>        ::= '"' [^"]* '"'
"""


def get_grammar(format: str = "ebnf") -> str:
    """Get the Starshot IR grammar in the specified format.

    Args:
        format: "ebnf" for EBNF (Lark/Outlines compatible) or "bnf" for pure BNF.
    """
    if format == "ebnf":
        return STARSHOT_GRAMMAR_EBNF
    elif format == "bnf":
        return STARSHOT_GRAMMAR_BNF
    else:
        raise ValueError(f"Unknown grammar format: {format}")
