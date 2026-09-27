# Editorial Revision Brief: From an Artifact Report to *Inside a Compiler System*

Status: **authoritative editorial brief for the current revision**
Language of this durable note: English; the manuscript remains Chinese.
Scope: narrative architecture, content priorities, formal exposition, visual system, and acceptance gates. It deliberately does not prescribe TeX line edits.

## 1. Product decision

The report must be rebuilt as a **survey/tutorial in the manner of CS:APP**, not as an experiment report whose main concern is whether its own claims have enough evidence. The clipped-dot-product program remains the single narrative carrier, but its role changes:

- it is a **lens** through which the reader sees compiler concepts;
- it is not a subject under test;
- its executions are a short completion check required by the assignment, not the paper's epistemic center;
- reproducibility details belong in the companion repository or a compact appendix, except where a concrete command/output is itself the object being explained.

The revised paper's promise should be:

> Follow one small SysY computation as its meaning is successively expressed as source structure, typed syntax, control/data flow, target-independent IR, optimized IR, target instructions, symbolic object code, and a loaded process; at every layer, explain what becomes explicit, what is deliberately forgotten, and which engineering trade-off that choice creates.

This is close to the genuine CS:APP pedagogical stance: systems are taught through how their mechanisms shape a program, rather than as isolated machinery to be implemented. The official CS:APP description explicitly contrasts a “programmer's perspective” with a builder-only presentation. The report should borrow that **reader perspective**, not imitate the book's chapter list.

### 1.1 Primary reader

A student who can read a C-like loop and basic assembly, but still thinks of a compiler as a monolithic source-to-binary translator. At the end, that reader should be able to:

1. locate one source-level fact in every later representation;
2. distinguish semantic preservation from representation choice and from profitability;
3. explain why SSA, an ABI, relocation, and progressive lowering exist;
4. identify where mathematical models guide engineering without pretending that real compilers are pure mathematics;
5. use the same questions to investigate a different program or compiler.

### 1.2 Central thesis and recurring questions

The existing thesis—compiler systems as a chain of representation contracts—is worth retaining, but “contract” must mean an explanatory relation between representations, not a reason to append verification bureaucracy.

Every core chapter should answer the same three questions:

1. **Meaning:** what fact about the clipped dot product matters at this layer?
2. **Representation:** how is that fact encoded here, and what information has been lost or made explicit?
3. **Choice:** what theoretical condition constrains the transformation, and what practical consideration decides among the legal choices?

These questions replace the current recurring pattern of “what evidence do we have, what remains unproved, and what would falsify it.” A short caveat is still appropriate when a technical limitation materially changes the reader's understanding; generic epistemic disclaimers are not.

## 2. Diagnosis of the current manuscript

The current report has strong technical coverage and a good concluding philosophy, but the editorial center is wrong.

### 2.1 Measured symptoms

The 13 section files contain roughly 38,000 Chinese characters. Terms matching `证据|验证|核验|可复现|预言机|实验` occur about 167 times. The dedicated validation chapter alone contains 33 such occurrences, and the frontiers chapter contains 39. The introduction begins with evidence categories, the case chapter ends in an oracle discussion, several technical chapters close by limiting the strength of evidence, and the conclusion again foregrounds validation.

This creates three costs:

1. **Narrative cost:** the reader repeatedly leaves the compiler mechanism to inspect the author's methodology.
2. **Conceptual cost:** elementary artifact checks receive more space than dominators, fixed points, instruction selection, scheduling, liveness, and semantic refinement.
3. **Visual cost:** tables and text-shaped flow diagrams carry relationships that should be seen spatially.

The present manuscript also has many equations containing case arithmetic, but almost no compact formal model of the compiler ideas themselves. A formula for the expected prefix sum is useful; it does not substitute for explaining CFGs, SSA, data-flow analysis, transformation correctness, liveness, scheduling, or relocation.

### 2.2 What is already valuable

Retain and elevate:

- the single bounded-prefix clipped dot product and its carefully chosen language features;
- the distinction between the normative SysY source and the C observation vehicle, stated once;
- the “one fact across layers” instinct;
- clear explanations of `getelementptr`, `phi`, poison/undefined behavior, ABI registers, symbols, relocation, and section-versus-segment distinctions;
- the Newlib/glibc episode, but only as a compact ABI/environment lesson rather than a forensic subplot;
- the insight that dialects are not a simple linear staircase;
- the conclusion's principles: stages are semantic responsibilities; representations are contracts; unresolved decisions survive into objects; abstractions should be lowered only after their last beneficiary.

