# Starshot

**Does AI produce better software when generating structured representations instead of text?**

Starshot is an experiment to find out. It defines a minimal intermediate representation (IR) with mandatory types, contracts, and effect declarations, then compares AI code generation in plain Python vs. grammar-constrained Starshot IR.

## Quick Start

```bash
# Parse a .sir file
python main.py parse examples/factorial.sir

# Compile to Python
python main.py compile examples/factorial.sir

# Compile and run
python main.py run examples/factorial.sir

# Type-check and effect-check
python main.py check examples/factorial.sir
```

## The IR

Starshot IR uses S-expressions. A program is a sequence of type definitions and computation graphs, each with typed inputs/outputs, declared effects, and optional contracts.

```scheme
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
```

This compiles to:

```python
def factorial(n: int) -> int:
    assert (n >= 0), "Precondition failed"
    result = (1 if (n == 0) else (n * factorial((n - 1))))
    assert (result > 0), "Postcondition failed"
    return result
```

### Key Features

- **Mandatory types** on all graph inputs and outputs
- **Contracts** (pre/post conditions) compiled to runtime assertions
- **Effect system** (`pure`, `io`, `fail`) — pure graphs can't call io graphs
- **Algebraic data types** — records (product types) and enums (sum types)
- **Functional core** — pipes, map/filter/reduce, pattern matching, lambdas
- **Formal grammar** (EBNF + BNF) for grammar-constrained decoding

### Why S-expressions?

- Minimal grammar = trivial CFG for constrained decoding
- LLMs have Lisp training data
- Easy to parse (the lexer is ~100 lines)
- Unambiguous — no operator precedence issues

## Project Structure

```
starshot/
├── ir/
│   ├── ast_nodes.py         # AST node dataclasses
│   ├── grammar.py           # Formal EBNF + BNF grammars
│   ├── lexer.py             # S-expression tokenizer
│   └── parser.py            # Recursive descent parser
├── compiler/
│   ├── type_checker.py      # Type checking pass
│   ├── effect_checker.py    # Effect checking pass
│   ├── contract_checker.py  # Contract validation
│   └── python_emitter.py    # AST → Python code generator
├── experiment/
│   ├── tasks.py             # 15 benchmark tasks with test cases
│   ├── runner.py            # Experiment runner (control vs test)
│   ├── evaluator.py         # Correctness evaluation
│   └── results.py           # Results analysis
├── examples/
│   ├── factorial.sir        # Recursive factorial with contracts
│   ├── fizzbuzz.sir         # FizzBuzz with pipes
│   ├── data_pipeline.sir    # Records + filter/map pipeline
│   ├── state_machine.sir    # Enums + pattern matching
│   └── crud.sir             # CRUD with functional updates
├── tests/                   # 85 tests (parser, compiler, type checker, e2e)
└── main.py                  # CLI
```

## Examples

**Data pipeline with records and pipes:**
```scheme
(program
  (type Order (Record (id Int) (total Float) (status String)))
  (type Summary (Record (id Int) (total Float) (tax Float)))

  (graph process-orders
    (input (orders (List Order)))
    (output (List Summary))
    (effect pure)
    (contract
      (pre (not (empty? orders)))
      (post (<= (length result) (length orders))))
    (body
      (pipe orders
        (filter (lambda (o) (> (get o total) 0.0)))
        (map (lambda (o)
          (record Summary
            (id (get o id))
            (total (get o total))
            (tax (* (get o total) 0.1)))))))))
```

**State machine with enums and pattern matching:**
```scheme
(program
  (type State (Enum (Idle) (Running Int) (Paused Int) (Done Int)))
  (type Event (Enum (Start) (Pause) (Resume) (Tick) (Stop)))

  (graph transition
    (input (state State) (event Event))
    (output State)
    (effect pure)
    (body
      (match state
        ((Idle) (match event
          ((Start) (Running 0))
          (_ (Idle))))
        ((Running n) (match event
          ((Tick) (Running (+ n 1)))
          ((Stop) (Done n))
          (_ (Running n))))
        ...))))
```

## Tests

```bash
python -m pytest tests/ -v
```

85 tests covering:
- Lexer tokenization
- Parser (all constructs)
- Compiler (arithmetic, control flow, records, enums, contracts, pipes)
- Type checker (mismatches, undefined vars, wrong arg counts)
- Effect checker (pure/io violations)
- Contract checker (variable scoping)
- End-to-end (all 5 examples parse, compile, and run correctly)

## The Experiment

The `experiment/` module defines 15 benchmark tasks across 3 difficulty levels. The runner:

1. Sends each task to an LLM as a Python prompt (control group)
2. Sends each task as a Starshot IR prompt with grammar constraints (test group)
3. Compiles the IR output to Python
4. Runs both against test cases
5. Compares pass rates

See `ROADMAP.md` for the full experimental plan.

## Type System

| Type | Syntax |
|------|--------|
| Primitives | `Int`, `Float`, `String`, `Bool`, `Unit` |
| Lists | `(List T)` |
| Options | `(Option T)` |
| Tuples | `(Tuple T1 T2 ...)` |
| Records | `(Record (field1 T1) (field2 T2) ...)` |
| Functions | `(-> T1 T2)` |
| Enums | `(Enum (Variant1 T...) ...)` |

## Effect System

```
(effect pure)        — no side effects
(effect io)          — performs I/O
(effect fail)        — can raise errors
(effect io fail)     — combined
```

A `pure` graph can only call other `pure` graphs. Checked at compile time.

## License

MIT
