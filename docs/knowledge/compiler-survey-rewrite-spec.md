# Rewrite Specification: *Understanding a Compiler System Through One Program*

## 1. Decision and product intent

The paper must be rewritten as a **deep, review-style guided tour of a compiler
system**, not as an artifact-evaluation paper, runtime-library audit, or CI
report. Its organizing device is one moderately sized program followed from
source text to a running RV64 Linux executable. The intended reading experience
is analogous to the systems exposition in *Computer Systems: A Programmer's
Perspective*: introduce a concrete piece of code, stop at each representation
boundary, point to a visible feature, and explain what mechanism produced it
and why that mechanism exists.

The manuscript's central thesis should be:

> A compiler is best understood as a sequence of representation contracts. At
> each boundary, some source-level intent is preserved, some information is
> made explicit, and some decisions are deliberately deferred to a later stage.

Depth must come from tracing the **same semantic facts** across representations,
not from accumulating programs, test matrices, toolchain incidents, or
unrelated advanced features.

### 1.1 Authority and interpretation

This specification applies the following sources in descending order:

1. The user's latest direction: one instance must integrate all baseline
   sections; the paper should be a survey titled in the spirit of “深入理解编译
   系统”; advanced material may be covered as outlook; the old implementation
   need not be preserved.
2. [`docs/预备工作-了解你的编译器.md`](../预备工作-了解你的编译器.md): the
   grading requirements, required report form, and explicit warning that
   multiple repetitive examples do not earn additional credit.
3. Current repository artifacts: reusable evidence, not a commitment to the
   current paper's framing or example design.
4. Primary technical references: Clang's toolchain documentation, the LLVM
   Language Reference, the RISC-V ELF psABI, the MLIR paper/documentation, and
   the official AscendNPU IR VecAdd material.

The resulting document is deliberately **not** a backward-compatible revision
of the current manuscript. Material survives only when it supports the new
narrative.

## 2. Audience, promise, and non-goals

### 2.1 Audience and promise

The primary reader is a compiler-systems course instructor or student who knows
C-like syntax but wants to see how a real toolchain realizes it. By the end, the
reader should be able to answer five connected questions:

1. What exact representation enters and leaves each major stage?
2. How do source constructs become AST nodes, LLVM IR operations, and RV64
   instructions?
3. Which responsibilities belong to the compiler, assembler, linker, runtime,
   and loader respectively?
4. Why can authored LLVM IR and authored RV64 assembly be called equivalent to
   the source program?
5. How would MLIR add more abstraction levels without changing the fundamental
   idea of staged representation contracts?

### 2.2 Explicit non-goals

The paper must not spend substantive space on:

- auditing `libsysy`, its libc provenance, `_impure_ptr`, or defects in
  `sylib.h`;
- explaining the repository's CMake, CTest, GitHub Actions, or cross-platform
  workflow architecture;
- presenting five execution paths or a large test matrix as a research result;
- treating lexical counts as a performance study;
- surveying every LLVM pass, ELF field, RV64 instruction, or ABI rule;
- claiming an AscendNPU/MLIR experiment that was not actually run;
- adding a second algorithm merely to illustrate another stage;
- using the manuscript to document debugging history.

These items may remain in the repository as engineering support. They are not
part of the paper's intellectual center.

## 3. The single case study

### 3.1 Selected program: bounded iterative factorial

Replace the current deliberately feature-dense `compiler_tour` narrative with
the bounded iterative-factorial case now represented by
`preflight/src/bounded_factorial.c` and
`preflight/src/bounded_factorial.sy`. These are not two examples: they are a C
observation form and a SysY form of the **same algorithm and semantic
contract**. The C form exposes a macro and external declarations to the
preprocessor; the SysY form is the source-language program used as the semantic
reference for the authored LLVM IR and RV64 assembly.

The program:

1. reads an integer through the SysY runtime;
2. uses `clamp_input` and two conditionals to normalize it to `[0, 10]`;
3. uses `factorial` and a `while` loop to compute the factorial iteratively;
4. prints the result and a newline through the SysY runtime.

