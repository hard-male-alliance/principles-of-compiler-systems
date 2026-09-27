# Narrative Audit of the Compiler-Systems Survey

## Purpose and verdict

This is an editorial audit of the current 55-page LLNCS report against the
author's revised intent: a CSAPP-style survey that uses one example to explain
compiler systems, not an artifact-evaluation paper that uses the example to
establish empirical claims. It does **not** propose changes to the companion
code and does not edit the manuscript.

The report contains enough technically strong material for an excellent
survey. Its central idea---a compiler as a succession of representation
contracts---is sound, and several passages already achieve the desired
"point at the object and explain what it is" style. The current manuscript,
however, is governed by the wrong editorial question. Too often it asks:

> What evidence permits us to say this without overclaiming?

The survey should normally ask:

> What meaning is represented here, why is it represented this way, what
> choice becomes possible, and what information or freedom is lost?

That distinction is not cosmetic. It changes the chapter architecture, the
choice of mathematics, the figures, and the amount of implementation detail.
At present, epistemic disclaimers, validation plumbing, tool versions, and
artifact inventories frequently displace explanation of compiler design.

**Editorial verdict:** retain the case, the cross-layer scope, and the best
mechanistic passages; remove the evidence taxonomy as a narrative device;
move almost all reproducibility material to a short appendix/companion README;
install a modest formal spine across the main chapters; replace table-heavy
"coverage" with a small visual system; and use the philosophical principles
from the conclusion as chapter-level organizing claims rather than saving them
for the end.

## Quantitative diagnosis

The counts below come from the current `report/sections/*.tex` sources. They
are indicators, not a semantic classifier, but the concentration is strong
enough to confirm the reader's complaint.

### Evidence-language concentration

The audit counted occurrences of this cluster:
`evidence/validation/reproducibility/reproduce/experiment/test/observe/
measurement/artifact/script/log/oracle/observation/proof` in Chinese, including
the manuscript's `\observed` and `\inferred` vocabulary. Approximate prose
character counts exclude code/verbatim blocks and much LaTeX markup.

| Section | Approx. prose chars | Evidence-cluster hits | Prose paragraphs | Paragraphs with cluster |
|---|---:|---:|---:|---:|
| 1 Introduction | 2,352 | 27 | 10 | 7 (70%) |
| 2 Case study | 2,884 | 33 | 14 | 9 (64%) |
| 3 Frontend | 4,283 | 18 | 17 | 5 (29%) |
| 4 LLVM IR | 3,935 | 19 | 17 | 7 (41%) |
| 5 Optimization | 3,573 | 26 | 16 | 10 (63%) |
| 6 Backend | 4,507 | 18 | 23 | 8 (35%) |
| 7 RISC-V | 3,071 | 8 | 17 | 4 (24%) |
| 8 Assembler/ELF | 2,795 | 8 | 14 | 4 (29%) |
| 9 Linker/loader | 3,596 | 35 | 20 | 9 (45%) |
| 10 Validation | 4,141 | 69 | 10 | 10 (100%) |
| 11 MLIR/Ascend | 4,716 | 13 | 20 | 8 (40%) |
| 12 Frontiers | 6,765 | 73 | 28 | 23 (82%) |
| 13 Conclusion | 1,586 | 18 | 5 | 3 (60%) |

Additional symptoms:

- `\observed` appears 20 times and `\inferred` 5 times as explicit prose
  labels.
- “observation carrier” appears 13 times; “oracle” appears 13 times.
- Variants of “does not prove/cannot prove/not a proof” occur at least 28
  times.
- Tool versions are mentioned as a rhetorical qualification at least seven
  times, independently of the environment table.
- The six-input oracle or its results are restated in Sections 2, 7, 9, and
  10, then alluded to again in Sections 1, 4, 11, and 13.
- The distinction among normative SysY, the C carrier, generated artifacts,
  and handwritten artifacts is introduced in Sections 1 and 2, repeated at
  the start of Section 3, and explained again in Section 10.
- Evidence taxonomies occur in Section 1, are reintroduced in Section 5, and
  are introduced a third time in Section 10. Section 11 opens with yet another
  three-way evidence classification.

The main visual imbalance is equally clear:

