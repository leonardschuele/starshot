"""Tests for the Starshot IR Python compiler."""
import pytest
import subprocess
import sys
import tempfile
from pathlib import Path

from starshot.ir.parser import parse
from starshot.compiler.python_emitter import compile_to_python


def _run_code(code: str, expression: str = None) -> str:
    """Run Python code and return stdout."""
    if expression:
        code += f"\nprint(repr({expression}))"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Code execution failed:\n{result.stderr}")
        return result.stdout.strip()
    finally:
        Path(tmp).unlink(missing_ok=True)


def _compile_and_run(sir_code: str, expression: str = None) -> str:
    """Parse SIR code, compile to Python, and run."""
    program = parse(sir_code)
    python_code = compile_to_python(program)
    return _run_code(python_code, expression)


class TestCompiler:
    def test_identity(self):
        output = _compile_and_run("""
        (program
          (graph identity
            (input (x Int))
            (output Int)
            (effect pure)
            (body x)))
        """, "identity(42)")
        assert output == "42"

    def test_arithmetic(self):
        output = _compile_and_run("""
        (program
          (graph add
            (input (a Int) (b Int))
            (output Int)
            (effect pure)
            (body (+ a b))))
        """, "add(3, 4)")
        assert output == "7"

    def test_factorial(self):
        output = _compile_and_run("""
        (program
          (graph factorial
            (input (n Int))
            (output Int)
            (effect pure)
            (body
              (if (== n 0)
                1
                (* n (call factorial (- n 1)))))))
        """, "factorial(10)")
        assert output == "3628800"

    def test_precondition_pass(self):
        output = _compile_and_run("""
        (program
          (graph positive
            (input (n Int))
            (output Int)
            (effect pure)
            (contract
              (pre (> n 0)))
            (body n)))
        """, "positive(5)")
        assert output == "5"

    def test_precondition_fail(self):
        with pytest.raises(RuntimeError, match="AssertionError"):
            _compile_and_run("""
            (program
              (graph positive
                (input (n Int))
                (output Int)
                (effect pure)
                (contract
                  (pre (> n 0)))
                (body n)))
            """, "positive(-1)")

    def test_postcondition(self):
        output = _compile_and_run("""
        (program
          (graph abs
            (input (n Int))
            (output Int)
            (effect pure)
            (contract
              (post (>= result 0)))
            (body (if (>= n 0) n (- 0 n)))))
        """, "abs(-5)")
        assert output == "5"

    def test_record_type(self):
        output = _compile_and_run("""
        (program
          (type Point (Record (x Float) (y Float)))
          (graph make-point
            (input (x Float) (y Float))
            (output Point)
            (effect pure)
            (body (record Point (x x) (y y)))))
        """, "make_point(1.0, 2.0)")
        assert "1.0" in output and "2.0" in output

    def test_record_get(self):
        output = _compile_and_run("""
        (program
          (type Point (Record (x Float) (y Float)))
          (graph get-x
            (input (p Point))
            (output Float)
            (effect pure)
            (body (get p x))))
        """, "get_x(Point(x=3.0, y=4.0))")
        assert output == "3.0"

    def test_enum_type(self):
        output = _compile_and_run("""
        (program
          (type Color
            (Enum
              (Red)
              (Green)
              (Blue)))
          (graph is-red
            (input (c Color))
            (output Bool)
            (effect pure)
            (body
              (match c
                ((Red) true)
                (_ false)))))
        """, "is_red(Red())")
        assert output == "True"

    def test_list_operations(self):
        output = _compile_and_run("""
        (program
          (graph sum-list
            (input (xs (List Int)))
            (output Int)
            (effect pure)
            (body (reduce (lambda (acc x) (+ acc x)) 0 xs))))
        """, "sum_list([1, 2, 3, 4, 5])")
        assert output == "15"

    def test_map_filter(self):
        output = _compile_and_run("""
        (program
          (graph even-doubled
            (input (xs (List Int)))
            (output (List Int))
            (effect pure)
            (body
              (pipe xs
                (filter (lambda (x) (== (% x 2) 0)))
                (map (lambda (x) (* x 2)))))))
        """, "even_doubled([1, 2, 3, 4, 5, 6])")
        assert output == "[4, 8, 12]"

    def test_let_chain(self):
        output = _compile_and_run("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body
              (let a (+ x 1)
                (let b (* a 2)
                  (+ a b))))))
        """, "test(5)")
        assert output == "18"  # a=6, b=12, 6+12=18

    def test_do_block(self):
        output = _compile_and_run("""
        (program
          (graph test
            (input)
            (output Unit)
            (effect io)
            (body
              (do
                (let x 42)
                (print (format x))))))
        """, "test()")
        assert "42" in output

    def test_multiple_graphs_call(self):
        output = _compile_and_run("""
        (program
          (graph double
            (input (x Int))
            (output Int)
            (effect pure)
            (body (* x 2)))
          (graph quad
            (input (x Int))
            (output Int)
            (effect pure)
            (body (call double (call double x)))))
        """, "quad(3)")
        assert output == "12"

    def test_lambda(self):
        output = _compile_and_run("""
        (program
          (graph apply
            (input (f (-> Int Int)) (x Int))
            (output Int)
            (effect pure)
            (body (call f x))))
        """, "apply(lambda x: x * 3, 7)")
        assert output == "21"

    def test_boolean_ops(self):
        output = _compile_and_run("""
        (program
          (graph test
            (input (a Bool) (b Bool))
            (output Bool)
            (effect pure)
            (body (and a (or b (not a))))))
        """, "test(True, False)")
        assert output == "False"

    def test_string_concat(self):
        output = _compile_and_run("""
        (program
          (graph greet
            (input (name String))
            (output String)
            (effect pure)
            (body (concat "Hello, " name "!"))))
        """, 'greet("World")')
        assert output == "'Hello, World!'"

    def test_nested_match(self):
        output = _compile_and_run("""
        (program
          (type Shape
            (Enum
              (Circle Float)
              (Rect Float Float)))
          (graph area
            (input (s Shape))
            (output Float)
            (effect pure)
            (body
              (match s
                ((Circle r) (* 3.14 (* r r)))
                ((Rect w h) (* w h))))))
        """, "area(Circle(5.0))")
        assert "78.5" in output

    def test_list_literal(self):
        output = _compile_and_run("""
        (program
          (graph test
            (input)
            (output (List Int))
            (effect pure)
            (body (list 1 2 3))))
        """, "test()")
        assert output == "[1, 2, 3]"

    def test_empty_list(self):
        output = _compile_and_run("""
        (program
          (graph test
            (input)
            (output (List Int))
            (effect pure)
            (body (list))))
        """, "test()")
        assert output == "[]"

    def test_none_value(self):
        output = _compile_and_run("""
        (program
          (graph test
            (input)
            (output (Option Int))
            (effect pure)
            (body none)))
        """, "test()")
        assert output == "None"

    def test_comparison_operators(self):
        for op, a, b, expected in [
            ("==", 1, 1, "True"), ("!=", 1, 2, "True"),
            ("<", 1, 2, "True"), (">", 2, 1, "True"),
            ("<=", 1, 1, "True"), (">=", 2, 1, "True"),
        ]:
            output = _compile_and_run(f"""
            (program
              (graph test
                (input (a Int) (b Int))
                (output Bool)
                (effect pure)
                (body ({op} a b))))
            """, f"test({a}, {b})")
            assert output == expected, f"{op} {a} {b} expected {expected}, got {output}"
