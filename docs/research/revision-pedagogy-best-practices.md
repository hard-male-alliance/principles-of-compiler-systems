# Revision pedagogy and visualization practices for the compiler-systems survey

**Date:** 2026-09-23
**Decision purpose:** revise the LLNCS survey from an evidence/audit-oriented report into a concise, case-driven explanation of compiler systems, while adding a small but real formal spine and replacing weak pipeline drawings with semantic visualizations.
**Scope:** exposition and visual design only. This note does not prescribe changes to the experiment harness or claim that the running example proves compiler correctness.

## Executive judgment

The strongest transferable model is not “attach evidence to every statement.” It is **keep one program semantically continuous while changing the reader's viewpoint**. CS:APP asks how a system changes the behavior and performance of a programmer's program; LLVM's Kaleidoscope and MLIR's Toy tutorials reduce upfront detail by growing one artifact across chapters. Classic compiler texts then supply the missing intellectual structure: each phase introduces an abstraction, an invariant, and an engineering problem.

For this survey, the clipped-dot-product example should therefore be a **narrative carrier**, not a validation subject. Its snapshots should answer “what became explicit, what information was lost or gained, and why was that trade made?” Reproduction commands and exact tool-output provenance belong in one compact methodology/sidebar or appendix. They should not determine the main chapter rhythm.

A useful recurring chapter pattern is:

> **Question → semantic object → minimal formal model → transformation of the running example → engineering trade-off → one-sentence principle.**

This is a synthesis/recommendation, not a directly evaluated pedagogical result. The sources below are authoritative exemplars and technical specifications, not a controlled comparison of textbook styles.

## What authoritative exemplars actually support