| Device | Count |
|---|---:|
| Figures | 4 |
| Tables | 25 |
| Listing/verbatim blocks | 28 |

Thus a 55-page systems survey has only four figures, while tables outnumber
figures by more than six to one. Moreover, three of the four figures are
essentially text arranged in a framed box or `tabular`; only the MLIR figure
uses a real diagram grammar. This is why the document feels like an audit
report even when the prose is good.

## What already works and should become the model

The critique should not cause a wholesale rewrite into a shallower tutorial.
Several passages are excellent counterexamples to the manuscript's dominant
mode and should define the new voice.

1. **The opening paragraph of Section 1.** The questions about why macros do
   not become AST nodes, when locals cease to denote memory, and how unresolved
   calls can already be encoded are concrete, layered, and intellectually
   inviting. This is CSAPP-style exposition.
2. **The per-term clipping versus saturating accumulation counterexample in
   Section 2.** It connects a tiny source-level distinction to associativity,
   vectorization legality, and parallel reduction. This is exactly the desired
   combination of mathematics and engineering consequence.
3. **The SSA loop explanation in Section 4.** Explaining `phi` as edge-indexed
   selection rather than sequential assignment is precise and pedagogically
   important. It needs a real CFG and one formal recurrence, not more evidence
   disclaimers.
4. **The pointer-induction transformation in Section 6.** The move from source
   index, through `sext+GEP`, to two advancing pointers plus an end pointer is
   the strongest “look at this object” example in the backend chapters.
5. **The two parallel data paths in Section 7.** Distinguishing 64-bit address
   arithmetic from 32-bit SysY values explains `add` versus `addw` and `lw`
   mechanistically rather than as an instruction catalogue.
6. **Relocation as a typed deferred expression in Section 8.** This is a real
   systems principle: unknown information is not zero-filled and forgotten;
   it is retained in a form the next stage can resolve and optimize.
7. **Bufferization as the transition from value equivalence to storage
   identity in Section 11.** This is a deep PL/systems explanation and already
   states the important engineering tradeoff: lower too early and aliasing,
   ownership, and allocation constrain optimization.
8. **The conclusion's principles.** “Stages are semantic responsibilities,
   not process boundaries,” “machine code still contains deferred decisions,”
   and “lower an abstraction only after its last beneficiary” are much more
   memorable than the evidence labels. They should be previewed and developed
   throughout the paper.

These passages share a pattern: concrete object, conceptual distinction,
mechanism, consequence. The revision should replicate this pattern.

## The central architectural correction

### Replace the evidence spine with a representation-and-decision spine

The report should adopt one thesis and three recurring questions:

> A compiler is a sequence of representation decisions that preserve required
> meaning while making some facts explicit, discarding others, and deferring
> choices until enough information is available.

At each layer ask:

1. **Meaning:** What observable or semantic relation must be preserved?
2. **Information:** Which facts become explicit, and which source distinctions
   are intentionally forgotten?
3. **Decision:** What choice is enabled here, what remains deferred, and what
   engineering cost constrains the theoretically ideal choice?

Evidence is still needed when the manuscript makes a factual claim about LLVM,
RISC-V, ELF, or Ascend. It should be handled by ordinary citations and precise
wording, not promoted into a repeated chapter-level ontology.

### Install one modest formal spine

The paper currently contains arithmetic formulas for the case and a behavioral
refinement formula only in the frontier chapter. This is backwards: the formal
relation that explains compilation should appear near the beginning, then be
specialized where useful.

Let (R_i) be a representation domain, (T_i:R_i\to R_{i+1}) a compiler
transformation, and (\llbracket\cdot\rrbracket_i) an interpretation into
observable behaviors. The core obligation is a refinement relation

\[
  \llbracket T_i(r)\rrbracket_{i+1}
  \preceq
  \llbracket r\rrbracket_i.
\]

Equality is often too strong because source and target may have nondeterminism,
undefined behavior, or additional internal steps. The exact direction should
be explained once. This single equation unifies type checking, optimization,
instruction selection, ABI lowering, linking, and progressive lowering far
better than a hierarchy of evidence labels.

The formalism should remain proportional. Each core chapter needs one or two
formal objects, not a proof assistant transcript:

