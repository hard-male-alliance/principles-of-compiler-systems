# Acceptance Map for the LLNCS Survey *Inside a Compiler System*

## 1. Purpose and authority

This document is the product and acceptance specification for the report requested in
[`docs/预备工作-了解你的编译器.md`](../预备工作-了解你的编译器.md). It is not a
design for a compiler implementation or an artifact-evaluation framework. Its purpose is
to make sure that a deep, Chinese, review-style paper covers every course clause while
remaining one coherent reading experience.

Authority, in descending order:

1. The latest user direction: write a deep survey in the manner of *Computer Systems: A
   Programmer's Perspective*; use one case study to integrate all baseline topics;
   treat advanced material as outlook; use `llncs`; do not preserve the rejected
   implementation.
2. The explicit grading, content, report, authorship, and submission clauses in the
   course task.
3. The SysY language and runtime documents in this repository.
4. Primary toolchain, ABI, MLIR, AscendNPU IR, and Springer documentation.

The old, deleted attempt is evidence about what **not** to optimize for. Its extensive
preflight framework, large acceptance bureaucracy, CI-centered story, and many auxiliary
artifacts must not be recreated merely because they once existed. The deliverable is a
paper whose technical statements are backed by a small amount of inspectable evidence,
not an infrastructure project with a paper attached.

## 2. Product decision

### 2.1 Reader and promise

The primary reader is a student who can read a small C-like program but still sees
"compiler" as a black box. The paper promises to make that box inspectable by following
one computation through successive representation contracts:

```text
source characters
  -> preprocessed tokens
  -> typed AST
  -> LLVM IR and its control/data-flow graph
  -> RISC-V assembly
  -> ELF relocatable object
  -> linked executable plus SysY runtime
  -> observable input/output behavior
```

At every boundary the exposition answers the same questions:

1. What representation enters this stage?
2. What facts are established or transformed here?
3. What representation leaves it?
4. Where can the reader see one fact from the case study in that output?
5. What remains unresolved for a later stage?

This recurring lens gives the report a CSAPP-like narrative: point at a concrete byte,
node, instruction, symbol, or relocation and explain both **what it is** and **why that
layer needs it**.

### 2.2 Recommended title and thesis

Chinese title:

> **深入理解编译系统：一个 SysY 程序从源代码到 RISC-V 可执行文件**

Working English title:

> **Inside a Compiler System: Following One SysY Program to a RISC-V Executable**

Central thesis:

> A compiler system is a chain of representation contracts. Each stage preserves the
> program's required behavior while making some decisions explicit and deliberately
> leaving other decisions to the next stage.

The paper is a technical survey anchored by a reproducible instance, not a claim of a
new algorithm or a benchmark study.

### 2.3 Scope choice: one bounded-prefix clipped integer dot product

Use one small program with two fixed integer arrays `a` and `b`, each of length eight.
It reads only a prefix length `n` through `getint`, clamps `n` to `[0,8]`, and calls
`clipped_dot(a, b, n, -8, 12)`. The helper multiplies corresponding elements, clips each
product to `[-8,12]`, accumulates the clipped products, and returns the sum. `main` emits
the result and a newline through `putint` and `putch`. In mathematical form,

\[
  D(n) = \sum_{i=0}^{\operatorname{clamp}(n,0,8)-1}
         \operatorname{clamp}(a_i b_i,-8,12).
\]

The exact two arrays are part of the checked-in semantic fixture. They must be chosen so
the prefix traverses products below the lower clip bound, inside the interval, and above
the upper bound. All raw products and prefix sums must remain within the SysY/C 32-bit
integer range, so the example has no signed-overflow ambiguity. This arithmetic bound is
part of the semantic contract, not an after-the-fact testing assumption.

This is a better expository carrier than either a feature catalogue or several toy
programs:

| Feature in the same program | Later mechanism it exposes |
|---|---|
| fixed array length | macro expansion in the C observation form; constant array layout and bounds reasoning |
| two length-8 arrays | aggregate initialization, array-to-pointer passage, LLVM `getelementptr`, loads, scaled addressing, and alias analysis |
| assignments to `i`, `term`, and `sum` | mutable source variables, `alloca/load/store` at `-O0`, SSA values after optimization |
| count clamp and product clipping | AST condition nodes, CFG branches/merges, comparisons, and branch or select/min/max lowering |
| prefix loop | basic blocks, loop back edge, loop-carried values, `phi` nodes or equivalent SSA block arguments |
| multiplication and reduction addition | typed LLVM operations, RV64 arithmetic, and a possible vectorization/reduction discussion |
| five-argument helper call | function type, pointer/scalar arguments, ABI argument/result registers, prologue/epilogue, possible inlining |
| `getint`, `putint`, `putch` | external declarations, undefined object symbols, call relocations, runtime resolution |

There is one **semantic program**, but two source views may be needed and must be labeled
honestly:

- the normative `.sy` form follows the SysY 2022 language and runtime contracts;
- a mechanically corresponding C observation form may add only the declarations and
  preprocessor directive needed to let Clang expose preprocessing and AST evidence.

They are not two case studies. The report must state the exact syntactic delta and must
not imply that stock Clang is a conforming SysY frontend. Authored LLVM IR and authored
RV64 assembly implement the same semantic contract independently; compiler-generated
IR/assembly are observation aids and must not be misrepresented as handwritten work.

### 2.4 Deliberate exclusions

The two arrays are central to the chosen example rather than optional feature decoration.
Do not add recursion, floating point, structs, heap allocation, global mutation,
exceptions, concurrency, or a second algorithm merely to accumulate features. Do not
turn the paper into:

- a tutorial reproducing the course handout paragraph by paragraph;
- a full survey of every LLVM pass, IR instruction, RISC-V instruction, or ELF field;
- a CMake/GitHub Actions report;
- a runtime-library audit;
- a performance paper based on file size, instruction count, emulator timing, or one run;
- an Ascend hardware result unless that result was actually observed.

These boundaries are important because the course explicitly says repeated examples do
not earn more credit and asks that baseline material already covered in the handout be
concise. Depth comes from cross-layer tracing, not breadth by accumulation.

## 3. Chapter architecture

The mandatory course headings are integrated into a scholarly LNCS structure rather
than reproduced as a checklist. The approximate proportions are guidance, not a page
limit.

| Chapter | Reader question and required substance | Main evidence in the paper |
|---|---|---|
| Front matter | What is studied, by whom, and with what result? | title; authors; affiliation if appropriate; abstract; keywords; an opening two-person contribution statement |
| 1. Introduction | Why is "source in, executable out" too coarse a mental model? What is the paper's one-program method? | compact research questions; representation-contract thesis; scope and target declaration |
| 2. The program and the map of the journey | What exactly must remain invariant while representations change? Why is this one program sufficient? | full numbered SysY listing once; semantic function/domain; feature-to-layer table; one pipeline figure |
| 3. From characters to a typed program | What do preprocessing, lexing, parsing, name/type analysis, and diagnostics each contribute? | a small C/SysY delta; `clang -E` excerpt; selected AST excerpt; one deliberately invalid mutation used only to explain a diagnostic |
| 4. From typed structure to LLVM IR | How do structured control, array indexing, pointer alias uncertainty, and mutable variables become explicit address calculations, CFG, and SSA/data flow? | paired source/IR excerpts; `getelementptr` and load trace; block/edge diagram; `-O0` central reading and a selective optimized comparison; authored IR distinguished from generated IR |
| 5. From LLVM IR to RV64 instructions | Which choices become target-specific, and what is enforced by the ABI? | paired IR/assembly excerpts; register/call/stack explanation; authored and generated assembly clearly labeled |
| 6. From symbolic assembly to a running process | What does the assembler know, what can it not yet know, and what does the linker resolve? | one object-file section/symbol/relocation trace; before/after symbol resolution; runtime-library link command; short loader boundary note |
| 7. Equivalence and one controlled compiler variation | What evidence supports "equivalent" and what changed when one compiler setting changed? | shared input/output table for source/IR/assembly; versions/commands; focused `-O0` versus `-O2` structural comparison with causal explanation |
| 8. Beyond a single-level IR: MLIR and AscendNPU IR | Which abstractions are lost too early in LLVM IR, and how do dialects and progressive lowering change the design space? | VecAdd-based stage map; dialect/operation/type changes; explicit observed/documented/inferred status; environment limitation if any |
| 9. Discussion and limitations | What did the case reveal, and where does it not justify generalization? | target/version/test-scope limits; optimizer-output instability; behavioral tests versus proof; loader/runtime boundary |
| 10. Conclusion | What coherent model should the reader carry away? | direct synthesis of the representation-contract thesis; no new results |
| References | Which external definitions and claims were relied upon? | cited primary/official sources plus any genuinely useful scholarly survey |