These are the manuscript's conceptual spine. The revision should move this quality of synthesis from the conclusion into every chapter.

## 3. Reader journey and top-down chapter architecture

Use ten logical chapters. The physical TeX file split may differ, but the reader should experience this progression. The old-to-new mapping prevents accidental loss of assignment coverage.

| New chapter and reader question | Main intellectual move | Case-study anchor | Old material disposition |
|---|---|---|---|
| **1. Introduction — What is a compiler system?** | Replace the black-box pipeline with successive representations and decisions. State the one-program method and the representation/choice thesis. | Show one source statement beside one IR fragment, one instruction, and one relocation as a teaser. | Rewrite old 01. Delete the evidence taxonomy/table and validation research question. Retain scope and the strong representation-contract idea. |
| **2. One computation, many forms** | Define the program's meaning before showing machinery. Give the journey map and the few invariants needed later. | Full SysY listing once; mathematical clipped-prefix function; feature-to-layer map. | Condense old 02. Keep the semantic function, range argument, and journey map. Move the test oracle and exact runtime behavior out of the narrative. |
| **3. Meaning before code generation: preprocessing and the front end** | Explain how characters become tokens, syntax, bindings, and typed operations. Treat preprocessing as token transformation and the front end as construction of a typed program. | Trace `VECTOR_LENGTH`, one array subscript, one call, and one invalid expression through tokens/AST/type judgment. | Reshape old 03. Keep the C/SysY distinction as a compact sidebar. Cut command inventories and reproducibility discussion. |
| **4. Control, data, and memory in LLVM IR** | Introduce CFG, dominance, SSA, `phi`, memory, aliasing, and GEP as a coherent answer to “what must become explicit?” | Turn the loop's `i` and `acc` into loop-carried SSA values; derive the address of `a[i]`; contrast `-O0` memory form with SSA form. | Rewrite old 04 around a new CFG/SSA visual and formal definitions. Retain poison/UB only where it changes legal transformations. |
| **5. Optimization: legal transformations under a cost model** | Separate semantic legality from profitability. Explain analyses as fixed points and transformations as constrained rewrites, not a list of passes. | Constant propagation/canonicalization, clipping control flow, alias limits, loop vectorization/reduction, and target-dependent profitability. | Rewrite old 05. Delete “evidence grading” and the causal experiment recipe. Add data-flow equations and a proof-versus-profit diagram. |
| **6. When the machine enters: lowering to RV64** | Explain instruction selection, scheduling, register allocation, calling convention, and frame construction as interacting constraints. | Map compares, loads, loop backedge, five arguments, return value, and runtime calls to RV64. | Merge old 06 and 07. Remove duplicated generated-versus-handwritten bookkeeping. Preserve the hand-written implementation as an annotated reading object. |
| **7. From names to addresses: assembly, ELF, linking, and loading** | Show how symbolic facts become bytes and addresses, and why some decisions must remain deferred. | Follow a single `putint` call from assembly symbol to relocation, archive extraction, final address, segment, and process call. | Merge old 08 and 09. Retain object anatomy and loader boundary. Reduce the library mismatch to one boxed lesson. Put exact inspection commands in an appendix/README. End with one paragraph stating that the three authored forms run equivalently. |
| **8. Keeping abstractions alive: MLIR and AscendNPU IR** | Explain why one low-level IR cannot economically serve every domain; present dialect coexistence, interface-based transformation, legalization, bufferization, and progressive lowering. | Re-express the dot product as structured map/clip/reduction, then show what is committed when lowered toward memory and HIVM. Use VecAdd only as the official concrete reference point. | Reshape old 11. Delete evidence-status preambles and proposed validation plans. Keep the warning that the official VecAdd starts at a relatively low level. |
| **9. Compiler frontiers as enduring design tensions** | Organize research by tensions, not maturity scoring: assurance vs coverage; search space vs compile budget; static knowledge vs runtime feedback; abstraction vs interoperability. | Ask how each direction would alter one decision in the same dot product. | Compress old 12 substantially. Keep verification, e-graphs/superoptimization, PGO/MLGO, heterogeneous scheduling, and JIT/AOT only as connected outlooks. Remove P1–P5 ratings, benchmark policing, reproducible-build excursus, and repeated falsification criteria. |
| **10. Principles for reading compiler systems** | Synthesize reusable principles and return to the opening teaser. | Revisit the same source fact at every layer in one final visual or compact ledger. | Retain the strongest parts of old 13, but remove the final inventory of validation limitations. End with a forward-looking method for studying any compiler. |

