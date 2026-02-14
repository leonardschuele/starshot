"""Tests for the Starshot IR type checker and effect checker."""
import pytest
from starshot.ir.parser import parse
from starshot.compiler.type_checker import check_types
from starshot.compiler.effect_checker import check_effects
from starshot.compiler.contract_checker import check_contracts


class TestTypeChecker:
    def test_valid_arithmetic(self):
        errors = check_types(parse("""
        (program
          (graph add
            (input (a Int) (b Int))
            (output Int)
            (effect pure)
            (body (+ a b))))
        """))
        assert len(errors) == 0

    def test_type_mismatch_return(self):
        errors = check_types(parse("""
        (program
          (graph test
            (input (x Int))
            (output String)
            (effect pure)
            (body (+ x 1))))
        """))
        assert len(errors) > 0
        assert "String" in errors[0] or "Int" in errors[0]

    def test_undefined_variable(self):
        errors = check_types(parse("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body (+ x y))))
        """))
        assert any("y" in e for e in errors)

    def test_arithmetic_on_string(self):
        errors = check_types(parse("""
        (program
          (graph test
            (input (s String))
            (output Int)
            (effect pure)
            (body (+ s 1))))
        """))
        assert any("String" in e for e in errors)

    def test_boolean_condition(self):
        errors = check_types(parse("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body (if (> x 0) x (- 0 x)))))
        """))
        assert len(errors) == 0

    def test_wrong_arg_count(self):
        errors = check_types(parse("""
        (program
          (graph add
            (input (a Int) (b Int))
            (output Int)
            (effect pure)
            (body (+ a b)))
          (graph test
            (input)
            (output Int)
            (effect pure)
            (body (call add 1))))
        """))
        assert any("expects 2 args" in e for e in errors)

    def test_let_binding_type(self):
        errors = check_types(parse("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body (let y (+ x 1) (* y 2)))))
        """))
        assert len(errors) == 0

    def test_record_field_access(self):
        errors = check_types(parse("""
        (program
          (type Point (Record (x Float) (y Float)))
          (graph test
            (input (p Point))
            (output Float)
            (effect pure)
            (body (get p x))))
        """))
        assert len(errors) == 0

    def test_record_invalid_field(self):
        errors = check_types(parse("""
        (program
          (type Point (Record (x Float) (y Float)))
          (graph test
            (input (p Point))
            (output Float)
            (effect pure)
            (body (get p z))))
        """))
        assert any("z" in e for e in errors)


class TestEffectChecker:
    def test_pure_graph(self):
        errors = check_effects(parse("""
        (program
          (graph test
            (input (x Int))
            (output Int)
            (effect pure)
            (body (+ x 1))))
        """))
        assert len(errors) == 0

    def test_pure_with_io(self):
        errors = check_effects(parse("""
        (program
          (graph test
            (input)
            (output Unit)
            (effect pure)
            (body (print "hello"))))
        """))
        assert len(errors) > 0
        assert any("pure" in e.lower() or "io" in e.lower() for e in errors)

    def test_io_graph_with_print(self):
        errors = check_effects(parse("""
        (program
          (graph test
            (input)
            (output Unit)
            (effect io)
            (body (print "hello"))))
        """))
        assert len(errors) == 0

    def test_pure_calling_io(self):
        errors = check_effects(parse("""
        (program
          (graph printer
            (input)
            (output Unit)
            (effect io)
            (body (print "hello")))
          (graph test
            (input)
            (output Unit)
            (effect pure)
            (body (call printer))))
        """))
        assert len(errors) > 0

    def test_io_calling_pure(self):
        errors = check_effects(parse("""
        (program
          (graph add
            (input (a Int) (b Int))
            (output Int)
            (effect pure)
            (body (+ a b)))
          (graph test
            (input)
            (output Unit)
            (effect io)
            (body (do
              (let x (call add 1 2))
              (print (format x))))))
        """))
        assert len(errors) == 0


class TestContractChecker:
    def test_valid_contract(self):
        errors = check_contracts(parse("""
        (program
          (graph test
            (input (n Int))
            (output Int)
            (effect pure)
            (contract
              (pre (>= n 0))
              (post (> result 0)))
            (body n)))
        """))
        assert len(errors) == 0

    def test_precondition_undefined_var(self):
        errors = check_contracts(parse("""
        (program
          (graph test
            (input (n Int))
            (output Int)
            (effect pure)
            (contract
              (pre (>= x 0)))
            (body n)))
        """))
        assert any("x" in e for e in errors)

    def test_postcondition_can_use_result(self):
        errors = check_contracts(parse("""
        (program
          (graph test
            (input (n Int))
            (output Int)
            (effect pure)
            (contract
              (post (>= result 0)))
            (body n)))
        """))
        assert len(errors) == 0