### 3.1 Cross-layer trace that must appear

At least one compact table must follow the **same facts** across layers. It should be
based on observed output rather than populated from this specification verbatim.

| Source fact | AST/front end | LLVM IR | RV64/object | Link/runtime |
|---|---|---|---|---|
| `n = clamp(n,0,8)` | typed relational expressions and assignments | `icmp` plus branches or `select` | compare/branch or branchless target sequence | no remaining symbolic dependency |
| `a[i] * b[i]` | two typed array subscripts | index extension, `getelementptr`, two loads, and `mul` | scaled address calculation, loads, and multiply | no external resolution; element addresses are computed at run time from ABI-passed bases |
| `term = clamp(term,-8,12)` | ordered conditional assignments | comparisons with branches or selects; possibly min/max idioms | conditional branches or target branchless sequence | no unresolved external dependency |
| loop-carried `i` and `sum` | assignments in loop body | memory traffic at `-O0`; SSA/`phi` values when promoted | physical registers/spills and a backward branch | internal branch targets are resolved by the assembler; no runtime symbol is needed |
| `clipped_dot(a,b,n,-8,12)` | resolved five-argument function call; arrays decay to addresses | pointer/scalar function type and typed `call`, or inlined body | ABI argument/result registers; `call` or inlined sequence | a remaining call relocation is resolved to the definition; an inlined call site needs none |
| `getint()` | external function declaration | external declaration and typed call | undefined symbol plus call relocation in `.o` | definition selected from SysY runtime; executable can call it |
| output newline | integer argument `10` to `putch` | constant and external call | immediate materialization and ABI call | runtime emits the observable byte |

Exact optimized forms are compiler-version-dependent. Acceptance is based on explaining
the **observed** form, not forcing the compiler to match a predicted instruction pattern.

## 4. Clause-by-clause requirement ledger

Every substantive clause in the course task is mapped below. “Paper” means content that
must be visible in the PDF; “support” means a small artifact that makes the claim
inspectable but need not dominate the narrative; “administrative” means a human action
outside the PDF build.

### 4.1 Administration, score, and collaboration

| ID | Source clause | Chapter or location | Evidence / artifact | Verification criterion |
|---|---|---|---|---|
| ADM-01 | The work is a group assignment worth 5 points: 4 baseline points and 1 advanced point. | opening contribution statement; project checklist | names of both members and one shared final PDF | exactly two contributors are identified; the baseline and outlook together cover the stated 4+1 scope; the paper does not imply a different score model |
| ADM-02 | Determine the two-person group first; cross-class grouping requires TA registration; the group should not later change. | not a technical chapter; optional one-line administrative note outside the scholarly argument | team/TA confirmation retained by students | both authors confirm the registered pairing; if cross-class, TA registration exists; no manuscript machinery is invented for this |
| ADM-03 | Two members submit one jointly completed report. | contribution statement | identical PDF checksum/version for both students | both receive the same final PDF; there is not a separate paper per student |
| ADM-04 | Both members must submit on Xiaoya or cannot be graded. | final submission checklist, not the conclusion | two independent submission confirmations | each member has submitted the identical final PDF; one member's submission is not treated as sufficient |
| ADM-05 | The report begins by clearly stating division of work. | immediately after abstract/keywords (or first clearly visible block after title material) | concrete responsibility statement plus shared responsibilities | names and non-vague responsibilities are visible before the main exposition; both share final verification and writing review |