### 3.1 The case study's narrative function

The case should recur as a **worked example**, not as repeated proof that the repository exists. The rhythm inside each technical chapter should be:

1. introduce a real compiler problem;
2. give the smallest formal model that exposes its structure;
3. instantiate it on the clipped dot product;
4. show the actual representation;
5. explain the engineering compromise;
6. hand one unresolved question to the next chapter.

Example transition:

> The front end can prove that `a[i]` denotes an `int`, but it does not yet choose an address instruction. LLVM IR therefore preserves the typed element stride in `getelementptr` while exposing the memory operation. Once this address relation is explicit, alias analysis—not syntax—limits whether the loop can be reordered.

That sentence simultaneously closes the front end, motivates IR, and prepares optimization. Every chapter should have a transition of this kind.

### 3.2 Work/results requirement without an experiment-paper voice

The course requires “work and results” and asks that the equivalent SysY, LLVM IR, and RISC-V versions be linked and checked. Satisfy it compactly:

- state once that all three authored representations and the C observation form produce the same result for representative boundary inputs;
- show at most one small input/output table;
- keep exact commands, version manifests, stderr bytes, file names, and full matrices in `preflight/README.md` or a compact appendix;
- do not create a standalone validation chapter;
- do not describe the runtime's timer line unless it is needed to explain a runtime/library boundary.

This preserves the assignment's observable requirement without allowing testing to become the topic.

## 4. Formal backbone: enough mathematics to explain design

Mathematics should function as a compression tool: it makes an invariant, dependency, or trade-off precise, and then returns immediately to the case and the implementation. The report must not become a theorem catalogue.

### 4.1 The three-part rule for every formal item

Every definition, judgment, or equation must be followed within two paragraphs by:

1. **case instantiation** — point to the exact source/IR/assembly fragment;
2. **engineering consequence** — explain what the model enables, excludes, or makes expensive.

Conversely, no mathematically central concept should be presented only as prose if a four-line definition would reveal its structure.

### 4.2 Required formal concepts by chapter

| Location | Minimal formal object | What it explains in the case | Engineering trade-off to state |
|---|---|---|---|
| Ch. 2 | Semantic function (D(x)=\sum_{i<\operatorname{clamp}(x,0,8)}\operatorname{clamp}(a_i b_i,-8,12)), observation function, and bound on products/sums | The stable meaning all representations must implement; why reassociation of the reduction is safe here but moving clipping after the sum is not | A precise but deliberately narrow integer domain avoids undefined overflow; generality would require wider arithmetic or overflow semantics |
| Ch. 3 | One typing judgment such as (\Gamma\vdash a[i]:\mathrm{int}) derived from array/pointer and integer-index premises; one small grammar/AST production | Why parsing alone cannot establish that the subscript and call are meaningful | Rich types and source locations improve optimization/diagnostics but enlarge front-end complexity and compile-time state |
| Ch. 4 | CFG (G=(V,E)); dominance; SSA single-definition property; edge semantics of (\phi); GEP address equation (p+i\cdot\mathrm{sizeof}(i32)) | The loop header, backedge, `i`/`acc` recurrence, and `a[i]` address | SSA simplifies sparse analysis but memory and aliasing require additional abstractions; stronger pointer facts enable optimization but create proof obligations |
| Ch. 5 | Forward data-flow fixed point, e.g. (IN_B=\bigwedge_{P\in pred(B)}OUT_P, OUT_B=F_B(IN_B)); transformation condition (\llbracket T(P)\rrbracket\succeq\llbracket P\rrbracket); cost selection among legal candidates | How facts converge around the loop and why a rewrite can be correct yet unprofitable | Precision vs analysis cost; code size/latency/throughput/compile time are competing objectives, not one scalar truth |
| Ch. 6 | Dependence DAG and schedule constraint (s(v)+\ell(v)\le s(w)); liveness equations; interference graph coloring as the idealized register-allocation model | Why independent loads may overlap, why `acc` remains live, why register pressure can cause spills, and why ABI-visible values occupy designated locations | More instruction-level parallelism can increase live ranges; better allocation/scheduling costs compile time and remains target-dependent |
| Ch. 7 | Relocation equation, for example (S+A-P), with every symbol defined; section-to-segment mapping relation | Why the assembler cannot finalize `putint`, how the linker fills the call, and how file regions become mapped process regions | Position independence and late binding improve reuse/deployment flexibility but add indirection, metadata, or range constraints |
| Ch. 8 | Dialect conversion as legalization: a target predicate (L(op)) and a rewrite sequence ending with no illegal operations; explicit type conversion/materialization relation | Why mixed dialects can coexist and how structured reduction gradually becomes buffers, loops, address spaces, and device operations | Preserving abstraction enables domain optimization; each dialect/interface increases integration and semantic maintenance cost; early bufferization exposes alias/lifetime costs |
| Ch. 9 | Pareto rather than single-score optimization; optionally (\arg\min_{Q\equiv P}(C_{run},C_{size},C_{compile})), plus distinction between static and profile distributions | Why PGO, MLGO, superoptimization, and JIT alter decision information rather than source meaning | Larger search and feedback can improve deployed code but consume build/runtime budget and may specialize to the wrong workload |