The C observation form additionally defines `FACTORIAL_LIMIT` as a macro so the
preprocessed output visibly replaces it with `10`. The SysY form expresses the
same bound as a literal because preprocessing is not part of the SysY language
contract.

### 3.2 Why this is the right complexity

| Language feature | What it unlocks in the exposition |
|---|---|
| Integer multiplication and addition | typed operations, constant materialization, and RV64 arithmetic lowering |
| Assignment and accumulator | source variables versus memory slots at `-O0` and SSA values after promotion |
| Two ordered conditionals | AST branch structure, IR basic blocks, and conditional RV64 branches |
| `while` loop | control-flow graph, loop-carried state, back edge, and possible `phi` nodes |
| Two user-defined functions | call expressions, IR functions/calls, RV64 calling convention, symbols and relocations |
| Runtime input/output | unresolved external symbols and the reason linking is required |
| Bounded input | avoidance of signed overflow and a small deterministic verification domain |

The explicit clamp makes the familiar factorial example sufficiently rich for
the whole tour: it supplies two functions and control-flow boundaries while
keeping the mathematical result obvious. Every feature serves a later
explanatory purpose. This avoids the current program's independent array,
recursion, global side-effect counter, and short-circuit probe, which force the
reader to track several mini-experiments at once.

### 3.3 Feature exclusions

Do **not** add arrays, recursion, short-circuit side effects, global mutable
state, floating point, structs, heap allocation, or multiple algorithms. They are
valid compiler topics but are not needed to expose any mandatory stage here.
If one of them is mentioned, it belongs in a one-sentence boundary note, not in
the case study.

### 3.4 Semantic contract and verification cases

The semantic contract is the printed integer followed by one newline and exit
status zero. A few inputs are needed to validate paths; they are **test cases of
one example**, not additional examples. Use a compact table such as:

| Input | Expected result | Purpose |
|---:|---:|---|
| `-3` | `1` | lower clamp and zero-iteration loop (`0!`) |
| `0` | `1` | factorial base case without entering the loop |
| `1` | `1` | positive value that still skips the loop |
| `5` | `120` | multiple loop iterations and multiplication |
| `10` | `3628800` | largest unclamped input |
| `20` | `3628800` | upper clamp |

The source, authored LLVM IR, and authored RV64 assembly must all be checked
against the same cases. The paper should report the boundary coverage and one
concise equivalence verdict, not expand the six inputs into an evaluation
campaign.

## 4. Narrative architecture

### 4.1 Working title

**深入理解编译系统：一个 SysY 程序从源代码到 RISC-V 可执行文件**

Possible English running title: **Understanding a Compiler System Through One
Program**.

### 4.2 Global explanatory template

Every stage subsection should answer the same five questions:

1. **Input:** What representation enters this stage?
2. **Work:** What transformation or decision does the stage perform?
3. **Output:** What representation leaves it?
4. **Concrete trace:** Where is one source construct visible in the output?
5. **Boundary:** What remains unresolved or is no longer directly visible?

This repeated template supplies coherence without repeating generic textbook
definitions. Each important excerpt should appear beside or immediately after
the source fragment it explains. Use a single overview diagram and a
source-to-representation trace table as visual anchors.

### 4.3 Required section structure and core questions

#### Front matter: abstract, keywords, and author contributions

- **Core question:** What journey will the paper explain, and what is the main
  understanding produced?
- State that one SysY program is followed through Clang/LLVM, LLVM IR, RV64,
  ELF assembly/linking, and execution.
- Report only the compact end-to-end result: the three representations produce
  the same output on the declared cases.
- Do not mention CI pass counts, runtime defects, or static MLIR tests.
- Keep the existing reasonable two-person split, but redefine responsibilities
  around exposition: one member leads source/front-end/LLVM IR analysis; the
  other leads RV64/object/linker analysis and typesetting; both verify behavior,
  references, and the final manuscript.

#### 1. Introduction: from black box to representation chain

- **Core question:** Why is “the compiler turns source into an executable” an
  inadequate model?