### 4.2 Baseline requirement 1: the complete language-processing system

| ID | Source clause | Chapter | Evidence / artifact | Verification criterion |
|---|---|---|---|---|
| PIPE-01 | Choose GCC, LLVM/Clang, or another familiar compiler tool as the object of study. | 1 and 2 | explicit choice of Clang/LLVM, target triple, relevant versions | toolchain and target are named once consistently; commands and excerpts come from that recorded family/version |
| PIPE-02 | Study the complete working process of a language-processing system. | 2 through 6 | overview figure with stage inputs/outputs, followed by the case trace | the path includes preprocessing, front end, IR/optimization/backend, assembly, linking, and execution; driver fusion is not mistaken for absence of logical stages |
| PIPE-03 | Explain what the preprocessor does. | 3 | source versus `clang -E` excerpt showing the case's macro; concise explanation of include/conditional expansion and line markers | actual changes are identified; general capabilities not exercised by the case are labeled as such; preprocessing is not confused with parsing |
| PIPE-04 | Explain what the compiler does, including its internal stages. | 3 to 5 | selected token/AST, IR, optimized IR, and assembly observations from the same case | lexing, parsing, semantic analysis, IR generation, optimization, and target code generation each have a distinct input/output or responsibility; text is not merely copied from the handout |
| PIPE-05 | Explain what the assembler does. | 6 | authored/generated `.s` to `.o`; one disassembly plus symbol/relocation excerpt | the paper shows that mnemonics/labels become encoded machine instructions in a relocatable object and that unresolved external addresses can remain as relocations |
| PIPE-06 | Explain what the linker does. | 6 | object before link, link command with SysY runtime, executable after link | the paper follows at least one runtime call symbol from undefined reference/relocation to a resolved executable dependency or statically linked definition; linking is not described as text concatenation |

### 4.3 Baseline requirement 2: SysY, LLVM IR, RISC-V, runtime, and validation

| ID | Source clause | Chapter | Evidence / artifact | Verification criterion |
|---|---|---|---|---|
| LANG-01 | Become familiar with LLVM IR and ARM or RISC-V assembly. | 4 and 5 | readable authored `.ll` and authored RV64 `.S`/`.s`, with small annotated excerpts in the PDF | one target is sufficient; types, blocks, SSA/data flow, calls, registers, branches, stack/ABI, and symbols are explained accurately enough to read the case |
| LANG-02 | Design one SysY example covering numeric operations, assignment, conditional branches, loops, functions, and other useful advanced features. | 2 | canonical `.sy` listing and feature map | the bounded-prefix clipped dot product visibly contains arrays, indexed loads, multiplication/addition, mutable assignments, ordered conditionals, a loop, a five-argument user function, and SysY runtime I/O; optional features are not added without explanatory value |
| LANG-03 | Write LLVM IR equivalent to the SysY source. | 4 and 7 | intentionally authored `.ll`, validation/build command, selected mapping annotations | the authored IR is syntactically valid for the recorded LLVM version and implements the declared semantic function for every shared test; generated IR is separately labeled |
| LANG-04 | Write ARM or RISC-V assembly equivalent to the SysY source. | 5 and 7 | intentionally authored RV64 assembly, assemble command, ABI declaration | the assembly assembles for the stated ISA/ABI, obeys the call/stack/register contract at runtime call sites, and matches the shared oracle |
| LANG-05 | Link the SysY runtime. | 6 and 7 | exact linker-driver command and runtime artifact identity; symbol evidence | the IR-derived and assembly-derived paths both link an architecture-compatible SysY runtime; a host/target mismatch or libc-only substitute is not hidden |
| LANG-06 | Use LLVM/Clang and the assembler to generate target programs. | 4 to 7 | concise commands from `.ll` and `.s` through objects to executables | commands are executable as recorded (modulo documented paths); stage-stopping options are used consistently; the resulting files have the stated target architecture |
| LANG-07 | Verify execution results. | 7 | one shared table containing input, expected output, and actual output for source-reference, authored IR, and authored assembly paths | all three forms are tested on the same cases; stdout and exit status agree with the oracle; failures are not silently omitted |