- **Frontend:** one grammar fragment plus typing judgments such as
  (\Gamma\vdash a:i32^*\), (\Gamma\vdash i:i32), and
  (\Gamma\vdash a[i]:i32\;\mathsf{lvalue}), followed by the lvalue-to-rvalue
  transition required by multiplication.
- **SSA/CFG:** define predecessors and dominance; give the loop recurrence
  (i_{t+1}=i_t+1), (acc_{t+1}=acc_t+clip(a_{i_t}b_{i_t})), and the invariant
  (acc_t=\sum_{j<t}clip(a_jb_j)). The two `phi` inputs then become inevitable,
  not merely a syntax fact.
- **Optimization:** separate legality
  (\llbracket P'\rrbracket\preceq\llbracket P\rrbracket) from profitability
  (C(P',\tau)<C(P,\tau)). Show one rewrite with explicit side conditions.
  For example, replacing a branch with a `select` is only semantics-preserving
  when evaluating both candidate expressions introduces no forbidden effects.
- **Backend:** formulate instruction selection as minimum-cost covering under
  legal patterns; scheduling as a precedence/resource-constrained ordering;
  register allocation as coloring an interference graph with spill choices.
  The manuscript need not solve these optimally; it should explain why real
  compilers use heuristics and why the objectives conflict.
- **Assembler/linker:** display representative relocation equations such as
  (S+A-P), then show how a logical value is split into RISC-V high/low
  immediate fields. This is the right mathematics for the chapter.
- **MLIR:** define a legality predicate (L(op)) and explain conversion as a
  typed graph rewrite that must remove all illegal operations at a full
  conversion boundary. Bufferization should expose an alias relation and a
  cost (allocation/copy) rather than remain entirely verbal.

### Use a stable chapter micro-structure

Each main technical chapter should follow:

1. a concrete snapshot of the same case;
2. the minimum formal model needed to interpret it;
3. how a production compiler approximates or realizes that model;
4. one engineering tradeoff or failure mode;
5. what decision is committed and what remains for the next layer.

This is both more rigorous and more concise than the current cycle of artifact,
qualification, validation limitation, and suggested future experiment.

## Section-by-section cut and rewrite plan

### Section 1 — Introduction

**Keep:** the opening paragraph, the representation-contract thesis, and the
driver/action/job distinction.

**Cut or replace:**

- Delete Table 1 (the evidence hierarchy) and all later dependence on
  `\observed`/`\inferred` labels.
- Replace the third research question about strength of evidence with the
  central semantic/design question: what each representation preserves,
  exposes, erases, or defers.
- Compress the paragraph distinguishing four artifact identities to two
  sentences and refer technical details to the companion artifact.
- Rewrite the contribution list. Items about the oracle and calibrating
  equivalence currently sound like a validation paper. The contribution is an
  integrated explanatory model, not a test methodology.

**Add:** the representation/refinement equation and a visual “three questions
per boundary” legend. Preview the strongest principles from Section 13 here.

### Section 2 — Case study and journey map

**Keep:** the source, mathematical definition, range bound, and especially the
per-term-clipping counterexample.

**Cut or move:**

- The prefix sums need appear once, not as an oracle that returns in multiple
  chapters.
- Compress “four identities” to a marginal note or short source-note.
- Remove the entire “behavior oracle” subsection from the main narrative;
  stdout/stderr byte checks belong in the companion appendix.
- Remove the final paragraph that again distinguishes structural and behavioral
  validation.

**Rewrite:** replace the framed text pipeline (`fbox` + `minipage` + arrows),
the feature-payoff table, and much of the cross-layer table with one flagship
multi-lane figure. The figure should track four colored facts across layers:

1. bounded length (n\mapsto k);
2. array element identity/address;
3. loop-carried accumulator;
4. external call `getint`.

Rows are facts; columns are source, AST, LLVM, RV64, ELF, process. Solid arrows
mean compiler transformation, dashed arrows mean explanatory correspondence,
and small “commit/defer” glyphs mark responsibility boundaries. This single
visual can serve as the paper's navigation map.

### Section 3 — Frontend

**Keep:** translation phases versus fused implementation; `-8` as operator plus
literal; the AST shape; Sema's name/type/value-category responsibilities.

**Cut or move:**

- Delete the command block for `-E`, `-dM`, and token dumps from the main text.
- Delete the include-search reproducibility aside.
- Reduce the detailed inventory of differences between SysY and the C carrier
  to one explicit footnote.
- Compress the diagnostic mutation experiment and remove instructions about
  saving tool versions and exit text.

**Add:** a small formal grammar/typing derivation for `a[i] * b[i]` and a visual
small multiple: raw source tokens -> compact AST -> typing annotations. The
formal judgment explains why the AST is more than a parse tree. This is a major
missing PL connection.

### Section 4 — LLVM IR

**Keep:** representation hierarchy, the CFG and `phi` explanation, GEP versus
load, and the treatment of poison/`freeze`.

**Cut or compress:**

- The exact LLVM 18 `nocapture` spelling and warning against rolling
  documentation are artifact-maintenance details.
- The six-row attribute catalogue is broader than the case needs. Keep
  `readonly`, `inbounds`, and `nsw`, because they support the main thesis that
  annotations enlarge the optimizer's legal world.
- Delete the closing validation taxonomy. State once that the verifier checks
  well-formedness, not source equivalence, and move on.

**Add:** a real CFG figure with blocks, back edge, dominance, and edge labels
feeding the two `phi` nodes. Put the loop invariant beside it. This should be a
central theoretical figure, not the current monospaced text sketch.

### Section 5 — Optimization

This section needs a structural rewrite rather than local trimming.

**Delete:** the evidence-grading subsection, the detailed endpoint-attribution
caveat, and “a reproducible causal experiment route.” The command recipe is
useful in a lab manual, not in the main survey.

**Reorganize around two questions:**

1. **Is the rewrite legal?** Use dominance, alias/effect information, overflow
   assumptions, and the clipping/range invariant.
2. **Is the rewrite profitable on this target?** Use vector width, trip count,
   remainder cost, and the absence of RVV in RV64GC.

Keep one before/after view of stack-form IR and SSA/vector form. Explain a
causal chain, but do not litigate which named pass owns every change. Introduce
the legality/profitability equations and a diagram whose horizontal axis is
semantic freedom and vertical axis is target cost. The important engineering
lesson is that canonicalization makes opportunities recognizable while target
cost determines whether they are realized.

### Section 6 — Backend

**Keep:** the pointer-induction example, the ABI-aware elimination of moves,
the distinction between saving `ra` and spilling, and the latency/register
pressure tradeoff.

**Cut or compress:**

- Remove the repeated caveats about not knowing whether SelectionDAG or
  GlobalISel ran. Explain both frameworks once as alternative implementations.
- Remove requests for MIR logs, scheduler logs, and `llvm-mca` evidence.
- Delete the final “what we know/cannot know” evidence table.
- Reduce the MC-layer discussion to the one transition needed by Section 8.

**Add:** three compact formal models: pattern-cover cost for selection,
precedence constraints for scheduling, and graph-color constraints for
allocation. A triangular visual should show the real conflict among latency,
register pressure, and code size. This is where theory/engineering tradeoffs
belong.

### Section 7 — RISC-V

This material is strong but partly duplicates Section 6. Either merge it into
Section 6 as “concretizing the backend,” or make the boundary explicit:
Section 6 is the compiler's constrained search; Section 7 is the architectural
contract it must satisfy.

**Keep:** ISA versus ABI, 64-bit addresses versus 32-bit values, pseudo-
instructions, register ownership, and the leaf/non-leaf contrast.

**Cut:** repeated references to the hand-written implementation as a validated
artifact and the repeated numeric oracle. The exact 80-byte frame can remain
as a concrete layout example, but it should be shown visually.

**Add:** a register-role strip and stack-frame diagram. Color address values
and i32 values differently through the instruction snippet.

### Section 8 — Assembler and ELF

**Keep:** the two-pass dependency model (carefully labeled conceptual), symbols
as multidimensional records, and relocation as typed deferred computation.

**Cut or move:**

- Exact object sizes, section counts, and symbol counts are artifact inventory.
- Remove `\observed` prefixes and the claim-by-claim audit language.
- The tool comparison table belongs in an appendix/README.

**Add:** the relocation equation and a bit-field diagram for a RISC-V PC-
relative pair. Replace the present `tabular` “figure” with an actual layered
object-file view: assembly expression -> symbol/addend/type -> relocation
record -> linked instruction bits.

### Section 9 — Linker, runtime, loader

**Keep:** the dependency ordering of archive extraction, layout, relocation,
and relaxation; sections versus segments; `_start`/CRT/`main`; and the principle
of progressively committing information.

**Compress heavily:** the Newlib/glibc `_impure_ptr` story is a vivid concrete
counterexample to “same ISA means compatible,” but it needs one sidebar, not a
mini incident report plus a repeated validation discussion. Remove the entire
“validation loop and evidence strength” subsection.

**Add:** a left-to-right visual showing `.o`/archive -> symbol graph -> output
sections -> program segments -> virtual-memory map -> `_start` -> `main`.
Overlay where addresses become known. This would replace several prose lists
and the section/segment table.

### Section 10 — Validation

This is the clearest mismatch with the revised purpose. It is 4,141 prose
characters, every prose paragraph contains evidence language, and it repeats
the oracle, artifact identities, ELF facts, runtime incompatibility, and formal
verification caveats already introduced elsewhere.

**Recommendation:** remove it as a numbered main chapter. Preserve a 1--2 page
unnumbered appendix, “Companion artifact and how to reproduce the snapshots,”
containing only:

- the build entry point;
- the four forms and six inputs in one compact matrix;
- the environment/toolchain boundary;
- a pointer to the checked-in preflight README.

Delete the file-size table, full environment table, eight-item reproducibility
checklist, and long epistemology discussion. Translation validation belongs in
the optimization/frontier discussion, not in an experiment report chapter.

### Section 11 — MLIR and Ascend

**Keep:** dialects as namespaces rather than stages; interfaces as reusable
capability contracts; legality-driven conversion; bufferization as value-to-
storage transition; and the cautious connection to Ascend HIVM.

**Cut:** the opening evidence classification and the five-item validation plan
at the end. Replace “unexecuted outlook” disclaimers with one scope sentence.

**Add:** formalize legality as a predicate over operations and full conversion
as elimination of illegal nodes. Draw the point case as a mixed-dialect graph
at two moments, not merely a left-to-right list of dialect names. The existing
TikZ figure is the best figure in the report, but it still depicts boxes rather
than showing how operations coexist.

### Section 12 — Frontiers

The four-loop organizing idea is better than a bare list, but the execution is
still literature stacking. Thirty citation keys, nine technology families,
and repeated maturity/falsification clauses make the section read like a
technology landscape memo. The P1--P5 maturity grades are especially risky:
the rubric is only loosely defined, the scores are not derived, and their
numeric appearance implies more precision than the sources support.

**Delete:** all P1--P5 ratings and the maturity table. Do not replace them with
another large comparison table.

**Condense around three conceptual axes:**

1. how the legal transformation space is defined or checked;
2. how a candidate is selected under a cost model;
3. when runtime/deployment information becomes available.

Use five representative directions, not a catalogue of every named technique:
verified/validated compilation; equality-saturation or superoptimization as
search; PGO/MLGO as empirical cost modeling; MLIR/heterogeneous scheduling as
information preservation; JIT/LTO as timing and visibility. Incremental and
reproducible builds can receive a brief systems sidebar if required by the
course specification.

The section's synthesis paragraphs are stronger than its surveys of individual
tools. Move the core connections forward and make named systems examples of a
principle, not parallel mini literature reviews.

### Section 13 — Conclusion

**Keep almost all five principles.** They are the most coherent intellectual
product in the report.

**Revise principle 4:** change “running is the start of an evidence chain” to a
more central PL/systems principle: correctness is relational and cross-layer,
not a property that any one artifact possesses in isolation. Examples can
briefly mention tests and validators without returning to the 24-run matrix.

**Cut:** the limitations paragraph's detailed experiment wishlist. It reopens
the artifact-evaluation frame just as the paper should synthesize.

**Add:** one final principle about irreversible information loss or
“abstraction debt”: lowering is valuable because it commits decisions, but
each commitment removes future optimization freedom. This connects the
frontend, LLVM, backend, linker, MLIR, and frontier chapters.

## Visual system proposal

The revision needs a designed figure family, not isolated TikZ experiments.
Use consistent colors and shapes across all figures:

- blue = source/semantic facts;
- violet = compiler IR and analysis facts;
- orange = machine/ABI commitments;
- green = linker/loader state;
- dashed border = decision deferred;
- solid border = decision committed;
- red side-condition marker = semantic precondition.

Recommended figures, in order of priority:

1. **Flagship semantic-thread map** (Section 2): four facts across six layers.
2. **Tokens -> AST -> typing derivation** (Section 3): a three-panel small
   multiple.
3. **Actual SSA CFG with invariant and phi-edge annotations** (Section 4).
4. **Legality versus profitability** (Section 5): one rewrite, side conditions,
   and target-dependent cost.
5. **Backend constraint diagram** (Section 6): selection, scheduling, and
   allocation with latency/pressure/size conflicts.
6. **Register and stack layout** (Section 7).
7. **Relocation lifecycle** (Sections 8--9): expression, record, resolved bits,
   segment, process.
8. **Mixed-dialect MLIR snapshots** (Section 11).
9. **Frontier design-space map** (Section 12): place methods by information
   availability and decision time rather than arbitrary maturity score.

TikZ is sufficient for diagrams that must share typography with LNCS. Graphviz
is preferable for CFGs and dense dependency graphs, exported as PDF/SVG.
Python/Matplotlib should be used only for quantitative plots; it should not be
used to draw box-and-arrow architecture diagrams. Every generated visual must
have a checked-in source and a deterministic build target.

## Redundancy map and deletion targets

The following concepts should have one canonical home:

| Repeated concept | Canonical home | Elsewhere |
|---|---|---|
| Four artifact identities | Short note in Section 2 | Remove from Sections 1, 3, 10 |
| Six-input outputs | Section 2 or appendix, once | Delete repetitions in 7, 9, 10, 13 |
| Test is not proof | One sentence in appendix/frontier | Delete routine disclaimers |
| Observed/inferred taxonomy | Nowhere in main paper | Use citations and direct prose |
| SysY vs C carrier | Section 3 footnote | Do not re-litigate later |
| Newlib vs glibc incident | Section 9 sidebar | Delete repetition in Section 10 |
| Tool versions/commands | Companion appendix/README | Remove from conceptual chapters |
| Formal verification limits | Section 12, concise | Avoid Sections 1, 2, 4, 5, 10, 13 repetitions |

A realistic target is a **20--25% reduction** in main-text prose while adding
formal definitions and figures. This is not an argument for brevity as an end
in itself. The space recovered from repeated epistemic caveats should be spent
on derivations, diagrams, and theory-to-engineering explanations. A main text
around 40--45 pages plus a short companion appendix would likely feel deeper
than the current 55 pages because each page would advance the conceptual model.

## Priority order for revision

1. Remove Section 10 from the numbered narrative and delete evidence labels.
2. Rewrite Sections 1--2 around the representation/refinement thesis and build
   the flagship visual.
3. Rebuild Section 5 around legality versus profitability.
4. Add the formal spine to Sections 3--6 and 8--11.
5. Replace the weakest text/table figures and introduce the visual system.
6. Collapse Section 12 and remove pseudo-quantitative maturity ratings.
7. Perform a global redundancy and compression pass only after the new chapter
   logic is stable.

## Completion criteria for the editorial revision

The revised report should pass the following reader-oriented checks:

- A reader can state the central thesis without using the words evidence,
  validation, or reproducibility.
- Every core chapter contains at least one explicit semantic/design relation
  and one engineering tradeoff.
- The same six-input result table is not reproduced in the main text.
- Tool versions and build commands do not interrupt conceptual chapters.
- The paper contains more explanatory diagrams than audit/checklist tables.
- The legality/profitability distinction is explicit before vectorization is
  discussed.
- SSA, optimization, lowering, and linking each receive an appropriate formal
  object rather than only prose and citations.
- The frontier section synthesizes design dimensions instead of assigning
  unsupported maturity scores to a list of technologies.
- The conclusion's principles are recognizable as claims developed throughout
  the paper, not insights that appear only on the final pages.

If these criteria are met, the report will retain its technical breadth while
changing genres: from a meticulously qualified artifact dossier into a deep,
case-driven survey of how compiler systems turn meaning into progressively
more committed machine reality.