- Motivate the distinction between compiler driver, preprocessor, compiler
  front/middle/back end, assembler, linker, loader, and runtime.
- Introduce the one-program method and three guiding ideas: representation,
  contract, and traceability.
- Give a roadmap rather than a list of artifact-engineering contributions.

#### 2. One program, one semantic thread

- **Core question:** Why is this program sufficient to reveal the complete
  system without becoming a feature catalogue?
- Present the full program once, preferably as a compact numbered listing.
- State its input domain, result function, language-feature map, runtime calls,
  and target (`riscv64-unknown-linux-gnu`, RV64GC/LP64D if that remains the
  actual toolchain).
- Show the single pipeline figure:

  ```text
  SysY source
    -> preprocessed text
    -> typed AST
    -> LLVM IR (-O0, with a selective -O2 comparison)
    -> RV64 assembly
    -> ELF relocatable object
    -> linked executable + SysY runtime
    -> observed output
  ```

- Explain that Clang may fuse logical phases; saved files are observation
  points, not proof that every phase ran as a separate process.

#### 3. From source text to a typed program

- **Core question:** How does text become a semantically checked program?
- **Preprocessing:** use `clang -E` on `bounded_factorial.c`. Point out the
  replacement of `FACTORIAL_LIMIT` by `10`, comment removal, and emitted line
  markers, while noting that the external runtime declarations remain ordinary
  declarations. Explain include and conditional-compilation responsibilities
  generally, but distinguish them from transformations actually exercised by
  this source.
- **Lexing and parsing:** identify representative tokens and show the AST shapes
  for a clamp conditional, the factorial loop, multiplication, and calls.
- **Semantic analysis:** explain name binding, types, lvalue/rvalue distinctions,
  function signatures, and the input-domain invariant. Include one plausible
  rejected mutation (for example, calling `factorial` with the wrong arity) only to
  explain what semantic analysis catches; it is not a second program.
- End by stating why an AST is not machine code and which decisions remain
  target-independent.

#### 4. From typed structure to LLVM IR

- **Core question:** How are structured source constructs expressed using typed
  operations, basic blocks, explicit memory, and SSA data flow?
- Use authored LLVM IR as the central readable listing; compare selected lines
  with Clang-generated IR rather than presenting them as unrelated artifacts.
- Trace at least:
  - `clamp_input`'s ordered conditionals into `icmp`, branches, and returns;
  - `factorial`'s loop into header/body/exit blocks and a back edge;
  - `result`/`factor` values into `alloca`/`load`/`store` at `-O0` and, where
    generated, `phi` nodes after promotion;
  - the multiplication and increment into typed integer operations;
  - calls to `clamp_input`, `factorial`, `getint`, `putint`, and `putch` into
    typed call sites.
- Explain opaque pointers only as needed to read the listing; do not turn pointer
  history into a side survey.
- Include a **small controlled `-O0`/`-O2` comparison** showing two or three
  causal transformations (for example, stack-to-SSA promotion, constant
  propagation, and helper inlining if actually observed). Avoid raw line-count
  claims unless a count directly supports a visible transformation. Explicitly
  state that fewer textual instructions do not prove faster execution.

#### 5. From LLVM IR to RV64 machine-oriented code

- **Core question:** Which previously abstract choices become concrete for
  RV64, and how does the ABI constrain them?
- Place a short generated-RV64 excerpt and the corresponding authored-assembly
  excerpt next to the source/IR trace.
- Explain instruction selection for integer arithmetic and comparisons, branch
  labels for control flow, register allocation, stack-frame layout, and calls.
- Cover only ABI rules exercised by the program: `a0` for the first integer
  argument/return value, caller/callee-saved consequences actually visible,
  saving `ra` when necessary, and 16-byte stack alignment.
- Distinguish pseudoinstructions from encodings when this matters to the later
  assembler discussion.
- Do not catalogue the RV64 ISA.

#### 6. Assembly and linking: from symbols to a process image