### 4.4 Advanced requirement: MLIR and AscendNPU IR

| ID | Source clause | Chapter | Evidence / artifact | Verification criterion |
|---|---|---|---|---|
| ADV-01 | Observe the processing of an AI compiler's MLIR middle end. | 8 | VecAdd lowering stage diagram/table and, when feasible, captured IR snapshots | the text distinguishes an actually run observation from documentation-based reconstruction; “observe” is not claimed when only a diagram was read |
| ADV-02 | Contrast single-level LLVM IR with MLIR dialects and progressive lowering. | 8 | conceptual comparison grounded in official LLVM/MLIR material | the contrast is nuanced: LLVM has many compiler representations and passes, while MLIR specifically provides an extensible dialect framework capable of retaining multiple abstraction levels; it must not say LLVM is literally only one internal representation everywhere |
| ADV-03 | Explain that AscendNPU IR is Huawei's MLIR-ecosystem hardware-abstraction layer whose dialects participate in the middle end. | 8 | an Ascend-specific box separated from generic MLIR mechanisms | general notions (operation, dialect, rewrite/conversion, legality, type conversion) are not attributed to Ascend; Ascend-specific dialect/tool claims are sourced to its official documentation |
| ADV-04 | Follow the official AscendNPU IR VecAdd quick start. | 8 | version/date, commands attempted, stage/output names, and short result or failure record | the named example is VecAdd; the report does not silently substitute an unrelated local MLIR example while claiming to reproduce the Ascend path |
| ADV-05 | Explore the successive lowering process. | 8 | a stage mapping that states which operations/types/abstractions disappear or become concrete | at least two materially different levels are compared; each transition names the relevant pass/pipeline when known; “lowering” is explained as a semantic change in representation rather than cosmetic syntax rewriting |
| ADV-06 | If environment setup is difficult, read documentation, understand dialect differences, and record the exploration. | 8 and limitations | failing command/diagnostic and environment boundary if an attempt was made; documentation-based continuation clearly marked | lack of CANN/NPU/tool support is reported honestly; the section still contains substantive, cited dialect/lowering analysis and a precise next reproducible step |
| ADV-07 | Advanced work is worth 1 point and may be treated as outlook under the latest user direction. | abstract, 8, conclusion | scope sentence | MLIR is present but does not interrupt the source-to-executable baseline thread; the abstract/conclusion do not overstate documentation-only material as experimental success |

### 4.5 Example method, scientific report, and formatting

