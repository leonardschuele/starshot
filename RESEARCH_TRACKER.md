# Research Tracker: Structured Code Representations for AI

**Why this matters to Starshot:** The "LLMs are text-native" objection is the single biggest swing factor. If research shows AI works significantly better with structured representations (ASTs, graphs, IR), the core Starshot thesis is validated. If text remains optimal, Starshot should augment the text stack rather than replace it.

**Last updated:** 2026-02-12

---

## STATUS SUMMARY

The field is **actively converging on a hybrid approach**: LLMs remain text-based at the architecture level, but structured representations (AST, IR, grammar constraints) are increasingly used to **guide, constrain, and augment** text-based generation. Pure graph/structured models have NOT displaced text-native LLMs, but structure-aware text models consistently outperform structure-unaware ones.

**Implication for Starshot:** The current evidence supports a **structured-text hybrid**, not a pure graph replacement. AI works best when it processes text tokens but is guided by structural knowledge. This suggests Starshot's computation graph should have a structured text serialization, not a purely binary format.

---

## TRACK 1: AST-Aware LLMs

Research that augments LLMs with Abstract Syntax Tree knowledge while keeping the text-based architecture.

### Key Papers

| Paper | Date | Key Finding | Relevance |
|---|---|---|---|
| [AST-T5](https://arxiv.org/abs/2401.03003) | ICML 2024 | AST-aware pretraining (segmentation + span corruption) consistently outperforms text-only T5 across code generation, transpilation, understanding. 277M param model beats 6.7B InCoder on HumanEval+. | **HIGH** — proves structure helps even within text-based architectures |
| [AST-FIM](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-50.html) (Berkeley, Gong 2025) | May 2025 | AST-guided masking for fill-in-the-middle surpasses traditional FIM methods on infilling while retaining left-to-right capability. | **HIGH** — structure-aware pretraining is strictly better |
| [TreeDiff](https://arxiv.org/abs/2508.01473) | Aug 2025, revised Jan 2026 | AST-guided diffusion: corrupts/denoises AST subtrees instead of random tokens. Significantly improves syntactic correctness and reconstruction accuracy. | **HIGH** — shows AST structure helps even non-autoregressive architectures |
| [SAGE-HLS](https://www.researchgate.net/publication/399211311) | 2025 | Syntax-aware AST-guided LLM for high-level synthesis code generation. | MEDIUM — domain-specific (hardware) but demonstrates pattern |
| [Structure-Aware FIM Pretraining](https://arxiv.org/html/2506.00204v1) | June 2025 | Structure-aware fill-in-the-middle pretraining for code, building on AST-T5 line of work. | **HIGH** — continued validation of structure-aware approach |

### Key Takeaway
AST-aware models consistently beat text-only models at the same parameter count. The gains are real (2-3 points exact match, significant HumanEval improvements) but not transformative (not 10x better). Structure is helpful, not revolutionary — **so far.**

### Open Question
Does the advantage scale with model size, or does it shrink? Large models may internalize structural knowledge from text alone, making explicit AST guidance redundant at frontier scale.

---

## TRACK 2: Grammar-Constrained Decoding

Research that constrains LLM output to conform to formal grammars (CFGs, PEGs) at decode time.

### Key Papers

| Paper | Date | Key Finding | Relevance |
|---|---|---|---|
| [SynCode](https://arxiv.org/abs/2403.01632) | ICLR 2025 | Grammar-augmented generation using DFA mask stores. Reduces 96% of syntax errors in Python/Go. Works with any CFG-defined language. | **VERY HIGH** — directly relevant to Starshot's "no syntax errors" goal |
| [TreeCoder](https://arxiv.org/html/2511.22277v1) | Nov 2025 | Decoding as tree search over candidate programs. Constraints (syntax, style, execution) are first-class optimizable components. | **VERY HIGH** — represents decoding as the kind of structured search Starshot envisions |
| [IterGen](https://openreview.net/) | ICLR 2025 | Forward/backward generation tied to grammar symbols with KV-cache reuse. Can backtrack invalid SQL clauses efficiently. | HIGH — shows structured backtracking is practical |
| [Grammar-Constrained Decoding for Logical Parsing](https://aclanthology.org/2025.acl-industry.34.pdf) | ACL 2025 | GCD makes LLMs better logical parsers, achieving gains on industry tasks. | MEDIUM — validates pattern in non-code domain |
| [Flexible and Efficient GCD](https://openreview.net/forum?id=L6CYAzpO1k) | ICML 2025 | 17.71x faster offline preprocessing while preserving state-of-the-art mask computation efficiency. | HIGH — solving the performance problem that blocked adoption |
| [Grammar-Aligned Decoding](https://arxiv.org/abs/2405.21047) | 2024 | Addresses distribution distortion caused by naive grammar masking. | MEDIUM — important correctness result |

### Key Takeaway
Grammar-constrained decoding is **mature and production-ready**. SynCode eliminates 96% of syntax errors. TreeCoder treats structured generation as tree search. This is the closest existing technology to Starshot's vision: AI generating structurally valid artifacts by construction. **The question isn't whether this works — it does — but whether you need to replace the entire stack or just constrain the output.**

### Implication for Starshot
Grammar-constrained decoding may be a "good enough" incumbent that absorbs Starshot's advantage. If an LLM can generate text that's guaranteed syntactically valid via grammar constraints, do you still need a computation graph? The answer depends on whether the benefit is purely syntactic (grammar constraints win) or also semantic (Starshot's deeper thesis about semantic structure).

---

## TRACK 3: Compiler IR as Training Data

Research on training models on intermediate representations (LLVM IR, bytecode) instead of or alongside source code.

### Key Papers

| Paper | Date | Key Finding | Relevance |
|---|---|---|---|
| [IRCoder](https://arxiv.org/abs/2403.03894) | ACL 2024 | Training on parallel source+IR data (4M files) produces sizeable gains in multilingual code generation, prompt robustness, and code understanding. IR acts as a "lingua franca" aligning different languages. | **VERY HIGH** — directly validates Starshot's thesis that IR/structured representations improve AI code capability |
| [Meta LLM Compiler](https://arxiv.org/html/2407.02524v1) | 2024-2025 | 7B and 13B param models trained predominantly on LLVM IR and assembly. Enhanced capabilities in code optimization and decompilation. | **VERY HIGH** — proves frontier-scale models can be trained on IR, not just source code |
| [MIREncoder](https://arxiv.org/html/2407.02238v1) | 2024 | Multi-modal IR-based pretrained embeddings. Self-supervised pretraining on IR for downstream optimization tasks. | HIGH — IR embeddings capture information text misses |
| [IR2Vec](https://dl.acm.org/doi/fullHtml/10.1145/3418463) | Updated 2024 | LLVM IR based scalable program embeddings. | MEDIUM — foundational work, continuously refined |

### Key Takeaway
**This is the strongest evidence for Starshot's thesis.** IRCoder shows that adding IR to training data improves AI coding across the board — not just for IR tasks, but for source-level tasks too. The IR serves as a shared semantic representation that aligns understanding across languages. Meta training a 13B model on LLVM IR proves this works at scale.

### Critical Question for Starshot
IRCoder improves by training on BOTH source code AND IR. It doesn't show that IR alone is better than source code alone. The benefit may come from the alignment between representations, not from IR being inherently superior. Starshot should test: does an AI trained ONLY on computation graphs perform as well as one trained on text+graphs?

---

## TRACK 4: Graph Neural Networks for Code

Research on processing code as graphs (control flow, data flow, program dependence graphs) using GNN architectures.

### Key Papers

| Paper | Date | Key Finding | Relevance |
|---|---|---|---|
| [MISIM](https://openreview.net/pdf?id=AZ4vmLoJft) | 2021 | GNN on context-aware semantic structures yields 1.5x-43.4x improvement over code2vec on code similarity. Graph significantly outperforms sequence-based. | HIGH — empirical evidence that graphs beat sequences for code understanding |
| [GraalNN](https://2025.cgo.org/details/cgo-2025-papers/45/) | CGO 2025 | GNN-based static profiling using control-flow graphs. Reduces reliance on handcrafted features. | MEDIUM — domain-specific (profiling) but validates graph approach |
| [ProGraML](https://arxiv.org/abs/2003.10536) | 2021 | Multi-relational program graphs for ML-based compiler optimization. Outperforms sequential models on optimization tasks. | HIGH — shows graphs capture information sequences miss |

| [GraphCodeBERT](https://arxiv.org/abs/2009.08366) | ICLR 2021 (Microsoft) | Incorporates data flow graph edges into transformer pre-training. Bridge between graph and transformer approaches — proves structural signals can be injected into standard architectures. | **HIGH** — the hybrid pattern that keeps winning |

### Key Takeaway
GNNs for code consistently outperform sequence models on **understanding/analysis tasks** (similarity, optimization, profiling). But GNNs have NOT been competitive with LLMs for **generation tasks**. The transformer architecture's ability to generate long coherent sequences remains unmatched. GNNs understand code structure better but can't write code as well.

**The generation/understanding split:** This is the most important empirical finding for Starshot. Structure helps AI *understand* code (vulnerability detection, similarity, optimization). Text helps AI *generate* code (completion, synthesis). The optimal architecture may be a split: generate in tokens, verify/analyze via graphs.

### Implication for Starshot
The evidence suggests a **split architecture**: graph-based representations for analysis/verification/understanding, text/transformer-based for generation. Starshot's computation graph might be the right target representation, but the AI that produces it may still think in tokens.

---

## TRACK 5: Post-Transformer Architectures

Research on architectures that might natively process structured/graph data, replacing sequence-based transformers.

### Key Developments

| Development | Date | Relevance |
|---|---|---|
| State Space Models (Mamba, S4) | 2023-2025 | Linear complexity alternative to attention. Better at long sequences but still sequence-based. Doesn't help with graphs. |
| Hybrid architectures (H3, BiGS) | 2024-2025 | Combine SSM layers with limited attention. Still fundamentally sequential. |
| Graph Transformers | 2022-2025 | Attention mechanisms adapted for graph inputs. Active research area but not at LLM scale for code. |
| Diffusion LLMs for code (TreeDiff) | 2025 | Non-autoregressive code generation with AST awareness. Early but promising. |

### Key Takeaway
No post-transformer architecture is close to displacing transformers for code generation. The "LLMs are text-native" constraint is likely to persist for 3-5 years. **Starshot should design for text-native AI in the near term, with graph-native AI as a future optimization.**

---

## RESEARCH QUESTIONS TO TRACK

### Settled (High Confidence)
1. **Does AST awareness help LLMs?** YES — consistent, replicated improvements across multiple papers and benchmarks.
2. **Can grammar constraints eliminate syntax errors?** YES — SynCode achieves 96% reduction, production-ready.
3. **Can models be trained on IR?** YES — IRCoder and Meta LLM Compiler prove this at scale.

### Active (Being Researched)
4. **Does structural advantage scale with model size?** UNKNOWN — small models benefit most, unclear if frontier models internalize structure from text alone.
5. **Can graph-native architectures match transformers for generation?** UNLIKELY near-term — GNNs excel at understanding but not generation.
6. **Is IR alone better than source code, or only IR+source together?** UNKNOWN — IRCoder tested IR+source, not IR alone.
7. **Can diffusion models with AST guidance match autoregressive LLMs?** EARLY — TreeDiff shows promise but hasn't matched frontier autoregressive models.

### Unresolved (Fundamental)
8. **Is there a representation that's better for BOTH AI understanding AND AI generation?** This is Starshot's core bet. Current evidence says NO — text wins generation, graphs win understanding. But no one has tried a purpose-built representation designed for AI from scratch.
9. **Will AI architectures evolve toward graph-native processing?** Depends on whether attention mechanisms are replaced by something structurally different.
10. **At what scale does explicit structure become redundant?** If a 1T parameter model internalizes all structural knowledge from text, structure-aware training adds nothing. This is the "scale is all you need" vs "structure provides inductive bias" debate — the single most important open question for Starshot.
11. **The evaluation gap.** Current benchmarks (HumanEval, MBPP, SWE-bench) are designed for text-based generation. No widely-adopted benchmarks specifically test structural correctness, semantic equivalence, or robustness to surface perturbations. Structured approaches may be undervalued because we're not measuring what they're good at.

---

## KEY RESEARCHERS & LABS TO FOLLOW

| Researcher/Lab | Affiliation | Focus | Why Follow |
|---|---|---|---|
| Linyuan Gong | UC Berkeley | AST-T5, AST-FIM, structure-aware pretraining | Leading the AST-aware LLM direction |
| Alvin Cheung | UC Berkeley | Code-structure-aware LLMs (advisor) | Faculty lead on structure-aware code AI |
| Dawn Song | UC Berkeley | AI + security + code (advisor) | Broad influence on AI-for-code |
| UKPLab | TU Darmstadt | IRCoder, IR-based training | Pioneering IR as training data |
| Meta FAIR | Meta | LLM Compiler, large-scale IR models | Frontier-scale IR models |
| Shaunak Saha, Ugare et al. | UIUC | SynCode, grammar-constrained decoding | Production-grade structured generation |
| Yiming Zeng et al. | UConn, multi-university | TreeDiff | AST-guided diffusion for code |
| Uri Alon | Previously Technion, now CMU | code2vec, code2seq | Foundational work on code representations |
| Chris Cummins | Google DeepMind (prev. Meta, Edinburgh) | ProGraML, CompilerGym, compiler optimization ML | Graph representations for compiler tasks |
| Miltiadis Allamanis | Google DeepMind (prev. Microsoft) | Code naturalness, graph models, Typilus | Foundational survey on ML for code; bridging graphs + transformers |
| Marc Brockschmidt | Google DeepMind (prev. Microsoft) | GNNs for code, bug detection | GGNN applications to code |
| Eran Yahav | Technion | Code representation learning | code2vec, code2seq — foundational path-based representations |
| Gagandeep Singh | UIUC (prev. Purdue) | Constrained generation, verification | SynCode lead; connects to Starshot's formal contracts direction |
| Isil Dillig | UT Austin | Program synthesis, verification | Neurosymbolic synthesis — relevant to formal contracts |
| Swarat Chaudhuri | UT Austin | Neurosymbolic programming | Bridging neural and symbolic — Starshot's core challenge |
| Koushik Sen | UC Berkeley | Testing + AI for code | ML-guided fuzzing; relevant to verification alternatives |

---

## SEARCH QUERIES FOR PERIODIC REFRESH

Run these quarterly to stay current:

### arxiv.org
```
"AST" AND "code generation" AND "LLM" (2026)
"grammar constrained" AND "decoding" AND "code" (2026)
"intermediate representation" AND "code model" (2026)
"computation graph" AND "program synthesis" (2026)
"structured code generation" AND "transformer" (2026)
"graph neural network" AND "code generation" (2026)
"diffusion model" AND "code" AND "AST" (2026)
```

### Google Scholar
```
"code structure aware" LLM 2026
"AST guided" code generation 2026
"compiler IR" language model training 2026
"graph transformer" code 2026
```

### Conferences to Monitor
- **ICML** (July) — ML methods for code
- **ICLR** (May) — representation learning, structured generation
- **ACL/EMNLP** (varies) — NLP for code
- **NeurIPS** (December) — ML architectures, code generation
- **CGO/PLDI/POPL** (varies) — compiler and PL research with ML
- **FSE/ICSE** (varies) — software engineering with AI
- **ASE** (varies) — automated software engineering

### Key Venues for Pre-prints
- [arxiv.org cs.CL](https://arxiv.org/list/cs.CL/recent) — computation and language
- [arxiv.org cs.SE](https://arxiv.org/list/cs.SE/recent) — software engineering
- [arxiv.org cs.PL](https://arxiv.org/list/cs.PL/recent) — programming languages
- [arxiv.org cs.LG](https://arxiv.org/list/cs.LG/recent) — machine learning

---

## PRODUCTION-DEPLOYED STRUCTURED CODE AI

These are not research prototypes — they're in production. Important because they show what's actually working at scale.

| System | Deployed Where | What It Does |
|---|---|---|
| [MLGO](https://ai.googleblog.com/2022/07/mlgo-a-machine-learning-framework-for.html) (Google) | Fuchsia, Android builds | ML models making inlining and register allocation decisions inside LLVM. **Structure-aware AI in production compilers.** |
| [Outlines](https://github.com/outlines-dev/outlines) (dottxt-ai) | Multiple production systems | FSM-based constrained generation. Grammar-guaranteed valid output from any LLM. |
| [Guidance](https://github.com/microsoft/guidance) (Microsoft) | Azure AI tooling | Template-based constrained generation with structural guarantees. |
| Tree-sitter | Neovim, Helix, Zed, GitHub | AST parsing powering syntax highlighting, navigation, structural editing in production editors. |
| Structured Outputs (OpenAI, Anthropic) | API products | JSON-schema constrained output. Grammar constraints entering mainstream AI APIs. |

**Pattern:** Structured approaches succeed in production as **invisible infrastructure** — they power tools that present a text interface. Starshot should note this: the winning deployment model may be structure under the hood, text at the surface.

---

## MONITORING SETUP

### Automated Alerts (set up once)

1. **arxiv email alerts:** Go to https://arxiv.org/help/subscribe — subscribe to cs.SE, cs.PL, cs.CL, cs.LG with keyword filters
2. **Google Scholar alerts:** Create alerts for key paper titles — you'll get notified when new papers cite them:
   - "AST-T5"
   - "SynCode grammar"
   - "IRCoder intermediate representation"
   - "grammar constrained decoding code"
3. **GitHub watch:** Star/watch these repos for release notifications:
   - `outlines-dev/outlines`
   - `structuredllm/syncode`
   - `albertan017/LLM4Decompile`
   - `tree-sitter/tree-sitter`
   - `UKPLab/acl2024-ircoder`
   - `gonglinyuan/ast_t5`
4. **Semantic Scholar feeds:** https://www.semanticscholar.org/me/research — create a research feed based on these papers

### Quarterly Manual Review

Every 3 months, run the search queries listed below and update this tracker. Key questions to answer each quarter:
- Has any structured approach beaten text-only at frontier model scale (100B+ params)?
- Have any new benchmarks emerged that specifically test structural understanding?
- Has grammar-constrained decoding been extended to semantic constraints (types, scoping)?
- Are there new architecture proposals (graph transformers, etc.) showing code generation results?

---

## DECISION FRAMEWORK

Use this to decide when to update Starshot's architecture based on new research:

### If research shows structure-aware models consistently beat text-only at frontier scale:
→ Starshot thesis STRENGTHENED. Invest in computation graph as primary representation.

### If research shows structural advantage disappears at frontier scale:
→ Starshot thesis WEAKENED for the computation graph component. Pivot to grammar-constrained generation of text-based code (SynCode/TreeCoder direction).

### If graph-native architectures emerge that match transformer generation quality:
→ Starshot thesis STRONGLY VALIDATED. Pure graph representation becomes viable.

### If IR-only training matches IR+source training:
→ Starshot thesis STRENGTHENED. Source code is confirmed as unnecessary intermediary.

### If grammar-constrained decoding eliminates all structural errors:
→ Starshot's syntactic argument weakens, but semantic argument remains. Reassess whether the computation graph adds value beyond what grammar constraints provide.
