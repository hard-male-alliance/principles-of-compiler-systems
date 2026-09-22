# Compiler Preflight: Acceptance Contract and Delivery Boundary

## 1. Purpose and status

This document translates the course task **"Preliminary Work: Know Your Compiler, LLVM IR, and Assembly Programming"** into an executable acceptance contract. It is intended to remain the grading and delivery reference while the implementation artifacts and LNCS paper evolve.

The target is the complete **5/5-point** assignment, not merely the four-point baseline:

- **Baseline (4 points):** demonstrate the complete language-processing pipeline; create semantically equivalent SysY, LLVM IR, and ARM or RISC-V programs; link the SysY runtime; and validate observable behavior.
- **Advanced (1 point):** investigate MLIR/AscendNPU IR progressive lowering using the VecAdd path, with actual intermediate evidence where the environment permits it and an honest, technically useful fallback record where it does not.

### Requirement vocabulary

- **Explicit:** stated by the course task and therefore non-negotiable.
- **Necessary implication:** not stated verbatim, but required to make an explicit claim inspectable (for example, recording tool versions when claiming reproducibility).
- **Recommended:** improves evidential quality or robustness but is not itself a grading claim.
- **Optional:** useful exploration that must not displace a mandatory item.

The repository-level constraints in [`AGENTS.md`](../../AGENTS.md) also apply: work must not be performed directly on `main`; C/C++ work uses C++23 and modern CMake; and development/testing is exercised through GitHub Actions across supported platforms.

## 2. Authoritative sources and interpretation