- **Core question:** Why is readable assembly still not an executable, and how
  are unknown addresses resolved?
- Use the actual authored `.s` file to produce one relocatable object. Inspect a
  small set of evidence: ELF type/machine, `.text`/`.data`/symbol table as
  present, the unresolved runtime symbols, and representative call/data
  relocations.
- Explain that the assembler encodes instructions and records unresolved
  symbolic relationships; it does not resolve the whole program.
- Link through the compiler driver with the SysY runtime. Show how `factorial`
  and `clamp_input` are locally defined while runtime calls are supplied by the linked
  runtime and startup/libc support.
- Explain static versus dynamic resolution only to the extent required by the
  actual artifact. Clearly distinguish **linking** from OS loading and QEMU
  execution.
- `libsysy` internals, newlib/glibc provenance, `_impure_ptr`, and header-symbol
  ownership are excluded. If a runtime must be rebuilt for the toolchain, state
  that fact once in the environment paragraph without analyzing the incident.

#### 7. Closing the loop: equivalence and what the tour establishes

- **Core question:** What evidence supports the claim that the three authored
  forms implement the same program, and what does that evidence not prove?
- Report source, LLVM IR, and RV64 assembly as three rows against the shared
  cases, preferably summarized as “6/6” plus one representative output.
- Synthesize the vertical trace: one clamp branch, one loop edge, one
  multiplication, one helper call, and one runtime call across all
  representations.
- Add a short limitation paragraph: finite tests show observable agreement on
  the declared domain but are not a formal proof; QEMU user mode establishes
  RV64 Linux behavior, not real-hardware performance.
- Do not retain a standalone, publication-style “threats to validity” section
  unless the final narrative genuinely needs it.

#### 8. Outlook: from LLVM IR to multi-level IR

- **Core question:** What limitation of lowering directly toward LLVM IR
  motivates MLIR, and how would the same representation-contract viewpoint
  extend to it?
- Keep this section explicitly as **outlook**, not experimental results.
- In roughly half to one page, explain dialects, progressive lowering, and why
  domain semantics such as vector operations and memory spaces can remain
  explicit longer.
- Use the official AscendNPU IR VecAdd flow as a compact illustration:
  device-oriented/vector/memory-space operations are progressively made more
  concrete before LLVM-level code generation.
- Clearly label which statements come from official documentation. Do not
  report local dialect parsing, lowering, binary generation, or NPU execution
  unless new direct evidence is actually produced during the rewrite.
- Conclude with one future-work sentence describing what tools/hardware would be
  needed for a real reproduction.

#### 9. Conclusion

- **Core question:** What does the single example teach about the compiler as a
  system?
- Answer the introduction's questions by summarizing the representation
  contracts and division of responsibility.
- Do not repeat test counts, implementation infrastructure, or runtime-library
  defects.

#### Reproducibility note or short appendix

- Preserve a compact command ladder and exact tool versions so a reader can
  regenerate the observation points.
- Prefer a one-page maximum appendix or a compact table. Long build commands,
  CI descriptions, generated-file inventories, and repository troubleshooting
  do not belong in the paper.

## 5. Disposition of the current manuscript

The following table is the rewrite boundary. “Retain” means retain the
technical idea, not necessarily the existing prose.

