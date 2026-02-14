"""Tests for the Starshot IR lexer and parser."""
import pytest
from starshot.ir.lexer import tokenize, TokenType, LexError
from starshot.ir.parser import parse, ParseError
from starshot.ir.ast_nodes import *


class TestLexer:
    def test_empty(self):
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_parens(self):
        tokens = tokenize("()")
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN

    def test_integer(self):
        tokens = tokenize("42")
        assert tokens[0].type == TokenType.INT
        assert tokens[0].value == "42"

    def test_negative_integer(self):
        tokens = tokenize("-7")
        assert tokens[0].type == TokenType.INT
        assert tokens[0].value == "-7"

    def test_float(self):
        tokens = tokenize("3.14")
        assert tokens[0].type == TokenType.FLOAT
        assert tokens[0].value == "3.14"

    def test_string(self):
        tokens = tokenize('"hello world"')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_string_escape(self):
        tokens = tokenize(r'"hello\nworld"')
        assert tokens[0].value == "hello\nworld"

    def test_ident(self):
        tokens = tokenize("foo-bar")
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "foo-bar"

    def test_operators(self):
        tokens = tokenize("+ - * / == >= <=")
        values = [t.value for t in tokens if t.type == TokenType.IDENT]
        assert values == ['+', '-', '*', '/', '==', '>=', '<=']

    def test_comment(self):
        tokens = tokenize(";; this is a comment\n42")
        assert tokens[0].type == TokenType.INT
        assert tokens[0].value == "42"

    def test_complex(self):
        tokens = tokenize('(program (graph foo (input (x Int)) (output Int) (effect pure) (body x)))')
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.LPAREN in types
        assert TokenType.RPAREN in types
        assert TokenType.IDENT in types

    def test_unterminated_string(self):
        with pytest.raises(LexError):
            tokenize('"hello')

    def test_ident_with_question_mark(self):
        tokens = tokenize("empty?")
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "empty?"