| Source | What it controls | Interpretation used here |
|---|---|---|
| [`docs/预备工作-了解你的编译器.md`](../预备工作-了解你的编译器.md) | Task score, baseline and advanced content, report minimum structure, team submission | Primary grading source |
| [`docs/了解编译器-LLVM-IR与汇编编程.md`](../了解编译器-LLVM-IR与汇编编程.md) | Suggested commands, concepts, and examples | Guidance only; commands must be checked against the installed tool versions |
| [`docs/上机大作业总体要求.md`](../上机大作业总体要求.md) | Target architecture, SysY scope, platform context, academic integrity | Project-wide constraints |
| [`docs/SysY2022语言定义-V1.md`](../SysY2022语言定义-V1.md) and [`docs/SysY2022运行时库-V1.md`](../SysY2022运行时库-V1.md) | Source semantics and runtime API | Normative for the SysY-facing artifacts |
| [Clang toolchain documentation](https://clang.llvm.org/docs/Toolchain.html) and [LLVM Command Guide](https://llvm.org/docs/CommandGuide/) | Meanings of current compiler stages and CLI tools | Primary external references for claims about Clang/LLVM |
| [MLIR dialect conversion](https://mlir.llvm.org/docs/DialectConversion/), [Toy partial lowering](https://mlir.llvm.org/docs/Tutorials/Toy/Ch-5/), and [LLVM IR target](https://mlir.llvm.org/docs/TargetLLVMIR/) | Progressive lowering concepts | Primary external references for interpreting the advanced experiment |
| [AscendNPU IR Quick Start](https://ascendnpu-ir.gitcode.com/en/introduction/quick_start/index.html) | Ascend-specific build and example procedure | Primary source for the advanced reproduction path |
| [Springer LNCS author resources](https://link.springer.com/series/558/information-for-authors-and-editors), [official proceedings instructions](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF), and [CTAN `llncs`](https://ctan.org/tex-archive/macros/latex/contrib/llncs) | Paper class and typesetting conventions | Normative for the user-requested LNCS presentation |

### Evidence status

- **Observed:** the course explicitly assigns 4 baseline points and 1 MLIR point; requires one report per two-person team; requires both members to submit; and requires PDF output.
- **Inferred:** semantic equivalence cannot be established by code inspection alone, so the same test vectors and output oracle must be applied to all executable representations.
- **Recommended:** store commands, versions, logs, and generated artifacts in a reproducible bundle rather than relying on screenshots. This follows normal systems artifact-review practice and makes every paper claim traceable.

## 3. Smallest complete product

The smallest complete product is **one coherent experiment**, not several disconnected demonstrations:

1. A single canonical program/algorithm covers integer arithmetic, assignment, a conditional, a loop, a user-defined function call, and SysY runtime input/output.
2. The program is represented in three author-controlled forms: SysY-compatible source, handwritten or deliberately authored LLVM IR, and handwritten target assembly for **one** selected architecture (AArch64 or RV64).
3. A compiler-driver experiment exposes preprocessing, front-end compilation, optimization/IR, code generation, assembly, linking, and execution. The paper relates each output to the same source semantics.
4. All three executable paths use the architecture-appropriate SysY runtime and are checked against the same inputs and expected outputs.
5. A focused comparison changes one meaningful compiler factor, such as optimization level, debug information, or a selected pass, and explains the causal change in generated artifacts.
6. The advanced section follows VecAdd through multiple MLIR dialect/abstraction levels and distinguishes observed output from documentation-derived interpretation.
7. A reproducible LNCS LaTeX paper reports the experiment and links every substantive claim to a repository artifact or a cited source.

The preferred data-flow invariant is:

```text
one semantic program
  -> source/compiler-stage evidence
  -> authored LLVM IR -> object/executable -> output
  -> authored target assembly -> object/executable -> output
  -> one shared test oracle
```

This avoids the ungradable special case in which each representation implements a different toy program.

## 4. Grading and acceptance matrix

### 4.1 Baseline: complete pipeline and equivalent programs (4 points)

| ID | Requirement | Type | Minimum evidence | Pass condition |
|---|---|---|---|---|
| B-01 | Identify the studied toolchain and complete processing flow | Explicit | Exact compiler, assembler, linker, emulator/native runner names and `--version` output; a stage diagram | The diagram and text cover preprocessing, compilation/front end, IR/optimization/backend, assembly, linking, and execution without conflating their inputs/outputs |
| B-02 | Explain preprocessing | Explicit | Reproducible command and preprocessed artifact; a small source-to-output comparison showing at least one visible transformation | The report explains what changed and why, rather than only defining a preprocessor |
| B-03 | Explain compiler internals | Explicit | Token or AST evidence, LLVM IR, and target assembly generated from the experiment source; selected excerpts cross-referenced to source constructs | Lexing, parsing, semantic analysis, IR generation, optimization, and code generation are each described at the appropriate level; no claim depends only on lecture prose |
| B-04 | Explain assembly | Explicit | Assembly command, relocatable object, and `file`/`readelf`/`objdump`-style inspection output | Evidence shows that symbolic assembly became target machine code in a relocatable object and identifies at least sections, symbols, or relocations |
| B-05 | Explain linking | Explicit | Link command, architecture-matching SysY library, symbol/relocation inspection before and after linking, and final executable metadata | The report identifies how external SysY runtime references are resolved and distinguishes object files from the linked executable |
| B-06 | Design one feature-bearing SysY example | Explicit | Source plus a feature-to-line/function table | The program contains numeric operations, assignments, a conditional branch, a loop, a user function, and runtime I/O; it is accepted by the declared source path |
| B-07 | Author equivalent LLVM IR | Explicit | Human-readable `.ll`, successful verification/assembly to bitcode or object, link command, and execution log | The IR is valid for the recorded LLVM version and matches the source's externally observable behavior on the shared tests |
| B-08 | Author equivalent ARM or RISC-V assembly | Explicit | `.s`/`.S`, assembly result, link command, ABI/ISA declaration, and native/emulated execution log | The code respects the selected target ABI sufficiently to link and produces the same observable behavior on the shared tests |
| B-09 | Link the SysY runtime in both low-level paths | Explicit | Link map or command/log showing the correct library, plus runtime symbol evidence | LLVM-derived and assembly-derived executables both resolve and call the intended SysY runtime API; no host/target architecture mismatch is hidden |
| B-10 | Validate results | Explicit / necessary implication | Shared test manifest containing inputs, expected outputs, actual outputs, exit codes, and pass/fail summary for source-reference, LLVM IR, and assembly paths | All required cases pass byte-for-byte after documented normalization; failures are not omitted |
| B-11 | Investigate a meaningful variation | Explicit recommendation in task | Baseline and variant commands/artifacts, a controlled comparison, and a stated mechanism | Exactly one main independent variable changes (for example `-O0` to `-O2`); the report separates observation from explanation and does not infer runtime performance from code size alone |
| B-12 | Produce a scientific report | Explicit | LNCS LaTeX sources and final PDF | The paper includes title, abstract, keywords, introduction, work/results, conclusion, and references; figures/tables are legible and cross-referenced |
| B-13 | Record two-person contribution and submission responsibility | Explicit | Front-matter contribution statement naming both members and a final submission checklist | Division of work is unambiguous, and the checklist states that **both members** must submit the same report to Xiaoya |

### 4.2 Advanced: MLIR/AscendNPU IR progressive lowering (1 point)

| ID | Requirement | Type | Minimum evidence | Pass condition |
|---|---|---|---|---|
| A-01 | Establish the conceptual contrast | Explicit | A compact comparison of LLVM IR's single principal IR layer with MLIR's dialect-based staged representation, citing primary documentation | Dialect, conversion target, rewrite pattern, type conversion, and progressive lowering are used accurately rather than as buzzwords |
| A-02 | Follow the official VecAdd example | Explicit | Repository version/commit or release, environment/tool versions, commands attempted, and captured logs | The report makes it possible to tell exactly what was attempted and against which version |
| A-03 | Observe multiple lowering stages | Explicit intent | At least two materially different IR snapshots, ideally including a higher-level/device-oriented form and a lower-level form, with a per-stage operation/type mapping | The paper explains which abstractions disappeared, appeared, or became concrete at each transition and attributes the transition to a pass/pipeline step |
| A-04 | Report execution or bounded non-execution honestly | Explicit fallback allowed by task | If runnable: compile/run output and correctness check. If blocked: the failing command, diagnostic, environment limitation, documentation-based continuation, and a precise next step | Hardware/tooling absence is never presented as successful reproduction; a fallback still yields a substantive dialect/lowering analysis |
| A-05 | Relate AscendNPU IR to general MLIR | Necessary implication | A diagram/table separating general MLIR mechanisms from Ascend-specific dialects and tools | No unsupported claim implies that all MLIR lowering is Ascend-specific or that AscendNPU IR is equivalent to LLVM IR |

**Advanced scoring risk:** the course explicitly permits a documentation-led exploration when environment setup is difficult, but it does not guarantee that such a fallback earns the full point. For a full 5/5 target, actual IR snapshots generated by the recorded toolchain are the acceptance goal; the fallback is a truthful degradation mode, not an equivalent success claim.

## 5. Test and evidence contract

### 5.1 Shared behavioral oracle

Use one machine-readable test manifest for all representations. It must contain at least:

| Case class | Purpose | Required example property |
|---|---|---|
| Branch A | Exercise the true branch | Input causes one branch outcome |
| Branch B | Exercise the false branch | Input causes the opposite outcome |
| Zero/minimal iteration | Check loop boundary | Loop performs zero or one iteration as designed |
| Multi-iteration | Check loop-carried state | Loop performs several iterations and invokes arithmetic/function logic |
| Arithmetic stress within defined range | Detect translation mistakes | Values remain within defined signed-integer behavior; expected output is independently computed |

Every result record contains: artifact identity, command, input, stdout, stderr, exit code, expected stdout, and verdict. If whitespace is normalized, the exact normalization rule is declared once and applied uniformly.

### 5.2 Structural evidence

Behavioral equality alone does not prove that the required pipeline was explored. Preserve:

- preprocessed source;
- token/AST excerpt or equivalent front-end evidence;
- unoptimized and selected optimized LLVM IR;
- compiler-generated target assembly;
- authored LLVM IR and authored target assembly;
- relocatable object metadata, disassembly, symbol table, and relocation information;
- final executable metadata and resolved/runtime symbols;
- MLIR snapshots before and after named lowering steps;
- full command logs and a concise toolchain/version manifest.

Generated files may be regenerated in CI, but the exact commands and selected paper evidence must remain stable and reviewable.

### 5.3 Claim-to-artifact rule

Each results subsection should contain a compact traceability row:

```text
Claim -> command -> input artifact -> output artifact/log -> interpretation
```

Screenshots may illustrate an environment, but they do not replace text artifacts, logs, or source. Timing claims require repeated measurements, a stated statistic, and controlled conditions; otherwise report only structural differences such as instruction count or file size.

## 6. LNCS paper contract

### 6.1 Required structure

The paper uses the official `llncs` document class and preserves its layout rather than manually changing margins, font sizes, or spacing. The minimum structure is:

1. **Title and author block** — both members, affiliation as appropriate, and stable author order.
2. **Abstract** — problem, studied toolchain/target, method, most important observed result, and MLIR scope; no citations or footnotes.
3. **Keywords** — focused terms such as compiler pipeline, LLVM IR, RISC-V/AArch64, linking, MLIR, progressive lowering.
4. **Author Contributions / Division of Work** — placed at the beginning, immediately after the abstract/keywords or otherwise clearly in the opening material, satisfying the course requirement.
5. **Introduction** — research questions, scope, selected toolchain/architecture, and contributions of the experiment.
6. **Experimental Setup and Reproducibility** — environment, versions, program features, build/run method, oracle, and limitations.
7. **Language-Processing Pipeline** — preprocessing; front end and compiler stages; assembler; linker; source-to-artifact relationships.
8. **Equivalent LLVM IR and Target Assembly** — design mapping, ABI/runtime calls, build/link steps, and shared correctness results.
9. **Controlled Compiler Exploration** — optimization/debug/pass comparison with a controlled variable and evidence.
10. **MLIR/AscendNPU IR Progressive Lowering** — advanced task, observed snapshots, interpretation, and environment limitations.
11. **Threats to Validity / Limitations** — target/emulator dependence, version sensitivity, test coverage, and any unexecuted advanced step.
12. **Conclusion** — answers to the research questions, not a repetition of the abstract.
13. **References** — all cited works and only cited works, prioritizing official tool documentation and primary sources.

Appendices, if used, appear before the references under current Springer guidance. Long listings belong in repository artifacts; the paper includes only the excerpts necessary for an argument.

### 6.2 LNCS formatting acceptance

- The source begins from the official current template and builds with the chosen documented TeX engine.
- Use the class's title, author, abstract, keyword, section, figure, table, theorem, and bibliography mechanisms.
- Citations are numeric in brackets. Bibliography entries use the template-provided LNCS style and include DOI/URL where appropriate.
- Figure captions are below figures; table captions are above tables; every figure/table is referenced in the prose.
- Prefer vector diagrams; all figures remain understandable in grayscale and contain readable text. Provide alternative text metadata or an adjacent textual explanation for non-text content.
- Do not add page numbers or custom running heads merely for styling. If the title is long, provide the class-supported abbreviated running title.
- The course specifies no page limit. Do not invent one; prioritize a complete, concise argument. Springer’s general paper-length ranges are publication guidance, not a course grading rule.
- The final PDF must correspond exactly to the committed source and contain no missing glyphs, clipped content, unresolved references, undefined citations, or accidental draft markers.

For Chinese prose, the TeX engine/font setup must be explicit and reproducible while leaving `llncs` layout semantics intact. CJK support is an implementation choice, not permission to replace the LNCS class.

## 7. Delivery boundary

### 7.1 Required deliverables

The implementation may choose repository names, but the final bundle must expose these roles clearly:

| Deliverable role | Required contents |
|---|---|
| Canonical program | SysY-compatible source and feature map |
| Pipeline fixture/evidence | Commands and selected outputs for preprocessing, front end, IR/optimization, backend, assembly, and linking |
| LLVM implementation | Authored textual LLVM IR and its verified build/run path |
| Assembly implementation | Authored AArch64 or RV64 assembly and its assemble/link/run path |
| Runtime integration | Architecture-matching SysY library usage and symbol/link evidence |
| Tests | Shared cases, expected outputs, automated runner, and machine-readable or plain-text verdict summary |
| MLIR exploration | VecAdd inputs/commands, staged IR/logs, mapping notes, and declared execution status |
| Paper | LNCS LaTeX source, bibliography, owned figures/tables, and final PDF |
| Reproduction entry point | A short README plus commands/scripts that rebuild artifacts and rerun checks |
| CI evidence | GitHub Actions configuration and a green run for the supported build/test jobs |

### 7.2 Explicitly out of scope

- Implementing a new SysY compiler; this assignment studies and programs existing toolchains.
- Supporting both ARM and RISC-V. One architecture is sufficient; a second target is optional and must not dilute correctness evidence.
- Multiple redundant example programs. The task explicitly states that repetition earns no extra credit.
- Full coverage of every LLVM pass, every object-file field, or the complete target ISA.
- Claiming NPU execution when only compilation/lowering was observed.
- Performance conclusions from a single timing sample or from emulator timings presented as native hardware performance.
- Copying generated compiler output and calling it authored LLVM IR/assembly without explaining and controlling the authored content.

## 8. Principal risks and controls

| Risk | Consequence | Acceptance control |
|---|---|---|
| Three representations drift semantically | “Equivalent” claim becomes untestable | One semantic program, one oracle, one shared case set, differential result table |
| Host/target library mismatch | Link failure or misleading workaround | Record target triple/ISA/ABI and inspect every library/executable architecture before linking |
| Undefined C/SysY behavior | Different outputs can all be compiler-legal | Choose bounded arithmetic and defined inputs; document domain assumptions |
| LLVM version drift, including opaque-pointer syntax and pass CLI changes | Checked-in IR or legacy commands fail | Pin/record versions; validate IR with the same version; cite current command help/docs rather than blindly copying the guide |
| Assembly violates the calling convention or stack alignment | Intermittent corruption or runtime-call failure | State ABI; inspect prologue/call sites; test more than the happy path |
| Emulator output is mistaken for native evidence | Invalid performance or hardware claims | Label emulator/native status in every result; use emulation for correctness only unless justified |
| MLIR environment or NPU hardware is unavailable | Advanced task stalls or is overstated | Preserve exact failing evidence; still analyze generated/documented stages; state the boundary and next reproducible step |
| Report becomes a paraphrase of lecture notes | Weak experimental contribution | Organize around research questions, comparisons, and artifact-backed observations |
| LNCS customization breaks layout or CJK glyphs | Unacceptable PDF despite correct content | Keep official class/layout, compile in CI, render-inspect every page, fail on LaTeX warnings that affect correctness |
| Figures/log excerpts are illegible | Evidence exists but cannot be graded | Use vector diagrams/tables, crop excerpts to the argued lines, cross-reference full text artifacts |
| Authorship/submission requirement is forgotten | No score for one member | Front-matter contribution statement plus final two-person submission checklist |
| References or borrowed code are unattributed | Academic-integrity failure | Cite sources in paper and comments; distinguish generated, adapted, and authored code |

## 9. Definition of Done

The task is complete only when all hard gates below are true.

### Repository and reproducibility

- [ ] Work is on a non-`main` branch with reviewable commits; the intended GitHub Actions jobs pass.
- [ ] A fresh documented environment can execute the reproduction entry point without undocumented manual edits.
- [ ] Toolchain, target, emulator/native status, TeX engine, and relevant versions are recorded.
- [ ] Generated evidence and paper claims are mutually traceable and do not contradict current artifacts.

### Baseline 4 points

- [ ] B-01 through B-13 each have the specified evidence and pass condition satisfied.
- [ ] The canonical program visibly covers arithmetic, assignment, both conditional outcomes, looping, a user function, and SysY runtime I/O.
- [ ] Authored LLVM IR and authored target assembly both assemble/compile, link the correct SysY runtime, execute, and match the source-reference output for every required test.
- [ ] At least one controlled compiler variation yields an explained, inspectable artifact difference.
- [ ] Object and linked executable inspection supports, rather than merely asserts, the assembler/linker discussion.

### Advanced 1 point

- [ ] A-01 through A-05 are addressed.
- [ ] For the full-credit target, at least two staged VecAdd IR outputs are generated by the recorded MLIR/Ascend toolchain and mapped to their passes/dialects.
- [ ] Any hardware-dependent execution boundary is explicit; no inferred or documentation-only result is labeled as observed.

### Paper and submission

- [ ] The PDF is generated from committed LaTeX using the official `llncs` class and contains all required sections.
- [ ] The opening material clearly identifies both authors and their division of work.
- [ ] Tables, figures, listings, citations, references, and hyperlinks render correctly; no unresolved-reference or missing-glyph defects remain.
- [ ] Every empirical claim has a command/artifact/result trail; every externally derived technical claim has an appropriate citation.
- [ ] The final PDF has been visually inspected page by page and exactly matches the final sources.
- [ ] Both team members have the same final PDF and have confirmed their independent Xiaoya submissions.

Completion means this checklist passes as written; it does not mean that a PDF merely compiles or that one executable prints the expected output once.