| ID | Source clause | Chapter or location | Evidence / artifact | Verification criterion |
|---|---|---|---|---|
| REP-01 | Use a simple C/C++ source example such as factorial or Fibonacci. | 2 and 3 | the small corresponding C observation form of the same reduction case | there is one compact, readable program; factorial/Fibonacci are examples, not mandatory algorithms; the C/SysY relationship is explicit |
| REP-02 | Complete one example; multiple repetitive examples earn no more credit. | whole paper | one canonical semantic contract and no second algorithm | every baseline chapter points back to the bounded-prefix clipped dot product; input cases and invalid mutations are observations of that case, not new case studies |
| REP-03 | Use compiler command-line options to obtain each stage's output. | 3 through 6; reproducibility note | concise command table and selected generated files | each major observation identifies the command/option that produced it; commands are not dumped into the prose without interpretation |
| REP-04 | Study the relationship between outputs and source. | 3 through 7 | paired excerpts and the cross-layer trace table | every selected artifact excerpt is tied to a source construct; merely listing files or definitions does not pass |
| REP-05 | Write a report conforming to scientific-paper conventions. | entire document | consistent terminology, numbered/captioned figures and tables, citations, evidence/status language | claims distinguish observed, inferred, documentation-derived, and recommended statements; figures/tables are referenced in prose; sources are attributed |
| REP-06 | Include at least title, abstract, keywords, introduction, work/results, conclusion, and references. | front matter; 1; 2--9; 10; references | compiled table of contents/visual inspection | every named component exists; “work and results” may be distributed across the case chapters but contains actual observations and validation |
| REP-07 | Text, figures, and tables follow formatting norms. | entire PDF | LLNCS mechanisms; vector or high-resolution figures; readable listings/tables | captions and labels are correct; tables do not overflow; fonts/glyphs are embedded; all material remains readable at normal zoom and in grayscale where color is nonessential |
| REP-08 | Submit a PDF; LaTeX is recommended. | delivery | `llncs` LaTeX source and final PDF | final PDF builds from the delivered source without unresolved citations/references, missing CJK glyphs, clipped material, or draft markers |
| REP-09 | Use the provided Overleaf template and linked LaTeX resources as help. | build notes, not scholarly content | optional acknowledgment of starting template | these are advisory resources, not sources that require prose coverage; acceptance is successful use of current official `llncs`, not reproduction of the tutorial links |
| REP-10 | Baseline material, especially handout-covered material, should be concise. | 3 through 6 | editorial review | generic definitions are short and immediately connected to case evidence; there is no long paraphrase of the teaching material |
| REP-11 | Free exploration may be detailed. | 4, 6, 7, 8 | deep cross-layer interpretation and focused outlook | depth is concentrated in mechanisms revealed by the case and MLIR outlook, not unrelated compiler trivia |
| REP-12 | Prefer changing the program or debug/optimization parameters (including auto-parallelization options) to observe changed outputs. | 7 | one controlled variation, recommended as `-O0` versus `-O2`; optional diagnostic showing why the loop was or was not vectorized | exactly what changed is recorded; explanations are tied to observed IR/assembly/optimization remarks; no performance conclusion is inferred merely from structural change |
| REP-13 | Do not write a repetitive “proposition essay” duplicating the handout. | entire paper | narrative and claim-to-evidence editorial pass | each section advances the one representation journey; there are no stand-alone textbook chapters disconnected from the instance |
| REP-14 | Use `llncs` (latest user requirement). | LaTeX root and PDF | official current `llncs.cls`/template obtained under its distribution terms; documented TeX engine/CJK setup | the document root uses `\documentclass{llncs}` (with supported options if needed); margins, type sizes, and spacing are not manually overridden; source and PDF agree |

The two sample programs printed at the end of the course task are suggestions, not
additional requirements. Their presence creates no acceptance obligation to implement
either or both.

## 5. Evidence and artifact budget

The smallest complete support bundle is deliberately paper-centered:

| Role | Minimum durable item | Why it exists |
|---|---|---|
| semantic anchor | one `.sy` source plus a tiny corresponding C observation form | keeps all stages tied to one computation while exposing the C preprocessor/AST honestly |
| compiler observations | preprocessed excerpt/file, selected AST, generated `-O0`/`-O2` IR and RV64 assembly | supports the paper's causal explanations |
| authored low-level forms | one `.ll` and one RV64 assembly source | satisfies the explicit programming requirement |
| object/link evidence | one object inspection and one linked-executable inspection per low-level path, consolidated where identical | makes assembler/linker responsibilities visible |
| behavioral evidence | a small shared input/output table and raw transcript | supports, but does not overclaim, equivalence |
| MLIR evidence | VecAdd snapshots if runnable, otherwise exact attempt record plus cited stage reconstruction | supports the advanced outlook with calibrated status |
| publication artifact | LLNCS source, bibliography, figures, final PDF, short build instruction | delivers the required report |

Avoid recreating a general-purpose test framework, elaborate CMake target graph, large
artifact manifest, bespoke metrics system, or cross-platform emulator matrix unless a
concrete build obstacle truly requires it. Repository CI may compile the paper and run a
small smoke check, as required by project practice, but CI must not be presented as a
research contribution. Engineering support is a means of preventing stale evidence, not
the intellectual center of the survey.