class TestParser:
    def test_minimal_program(self):
        prog = parse("(program)")
        assert isinstance(prog, Program)
        assert len(prog.definitions) == 0

    def test_simple_graph(self):
        prog = parse("""
        (program
          (graph identity
            (input (x Int))
            (output Int)
            (effect pure)
            (body x)))
        """)
        assert len(prog.graphs) == 1
        g = prog.graphs[0]
        assert g.name == "identity"
        assert len(g.inputs) == 1
        assert g.inputs[0][0] == "x"
        assert isinstance(g.inputs[0][1], PrimitiveType)
        assert g.effects == ["pure"]
        assert isinstance(g.body, IdentExpr)

    def test_type_def_record(self):
        prog = parse("""
        (program
          (type Point (Record (x Float) (y Float))))
        """)
        assert len(prog.types) == 1
        td = prog.types[0]
        assert td.name == "Point"
        assert isinstance(td.type_expr, RecordType)
        assert len(td.type_expr.fields) == 2

    def test_type_def_enum(self):
        prog = parse("""
        (program
          (type Shape
            (Enum
              (Circle Float)
              (Rect Float Float))))
        """)
        td = prog.types[0]
        assert isinstance(td.type_expr, EnumType)
        assert len(td.type_expr.variants) == 2
        assert td.type_expr.variants[0][0] == "Circle"
        assert len(td.type_expr.variants[0][1]) == 1
        assert td.type_expr.variants[1][0] == "Rect"
        assert len(td.type_expr.variants[1][1]) == 2

    def test_if_expr(self):
        prog = parse("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body (if (> x 0) x (- 0 x)))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, IfExpr)

    def test_let_expr(self):
        prog = parse("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body (let y (+ x 1) (* y 2)))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, LetExpr)
        assert body.name == "y"

    def test_let_without_body(self):
        prog = parse("""
        (program
          (graph test
            (input)
            (output Unit)
            (effect io)
            (body
              (do
                (let x 1)
                (let y 2)
                (print (format (+ x y)))))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, DoExpr)
        # After chaining, the first item should be a LetExpr with a body
        assert isinstance(body.exprs[0], LetExpr)
        assert body.exprs[0].name == "x"

    def test_lambda_expr(self):
        prog = parse("""
        (program
          (graph test
            (input (xs (List Int)))
            (output (List Int))
            (effect pure)
            (body (map (lambda (x) (* x 2)) xs))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, BuiltinExpr)
        assert body.name == "map"
        assert isinstance(body.args[0], LambdaExpr)

    def test_contract(self):
        prog = parse("""
        (program
          (graph test
            (input (n Int))
            (output Int)
            (effect pure)
            (contract
              (pre (>= n 0))
              (post (> result 0)))
            (body n)))
        """)
        g = prog.graphs[0]
        assert g.contract is not None
        assert len(g.contract.preconditions) == 1
        assert len(g.contract.postconditions) == 1

    def test_match_expr(self):
        prog = parse("""
        (program
          (graph test
            (input (x Int))
            (output String)
            (effect pure)
            (body
              (match x
                (0 "zero")
                (1 "one")
                (_ "other")))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, MatchExpr)
        assert len(body.arms) == 3
        assert isinstance(body.arms[2].pattern, WildcardPattern)

    def test_pipe_expr(self):
        prog = parse("""
        (program
          (graph test
            (input (xs (List Int)))
            (output (List Int))
            (effect pure)
            (body
              (pipe xs
                (filter (lambda (x) (> x 0)))
                (map (lambda (x) (* x 2)))))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, PipeExpr)
        assert len(body.steps) == 2

    def test_record_expr(self):
        prog = parse("""
        (program
          (type Point (Record (x Float) (y Float)))
          (graph test
            (input)
            (output Point)
            (effect pure)
            (body (record Point (x 1.0) (y 2.0)))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, RecordExpr)
        assert body.type_name == "Point"
        assert len(body.fields) == 2

    def test_get_expr(self):
        prog = parse("""
        (program
          (graph test
            (input (p Int))
            (output Int)
            (effect pure)
            (body (get p x))))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, GetExpr)

    def test_list_type(self):
        prog = parse("""
        (program
          (graph test
            (input (xs (List Int)))
            (output (List Int))
            (effect pure)
            (body xs)))
        """)
        assert isinstance(prog.graphs[0].inputs[0][1], ListType)
        assert isinstance(prog.graphs[0].output, ListType)

    def test_function_type(self):
        prog = parse("""
        (program
          (graph test
            (input (f (-> Int Int)))
            (output Int)
            (effect pure)
            (body (call f 42))))
        """)
        assert isinstance(prog.graphs[0].inputs[0][1], FunctionType)

    def test_multiple_graphs(self):
        prog = parse("""
        (program
          (graph add
            (input (a Int) (b Int))
            (output Int)
            (effect pure)
            (body (+ a b)))
          (graph main
            (input)
            (output Int)
            (effect pure)
            (body (call add 1 2))))
        """)
        assert len(prog.graphs) == 2

    def test_parse_error(self):
        with pytest.raises(ParseError):
            parse("(program (invalid))")

    def test_no_input_params(self):
        prog = parse("""
        (program
          (graph hello
            (input)
            (output Unit)
            (effect io)
            (body (print "hello"))))
        """)
        assert len(prog.graphs[0].inputs) == 0

    def test_literals(self):
        prog = parse("""
        (program
          (graph test
            (input)
            (output Bool)
            (effect pure)
            (body true)))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, LitExpr)
        assert body.value is True

    def test_string_literal(self):
        prog = parse("""
        (program
          (graph test
            (input)
            (output String)
            (effect pure)
            (body "hello world")))
        """)
        body = prog.graphs[0].body
        assert isinstance(body, LitExpr)
        assert body.value == "hello world"
