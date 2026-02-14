"""Experiment runner: orchestrates control vs test group generation and evaluation."""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .tasks import BenchmarkTask, TASKS
from .evaluator import EvalResult, evaluate_python, evaluate_starshot


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""
    model: str = "claude-sonnet-4-5-20250929"
    tasks: list[str] | None = None  # None = all tasks
    num_trials: int = 1
    temperature: float = 0.0
    use_grammar_constraints: bool = True
    output_dir: str = "experiment_results"


@dataclass
class TrialResult:
    """Result of a single trial (one task, one group)."""
    task_id: str
    trial: int
    group: str  # "control" or "test"
    generated_code: str
    eval_result: EvalResult | None = None
    generation_time_ms: float = 0.0
    error: str = ""


@dataclass
class ExperimentResults:
    """Aggregate results of an experiment."""
    config: ExperimentConfig
    trials: list[TrialResult] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""

    def summary(self) -> dict:
        """Compute summary statistics."""
        control = [t for t in self.trials if t.group == "control" and t.eval_result]
        test = [t for t in self.trials if t.group == "test" and t.eval_result]

        return {
            "total_tasks": len(set(t.task_id for t in self.trials)),
            "total_trials": len(self.trials),
            "control": {
                "count": len(control),
                "pass_rate": (sum(r.eval_result.pass_rate for r in control) / len(control)
                              if control else 0),
                "all_passed": sum(1 for r in control if r.eval_result.all_passed),
                "parse_failures": sum(1 for t in self.trials
                                      if t.group == "control" and t.eval_result
                                      and not t.eval_result.parse_success),
            },
            "test": {
                "count": len(test),
                "pass_rate": (sum(r.eval_result.pass_rate for r in test) / len(test)
                              if test else 0),
                "all_passed": sum(1 for r in test if r.eval_result.all_passed),
                "parse_failures": sum(1 for t in self.trials
                                      if t.group == "test" and t.eval_result
                                      and not t.eval_result.parse_success),
                "compile_failures": sum(1 for t in self.trials
                                        if t.group == "test" and t.eval_result
                                        and not t.eval_result.compile_success),
            },
        }


def build_python_prompt(task: BenchmarkTask) -> str:
    """Build the prompt for Python code generation (control group)."""
    return f"""Write a Python function that solves the following task.
Return ONLY the function definition, no imports, no examples, no explanation.

Task: {task.description}

Function signature:
{task.python_signature}

{f"Hints: {task.hints}" if task.hints else ""}"""


