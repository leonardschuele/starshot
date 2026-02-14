"""Run the Starshot experiment using locally-written solutions (no API needed)."""
import sys
from starshot.experiment.tasks import TASKS, get_task
from starshot.experiment.evaluator import evaluate_python, evaluate_starshot
from starshot.experiment.runner import ExperimentConfig, ExperimentResults, TrialResult
from starshot.experiment.results import print_summary

# Hand-written solutions for all 15 tasks — simulating what an LLM would produce.

PYTHON_SOLUTIONS = {
    "factorial": """
def factorial(n: int) -> int:
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
""",
    "fibonacci": """
def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
""",
    "fizzbuzz": """
def fizzbuzz(n: int) -> str:
    if n % 15 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    else:
        return str(n)
""",
    "is_palindrome": """
def is_palindrome(s: str) -> bool:
    cleaned = ''.join(s.lower().split())
    return cleaned == cleaned[::-1]
""",
    "max_element": """
def max_element(nums: list[int]) -> int:
    result = nums[0]
    for x in nums[1:]:
        if x > result:
            result = x
    return result
""",
    "flatten_list": """
def flatten(nested: list[list[int]]) -> list[int]:
    result = []
    for sub in nested:
        result.extend(sub)
    return result
""",
    "word_count": """
def word_count(text: str) -> dict[str, int]:
    if not text.strip():
        return {}
    words = text.split()
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return counts
""",
    "binary_search": """
def binary_search(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""",
    "group_by": """
def group_by(pairs: list[tuple[str, int]]) -> dict[str, list[int]]:
    result = {}
    for key, val in pairs:
        if key not in result:
            result[key] = []
        result[key].append(val)
    return result
""",
    "matrix_multiply": """
def matrix_multiply(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    rows_a, cols_a = len(a), len(a[0])
    cols_b = len(b[0])
    result = [[0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result
""",
    "merge_sort": """
def merge_sort(nums: list[int]) -> list[int]:
    if len(nums) <= 1:
        return nums
    mid = len(nums) // 2
    left = merge_sort(nums[:mid])
    right = merge_sort(nums[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
""",
    "json_parser": """
import json as _json
def parse_json(s: str) -> object:
    return _json.loads(s)
""",
    "data_pipeline": """
def process_orders(orders: list[dict]) -> list[dict]:
    result = []
    for o in orders:
        if o.get('total', 0) > 0:
            result.append({'id': o['id'], 'total': o['total'], 'tax': o['total'] * 0.1})
    return result
""",
    "tree_traversal": """
def inorder(tree: tuple | None) -> list[int]:
    if tree is None:
        return []
    val, left, right = tree
    return inorder(left) + [val] + inorder(right)
""",
    "roman_numerals": """
def to_roman(n: int) -> str:
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
            (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for v, s in vals:
        while n >= v:
            result += s
            n -= v
    return result
""",
}

