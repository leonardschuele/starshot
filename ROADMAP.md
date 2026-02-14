# Starshot Roadmap

## Phase 0: Prove the Thesis (START HERE)

### The Experiment

Build the minimum artifact needed to answer one question:
**Does an AI produce better software when generating structured representations vs text?**

"Better" means measurable: fewer bugs, more correct, faster to produce, fewer iterations to get right.

### What to Build

#### Step 1: Design the Starshot IR
A minimal computation graph format. Not the final format — just enough to test the thesis.

Requirements:
- Typed nodes (operations) and edges (data flow)
- Serializable as structured text (S-expressions or typed JSON — NOT binary yet)
  - Why text: current LLMs are text-native. Binary hurts the experiment. Text serialization lets us use existing LLMs without fine-tuning.
  - Why structured: grammar-constrained decoding (SynCode) can guarantee valid output
- Expressive enough to represent simple programs (data transformations, CRUD logic, control flow)
- Simple enough to define in days, not months

What it's NOT:
- Not a general-purpose programming language
- Not the final Starshot format
- Not binary
- Not comprehensive

#### Step 2: Write the Grammar
A formal grammar (CFG) for the Starshot IR text serialization.

This enables:
- Grammar-constrained decoding (SynCode/Outlines) to guarantee every LLM output is a valid computation graph
- Zero syntax errors by construction — the first concrete advantage over text code

#### Step 3: Build a Minimal Compiler
Starshot IR → executable code (pick ONE target).

Target options (pick one):
- **Python** — easiest to build, easiest to verify correctness, largest comparison baseline
- **WASM** — more aligned with long-term vision, harder to build
- **Direct interpretation** — skip compilation, just execute the graph. Simplest but least realistic.

Recommendation: **Python first.** Speed of iteration matters more than architectural purity at this stage.

#### Step 4: Run the Experiment
Give an LLM the same set of tasks. Run each task twice:

**Control group:** LLM generates Python directly (current standard approach)
**Test group:** LLM generates Starshot IR (with grammar-constrained decoding), compiled to Python

Tasks should be:
- Simple enough to complete in one shot (no multi-file projects yet)
- Complex enough to have bugs (not just "hello world")
- Diverse: data transformation, API handler, state machine, algorithm, simple UI logic
- ~20-50 tasks for statistical significance

Metrics:
- **Correctness:** Does it pass a test suite? (primary metric)
- **Syntax validity:** Does it parse? (expect 100% for Starshot IR with grammar constraints vs <100% for raw Python)
- **Semantic bugs:** Manual or AI-assisted review of logical errors
- **Iteration count:** How many attempts to get a working solution?
- **Token efficiency:** How many tokens to express the same computation?

#### Step 5: Analyze and Decide

| Result | Implication | Next Step |
|---|---|---|
| Starshot IR significantly better | Thesis validated. Proceed to Phase 1. | Invest in the IR format, expand scope |
| Starshot IR marginally better | Thesis partially validated. Structure helps but may not justify a new stack. | Consider augmenting existing stack instead of replacing |
| No difference | Thesis invalidated for this representation. | Try a different IR design, or pivot to augmentation strategy |
| Starshot IR worse | Text is genuinely better for current AI. | Pivot entirely. Augment the text stack. Wait for new AI architectures. |

### Why This First

- **Cheap.** Days to weeks of work, not months or years.
- **Decisive.** Answers the single most important question before investing in everything else.
- **No ecosystem needed.** One IR format, one grammar, one compiler, one experiment. No capability registry, no state graph, no bridge layer.
- **Uses existing AI.** No fine-tuning, no new architecture. Uses current LLMs with grammar-constrained decoding.
- **Produces evidence.** "AI generates 40% fewer bugs in Starshot IR" is a concrete claim. "AI-native stack is theoretically better" is not.

---

## Phase 1: The Foundation (only if Phase 0 validates)

Build the core infrastructure that everything else depends on.

### 1a: Starshot IR v1
Take the Phase 0 prototype and make it real:
- Full type system (parameterized types, sum types, product types)
- Composition primitives (subgraph encapsulation, typed interfaces)
- Effect annotations (IO, state mutation, network — for contract verification)
- Formal semantics (so contracts can be verified against)
- Efficient binary serialization (for AI-to-AI, alongside text serialization for LLM generation)