def build_starshot_prompt(task: BenchmarkTask) -> str:
    """Build the prompt for Starshot IR generation (test group)."""
    func_name = task.python_signature.split("(")[0].replace("def ", "")
    return f"""Write a Starshot IR program that solves the following task.
The program should define a graph named '{func_name}' with appropriate typed inputs and outputs.
Return ONLY the Starshot IR code (an S-expression starting with (program ...)), no markdown fences.

Task: {task.description}

## Starshot IR Reference

### Structure
(program
  (graph name
    (input (param1 Type1) (param2 Type2))
    (output ReturnType)
    (effect pure)
    (body expr)))

### Types
Primitives: Int, Float, String, Bool, Unit
Compound: (List T), (Option T), (Tuple T1 T2), (Dict K V), (-> T1 T2)

### Expressions
- Arithmetic: (+ a b), (- a b), (* a b), (/ a b), (% a b)
- Comparison: (== a b), (!= a b), (< a b), (> a b), (<= a b), (>= a b)
- Boolean: (and a b), (or a b), (not a)
- Control: (if cond then else), (let name value body)
- Lambda: (lambda (x y) body)
- Call a named graph: (call graph-name arg1 arg2)

### Builtin functions (use directly, NOT with call):
- (head xs) -> first element
- (tail xs) -> all but first
- (cons x xs) -> prepend x to list
- (append xs x) -> append x to list
- (length xs) -> length of list or string
- (empty? xs) -> true if list is empty
- (nth xs i) -> element at index i
- (range start end) -> list of ints
- (map (lambda (x) body) xs) -> transform each element
- (filter (lambda (x) body) xs) -> keep matching elements
- (reduce (lambda (acc x) body) init xs) -> fold list
- (reverse xs) -> reversed list
- (contains xs x) -> true if x is in xs
- (concat s1 s2 ...) -> concatenate strings
- (format x) -> convert to string
- (split s delim) -> split string into list
- (join delim parts) -> join list into string
- (to-lower s) -> lowercase string
- (to-upper s) -> uppercase string
- (abs n) -> absolute value
- (min a b), (max a b) -> min/max of two values
- (list a b c) -> create a list literal
- (slice xs start end) -> sublist
- (sum xs) -> sum of numeric list
- (dict) -> empty dict
- (dict-set d k v) -> dict with key k set to value v
- (dict-get d k) -> value at key k
- (dict-from-pairs pairs) -> dict from list of [key, value] pairs
- (get-or d k default) -> value at key k, or default if missing
- (has-key d k) -> true if key k exists in dict
- (keys d) -> list of keys
- (values d) -> list of values
- (json-parse s) -> parse JSON string to value

### Example: Factorial with contract
(program
  (graph factorial
    (input (n Int))
    (output Int)
    (effect pure)
    (contract
      (pre (>= n 0))
      (post (> result 0)))
    (body
      (if (== n 0)
        1
        (* n (call factorial (- n 1)))))))

### Example: Filter and map a list
(program
  (graph double-positives
    (input (xs (List Int)))
    (output (List Int))
    (effect pure)
    (body
      (let positives (filter (lambda (x) (> x 0)) xs)
        (map (lambda (x) (* x 2)) positives)))))

### Example: Recursive helper with let
(program
  (graph sum-list
    (input (xs (List Int)))
    (output Int)
    (effect pure)
    (body
      (if (empty? xs)
        0
        (+ (head xs) (call sum-list (tail xs)))))))

IMPORTANT:
- Use builtins directly: (head xs), (empty? xs), (length xs) — NOT (call head xs)
- Use (call name args) ONLY for calling named graphs defined in the program
- Lambdas: (lambda (x) body) for one param, (lambda (x y) body) for two
- Let bindings: (let name value body) where body uses name
{f"- Hints: {task.hints}" if task.hints else ""}\
"""


def run_experiment(config: ExperimentConfig,
                   generate_fn=None) -> ExperimentResults:
    """Run the experiment.

    Args:
        config: Experiment configuration.
        generate_fn: Optional function(prompt, model, temperature) -> str
                     that calls the LLM. If None, uses a placeholder.
    """
    results = ExperimentResults(
        config=config,
        start_time=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Select tasks
    tasks = TASKS
    if config.tasks:
        tasks = [t for t in TASKS if t.id in config.tasks]

    for task in tasks:
        for trial in range(config.num_trials):
            # Control group: generate Python
            control_prompt = build_python_prompt(task)
            if generate_fn:
                try:
                    py_code = generate_fn(control_prompt, config.model, config.temperature)
                    control_result = TrialResult(
                        task_id=task.id, trial=trial, group="control",
                        generated_code=py_code
                    )
                    control_result.eval_result = evaluate_python(task, py_code)
                except Exception as e:
                    control_result = TrialResult(
                        task_id=task.id, trial=trial, group="control",
                        generated_code="", error=str(e)
                    )
            else:
                control_result = TrialResult(
                    task_id=task.id, trial=trial, group="control",
                    generated_code="# placeholder — no LLM configured",
                    error="No generate_fn provided"
                )
            results.trials.append(control_result)

            # Test group: generate Starshot IR
            test_prompt = build_starshot_prompt(task)
            if generate_fn:
                try:
                    ir_code = generate_fn(test_prompt, config.model, config.temperature)
                    test_result = TrialResult(
                        task_id=task.id, trial=trial, group="test",
                        generated_code=ir_code
                    )
                    test_result.eval_result = evaluate_starshot(task, ir_code)
                except Exception as e:
                    test_result = TrialResult(
                        task_id=task.id, trial=trial, group="test",
                        generated_code="", error=str(e)
                    )
            else:
                test_result = TrialResult(
                    task_id=task.id, trial=trial, group="test",
                    generated_code="; placeholder — no LLM configured",
                    error="No generate_fn provided"
                )
            results.trials.append(test_result)

    results.end_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # Save results
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    with open(output_dir / f"experiment_{timestamp}.json", "w") as f:
        json.dump({
            "config": asdict(config),
            "summary": results.summary(),
            "start_time": results.start_time,
            "end_time": results.end_time,
            "trial_count": len(results.trials),
        }, f, indent=2)

    return results