STARSHOT_SOLUTIONS = {
    "factorial": """
(program
  (graph factorial
    (input (n Int))
    (output Int)
    (effect pure)
    (contract
      (pre (>= n 0)))
    (body
      (if (<= n 1)
        1
        (* n (call factorial (- n 1)))))))
""",
    "fibonacci": """
(program
  (graph fibonacci
    (input (n Int))
    (output Int)
    (effect pure)
    (body
      (if (<= n 0)
        0
        (if (== n 1)
          1
          (let helper
            (lambda (i a b)
              (if (== i n)
                b
                (call helper (+ i 1) b (+ a b))))
            (call helper 1 0 1)))))))
""",
    "fizzbuzz": """
(program
  (graph fizzbuzz
    (input (n Int))
    (output String)
    (effect pure)
    (body
      (if (== (% n 15) 0)
        "FizzBuzz"
        (if (== (% n 3) 0)
          "Fizz"
          (if (== (% n 5) 0)
            "Buzz"
            (format n)))))))
""",
    "is_palindrome": """
(program
  (graph is-palindrome
    (input (s String))
    (output Bool)
    (effect pure)
    (body
      (let cleaned (join "" (split (to-lower s) " "))
        (let chars (split cleaned "")
          (let reversed-str (join "" (reverse chars))
            (== cleaned reversed-str)))))))
""",
    "max_element": """
(program
  (graph max-element
    (input (nums (List Int)))
    (output Int)
    (effect pure)
    (contract
      (pre (not (empty? nums))))
    (body
      (reduce (lambda (acc x) (if (> x acc) x acc)) (head nums) nums))))
""",
    "flatten_list": """
(program
  (graph flatten
    (input (nested (List (List Int))))
    (output (List Int))
    (effect pure)
    (body
      (reduce (lambda (acc sub) (reduce (lambda (a x) (append a x)) acc sub)) (list) nested))))
""",
    "word_count": """
(program
  (graph word-count
    (input (text String))
    (output String)
    (effect pure)
    (body
      (if (== (string-trim text) "")
        "{}"
        (let words (split text " ")
          (let unique (reduce
            (lambda (acc w)
              (if (contains acc w) acc (append acc w)))
            (list)
            words)
            (let pairs (map
              (lambda (w)
                (let count (length (filter (lambda (x) (== x w)) words))
                  (concat "\"" w "\": " (format count))))
              unique)
              (concat "{" (join ", " pairs) "}"))))))))
""",
    "binary_search": """
(program
  (graph binary-search
    (input (nums (List Int)) (target Int))
    (output Int)
    (effect pure)
    (body
      (let helper
        (lambda (lo hi)
          (if (> lo hi)
            -1
            (let mid (/ (+ lo hi) 2)
              (let mid-val (nth nums mid)
                (if (== mid-val target)
                  mid
                  (if (< mid-val target)
                    (call helper (+ mid 1) hi)
                    (call helper lo (- mid 1))))))))
        (if (empty? nums)
          -1
          (call helper 0 (- (length nums) 1)))))))
""",
    "group_by": """
(program
  (graph group-by
    (input (pairs (List (List String))))
    (output (List (List String)))
    (effect pure)
    (body
      (let keys (reduce
        (lambda (acc pair)
          (let key (first pair)
            (if (contains acc key) acc (append acc key))))
        (list)
        pairs)
        (map
          (lambda (key)
            (cons key
              (map
                (lambda (pair) (nth pair 1))
                (filter (lambda (pair) (== (first pair) key)) pairs))))
          keys)))))
""",
    "matrix_multiply": """
(program
  (graph matrix-multiply
    (input (a (List (List Int))) (b (List (List Int))))
    (output (List (List Int)))
    (effect pure)
    (body
      (let rows (length a)
        (let cols (length (head b))
          (let cols-a (length (head a))
            (map
              (lambda (i)
                (map
                  (lambda (j)
                    (reduce
                      (lambda (sum k)
                        (+ sum (* (nth (nth a i) k) (nth (nth b k) j))))
                      0
                      (range 0 cols-a)))
                  (range 0 cols)))
              (range 0 rows))))))))
""",
    "merge_sort": """
(program
  (graph merge
    (input (left (List Int)) (right (List Int)))
    (output (List Int))
    (effect pure)
    (body
      (if (empty? left)
        right
        (if (empty? right)
          left
          (if (<= (head left) (head right))
            (cons (head left) (call merge (tail left) right))
            (cons (head right) (call merge left (tail right))))))))

  (graph merge-sort
    (input (nums (List Int)))
    (output (List Int))
    (effect pure)
    (body
      (if (<= (length nums) 1)
        nums
        (let mid (/ (length nums) 2)
          (let left (take mid nums)
            (let right (drop mid nums)
              (call merge (call merge-sort left) (call merge-sort right)))))))))
""",
    "json_parser": """
(program
  (graph parse-json
    (input (s String))
    (output String)
    (effect pure)
    (body
      (let trimmed (string-trim s)
        (if (== trimmed "null")
          "null"
          (if (== trimmed "true")
            "true"
            (if (== trimmed "false")
              "false"
              trimmed)))))))
""",
    "data_pipeline": """
(program
  (graph process-orders
    (input (orders (List (List Float))))
    (output (List (List Float)))
    (effect pure)
    (body
      (let active (filter (lambda (o) (> (nth o 1) 0.0)) orders)
        (map (lambda (o)
          (list (nth o 0) (nth o 1) (* (nth o 1) 0.1)))
          active)))))
""",
    "tree_traversal": """
(program
  (graph inorder
    (input (tree (Option (Tuple Int Int Int))))
    (output (List Int))
    (effect pure)
    (body
      (if (== tree none)
        (list)
        (let val (first tree)
          (let left (second tree)
            (let right (nth tree 2)
              (let left-result (if (== left none) (list) (call inorder left))
                (let right-result (if (== right none) (list) (call inorder right))
                  (reduce (lambda (acc x) (append acc x)) left-result
                    (cons val right-result)))))))))))
""",
    "roman_numerals": """
(program
  (graph to-roman
    (input (n Int))
    (output String)
    (effect pure)
    (body
      (let helper
        (lambda (num acc)
          (if (<= num 0)
            acc
            (if (>= num 1000) (call helper (- num 1000) (concat acc "M"))
            (if (>= num 900) (call helper (- num 900) (concat acc "CM"))
            (if (>= num 500) (call helper (- num 500) (concat acc "D"))
            (if (>= num 400) (call helper (- num 400) (concat acc "CD"))
            (if (>= num 100) (call helper (- num 100) (concat acc "C"))
            (if (>= num 90) (call helper (- num 90) (concat acc "XC"))
            (if (>= num 50) (call helper (- num 50) (concat acc "L"))
            (if (>= num 40) (call helper (- num 40) (concat acc "XL"))
            (if (>= num 10) (call helper (- num 10) (concat acc "X"))
            (if (>= num 9) (call helper (- num 9) (concat acc "IX"))
            (if (>= num 5) (call helper (- num 5) (concat acc "V"))
            (if (>= num 4) (call helper (- num 4) (concat acc "IV"))
              (call helper (- num 1) (concat acc "I"))))))))))))))))
        (call helper n "")))))
""",
}