### 1b: Grammar-Constrained Generation
Integrate with SynCode/Outlines to guarantee valid IR generation:
- Full CFG for Starshot IR
- Semantic constraints beyond syntax (type checking at generation time)
- This is the "no syntax errors, no type errors" milestone

### 1c: Compiler v1
- Starshot IR → Python (from Phase 0, hardened)
- Starshot IR → WASM (second target, proves portability)
- Optimization passes on the graph (dead node elimination, constant folding)

### 1d: Formal Contracts
The AI game changer analysis identified this as the highest-value AI-native feature:
- Contract language for specifying pre/post-conditions on subgraphs
- AI generates contracts alongside computation graphs (near-zero marginal cost)
- Automated verification of contracts against the IR
- This is where Starshot can offer something grammar-constrained text generation CANNOT

---

## Phase 2: The Vertical Slice (prove it end-to-end)

Build ONE complete application using the Starshot stack. Pick a domain:

Options:
- **CLI tool** — no UI complexity, pure computation, easy to test
- **API service** — computation + state + network, moderate complexity
- **Data pipeline** — transformation-heavy, good fit for computation graphs

Build it entirely in Starshot IR. Measure everything. Compare to the same app built traditionally.

This phase adds:
- Persistent state (use existing DB underneath, Starshot interface on top)
- Causal tracing (structured trace output, not full graph — respect physics)
- AI-to-AI binary protocols (if the app involves agent communication)

---

## Phase 3: The Ecosystem (only if Phase 2 proves dramatic advantage)

Now — and only now — start building the rest:
- Capability registry
- UI intent graph
- Semantic versioning (intent-recording, not semantic-diff)
- Bridge layer to legacy systems
- Multi-agent coordination primitives

Each component should be independently useful and adoptable without the rest (the tree-sitter strategy: infiltrate as a component, not a revolution).

---

## Anti-Patterns to Avoid

1. **Don't build Phase 3 before proving Phase 0.** Every failed predecessor did this.
2. **Don't design the final IR before testing a prototype.** The first IR will be wrong. Make it cheap to throw away.
3. **Don't go binary-only.** Current AI is text-native. The structured text serialization isn't a compromise — it's the correct interface for 2026-era AI.
4. **Don't build the whole ecosystem at once.** Each component independently useful or don't build it.
5. **Don't fight the math.** Semantic diff is undecidable. Graph optimization is NP-hard. Full-fidelity tracing is physically expensive. Design around these limits, don't pretend they don't exist.
6. **Don't ignore the incumbent.** Grammar-constrained decoding (SynCode) is the closest competitor. If Starshot doesn't offer something beyond what grammar constraints on text provide, it has no moat.

---

## The Moat Question

What does Starshot offer that grammar-constrained text generation does NOT?

1. **Semantic structure.** Grammar constraints ensure syntactic validity. Starshot IR captures semantic relationships (data flow, type dependencies, effect annotations) that enable deeper verification.
2. **Formal contracts.** You can't verify pre/post-conditions on Python text. You CAN verify them on a typed computation graph with formal semantics.
3. **Language independence.** Python text is Python. Starshot IR compiles to any target. One representation, every platform.
4. **Semantic operations.** "Rename this function" on text is find-and-replace. On a computation graph, it's a node label change with guaranteed correctness.
5. **AI-native optimization.** The graph structure enables optimizations (parallelization, fusion, dead code elimination) that are hard to perform on text.

If the experiment shows these advantages are real and measurable, Starshot has a moat. If not, use SynCode and save yourself the effort.

---

## Timeline Estimates

Not providing calendar estimates (too speculative). Instead, rough effort sizing:

| Phase | Scope | Dependencies |
|---|---|---|
| Phase 0: Experiment | 1 person, weeks | None |
| Phase 1: Foundation | Small team, months | Phase 0 validates |
| Phase 2: Vertical slice | Small team, months | Phase 1 delivers |
| Phase 3: Ecosystem | Larger team, ongoing | Phase 2 proves dramatic advantage |

The key insight: **Phase 0 is the gate.** Everything else is contingent on its result. Don't plan past Phase 0 until Phase 0 is done.
