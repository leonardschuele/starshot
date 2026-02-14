"""Evaluator: run generated code against test cases and collect metrics."""
from __future__ import annotations
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .tasks import BenchmarkTask, TestCase


@dataclass
class TestResult:
    """Result of running a single test case."""
    test_case: TestCase
    passed: bool
    actual_output: object = None
    error: str = ""
    runtime_ms: float = 0.0


@dataclass
class EvalResult:
    """Result of evaluating generated code against all test cases."""
    task_id: str
    group: str  # "control" (Python) or "test" (Starshot IR)
    code: str
    compiled_code: str = ""  # For IR group, the compiled Python
    parse_success: bool = True
    compile_success: bool = True
    test_results: list[TestResult] = field(default_factory=list)
    total_time_ms: float = 0.0

    @property
    def pass_rate(self) -> float:
        if not self.test_results:
            return 0.0
        return sum(1 for r in self.test_results if r.passed) / len(self.test_results)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.test_results)


def evaluate_python(task: BenchmarkTask, code: str) -> EvalResult:
    """Evaluate generated Python code against test cases."""
    result = EvalResult(task_id=task.id, group="control", code=code)
    start = time.time()

    for tc in task.test_cases:
        tr = _run_test_case(code, task.python_signature.split("(")[0].replace("def ", ""), tc)
        result.test_results.append(tr)

    result.total_time_ms = (time.time() - start) * 1000
    return result


def evaluate_starshot(task: BenchmarkTask, ir_code: str) -> EvalResult:
    """Evaluate generated Starshot IR code: parse, compile, then test."""
    result = EvalResult(task_id=task.id, group="test", code=ir_code)
    start = time.time()

    try:
        from starshot.ir.parser import parse
        from starshot.compiler.python_emitter import compile_to_python
        program = parse(ir_code)
    except Exception as e:
        result.parse_success = False
        result.total_time_ms = (time.time() - start) * 1000
        return result

    try:
        compiled = compile_to_python(program)
        result.compiled_code = compiled
    except Exception as e:
        result.compile_success = False
        result.total_time_ms = (time.time() - start) * 1000
        return result

    # Find the main function name from the task
    func_name = task.python_signature.split("(")[0].replace("def ", "")
    for tc in task.test_cases:
        tr = _run_test_case(compiled, func_name, tc)
        result.test_results.append(tr)

    result.total_time_ms = (time.time() - start) * 1000
    return result


def _run_test_case(code: str, func_name: str, tc: TestCase) -> TestResult:
    """Run a single test case by executing the code in a subprocess."""
    # Build a test script
    args_str = ', '.join(repr(v) for v in tc.input_args.values())
    test_script = f"""
{code}

import json
try:
    result = {func_name}({args_str})
    print(json.dumps({{"result": result, "error": None}}))
except Exception as e:
    print(json.dumps({{"result": None, "error": str(e)}}))
"""
    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            tmp = f.name

        proc = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=10
        )
        runtime = (time.time() - start) * 1000
        Path(tmp).unlink(missing_ok=True)

        if proc.returncode != 0:
            return TestResult(
                test_case=tc, passed=False,
                error=proc.stderr[:500], runtime_ms=runtime
            )

        import json
        output = json.loads(proc.stdout.strip())
        if output["error"]:
            return TestResult(
                test_case=tc, passed=False,
                error=output["error"], runtime_ms=runtime
            )

        actual = output["result"]
        passed = actual == tc.expected_output
        return TestResult(
            test_case=tc, passed=passed,
            actual_output=actual, runtime_ms=runtime
        )

    except subprocess.TimeoutExpired:
        Path(tmp).unlink(missing_ok=True)
        return TestResult(test_case=tc, passed=False, error="Timeout (10s)")
    except Exception as e:
        return TestResult(test_case=tc, passed=False, error=str(e))