The semantic-refinement symbol and direction must be defined carefully. For source languages or IRs with undefined behavior, do not claim naïve equality of trace sets. A concise exposition can say that a legal lowering may restrict implementation freedom while preserving every behavior promised for defined source executions. The report need not formalize all LLVM semantics, but it must make the caveat substantive rather than ritual.

### 4.3 Formalism budget

Target **8–12 numbered formal items** across the whole manuscript, normally no more than two in a chapter. This is enough to establish a PL/computation-theory backbone without interrupting tutorial flow. Each item must earn its place by supporting a diagram, a code reading, or a design trade-off. A formula that merely restates prose or computes a test answer should not be numbered.

## 5. Engineering judgment woven into the theory

Each chapter should contain at least one explicit “why not the theoretically cleanest design?” discussion. Suitable tensions are:

- token-level preprocessing is historically composable and fast, but largely unaware of language types;
- a richly structured AST supports precise diagnostics but is not a convenient optimization interchange;
- SSA makes def-use relations explicit, while memory SSA/alias analysis must approximate effects that ordinary SSA cannot name directly;
- optimization correctness is a hard constraint, but cost models decide among correct outputs under uncertain hardware/workloads;
- instruction selection, scheduling, and allocation are coupled NP-hard-style search problems, so production compilers use staged approximations and repair mechanisms;
- an ABI sacrifices locally optimal register/layout choices to make separately compiled code interoperable;
- relocation defers decisions to gain separate compilation and deployment flexibility, at the cost of metadata and sometimes indirection;
- multi-level IR preserves intent longer but moves complexity into dialect semantics, interfaces, legalization, and ownership;
- verified compilation increases assurance for a modeled subset, while broad industrial compilers optimize coverage, extension velocity, debugging, and ecosystem compatibility.

These are not “pros and cons” sidebars. Each should arise exactly where the case forces the choice.

## 6. Visual redesign

The visual system should make transformations and dependencies visible. Current text tables masquerading as flowcharts and the oversized MLIR staircase should be replaced rather than cosmetically restyled.

### 6.1 Visual grammar

Use a consistent vocabulary across all figures:

- **rounded rectangle:** a representation or artifact;
- **solid arrow:** a transformation that commits a decision;
- **dashed arrow:** a relation, observation, or mapping, not an executed stage;
- **small colored tag:** the same source fact (`n`, `i`, `acc`, array address, external call) as it reappears at another layer;
- **upper annotation:** information preserved or newly exposed;
- **lower annotation:** information forgotten or deferred.

Use at most four semantic colors, chosen from a color-vision-safe palette and backed by shape/line style so grayscale remains meaningful. Text in figures must remain at least the manuscript's `\footnotesize` after placement; do not rescue an overfull diagram with an indiscriminate `\resizebox`.