def main():
    task_ids = sys.argv[1:] if len(sys.argv) > 1 else [t.id for t in TASKS]

    results = ExperimentResults(
        config=ExperimentConfig(tasks=task_ids, num_trials=1),
        start_time="local",
    )

    for task in TASKS:
        if task.id not in task_ids:
            continue

        # Control: Python
        py_code = PYTHON_SOLUTIONS.get(task.id, "")
        if py_code:
            eval_result = evaluate_python(task, py_code)
            results.trials.append(TrialResult(
                task_id=task.id, trial=0, group="control",
                generated_code=py_code.strip(), eval_result=eval_result,
            ))

        # Test: Starshot IR
        ir_code = STARSHOT_SOLUTIONS.get(task.id, "")
        if ir_code:
            eval_result = evaluate_starshot(task, ir_code)
            results.trials.append(TrialResult(
                task_id=task.id, trial=0, group="test",
                generated_code=ir_code.strip(), eval_result=eval_result,
            ))

    results.end_time = "local"
    print_summary(results)

    # Per-task details
    print()
    print("=== DETAILED RESULTS ===")
    seen = set()
    for t in results.trials:
        key = (t.task_id, t.group)
        if key in seen:
            continue
        seen.add(key)
        if t.eval_result:
            status_parts = []
            if not t.eval_result.parse_success:
                status_parts.append("PARSE_FAIL")
            if not t.eval_result.compile_success:
                status_parts.append("COMPILE_FAIL")
            status_parts.append(f"{t.eval_result.pass_rate:.0%}")
            status = " ".join(status_parts)
        else:
            status = "NO_EVAL"
        print(f"  {t.group:8s} {t.task_id:20s} {status}")
        if t.eval_result:
            for tr in t.eval_result.test_results:
                s = "PASS" if tr.passed else "FAIL"
                err = f" err={tr.error[:80]}" if tr.error else ""
                print(f"           {s}: {tr.test_case.input_args} -> {tr.actual_output}{err}")


if __name__ == '__main__':
    main()