## 6. Behavioral and structural verification

### 6.1 Shared behavioral oracle

Use the fixed arrays and six prefix lengths below. They are boundary/path cases of the
same program, not six examples.

| Input `n` | Effective prefix length | Expected output | What it exercises |
|---:|---:|---:|---|
| `-1` | `0` | `0` | lower count clamp and zero-iteration loop |
| `0` | `0` | `0` | exact lower boundary and zero-iteration loop |
| `1` | `1` | `-8` | first clipped product and one loop iteration |
| `4` | `4` | `8` | mixed products, clipping decisions, and loop-carried accumulation |
| `8` | `8` | `16` | full valid prefix and upper in-range boundary |
| `10` | `8` | `16` | upper count clamp without an out-of-bounds array read |

For each case, the source-reference executable, authored LLVM IR executable, and authored
assembly executable must agree on stdout and exit status. Behavioral agreement over
finite tests is evidence of consistency, **not a proof of semantic equivalence over all
inputs**. The paper must state this limitation.

### 6.2 Structural checks

The following questions are sufficient; there is no need for a separate auditing system:

1. Does the preprocessed output exhibit the claimed macro/directive effect?
2. Does the AST excerpt exhibit the claimed types, bindings, loop, branch, and calls?
3. Does LLVM accept/verify the authored IR for the recorded version?
4. Does the RV64 assembler accept the authored assembly for the stated ISA/ABI?
5. Do object metadata and relocation/symbol tables support the assembler/linker claims?
6. Do both low-level executables link the intended target-compatible SysY runtime?
7. Do all shared behavior cases pass?
8. Does the controlled compiler variation change only the declared independent setting?
9. Are MLIR claims labeled by evidence status?

### 6.3 Suggested optimization comparison

Use `-O0` as the main explanatory form because it usually preserves an obvious relation
to source variables. Compare only selected `-O2` regions to show, as actually observed:

- promotion of stack slots to SSA values;
- constant propagation or control-flow simplification;
- possible inlining of `clipped_dot` and exposure of the two fixed arrays to further
  analysis;
- changed register allocation/instruction selection;
- an optimization remark indicating whether the array reduction was vectorized or
  parallelized and why. Relevant facts may include the bounded dynamic trip count,
  reduction recognition, clipping control flow, available target vector extensions, and
  what alias analysis can or cannot prove about the two pointer parameters.

Do not hard-code these as promised outcomes. Toolchain version, target, alias analysis,
and the exact source affect the result. A negative optimization result is useful if the
paper explains the blocking dependency or side effect; there is no need to mutate the
example until a fashionable transformation appears.

## 7. MLIR outlook evidence policy

The advanced chapter should use an evidence-status table:

| Status | Meaning | Permitted wording |
|---|---|---|
| Observed | produced by recorded commands in the available environment | “The captured stage contains …” |
| Documentation-derived | shown or specified by the cited official source | “The official VecAdd guide shows/describes …” |
| Inferred | reasoned from observed/documented stage differences | “This suggests … because …” |
| Hypothesized | plausible but unverified behavior in a missing environment | “We expect …; verification would require …” |

The paper should explain dialect conversion using the primary concepts of conversion
targets, legality, rewrite patterns, and type conversion, then show how the VecAdd case
retains and progressively lowers domain/hardware structure. It should also make the
important conceptual correction that “LLVM IR is single-level” is pedagogical shorthand:
LLVM-based compilers have multiple internal representations and lowering phases, whereas
MLIR standardizes an extensible common infrastructure for coexisting dialects and staged
conversion.

The advanced section passes in documentation-only mode if the task's allowed fallback is
followed honestly and the analysis is substantive. Actual captured AscendNPU IR stages
are stronger evidence and should be used when feasible; NPU execution is not necessary
for a middle-end survey unless the paper claims end-to-end device execution.