Generate structural graphs from source-controlled descriptions (TikZ or Graphviz/DOT are appropriate). Python may orchestrate deterministic generation and produce PDF/SVG; quantitative plotting libraries should only be used when there are real quantities. There is no reason to introduce a JavaScript stack for static diagrams. Commit editable sources, not only raster screenshots.

### 6.2 Required figure set

| Figure | Question answered | Recommended construction |
|---|---|---|
| **F1. The semantic spine** | Where does the same computation travel, and what is decided at each boundary? | Full-width layered timeline, 7–8 representations, with one recurring `acc`/call thread. This replaces the current tabular pipeline map. |
| **F2. From text to typed structure** | What do preprocessing, parsing, binding, and typing add? | Three-panel small multiple: token excerpt → compact AST → typing judgment, with matching highlights. |
| **F3. The loop as CFG and SSA** | Why do dominance and `phi` exist? | Actual graph generated from DOT/TikZ; source lines attached to blocks; incoming `i` and `acc` values shown on edges. This is the central pedagogical figure. |
| **F4. Optimization has two gates** | Why is “equivalent” not the same as “worthwhile”? | Before/after IR shapes passing first through a legality gate and then a profitability gate; annotate alias/range facts and code-size/register-pressure costs. |
| **F5. Backend constraint stack** | How do selection, scheduling, allocation, and ABI interact? | Four aligned small multiples of the same operations: IR DAG → selected instructions → scheduled order/live intervals → physical registers/frame. |
| **F6. One call from symbol to process** | How does `putint` move from an unresolved name to executable memory? | Object-section blocks + symbol/relocation card + final segments/process map; label (S,A,P) directly. This replaces text-only assembler/linker diagrams. |
| **F7. Progressive lowering without a fake staircase** | What information does each MLIR representation preserve, and where can dialects coexist? | Sankey-like or layered mixed-dialect view for structured reduction → buffers/loops → HIVM/device memory → LLVM/object, with explicit side branch for host code. |
| **F8. Closing ledger (optional)** | What was preserved, committed, and deferred across all layers? | Compact matrix or radial summary that reuses F1's visual tokens; no new concepts. |

Each figure caption should state the inference the reader should take away, not merely enumerate boxes. Every figure must be introduced in the prose before it appears and interpreted afterward.

### 6.3 Tables and listings

Tables remain useful for genuinely two-dimensional comparisons: source feature versus later mechanism, ABI register roles, and section versus segment. Do not use a table to simulate time, flow, containment, or a graph.

- Show the complete SysY program once.
- All later listings should normally be 6–14 lines and isolate one idea.
- Use consistent highlighting to connect source/IR/assembly fragments.
- Move long command lines and raw tool output to the companion README or appendix.
- Avoid consecutive pages dominated by listings/tables; after every dense artifact, include explanatory prose or a visual interpretation.

## 7. Cut, merge, retain, and move

### 7.1 Cut from the main narrative

- the introduction's evidence-level taxonomy and its table;
- the standalone validation chapter and its four-layer methodology;
- “observed/inferred/assumed/recommended” labels in ordinary exposition;
- repeated statements that six cases do not constitute a proof;
- exact stdout/stderr byte policies and the runtime timer line;
- repeated tool-version and command-recording advice;
- P1–P5 frontier maturity ratings and the “what would falsify this” column;
- reproducible-build and incremental-build material unless reduced to a brief future systems concern directly tied to compiler artifacts;
- detailed plans for experiments not performed;
- multiple near-identical tables that map the same source feature to stages.

### 7.2 Merge

- target backend and RISC-V instruction/ABI chapters;
- assembler/ELF and linker/loader chapters;
- finite execution checks into the end of the object-to-process journey;
- frontier material into four design tensions, followed immediately by the philosophical synthesis.

### 7.3 Retain in the main narrative

- one precise semantic definition and the value-range argument;
- one honest paragraph on SysY versus the C observation form;
- representative AST, IR, assembly, symbol, relocation, and segment excerpts;
- one executable-trace statement satisfying the assignment;
- primary references for language/IR/ABI/object-format semantics;
- MLIR/Ascend content as an outlook grounded in the official VecAdd boundary;
- the conclusion's existing principles, revised to echo the new formal and visual spine.

