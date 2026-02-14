"""Benchmark task definitions for the Starshot experiment."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TestCase:
    """A single test case for a benchmark task."""
    input_args: dict[str, object]
    expected_output: object
    description: str = ""


@dataclass
class BenchmarkTask:
    """A benchmark task for comparing IR vs plain Python generation."""
    id: str
    name: str
    description: str
    difficulty: str  # "easy", "medium", "hard"
    category: str  # "math", "strings", "data", "algorithms", "io"
    test_cases: list[TestCase] = field(default_factory=list)
    # The function signature for Python baseline
    python_signature: str = ""
    # Optional hints for the LLM
    hints: str = ""


# === Task Definitions ===

TASKS: list[BenchmarkTask] = [
    # --- Easy ---
    BenchmarkTask(
        id="factorial",
        name="Factorial",
        description="Compute the factorial of a non-negative integer n.",
        difficulty="easy",
        category="math",
        python_signature="def factorial(n: int) -> int:",
        test_cases=[
            TestCase({"n": 0}, 1),
            TestCase({"n": 1}, 1),
            TestCase({"n": 5}, 120),
            TestCase({"n": 10}, 3628800),
        ],
    ),
    BenchmarkTask(
        id="fibonacci",
        name="Fibonacci",
        description="Compute the nth Fibonacci number (0-indexed). fib(0)=0, fib(1)=1.",
        difficulty="easy",
        category="math",
        python_signature="def fibonacci(n: int) -> int:",
        test_cases=[
            TestCase({"n": 0}, 0),
            TestCase({"n": 1}, 1),
            TestCase({"n": 10}, 55),
            TestCase({"n": 20}, 6765),
        ],
    ),
    BenchmarkTask(
        id="fizzbuzz",
        name="FizzBuzz",
        description="Given an integer n, return 'FizzBuzz' if divisible by 15, 'Fizz' if by 3, 'Buzz' if by 5, else the number as a string.",
        difficulty="easy",
        category="strings",
        python_signature="def fizzbuzz(n: int) -> str:",
        test_cases=[
            TestCase({"n": 1}, "1"),
            TestCase({"n": 3}, "Fizz"),
            TestCase({"n": 5}, "Buzz"),
            TestCase({"n": 15}, "FizzBuzz"),
            TestCase({"n": 7}, "7"),
        ],
    ),
    BenchmarkTask(
        id="is_palindrome",
        name="Is Palindrome",
        description="Check if a string is a palindrome (case-insensitive, ignoring spaces).",
        difficulty="easy",
        category="strings",
        python_signature="def is_palindrome(s: str) -> bool:",
        test_cases=[
            TestCase({"s": "racecar"}, True),
            TestCase({"s": "hello"}, False),
            TestCase({"s": "A man a plan a canal Panama"}, True),
            TestCase({"s": ""}, True),
        ],
    ),
    BenchmarkTask(
        id="max_element",
        name="Maximum Element",
        description="Find the maximum element in a non-empty list of integers.",
        difficulty="easy",
        category="algorithms",
        python_signature="def max_element(nums: list[int]) -> int:",
        test_cases=[
            TestCase({"nums": [1, 2, 3]}, 3),
            TestCase({"nums": [5]}, 5),
            TestCase({"nums": [-1, -2, -3]}, -1),
            TestCase({"nums": [3, 1, 4, 1, 5, 9]}, 9),
        ],
    ),

    # --- Medium ---
    BenchmarkTask(
        id="flatten_list",
        name="Flatten Nested List",
        description="Flatten a list of lists into a single list.",
        difficulty="medium",
        category="data",
        python_signature="def flatten(nested: list[list[int]]) -> list[int]:",
        test_cases=[
            TestCase({"nested": [[1, 2], [3, 4], [5]]}, [1, 2, 3, 4, 5]),
            TestCase({"nested": [[]]}, []),
            TestCase({"nested": []}, []),
        ],
    ),
    BenchmarkTask(
        id="word_count",
        name="Word Count",
        description="Count the frequency of each word in a string. Return a dict.",
        difficulty="medium",
        category="strings",
        python_signature="def word_count(text: str) -> dict[str, int]:",
        test_cases=[
            TestCase({"text": "hello world hello"}, {"hello": 2, "world": 1}),
            TestCase({"text": "a b c a b a"}, {"a": 3, "b": 2, "c": 1}),
            TestCase({"text": ""}, {}),
        ],
    ),
    BenchmarkTask(
        id="binary_search",
        name="Binary Search",
        description="Find the index of target in a sorted list, or -1 if not found.",
        difficulty="medium",
        category="algorithms",
        python_signature="def binary_search(nums: list[int], target: int) -> int:",
        test_cases=[
            TestCase({"nums": [1, 3, 5, 7, 9], "target": 5}, 2),
            TestCase({"nums": [1, 3, 5, 7, 9], "target": 4}, -1),
            TestCase({"nums": [1], "target": 1}, 0),
            TestCase({"nums": [], "target": 1}, -1),
        ],
    ),
    BenchmarkTask(
        id="group_by",
        name="Group By Key",
        description="Group a list of (key, value) pairs by key. Return dict mapping keys to lists of values.",
        difficulty="medium",
        category="data",
        python_signature="def group_by(pairs: list[tuple[str, int]]) -> dict[str, list[int]]:",
        test_cases=[
            TestCase(
                {"pairs": [("a", 1), ("b", 2), ("a", 3)]},
                {"a": [1, 3], "b": [2]}
            ),
            TestCase({"pairs": []}, {}),
        ],
    ),
    BenchmarkTask(
        id="matrix_multiply",
        name="Matrix Multiply",
        description="Multiply two 2D matrices (list of lists). Assume compatible dimensions.",
        difficulty="medium",
        category="math",
        python_signature="def matrix_multiply(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:",
        test_cases=[
            TestCase(
                {"a": [[1, 2], [3, 4]], "b": [[5, 6], [7, 8]]},
                [[19, 22], [43, 50]]
            ),
            TestCase(
                {"a": [[1, 0], [0, 1]], "b": [[5, 6], [7, 8]]},
                [[5, 6], [7, 8]]
            ),
        ],
    ),

    # --- Hard ---
    BenchmarkTask(
        id="merge_sort",
        name="Merge Sort",
        description="Implement merge sort to sort a list of integers in ascending order.",
        difficulty="hard",
        category="algorithms",
        python_signature="def merge_sort(nums: list[int]) -> list[int]:",
        test_cases=[
            TestCase({"nums": [3, 1, 4, 1, 5, 9, 2, 6]}, [1, 1, 2, 3, 4, 5, 6, 9]),
            TestCase({"nums": [5, 4, 3, 2, 1]}, [1, 2, 3, 4, 5]),
            TestCase({"nums": [1]}, [1]),
            TestCase({"nums": []}, []),
        ],
    ),
    BenchmarkTask(
        id="json_parser",
        name="Simple JSON Value Parser",
        description="Parse a JSON value string and return it as a Python object. Support strings, numbers, booleans, null, lists, and objects.",
        difficulty="hard",
        category="strings",
        python_signature="def parse_json(s: str) -> object:",
        test_cases=[
            TestCase({"s": '"hello"'}, "hello"),
            TestCase({"s": "42"}, 42),
            TestCase({"s": "true"}, True),
            TestCase({"s": "null"}, None),
            TestCase({"s": "[1, 2, 3]"}, [1, 2, 3]),
        ],
    ),
    BenchmarkTask(
        id="data_pipeline",
        name="Data Pipeline",
        description="Given a list of orders (dicts with 'id', 'total', 'status'), filter to active orders with total > 0, compute 10% tax for each, and return list of dicts with 'id', 'total', 'tax'.",
        difficulty="hard",
        category="data",
        python_signature="def process_orders(orders: list[dict]) -> list[dict]:",
        test_cases=[
            TestCase(
                {"orders": [
                    {"id": 1, "total": 100.0, "status": "active"},
                    {"id": 2, "total": 0.0, "status": "cancelled"},
                    {"id": 3, "total": 250.0, "status": "active"},
                ]},
                [
                    {"id": 1, "total": 100.0, "tax": 10.0},
                    {"id": 3, "total": 250.0, "tax": 25.0},
                ]
            ),
        ],
    ),
    BenchmarkTask(
        id="tree_traversal",
        name="Binary Tree Inorder Traversal",
        description="Given a binary tree as nested tuples (value, left, right) where None means empty, return the inorder traversal as a list.",
        difficulty="hard",
        category="algorithms",
        python_signature="def inorder(tree: tuple | None) -> list[int]:",
        test_cases=[
            TestCase(
                {"tree": (2, (1, None, None), (3, None, None))},
                [1, 2, 3]
            ),
            TestCase({"tree": None}, []),
            TestCase(
                {"tree": (1, None, (2, None, (3, None, None)))},
                [1, 2, 3]
            ),
        ],
    ),
    BenchmarkTask(
        id="roman_numerals",
        name="Integer to Roman Numerals",
        description="Convert an integer (1-3999) to its Roman numeral representation.",
        difficulty="hard",
        category="math",
        python_signature="def to_roman(n: int) -> str:",
        test_cases=[
            TestCase({"n": 1}, "I"),
            TestCase({"n": 4}, "IV"),
            TestCase({"n": 9}, "IX"),
            TestCase({"n": 42}, "XLII"),
            TestCase({"n": 1994}, "MCMXCIV"),
            TestCase({"n": 3999}, "MMMCMXCIX"),
        ],
    ),
]


def get_task(task_id: str) -> BenchmarkTask | None:
    """Get a task by ID."""
    for task in TASKS:
        if task.id == task_id:
            return task
    return None


def get_tasks_by_difficulty(difficulty: str) -> list[BenchmarkTask]:
    """Get all tasks of a given difficulty level."""
    return [t for t in TASKS if t.difficulty == difficulty]