## 8. LLNCS publication acceptance

Use the current official Springer proceedings template rather than a copied historical
class of uncertain origin. The course imposes no page limit, so the report may be long
enough to explain the mechanisms; depth must still be edited for relevance.

Hard publication checks:

- `\documentclass{llncs}` is retained and class geometry/typography are not overridden.
- The Chinese engine/font setup is documented and produces selectable, embedded CJK text.
- Abstract and keywords use class-supported structures.
- Figures have captions below; tables have captions above; every float is referenced.
- Listings fit the text block and show only lines discussed in the prose; complete files
  remain in support artifacts.
- Numeric citations and the bibliography compile without undefined references.
- URLs/DOIs are legible and do not overflow.
- The PDF has been visually inspected page by page for missing glyphs, blank pages,
  clipped tables, bad float placement, or orphaned headings.
- The compiled PDF corresponds to the final source revision.

The manuscript should prefer primary technical sources:

- Clang's official toolchain description:
  <https://clang.llvm.org/docs/Toolchain.html>
- Clang command guide:
  <https://clang.llvm.org/docs/CommandGuide/clang.html>
- LLVM Language Reference:
  <https://llvm.org/docs/LangRef.html>
- RISC-V ELF psABI:
  <https://riscv-non-isa.github.io/riscv-elf-psabi-doc/>
- MLIR language and dialect-conversion documentation:
  <https://mlir.llvm.org/docs/LangRef/> and
  <https://mlir.llvm.org/docs/DialectConversion/>
- MLIR-to-LLVM target documentation:
  <https://mlir.llvm.org/docs/TargetLLVMIR/>
- AscendNPU IR VecAdd/quick-start material linked by the course task:
  <https://ascendnpu-ir.gitcode.com/en/introduction/quick_start/index.html>
- Springer's official LNCS author/template page:
  <https://www.springer.com/gp/computer-science/lncs/forthcoming-proceedings>

The report may cite CSAPP as a pedagogical influence, but its technical definitions must
not replace current primary documentation.

## 9. Acceptance gates

The report is complete when all of the following are true:

### Narrative and coverage

- [ ] One bounded-prefix clipped integer dot product is the semantic thread of every baseline
      chapter; no competing case study is introduced.
- [ ] Every row ADM-01 through REP-14 is either satisfied in the indicated location or,
      for administrative actions outside the PDF, present on the final human checklist.
- [ ] Each pipeline stage states input, work, output, visible case trace, and deferred
      responsibility.
- [ ] The paper explains mechanisms through evidence rather than paraphrasing the handout.
- [ ] Observed, inferred, documentation-derived, and hypothesized claims are not blurred.

### Technical evidence

- [ ] The SysY source, C observation form, generated observations, authored LLVM IR, and
      authored RV64 assembly all have unambiguous roles and are never conflated.
- [ ] The source-reference, IR-derived, and assembly-derived executables agree on the
      shared cases and declared exit behavior.
- [ ] At least one runtime symbol is traced through declaration, LLVM call, assembly call,
      object relocation/undefined symbol, link resolution, and observed I/O.
- [ ] The RV64 discussion is consistent with the recorded target ISA/ABI and the RISC-V
      psABI.
- [ ] The `-O0`/`-O2` comparison reports actual structural observations without turning
      them into unsupported performance claims.
- [ ] The MLIR/Ascend chapter follows VecAdd and declares its evidence boundary honestly.

### Publication and submission

- [ ] The LLNCS source builds the final PDF with no unresolved references/citations or
      missing-glyph/layout defects.
- [ ] Title, abstract, keywords, introduction, work/results, conclusion, and references
      are present.
- [ ] The opening material names both students and their concrete division of work.
- [ ] Figures, tables, equations, and listings are readable, numbered as appropriate, and
      discussed in the prose.
- [ ] Both members possess and independently submit the identical final PDF.

Passing these gates means the requested survey is complete. It does **not** require
restoring any deleted preflight architecture, preserving any former implementation, or
maximizing the number of generated artifacts.
