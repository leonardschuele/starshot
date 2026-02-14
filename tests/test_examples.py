"""End-to-end tests for all example .sir files."""
import pytest
import subprocess
import sys
import tempfile
from pathlib import Path

from starshot.ir.parser import parse
from starshot.compiler.python_emitter import compile_to_python


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _compile_and_run_file(sir_path: Path) -> tuple[str, str]:
    """Compile a .sir file and run it, returning (python_code, output)."""
    source = sir_path.read_text()
    program = parse(source)
    python_code = compile_to_python(program)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_code)
        tmp = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=10
        )
        return python_code, result.stdout.strip()
    finally:
        Path(tmp).unlink(missing_ok=True)


class TestExamples:
    def test_factorial_parses(self):
        source = (EXAMPLES_DIR / "factorial.sir").read_text()
        prog = parse(source)
        assert len(prog.graphs) == 2

    def test_factorial_compiles_and_runs(self):
        code, output = _compile_and_run_file(EXAMPLES_DIR / "factorial.sir")
        assert output == "3628800"

    def test_fizzbuzz_parses(self):
        source = (EXAMPLES_DIR / "fizzbuzz.sir").read_text()
        prog = parse(source)
        assert len(prog.graphs) == 2

    def test_fizzbuzz_runs(self):
        _, output = _compile_and_run_file(EXAMPLES_DIR / "fizzbuzz.sir")
        lines = output.strip().split('\n')
        assert lines[0] == "1"
        assert lines[2] == "Fizz"
        assert lines[4] == "Buzz"
        assert lines[14] == "FizzBuzz"

    def test_data_pipeline_parses(self):
        source = (EXAMPLES_DIR / "data_pipeline.sir").read_text()
        prog = parse(source)
        assert len(prog.types) == 2
        assert len(prog.graphs) == 2

    def test_data_pipeline_runs(self):
        _, output = _compile_and_run_file(EXAMPLES_DIR / "data_pipeline.sir")
        assert "Order 1" in output
        assert "Order 3" in output
        assert "Order 2" not in output  # filtered out

    def test_state_machine_parses(self):
        source = (EXAMPLES_DIR / "state_machine.sir").read_text()
        prog = parse(source)
        assert len(prog.types) == 2

    def test_state_machine_runs(self):
        _, output = _compile_and_run_file(EXAMPLES_DIR / "state_machine.sir")
        assert "Done" in output
        assert "2" in output  # 2 ticks

    def test_crud_parses(self):
        source = (EXAMPLES_DIR / "crud.sir").read_text()
        prog = parse(source)
        assert len(prog.types) == 2
        assert len(prog.graphs) >= 4

    def test_crud_runs(self):
        _, output = _compile_and_run_file(EXAMPLES_DIR / "crud.sir")
        assert "Users: 3" in output
        assert "Bob" in output
        assert "After delete: 2" in output

    def test_all_examples_parse(self):
        """Every .sir file in examples/ should parse without error."""
        for sir_file in EXAMPLES_DIR.glob("*.sir"):
            source = sir_file.read_text()
            try:
                prog = parse(source)
                assert isinstance(prog.definitions, list)
            except Exception as e:
                pytest.fail(f"Failed to parse {sir_file.name}: {e}")

    def test_all_examples_compile(self):
        """Every .sir file should compile to valid Python."""
        for sir_file in EXAMPLES_DIR.glob("*.sir"):
            source = sir_file.read_text()
            program = parse(source)
            code = compile_to_python(program)
            assert "def " in code, f"{sir_file.name} compiled to code without function defs"

    def test_all_examples_run(self):
        """Every .sir file should run without errors."""
        for sir_file in EXAMPLES_DIR.glob("*.sir"):
            try:
                code, output = _compile_and_run_file(sir_file)
            except Exception as e:
                pytest.fail(f"Failed to run {sir_file.name}: {e}")