| Current material | Decision | Rewrite instruction |
|---|---|---|
| Title and empirical-study framing | **Replace** | Use the survey/case-study title and representation-chain thesis. |
| Abstract's five-path/CTest counts | **Delete** | Replace with the one-program journey and compact equivalence result. |
| Abstract's runtime audit | **Delete** | It is outside the assignment and distracts from the compiler system. |
| Introduction's distinction among source, IR, ABI, and executable | **Retain and deepen** | Recast as the paper's conceptual spine. |
| Introduction's artifact-oriented “contributions” list | **Replace** | Use guiding questions and a narrative roadmap. |
| Current feature-dense program (`fib`, `sum`, `mark`, `ticks`) | **Replace** | Adopt the bounded iterative factorial; reuse infrastructure only where convenient. |
| Five-fixture formal pass equation | **Delete** | A short semantic contract and compact boundary-case table are sufficient. |
| Clang/RV64 environment and target declaration | **Retain, compress** | One reproducibility paragraph/table; exact versions stay. |
| CMake/Ninja/CTest architecture | **Remove from paper** | Keep only in repository documentation if needed. |
| Preprocessor and AST discussion | **Retain and reorganize** | Tie each observation to the new source listing and semantic-stage questions. |
| LLVM IR explanation of SSA and `phi` | **Retain selectively** | Explain only operations actually visible in the new case and show source/IR correspondence; delete GEP discussion because the new case has no array. |
| Short-circuit control-flow analysis | **Delete** | The new helper conditional and loop already expose control flow. |
| `-O0`/`-O2` comparison | **Retain, compress** | Prefer two or three structural before/after observations over metrics tables. |
| RV64 psABI, stack, registers, arithmetic, and branches | **Retain and integrate** | Make them the concrete continuation of the IR trace. |
| Assembler, ELF, symbol, relocation, and linker explanation | **Retain and deepen** | This is a baseline requirement; show selected actual evidence. |
| Five execution paths by host/target/representation | **Compress heavily** | Report only the three semantically relevant representations and shared verdict. |
| Entire runtime compatibility audit | **Delete** | No `_impure_ptr`, libc-family analysis, or `sylib.h` defect discussion. |
| MLIR/Ascend static-structure experiment and test | **Replace** | A documentation-grounded outlook only, unless a new real lowering run is produced. |
| Standalone threats-to-validity section | **Compress** | Put finite-testing and emulator limits in the equivalence section. |
| Conclusion's runtime-audit lesson | **Delete** | Conclude on representation contracts and component responsibilities. |
| Reproduction appendix | **Retain, compress** | Keep the command ladder and versions; remove workflow architecture. |
| Existing author-contribution statement | **Retain with edits** | Remove runtime audit and CI duties; align it with the rewritten analysis. |
| Existing authoritative references | **Filter** | Retain sources actually cited; remove CMake/CI/runtime-audit-only references. |

## 6. Evidence and figure plan

### 6.1 Required evidence artifacts

The rewrite should be backed by the following artifacts, all derived from the
single program:

1. SysY source and minimal injected declarations;
2. preprocessed source;
3. readable AST excerpt (text is preferable to an enormous JSON dump in the
   paper);
4. Clang-generated `-O0` and `-O2` LLVM IR;
5. authored LLVM IR;
6. compiler-generated RV64 assembly;
7. authored RV64 assembly;
8. a relocatable RV64 object with disassembly, symbol, and relocation evidence;
9. a linked RV64 Linux executable with format/symbol evidence;
10. shared execution results for source, authored IR, and authored assembly.

Generated material may remain outside version control if it is reproducible.
The manuscript must quote only small, legible excerpts and give the command or
artifact path for the complete evidence.

### 6.2 Required visuals

| Visual | Purpose | Constraint |
|---|---|---|
| One vertical pipeline diagram | Orient the reader and establish stage boundaries | Show representations, not internal build targets |
| One feature-to-representation table | Trace the same constructs across source, AST, IR, and RV64 | Keep to 5–7 constructs |
| One object-to-executable diagram | Explain assembler/linker/runtime roles and relocation | Distinguish object, archive/runtime, executable, and loader |
| One compact equivalence table | Close the semantic loop | Three representations; no infrastructure rows |
| Optional `-O0`/`-O2` before/after figure | Explain a causal optimization | Use only if it is more readable than a listing |

Avoid screenshots of terminals. Prefer vector diagrams, typeset tables, and
syntax-highlighted excerpts. All figures and tables must be referenced in prose
and remain legible in grayscale under `llncs` formatting.

## 7. Completion criteria

The rewrite is complete only when all of the following are true.

### 7.1 Content and scope

- [ ] The title, abstract, introduction, and conclusion consistently present a
      review-style “deep understanding” paper, not an artifact study.
- [ ] Exactly one algorithm is used throughout; all source, IR, assembly,
      object, link, and runtime observations refer to it.
