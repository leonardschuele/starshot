# Starshot Architecture

**Thesis:** AI struggles to code because the entire software stack is a human cognitive interface. Replace every layer that doesn't make sense without a human in the loop.

**Constraints:**
- Humans (input/output/audit boundaries)
- Hardware (silicon, displays, network physics)
- Difficulty of change (TCP/IP, DNS, OS kernels stay — wrap, don't replace)

---

## Changeability Gradient

```
FROZEN — cannot change
  silicon, instruction sets, display hardware, physical networks

CEMENTED — wrap, don't replace
  TCP/IP, DNS, OS syscalls, x86/ARM ABIs

INTEROP REQUIRED — bridge to, eventually supersede
  HTTP, TLS, file systems, GPU APIs

REPLACE — the starshot surface area
  everything above this line
```

---

## The Replacement Map

### 1. Programming Languages → Computation Graph

**What it replaces:** Python, JS, Rust, Go, C — all of them.

**Why they exist:** Humans can't write machine code. Languages are a cognitive interface: syntax gives structure to human reading, keywords map to English, variable names are mnemonics, formatting aids visual scanning. None of this helps an AI.

**AI-native replacement:** A typed computation graph.

- Nodes are operations (transform, branch, iterate, call)
- Edges are typed data flows
- No syntax, no formatting, no variable names — just structure and semantics
- Directly manipulable as data (not text to parse and rewrite)
- Semantic annotations where needed (intent markers, constraints, invariants)
- Compiles to any target: WASM, native, GPU, FPGA

**Key properties:**
- Structural, not textual — no parse errors, no formatting debates
- Diffable at the semantic level — "added a sorting step" not "changed lines 42-67"
- Composable — subgraphs plug together by matching typed ports
- Verifiable — types and constraints are checked structurally, not by linting text

**Human boundary:** When a human needs to audit, the graph renders to a readable visualization or pseudocode. But the source of truth is the graph, not the text.

---

### 2. HTML/CSS/JS → UI Intent Graph

**What it replaces:** The entire web frontend stack. HTML, CSS, JavaScript, React, Tailwind, the DOM, the CSSOM, the JS event loop as an authoring target.

**Why they exist:** HTML is document markup from 1993. CSS is a visual styling language because humans look at screens. JS was bolted on for interactivity. Three languages duct-taped together by historical accident, none designed for programmatic generation.

**AI-native replacement:** A UI intent graph compiled to render instructions.

- Nodes are semantic UI elements: `data_table`, `user_card`, `navigation`, `form`
- Properties are semantic: `sortable`, `editable`, `primary_action` — not `px-4 flex items-center`
- Layout is relational: `beside`, `within`, `above`, `grouped_with` — not CSS flexbox/grid
- Interaction is event flow: `on_select → filter_list` — not JS event listeners on DOM nodes
- Style is thematic: `emphasis`, `muted`, `danger` — not `color: #ef4444`

**Compilation targets:**
- Browser: compiles to optimized DOM + CSS + JS (backward compat with cemented web)
- Native: compiles to platform UI (Cocoa, Win32, Android Views)
- Terminal: compiles to TUI
- Future: compiles directly to GPU render calls, skipping DOM entirely

**Key properties:**
- One representation, every target — no "responsive design" as a manual concern
- The AI never thinks in pixels or CSS properties
- Accessibility is structural, not bolted on (semantic elements are inherently accessible)
- Theming/branding is a compilation parameter, not woven through the source

**Human boundary:** Humans see rendered output. Designers can work in visual tools that read/write the intent graph. But no human writes `<div>` tags.

---

### 3. JSON/YAML/TOML/XML → Typed Structured Data

**What it replaces:** Every text-based data serialization format used for configuration, data exchange, and storage.

**Why they exist:** Humans need to read and hand-edit configuration. Text formats with visible structure (indentation, braces, colons) serve human visual parsing. Schema is bolted on separately (JSON Schema, XML DTD) because the format itself is stringly-typed.

**AI-native replacement:** Schema-first typed binary structures.

- Every piece of data has an inherent schema — the type IS the format
- Serialization is binary (compact, unambiguous, fast)
- No parsing ambiguity (YAML's Norway problem: `NO` → boolean false)
- No formatting choices (tabs vs spaces, trailing commas)
- Schema evolution is explicit (add field, deprecate field — not "hope the JSON still parses")

**For AI-to-AI communication:** Binary typed messages. No serialization overhead.
**For AI-to-human boundary:** Render to whatever the human needs (table, form, tree view).

---

### 4. REST/GraphQL/gRPC → Capability-Based Service Protocol

**What it replaces:** REST APIs, GraphQL schemas, gRPC service definitions, OpenAPI specs, webhooks.

**Why they exist:** REST maps CRUD operations to HTTP verbs because humans understand "get this resource" and "update that thing." URLs are human-readable resource locators. GraphQL exists because REST's fixed response shapes waste bandwidth and require multiple round-trips — a problem caused by designing for human mental models of resources.

**AI-native replacement:** Typed capability exchange.

- Services expose capabilities, not endpoints: `can_sort<T: Orderable>`, `can_store<T: Serializable>`, `can_authenticate<Identity>`
- Discovery is semantic: "I need something that can resize images" → capability search, not API documentation browsing
- Invocation is typed: pass structured input, get structured output. No URL construction, no header management, no status code interpretation
- Composition is automatic: capabilities chain — output type of one matches input type of another
- Contracts are the capability signatures. No separate OpenAPI spec. The interface IS the documentation.

**Wire protocol:** Compiles down to HTTP/TCP for transport (cemented layer). But the abstraction above is capabilities, not URLs and verbs.

---

### 5. Git → Semantic Version Graph

**What it replaces:** Git, GitHub, diffs, merge conflicts, commit messages, branching strategies, pull requests as code review artifacts.

**Why it exists:** Git tracks text changes line-by-line because code is stored as text files. Merge conflicts happen because two humans edited the same lines. Commit messages exist because diffs are hard for humans to interpret. Pull requests exist because humans need to review changes before they go live.

**AI-native replacement:** A version graph of semantic transformations.

- Track what changed semantically: "added sorting capability to user_list" not "modified lines 42-67 of users.py"
- No merge conflicts from coincidental text proximity — conflicts are semantic contradictions ("A made this field required, B removed it")
- Branching is intent-based: "exploring approach A vs approach B for performance" — the version graph tracks divergent experiments, not divergent file states
- No commit messages — the transformation itself IS the description
- History is a causal graph: transformation Y happened because of intent X, enabling transformation Z

**Human boundary:** Humans review semantic change summaries. "This version adds sorting and removes the deprecated filter" — not a wall of green/red diffs.

---

### 6. Build Systems → Graph Compilation

**What it replaces:** Make, CMake, Webpack, Vite, Gradle, Cargo, Bazel, and every build configuration DSL.

**Why they exist:** Humans need to declare "compile this, then link that, copy these assets, run this preprocessor" because source code is scattered across text files with implicit dependencies. Build systems are dependency resolvers for file-based workflows.

**AI-native replacement:** Compilation is an intrinsic property of the computation graph.

- The computation graph knows its own dependencies — they're the edges
- "Building" is traversing the graph and emitting target code
- Incremental by nature — nodes track their own dirty state
- No configuration files — the build IS the structure
- Cross-compilation is choosing a different code generator for the same graph
- Asset handling, preprocessing, optimization — all graph transformations applied before final emission

**Key insight:** Build systems exist because of the impedance mismatch between human-authored text files and machine-executable code. Remove text files, remove build systems.

---

### 7. Package Managers → Capability Registry

**What it replaces:** npm, pip, cargo, apt, brew, and all their lock files, version conflicts, and dependency hell.

**Why they exist:** Humans discover, evaluate, and compose libraries. Version numbers are trust signals. Lock files prevent "works on my machine." Dependency resolution is a constraint satisfaction problem created by human-chosen version ranges.

**AI-native replacement:** A registry of verified capabilities with formal contracts.

- Request by contract, not by name: "I need SHA-256 hashing that runs in constant time" not `npm install crypto-lib@^3.2.1`
- No version conflicts — capabilities are composed by type compatibility, not semver
- No lock files — determinism is guaranteed by capability identity (content-addressed)
- Trust is formal verification, not download counts and GitHub stars
- Capabilities can be inlined, composed, or referenced — granularity is flexible

---

### 8. Databases / SQL → Persistent State Graph

**What it replaces:** SQL databases, NoSQL databases, ORMs, query languages, migrations, schema management.

**Why they exist:** Humans think in tables (spreadsheet mental model → relational algebra). SQL is English-like because humans write queries. Migrations exist because schema changes are risky text transformations.

**AI-native replacement:** A typed persistent graph with structural access.

- State is a typed graph — nodes are entities, edges are relationships (closer to how data actually relates)
- Access is structural pattern matching: "find all users connected to this organization with active sessions" is a graph traversal, not a multi-JOIN SQL string
- Schema evolution is graph transformation: add node type, add edge type, migrate data structurally
- Indexing is automatic based on access patterns — the system observes how the graph is queried and optimizes
- Consistency guarantees are properties of the graph, declared as constraints on subgraph patterns
- No ORM — the computation graph and state graph share the same type system

---

### 9. Logging / Observability → Causal Trace Graph

**What it replaces:** Log files, log levels, ELK stacks, Prometheus, Grafana, distributed tracing, APM tools.

**Why they exist:** Humans read log lines to reconstruct what happened. Log levels (DEBUG, INFO, WARN, ERROR) filter for human attention. Dashboards are visual summaries for human monitoring. Distributed tracing exists because log files don't connect cause to effect across services.

**AI-native replacement:** Every operation produces a causal trace.

- A directed graph: node A caused node B, which caused node C
- No log levels — relevance is determined by querying the causal structure
- Debugging is graph traversal: start at the failure, walk backward through causes
- Monitoring is graph invariant checking: "does this subgraph satisfy the latency constraint?"
- Anomaly detection is structural: "this trace has a shape we've never seen before"
- No need for log aggregation — the trace graph IS the single source of truth

**Key insight:** Logging is what you do when you can't inspect causality directly. If the system records causality as a first-class structure, "logs" are just one possible rendering of the trace graph.

---

### 10. Auth Protocols → Cryptographic Capability Delegation

**What it replaces:** OAuth 2.0, OIDC, JWTs, API keys, session cookies, SAML, RBAC, ACLs.

**Why they exist:** Humans need login flows. Passwords are human-memorizable secrets. OAuth exists because humans need to grant third-party apps access without sharing credentials. RBAC maps to human organizational hierarchies.

**AI-native replacement:** Cryptographic capability tokens.

- An agent holds a token that proves "I can do X" — not "I am user Y who has role Z that grants permission to X"
- Authorization is capability possession, not identity lookup
- Delegation is cryptographic: agent A can mint a token granting agent B a subset of its own capabilities
- Fine-grained by default: a token grants exactly one capability, not "admin access"
- Revocation is token invalidation, not session management
- No passwords, no API keys — capabilities are cryptographic objects

---

## Cross-Cutting Principles

### Everything is a graph
Text files impose linear order on inherently non-linear structures. The computation graph, UI graph, state graph, version graph, trace graph, and capability graph are all... graphs. The universal data structure of the AI-native stack is the typed, directed graph.

### Types are the universal interface
Every boundary — between components, between services, between agents — is a typed contract. No stringly-typed interfaces. No "parse this JSON and hope it has the right fields." Types flow from intent to execution without gaps.

### No serialization-to-text by default
Text is a rendering format for humans. AI-to-AI communication is binary typed structures. Text is only generated at the human boundary.

### Causality is first-class
Every transformation records why it happened and what it affected. This subsumes logging, version history, debugging, and audit trails into a single causal structure.

### Intent over instruction
The human says what they want. The AI determines how to achieve it. The intermediate representations between intent and execution are optimized for AI manipulation, not human reading.

---

## Architecture Diagram

```
HUMAN BOUNDARY (input)
│  natural language intent
│  visual design tools
│  constraint specification
▼
┌─────────────────────────────────────────────┐
│              INTENT LAYER                    │
│  parse intent → semantic goal specification  │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          COMPUTATION GRAPH                   │
│  typed operations, data flow, composition    │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ │
│  │ UI Graph │ │State Graph│ │Trace Graph │ │
│  └──────────┘ └───────────┘ └────────────┘ │
│  ┌───────────────┐ ┌──────────────────────┐ │
│  │Capability Reg.│ │Semantic Version Graph│ │
│  └───────────────┘ └──────────────────────┘ │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          COMPILATION LAYER                   │
│  graph → target code / render instructions   │
│  targets: WASM, native, GPU, browser, TUI    │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          BRIDGE LAYER                        │
│  translates to cemented protocols            │
│  HTTP, TCP/IP, DNS, file systems, OS APIs    │
└──────────────────┬──────────────────────────┘
                   ▼
HARDWARE
  CPU, GPU, network, storage, display
                   │
                   ▼
HUMAN BOUNDARY (output)
  rendered UI, reports, notifications
```

---

## Open Questions

1. **Bootstrap problem:** Starshot must be built using legacy tools before it can build itself. What's the minimal viable self-hosting path?
2. **Graph representation:** What is the concrete binary format for the computation graph? Does it need to be standardized, or can it evolve?
3. **AI model coupling:** How tightly should the representation be coupled to current LLM capabilities? Design for today's models or hypothetical future ones?
4. **Interop period:** During transition, legacy systems must interop with AI-native ones. Where are the adapters, and how thick are they?
5. **Multi-agent coordination:** When multiple AI agents collaborate on a computation graph, what are the concurrency primitives?
6. **Verification without tests:** If formal contracts replace test suites, what is the specification language for those contracts?
7. **Human trust:** How do humans audit and trust a system whose internals are not human-readable? What does the audit boundary actually look like?