### 7.4 Move to repository documentation or appendix

- build presets and full commands;
- file-name inventories;
- the complete six-input/four-form matrix;
- exact runtime diagnostics;
- environment and version manifests;
- full hand-authored IR and assembly when the body already contains curated excerpts;
- diagnostic mutations and extra object-inspection output beyond the one pedagogical trace.

## 8. Prose discipline

Depth is not the same as accumulation. Apply these paragraph-level rules:

1. A paragraph should make one claim, show one mechanism or example, and state its consequence.
2. Prefer causal verbs: “because,” “therefore,” “forces,” “permits,” and “defers.” Reduce inventory verbs such as “includes,” “supports,” and “also has.”
3. Introduce a term only when the case immediately needs it; define uncommon Chinese technical terms with the English name once.
4. Do not stack papers. A citation should support a specific mechanism, historical claim, or result. Survey multiple works only after giving the organizing idea.
5. Avoid defensive phrases (“we do not claim,” “this does not prove”) unless a plausible misreading would materially change the conclusion.
6. End each core chapter with a conceptual handoff, not a validation disclaimer or a list of commands.
7. Use short boxed “engineering lens” passages sparingly—at most one per core chapter—to make a trade-off memorable.

The desired tone is confident but calibrated: explain what established compiler theory says, show how production designs approximate it, and name a limitation when it is causally relevant.

## 9. Acceptance gates

These gates are intentionally observable so an editor and reviewer can agree whether the revision succeeded.

### 9.1 Narrative and scope gates

- [ ] The abstract describes a survey/tutorial, the cross-layer journey, major mechanisms, and principles; it does not mention test counts, evidence levels, reproducibility, or a runtime-library incident.
- [ ] The introduction contains no evidence taxonomy and poses questions about representations, semantics, decisions, and engineering trade-offs.
- [ ] There is no standalone validation/reproducibility chapter.
- [ ] The clipped dot product is the only algorithmic case and appears substantively in every core chapter (3–8), not merely in the opening sentence.
- [ ] Each core chapter answers “meaning, representation, choice” and ends by motivating the next abstraction boundary.
- [ ] The body contains at most one input/output table and at most two paragraphs whose primary purpose is reporting test execution.
- [ ] Exact build commands, stderr strings, artifact paths, and tool-version manifests do not interrupt the main exposition.
- [ ] Basic assignment material occupies the clear majority of the body; advanced MLIR/frontier outlook together occupies roughly 20–30%, not half the article.
- [ ] The course requirements can be mapped to a chapter and concrete artifact without relying on a validation chapter.

### 9.2 Formal and explanatory gates

- [ ] The manuscript contains 8–12 meaningful numbered formal items covering source meaning, typing, CFG/SSA, data flow or transformation correctness, backend constraints, relocation, and progressive lowering.
- [ ] Every formal item defines its symbols and is instantiated on the clipped-dot-product case within two paragraphs.
- [ ] Every core technical chapter states at least one real engineering trade-off produced by the formal model.
- [ ] The report explicitly distinguishes transformation legality from profitability and illustrates both on the same optimization.
- [ ] The report explains dominance/SSA, a data-flow fixed point, liveness/interference, and relocation with more precision than a prose definition.
- [ ] Undefined behavior/poison and aliasing are discussed only where they affect a concrete legal transformation or representation contract.
- [ ] No equation exists solely to decorate a claim already stated more clearly in prose.

### 9.3 Visual gates

- [ ] The body contains at least six purpose-built vector figures, including the semantic spine, typed-front-end view, CFG/SSA graph, backend constraint view, symbol-to-process trace, and MLIR lowering view.
- [ ] No `tabular` environment is used as the main content of a figure, and no process/flow figure is a row of text boxes without semantic annotations.
- [ ] Figure text remains legible at 100% page scale and does not rely on color alone.
- [ ] Every figure has an editable source and deterministic generation path, or is directly authored in maintainable TikZ.
- [ ] Every figure is cited before placement and its caption states the conceptual takeaway.
- [ ] The rendered PDF has no clipped labels, crossing arrows through text, illegible resize scaling, or figures stranded from their explanatory paragraph.