| Source | What it establishes | Directly transferable | Important limit / not transferable |
|---|---|---|---|
| Bryant and O'Hallaron, [CS:APP: A Programmer's Perspective](https://csapp.cs.cmu.edu/3e/perspective.html) and [book overview](https://csapp.cs.cmu.edu/) | The authors explicitly contrast a “builder's perspective” with explaining how systems affect program behavior and performance; they advocate a whole-system view grounded in real programs. | Organize the tour around consequences visible in one program, repeatedly crossing abstraction boundaries. | CS:APP is not a compiler textbook and its authors' rationale is not causal evidence that this format is universally superior. Do not copy its hardware/OS balance mechanically. |
| LLVM, [Kaleidoscope tutorial](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/) | One small language is built iteratively; each chapter adds one concept, reducing overwhelming detail. It proceeds from lexer and AST through IR, optimization/JIT, object emission, and debug information. | Reuse one artifact; reveal only the detail needed by the current abstraction; let later chapters reinterpret earlier objects. | The tutorial explicitly warns that its implementation is **not** software-engineering best practice. Its intentionally simple code structure must not be promoted as production architecture. |
| MLIR, [Toy tutorial](https://mlir.llvm.org/docs/Tutorials/Toy/) | One language is progressively represented, optimized, partially lowered, and finally converted to LLVM IR. | Show representation changes as changes in available semantics, not as a list of tools. A “mixed abstraction” intermediate snapshot can be pedagogically valuable. | Toy is designed to teach MLIR concepts, not to survey a conventional native toolchain or establish performance claims. |
| Cooper and Torczon, [*Engineering a Compiler*, 3rd ed.](https://shop.elsevier.com/books/engineering-a-compiler/cooper/978-0-12-815412-0) | The book combines principles with pragmatic compiler-building insight and structures the subject around scanning, parsing, IR, translation, procedures/code shape, optimization, data flow, instruction selection, scheduling, and allocation. | For each phase, pair the mathematical abstraction with the engineering reason it exists. Treat “code shape” as an explicit design variable rather than incidental syntax. | A phase-by-phase table of contents is a coverage map, not necessarily the best narrative order for a short review. |
| Appel, [*Modern Compiler Implementation* contents](https://www.cs.princeton.edu/~appel/modern/toc.html) | A single Tiger compiler connects type checking, activation records, IR, blocks/traces, selection, liveness, allocation, and “putting it all together”; advanced topics follow the complete basic path. | Keep prerequisites local and make advanced material visibly grow from the completed path. | Its 1998 implementation choices and target assumptions are not a template for modern LLVM/MLIR internals. |
| CompCert, [semantic-preservation overview](https://compcert.org/man/manual001.html) | Compiler correctness is stated over observable behaviors; target behavior refines an allowed source behavior rather than necessarily being textually or operationally identical. Formal semantics maps programs to possible behaviors. | Use one precise refinement statement to explain what “preserves meaning” can mean, especially with source nondeterminism and undefined behavior. | CompCert's theorem starts after preprocessing/parsing/type checking and ends before assembling/linking. It does not justify claiming an end-to-end theorem for this report or its concrete toolchain. |
| LLVM, [IR undefined-behavior manual](https://llvm.org/docs/UndefinedBehavior.html) | Immediate UB, poison, `undef`, and `freeze` have different roles; UB supplies optimization latitude and reflects target trade-offs. | Use one localized example to show why equality of ordinary values is too weak a model for optimization correctness. | LLVM's current semantics are evolving and are specific to LLVM IR; do not silently project them onto SysY, C, machine ISA, or MLIR dialects. |
| Alive2, [project documentation](https://github.com/AliveToolkit/alive2/blob/master/README.md) and [PLDI 2021 publication page](https://web.ist.utl.pt/nuno.lopes/pubs.php?id=alive2-pldi21) | Translation validation for LLVM can be formulated as refinement and checked symbolically; the tool explicitly documents scope limits, including unsupported interprocedural transformations and possible spurious counterexamples. | A useful frontier example of turning a local proof obligation into a tool. | Alive2 is not needed to explain the running example and must not dominate the main narrative. “Bounded translation validation” is not a proof of the whole compiler. |
| Gansner et al., [“A Technique for Drawing Directed Graphs”](https://graphviz.org/documentation/TSE93.pdf), IEEE TSE 1993 | Hierarchical drawings should expose overall flow, reduce crossings/bends, keep edges short, and use balance where possible; these objectives conflict and require heuristics. | Use a layered layout for actual control/data/dependency graphs, with a stable direction and few crossings. | A compiler pipeline is often a sequence of representations, not an arbitrary graph. Applying Graphviz to every conceptual figure can produce technically laid-out but semantically poor diagrams. |
| LLVM, [`dot-cfg` pass documentation](https://llvm.org/docs/Passes.html) | LLVM can emit actual CFGs and dominance graphs in DOT form. | Generate a case CFG from the same IR, then simplify labels for publication rather than redrawing its topology by hand. | Raw compiler dumps are inspection artifacts, not publication-ready figures; dense instructions and unstable autogenerated names should be curated. |
| LLVM, [optimization remarks and `opt-viewer`](https://llvm.org/docs/Remarks.html) | Optimization remarks can be visualized at source locations and diffs can compare two remark sets. | For optimization, show a localized before/after plus the compiler's reason, rather than a generic “optimizer” box. | Remarks report selected compiler decisions and omissions; they neither prove legality nor fully reveal pass causality. |
| V8, [Turbolizer](https://v8.github.io/tools/head/turbolizer/) | A production compiler visualization supports movement across phases, origin/history tracing, filtering, and collapsing irrelevant graph regions. | Preserve node identity across before/after views and visually suppress unchanged material. | Interactive navigation cannot be reproduced in a static paper; a full sea-of-nodes view would overwhelm this example. |
| W3C, [WCAG 2.2 explanation of color use](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color) | Meaning must not be conveyed by color alone; text, shape, or other redundant signals should accompany color. | Give transformations, representations, runtime entities, and hazards distinct labels/shapes/line styles as well as color. | WCAG is a web-accessibility standard, not a complete theory of print information design; apply its redundancy rule, not every web interaction requirement. |

## Revision architecture

### 1. Change the controlling question

The current report's section titles show a strong audit frame: “evidence levels,” “reproducible causal experiment,” “what we know/cannot know,” “explicit evidence,” “validation loop,” and an entire validation chapter. Those ideas are legitimate but overrepresented for a survey whose purpose is explanation.

Recommended controlling question:

> **At this boundary, what fact about the program becomes explicit, what mechanism uses it, and what engineering freedom or cost follows?**

Apply it consistently:

| Boundary | What becomes explicit | Mechanism it enables | Engineering price |
|---|---|---|---|
| text → AST | grammatical and binding structure | diagnostics, typed elaboration | source trivia and macro origin become harder to retain |
| AST → LLVM IR | control flow, data dependence, memory operations | target-independent analysis and rewriting | source constructs and evaluation intent are flattened |
| memory form → SSA | unique value definitions and joins | sparse analysis and simple rewrite matching | memory and alias facts require separate models |
| IR → machine IR | legal target operations and register classes | instruction selection, scheduling, allocation | portability decreases as hardware constraints enter |
| assembly → relocatable ELF | bytes, symbols, sections, unresolved address equations | independent assembly and later composition | final addresses and some call sequences remain unknown |
| linked ELF → process | virtual-memory segments and runtime entry protocol | executable process semantics | loader/ABI/runtime behavior now participates in meaning |

This table's logic can replace repeated taxonomies of evidence strength.

### 2. Use a stable chapter rhythm

For every core chapter:

1. **Opening puzzle (2–4 sentences).** Something in the current representation cannot yet be explained: e.g., “Why can the optimizer delete this branch?”
2. **Abstraction.** Name the object and what information it carries.
3. **Formal kernel.** One definition, judgment, equation, or optimization objective—only enough mathematics to make the design non-metaphorical.
4. **Case transition.** Show a small before/after slice of the clipped dot product.
5. **Mechanism.** Explain the algorithm or system component acting on that slice.
6. **Trade-off.** State what is gained, lost, approximated, or delayed in production.
7. **Principle.** End with a portable idea, not an evidence disclaimer.

Commands, exact hashes, exhaustive output tables, and environment notes should be consolidated outside this rhythm. One half-page “How the snapshots were obtained” box is enough for intellectual honesty.

### 3. Give the paper a minimal formal spine

The paper does not need a mechanized proof. It does need notation that explains *why* the layers exist. The following six pieces are sufficient and mutually connected.

#### A. Meaning as observations, not textual identity

Let `Beh_L(P)` be the set of observable traces permitted by language/representation `L` for program `P`. For a lowering `T : L_s -> L_t`, state the design obligation as refinement:

\[
  \operatorname{Beh}_{L_t}(T(P)) \subseteq \operatorname{Beh}_{L_s}(P),
\]

under explicit well-definedness and ABI/environment assumptions. Equality is too strong when the source permits multiple evaluation orders; an ordinary input/output test is too weak because it observes only a finite subset. This formula should frame the journey, **not turn it into a verification paper**.

For the running example, separately define its mathematical function:

\[
  F(n,A,B)=\sum_{i=0}^{\operatorname{clamp}(n,0,8)-1}
  \operatorname{clamp}(A_iB_i,-8,12).
\]

Every representation should then be described as a different implementation of the same abstract state transformation.

#### B. Front-end judgments

Use one typing judgment such as

\[
  \Gamma \vdash A[i]\,B[i] : \mathtt{int}
\]

and unpack `Gamma` (bindings/types), the premises (array element and index types), and the produced implicit operations. If grammar is shown, connect one production to one AST node. This explains what the front end establishes; a token dump does not.

#### C. CFG, dominance, and SSA

Define the control-flow graph `G=(V,E)`, then dominance:

\[
  d \dom v \iff \text{every path from entry to }v\text{ contains }d.
\]

Explain a `phi`/block argument as selecting the predecessor-indexed value at a join. On the case CFG, color/shape the loop header and show the induction value's two incoming definitions. This is the mathematical reason SSA construction and many sparse analyses work.

#### D. Data flow and fixed points

For liveness, one pair of equations is enough:

\[
\operatorname{out}[b]=\bigcup_{s\in succ(b)}\operatorname{in}[s],\qquad
\operatorname{in}[b]=use[b]\cup(\operatorname{out}[b]-def[b]).
\]

Connect the least fixed point to the case's live values, then to interference and spills. State the production trade-off: more precise analysis can improve code but costs compile time and memory.

#### E. Local transformation obligation

For an optimization `p -> q` under precondition `C`, write

\[
  C \Longrightarrow \operatorname{Beh}(q)\subseteq\operatorname{Beh}(p).
\]

Use the clamp or loop canonicalization as the worked example. Immediately discuss overflow, poison, aliasing, and target profitability as *different questions*: legality, semantic modeling, memory dependence, and cost. This separation is more explanatory than ranking “evidence strength.”

#### F. Back-end constraints as optimization problems

Use small formal objects rather than prose-only descriptions:

- instruction selection: cover an expression/DAG with legal patterns while minimizing a target cost;
- scheduling: choose a topological order of the dependence DAG subject to resource/latency constraints;
- register allocation: color the interference graph with `K` registers, inserting spills when coloring fails;
- relocation: illustrate one concrete ABI equation such as `S + A - P`, defining symbol, addend, and place.

These are explanatory models, not claims that LLVM literally runs the textbook algorithm in every configuration. Make that distinction explicit.

### 4. Replace pipeline art with a visual system

#### Canonical visual vocabulary

Use the same grammar throughout the paper:

| Meaning | Shape / line | Suggested color (secondary encoding) |
|---|---|---|
| representation/artifact | rounded rectangle | blue |
| transformation/analysis | narrow labeled arrow or hexagon | amber |
| runtime/platform component | rectangle with double border | gray |
| invariant/semantic contract | small attached badge | green |
| loss, approximation, or undefinedness | warning triangle / dashed red edge | red |

All distinctions must survive grayscale: labels, shape, border, and line style carry the primary meaning.

#### Figure portfolio (avoid one overloaded mega-diagram)

1. **Journey map:** a simple left-to-right sequence of representations. Put tools beneath the arrows, not as first-class pipeline nodes. Highlight only the current chapter's boundary.
2. **Representation small multiples:** source fragment, AST/typed expression, LLVM block, RV64 instructions, and relocation record aligned vertically around the same operation. Use stable callout numbers to preserve identity.
3. **Actual CFG:** generate topology with LLVM `dot-cfg`/Graphviz; shorten node text; emphasize entry, loop header, latch, and exit. Do not include the entire function body in every block.
4. **Optimization before/after:** two aligned panels with unchanged nodes faded; label the rewrite precondition and the downstream opportunity it creates. Preserve node IDs where possible, following the useful idea behind Turbolizer phase navigation.
5. **Semantic-refinement ladder:** a compact commuting/refinement diagram with `Beh` on the side; use it once, then refer back to it.
6. **ELF-to-process map:** two aligned columns—file sections and loadable segments—with address ranges and a few noncrossing mapping bands. This communicates the section/segment distinction better than another pipeline.
7. **Trade-off radar is not recommended.** The axes would mix incomparable quantities and imply measurements the report does not have. Prefer a table with explicit qualitative dimensions.

#### Tool choice

- **Graphviz/DOT:** CFGs, dominance trees, dependency graphs, and other genuine directed graphs.
- **TikZ/PGF:** semantic diagrams, aligned representation ladders, memory/file maps, and publication typography.
- **Python/Matplotlib:** only for quantitative plots backed by data; not for decorative pipelines.
- **SVG generated by a script:** acceptable for complex layered diagrams if the source and fonts are deterministic; embed text as text where the LNCS toolchain permits.

The rule is “choose layout by semantic structure,” not “use one drawing tool everywhere.”

## Suggested content-level cuts and moves

These recommendations follow from the current section structure, not from external sources.

| Current emphasis | Revision action | Reason |
|---|---|---|
| Introduction repeatedly defines evidence tiers, falsification, and reproducibility | Retain one paragraph on artifact provenance; replace the rest with the journey's semantic question and reader promises. | The methods language currently competes with the compiler-system thesis. |
| “Cross-layer tracking table and behavioral oracle” | Rename/recast as “semantic thread across representations”; show `F` and the one traced operation. | The example illustrates continuity; it is not principally an oracle design. |
| Optimization section opens with evidence hierarchy | Open with legality vs profitability, formalize refinement, then explain one transformation chain. | This directly answers why optimizers are both mathematical and heuristic. |
| Backend closes on epistemic limits | Close on the principle that the backend converts semantic freedom into target constraints. Put tool-version caveats in a note. | A chapter should resolve its design question rather than end as an audit report. |
| ELF chapter calls unknown quantities “evidence” | Call them symbolic obligations/deferred address computations. | Relocations are mechanisms, not primarily epistemic artifacts. |
| Full validation chapter | Compress into a short interlude or appendix: observation matrix, scope, and difference between testing, translation validation, and compiler verification. | Keeps terminology correct without allowing validation to become the paper's subject. |
| Frontier chapter repeatedly qualifies evidence maturity | Organize each frontier by the bottleneck it changes: legality, search, cost modeling, heterogeneous mapping, staging. Give one readiness sentence each. | Produces an argument instead of a literature inventory. |

## Quality checks for the rewritten paper

Use these as editorial tests, not as claims of formal verification:

1. **Narrative continuity:** every core chapter points to the exact case expression/value/control edge it is transforming.
2. **Formal usefulness:** every displayed equation is instantiated on the case within the next paragraph; remove equations that merely decorate terminology.
3. **Mechanism–trade-off pairing:** every mechanism names at least one resource or constraint it trades (compile time, precision, code size, runtime, portability, debuggability).
4. **Visual necessity:** every figure answers a question that would require more effort in prose; delete figures that merely repeat a linear list.
5. **Stable visual semantics:** colors/shapes/line styles have the same meanings across figures and remain understandable in grayscale.
6. **Provenance proportionality:** exact commands and versions appear once; the main text uses outputs only when they explain a transformation.
7. **Claim calibration:** distinguish textbook model, current LLVM/ABI rule, observation from the case, and forward-looking inference.
8. **Compression:** remove repeated caveats after their scope is established. A limitation should be repeated only when it changes the local conclusion.

## Bottom line

The revision should feel like following a conserved semantic thread through a sequence of increasingly explicit machines. Formalism supplies the joints; the running example supplies continuity; engineering trade-offs explain why real compilers deviate from ideal algorithms; visuals expose structure that prose cannot. Reproducibility remains a compact supporting property, not the paper's organizing philosophy.