- [ ] The example covers arithmetic, assignment, conditionals, a loop,
      user-defined functions, and SysY runtime I/O without unrelated feature
      demonstrations.
- [ ] Preprocessor, compiler internal stages, assembler, linker, LLVM IR, RV64
      assembly, and execution are each explained with concrete evidence.
- [ ] Each major stage states its input, transformation, output, concrete trace,
      and unresolved boundary.
- [ ] MLIR/AscendNPU IR appears only as clearly labelled outlook unless genuine
      new execution evidence exists.
- [ ] Runtime-library forensics, CI architecture, and debugging history are
      absent from the manuscript.

### 7.2 Technical correctness

- [ ] The exact source shown in the paper regenerates the discussed artifacts.
- [ ] Authored LLVM IR verifies and links with the declared LLVM/toolchain
      version.
- [ ] Authored RV64 assembly follows the declared psABI, assembles, links with
      the SysY runtime, and runs under the declared execution environment.
- [ ] Source, authored IR, and authored assembly produce exact matching standard
      output and zero exit status on every declared case.
- [ ] The object/executable discussion is supported by actual headers,
      disassembly, symbols, and relocations from those artifacts.
- [ ] The paper never calls the linker the loader, never treats assembly text as
      machine code, and never infers runtime speed from textual code size.
- [ ] Observed, documentation-derived, and prospective claims are distinguishable
      in the prose.

### 7.3 Manuscript quality and LLNCS conformance

- [ ] The LaTeX source uses the repository's official `llncs` class without
      margin, font-size, or spacing hacks.
- [ ] The required title, abstract, keywords, introduction, work/results,
      conclusion, references, and front-of-paper contribution statement are
      present.
- [ ] The main body follows the section structure in Section 4.3 or an
      explicitly equivalent structure preserving the same questions.
- [ ] Listings are excerpts rather than dumps; every table/figure earns its
      space by explaining a relationship.
- [ ] Citations prioritize primary sources and peer-reviewed papers. Claims
      about Clang, LLVM IR, RISC-V ABI, MLIR, and AscendNPU IR cite their
      respective authoritative sources.
- [ ] A clean build produces the final PDF with no unresolved citations or
      references, missing glyphs, clipped content, or placeholder identity text
      other than author details that the students must supply themselves.
- [ ] The PDF is read end to end after rendering; build success alone is not
      accepted as layout or narrative verification.

## 8. Recommended source hierarchy for the rewrite

Use these sources as the factual backbone; the existing research notes in
[`docs/research/preflight-research.md`](../research/preflight-research.md)
already record version caveats and evidence boundaries.

1. Clang, *Clang Compiler User's Manual* and *Clang Toolchain* documentation:
   <https://clang.llvm.org/docs/Toolchain.html>
2. LLVM, *LLVM Language Reference Manual*:
   <https://llvm.org/docs/LangRef.html>
3. LLVM, *The LLVM Target-Independent Code Generator*:
   <https://llvm.org/docs/CodeGenerator.html>
4. RISC-V, *ELF psABI Specification*:
   <https://riscv-non-isa.github.io/riscv-elf-psabi-doc/>
5. Lattner et al., “MLIR: Scaling Compiler Infrastructure for Domain Specific
   Computation,” CGO 2021.
6. MLIR, *Dialect Conversion* and Toy lowering tutorial:
   <https://mlir.llvm.org/docs/DialectConversion/> and
   <https://mlir.llvm.org/docs/Tutorials/Toy/Ch-5/>
7. Official AscendNPU IR VecAdd quick start, cited only for the outlook's
   documented example flow.

Secondary tutorials may help with phrasing but should not be used to establish
tool semantics where primary documentation exists.

## 9. Editorial guardrail

The final editing question for every paragraph is:

> Does this paragraph help the reader follow the selected program across a
> representation boundary or understand the responsibility of the component at
> that boundary?

If the answer is no, remove it or move it to repository documentation. This is
the main protection against repeating the current over-scoped paper.