### 9.4 Precision and concision gates

- [ ] A search for `证据|验证|核验|可复现|预言机|实验` shows a substantial reduction from the current baseline of about 167 matches; remaining uses are locally necessary rather than a recurring rhetorical frame. A practical target is fewer than 45 total, excluding bibliography and repository appendix material.
- [ ] No concept is defined from scratch in more than one chapter; later uses link back and deepen it.
- [ ] No raw output/listing other than the full source exceeds about 14 lines without a specific line-by-line reading.
- [ ] The frontier chapter is shorter than each of the LLVM and backend chapters and is organized by tensions rather than a technology inventory.
- [ ] The revised body is materially shorter than the current one even after adding formal explanations. A useful target is a 20–30% reduction in body prose, with space reinvested in figures and derivations rather than a hard page limit.
- [ ] Citation clusters do not substitute for synthesis: every multi-source paragraph has an explicit comparison or causal connection.

### 9.5 Assignment and production gates

- [ ] The title, abstract, keywords, introduction, work/results, conclusion, references, and two-person contribution statement remain present.
- [ ] Preprocessor, compiler internal stages, assembler, and linker are all explained.
- [ ] The SysY program covers arithmetic, assignment, conditions, loops, functions, arrays, and runtime calls.
- [ ] Equivalent complete LLVM IR and RV64 assembly remain repository artifacts and are represented accurately in the paper.
- [ ] Linking to the SysY runtime and successful output checking are stated once with enough information to satisfy the assignment.
- [ ] MLIR progressive lowering and the AscendNPU IR VecAdd material remain clearly identified as an advanced outlook.
- [ ] LLNCS builds cleanly; citations and cross-references resolve; all pages are visually reviewed after figure replacement.

## 10. Recommended revision sequence

1. **Rewrite the abstract and introduction first.** They establish whether the paper is a tutorial or an evidence report.
2. **Delete/move before adding.** Remove the standalone validation chapter, evidence taxonomy, repeated caveats, and command/output details so they do not influence new prose.
3. **Build F1 and F3.** The semantic spine and CFG/SSA figure force the narrative and notation to become coherent.
4. **Rewrite Chapters 2–5 around the formal backbone.** These chapters establish the language/PL theory needed downstream.
5. **Merge and rewrite the backend and binary journey.** Follow one computation and one call rather than surveying every mechanism.
6. **Replace the MLIR visual and compress the frontier chapter.** Make them consequences of the abstraction story, not separate literature piles.
7. **Rewrite the conclusion from the new chapters.** Retain the existing philosophical strength, but make every principle something the reader has already experienced.
8. **Run the acceptance gates, then render every page.** Page-level visual review is essential because the requested improvement is not detectable from a successful LaTeX build alone.

## 11. External anchors for editors

These sources support the editorial and conceptual direction; they are not a mandate to quote their wording.

- Bryant and O'Hallaron, **CS:APP: A Programmer's Perspective**: the official description frames systems through their effect on program behavior rather than builder-only component catalogues: <https://csapp.cs.cmu.edu/3e/perspective.html>.
- LLVM, **Language Reference Manual**: authoritative semantics for `phi`, `getelementptr`, poison, attributes, and other IR constructs: <https://llvm.org/docs/LangRef.html>.
- LLVM, **The Often Misunderstood GEP Instruction**: focused semantic clarification for the address calculation used in the case: <https://llvm.org/docs/GetElementPtr.html>.
- MLIR, **Dialect Conversion**: the operational meaning of legal, dynamically legal, illegal, partial/full conversion, type conversion, and materialization: <https://mlir.llvm.org/docs/DialectConversion/>.
- MLIR, **LLVM IR Target**: why lowering to LLVM is staged through the LLVM dialect and how progressive conversion accommodates mixed representations: <https://mlir.llvm.org/docs/TargetLLVMIR/>.

## 12. One-sentence editorial test

For any paragraph, table, formula, or figure, ask:

> Does this help the reader see how one fact in the program becomes a new representation or engineering decision?

If the answer is “it mainly proves that we ran a command carefully,” move it out of the survey. If the answer is “it names several technologies,” reorganize it around a shared design tension. If the answer is “it makes a mechanism, invariant, or trade-off visible,” keep it and connect it to the next layer.
