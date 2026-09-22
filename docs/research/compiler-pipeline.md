# Evidence notes: the C/Clang language-processing pipeline

## Research question and decision purpose

**Question.** What actually happens between a C translation unit and emitted assembly/object code in a contemporary Clang/LLVM toolchain, and which boundaries are driver abstractions rather than separable compiler internals?

**Purpose.** These notes support a review-style LLNCS report whose running example follows one program through preprocessing, the Clang front end, LLVM IR optimization, and target code generation. They are deliberately more precise than the common “preprocessor → compiler → assembler → linker” cartoon.

**Scope and evidence policy.** The main evidence is current rolling Clang/LLVM documentation and the GNU CPP manuals (accessed 2026-09-22), supplemented by foundational peer-reviewed work. Statements labelled **Observed** come from the local probe described below; **documented** statements paraphrase a cited primary source; **inference** is an interpretation that should not be presented as an upstream guarantee. The rolling LLVM pages describe current mainline and can diverge from an installed release. Always record `clang --version`, target triple, flags, and preferably the LLVM commit when presenting experimental artifacts.

## Executive synthesis

```text
command line
   │
   ▼
Clang driver: parse options → construct action graph → bind tools → run jobs
   │
   ├─ conceptual preprocess action
   │      source buffers ↔ lexer ↔ preprocessor
   │      includes, directives, conditional inclusion, macro expansion
   │                         │ expanded preprocessing tokens
   │                         ▼
   ├─ frontend compile action
   │      recursive-descent parser ↔ Sema → typed Clang AST → LLVM IRGen
   │                                                        │ LLVM IR
   │                                                        ▼
   ├─ LLVM middle end
   │      analysis/transform pass pipeline, dependent on -O*, target,
   │      LTO/PGO/sanitizers, and LLVM version
   │                                                        │ optimized IR
   │                                                        ▼
   ├─ target backend
   │      lowering/legalization → instruction selection → Machine IR
   │      scheduling/machine optimization → register allocation/spilling
   │      prologue/epilogue + late passes → MCInst/MCStreamer
   │                                                        │
   ├─ assembly text (.s) ── external or integrated assembler ─┐
   └─ direct integrated object emission ──────────────────────┴→ object (.o/.obj)
                                                                  │
                                                                  ▼
                                                    linker (a separate action)
```

The strongest supported account is therefore **a graph of driver actions implemented by a smaller number of possibly in-process jobs, each of which contains multiple coupled internal representations and passes**. It is inaccurate to imply that every arrow is a process, file, or cleanly materialized representation. The Clang command guide explicitly calls `clang` a small driver controlling tools, while the driver internals distinguish abstract `Action`s from bound `Tool`s/jobs; a tool may combine multiple actions, including an integrated preprocessor or assembler [Clang command guide](https://clang.llvm.org/docs/CommandGuide/clang.html), [driver internals](https://clang.llvm.org/docs/DriverInternals.html).

## 1. Driver stages are not compiler-internal stages

### 1.1 Three different decompositions must not be conflated

| Layer | Its question | Typical units | Materialization guarantee |
|---|---|---|---|
| Driver action graph | “What result did the user ask for?” | input, preprocess, compile, backend, assemble, link | None: `-ccc-print-phases` is a conceptual action graph |
| Bound jobs/tools | “Which executable or in-process tool performs those actions?” | `clang -cc1`, integrated assembler, system linker | `-###` prints commands without executing; several actions may be fused |
| Compiler internals | “Which representations and algorithms transform the program?” | tokens, AST, LLVM IR, MIR, MC layer | Usually in-memory; debug dumps are projections, not stable interchange contracts |

The driver itself is documented as: (1) parse command-line options, (2) construct a compilation action graph, (3) bind actions to tools and filenames, (4) translate arguments for tools, and (5) execute jobs. `-ccc-print-phases` exposes stage (2), whereas `-###` exposes the commands after binding/translation without executing them [driver internals](https://clang.llvm.org/docs/DriverInternals.html). Consequently, “the preprocessor runs, then the compiler runs” may be a useful pedagogical model but is not necessarily a process-level observation.

### 1.2 Reproducible local observation

Environment: Windows, `clang version 22.1.8`, commit `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`, target `x86_64-pc-windows-msvc`, observed 2026-09-22.

```powershell
clang --version
clang -ccc-print-phases -O2 -c probe.c
clang -### -O2 -c probe.c
```

**Observed.** The first command displayed five actions: input → preprocessor → compiler (IR) → backend (assembler text as an abstract type) → assembler (object). The second displayed only one in-process `clang -cc1 ... -emit-obj ... -O2` job. Thus one job implemented the four transformation actions after input, including integrated assembly. This is a concrete counterexample to a one-box/one-process interpretation, not proof that all hosts or configurations fuse the same actions.

### 1.3 User-visible stopping points

The current option reference defines `-E` as preprocessing only, `-S` as preprocessing plus compilation (ending in assembly), `-c` as preprocessing/compilation/assembly (ending in an object), and `-fsyntax-only` as preprocessing plus parsing/semantic analysis. `-emit-llvm -S` yields textual LLVM IR; `-emit-llvm -c` yields bitcode [Clang option reference](https://clang.llvm.org/docs/ClangCommandLineReference.html), [toolchain guide](https://clang.llvm.org/docs/Toolchain.html).

| Evidence wanted | Representative command | Interpretation caveat |
|---|---|---|
| Abstract action graph | `clang -ccc-print-phases x.c` | Driver plan, not processes |
| Bound commands | `clang -### x.c` | Printed, not run; exact output is platform/toolchain dependent |
| Preprocessed spelling | `clang -E x.c -o x.i` | Textual rendering of the preprocessed stream, with line markers unless suppressed |
| Macro environment | `clang -E -dM x.c` | Includes predefined/command-line/header macros at that point |
| Typed AST | `clang -Xclang -ast-dump -fsyntax-only x.c` | Developer dump, not a stable serialized schema |
| Frontend/optimizer IR result | `clang -O0 -S -emit-llvm x.c -o x.ll` | IRGen plus whatever pipeline the selected mode entails; compare flags explicitly |
| Optimized IR | `clang -O2 -S -emit-llvm x.c -o x.O2.ll` | Pipeline changes by release, target, and feature flags |
| Target assembly | `clang -O2 -S x.c -o x.s` | Target ABI, CPU, and assembly syntax must be recorded |
| Object | `clang -O2 -c x.c -o x.o` | May use integrated assembler without ever writing `.s` |
| LLVM pass trace | `clang -O2 -c x.c -mllvm -print-after-all` | Very large; LLVM flags passed through the driver require `-mllvm` |
| Controlled IR passes | `opt -S -passes='sroa,instcombine' x.ll` | This is an experiment, not necessarily Clang's default pipeline |

The pass-dump flags and their scoping/filtering options are documented in [Debugging LLVM](https://llvm.org/docs/DebuggingLLVM.html); `opt` and `-passes=` are documented in the [`opt` command guide](https://llvm.org/docs/CommandGuide/opt.html).

## 2. Preprocessing: a token transformation system, not naïve text substitution

### 2.1 Conceptual translation order versus implementation

GNU CPP documents the initial transformations as corresponding roughly to the first three standard translation phases: normalize input/line endings, join backslash-newline continuations, and replace comments with spaces while identifying preprocessing tokens. It explicitly says CPP performs these transformations together for performance even though the language specification describes a rigid conceptual order [GNU CPP, “Initial processing”](https://gcc.gnu.org/onlinedocs/cpp/Initial-processing.html). This is a useful general warning: **language semantics define an as-if ordering; implementation data flow may be fused**.

After tokenization, preprocessing directives and macros perform the phase usually thought of as “the preprocessor”: header inclusion, macro expansion, conditional compilation, line control, pragmas, diagnostics, and implementation extensions [GNU CPP manual](https://gcc.gnu.org/onlinedocs/cpp/). Clang's user-facing guide summarizes the same stage as tokenization, macro expansion, `#include` expansion, and other directives [Clang command guide](https://clang.llvm.org/docs/CommandGuide/clang.html).

### 2.2 Includes

`#include` causes the named file to be scanned as input before scanning resumes after the directive. Semantically, the parser consumes one resulting preprocessing-token stream; an included header can technically contain arbitrary token fragments, although complete declarations/definitions are the maintainable convention [GNU CPP, “Include Operation”](https://gcc.gnu.org/onlinedocs/cpp/Include-Operation.html). Header search order and the chosen physical file depend on quoted/angle form, `-I`/system paths, the resource directory, sysroot, and toolchain configuration, so a reproducible report should capture `clang -v -E` or an equivalent include-search trace.

Important implications for the running example:

* “Including a library” does **not** copy a compiled library into the program; it contributes declarations/macros/tokens. Linking supplies definitions later.
* Include guards and `#pragma once` affect repeated scanning but do not create a language-level module boundary.
* The `.i` output can be enormous because it renders included tokens, yet the implementation may avoid a literal concatenated buffer.

### 2.3 Macro expansion

Object-like and function-like macro replacement operates on preprocessing tokens. Function arguments may be macro-expanded before substitution; replacement lists are rescanned; the currently expanding macro is temporarily disabled to prevent invalid recursive re-expansion; stringification (`#`) and token pasting (`##`) impose special argument-expansion rules. GCC's implementation notes describe a context stack, tokenized stored replacement lists, argument substitution, rescanning, and “not eligible for future expansion” marks [GNU CPP internals, “Macro Expansion”](https://gcc.gnu.org/onlinedocs/cppinternals/Macro-Expansion.html).

This implementation evidence should not be overgeneralized into “Clang uses exactly GCC's context stack.” The portable claim is the externally required expansion behavior; the context-stack detail is **GCC-specific evidence of why correct macro expansion is not global search-and-replace**. Clang's own internals similarly expose a `Preprocessor::Lex` interface over buffer lexers and buffered token streams, but the concrete bookkeeping differs [Clang internals manual](https://clang.llvm.org/docs/InternalsManual.html).

### 2.4 Conditional inclusion and directives

`#if`, `#ifdef`, and related directives select which preprocessing tokens survive; `#define`/`#undef` mutate macro state; `#line` changes presumed source locations; pragmas convey implementation-specific instructions; `#error`/`#warning` produce diagnostics. These occur before C parsing, which explains why code excluded by `#if 0` need not be syntactically valid C. Clang's lexer even has a raw mode used for rapidly lexing such skipped regions [Clang internals manual](https://clang.llvm.org/docs/InternalsManual.html).

### 2.5 Lexing is interleaved with preprocessing in Clang

The common diagram places “lexing” after “preprocessing,” but Clang's implementation does not support that simple temporal claim. Its `Preprocessor` repeatedly asks lexers/token lexers for tokens and itself supplies the stream consumed by the parser. The lexer has modes for filenames, preprocessor directives, comment retention, language options, and skipped conditional regions. Macro definitions are stored as tokens. Therefore a better model is:

```text
source buffers → raw/preprocessing lexing ↔ directive and macro engine
                                      └──→ expanded token stream → parser
```

Tokens are short-lived communication objects for lexer/preprocessor/parser and are not stored as the AST itself [Clang internals manual](https://clang.llvm.org/docs/InternalsManual.html). This distinction matters when explaining why whitespace/comments and macro spelling do not simply reappear as AST nodes.

## 3. Parsing, semantic analysis, and the Clang AST

### 3.1 Coupled parser and Sema

Clang documents a recursive-descent parser that pulls tokens from the preprocessor and calls the semantic-analysis library (`Sema`) while parsing. The parser does not first build a complete concrete parse tree and then hand it to a separate semantic pass. Instead, Sema validates and constructs AST nodes for valid constructs as productions are recognized; the parser sees AST results through opaque wrappers such as `ExprResult` and `StmtResult` [Clang internals manual](https://clang.llvm.org/docs/InternalsManual.html).

It is therefore safer to write “conceptually, syntax analysis and semantic analysis have distinct responsibilities; in Clang they cooperate incrementally” than “Clang completes parsing, then starts semantic analysis.”

### 3.2 Responsibilities

| Concern | Principal component | Examples |
|---|---|---|
| Syntactic structure | Parser | declaration/statement/expression grammar, precedence, recovery from malformed token sequences |
| Names and scopes | Sema | declaration lookup, redeclaration compatibility, linkage, overload resolution in C++ |
| Types and conversions | Sema | expression types/value categories, integer promotions, usual arithmetic conversions, implicit casts |
| Language constraints | Sema | valid lvalues, argument/parameter compatibility, required constant expressions, control-statement restrictions |
| Diagnostics | Parser + Sema + supporting libraries | source-ranged errors, warnings, notes, and fix-its |
| Durable source-level representation | AST library | declarations, types, statements, expressions, source locations, implicit semantic nodes |

The Clang AST intentionally resembles the written C/C++ program and language standard rather than being an aggressively desugared optimization IR. For example, parentheses and unreduced compile-time constants may remain; implicit conversions appear as `ImplicitCastExpr` nodes. This source fidelity benefits refactoring and diagnostics [Introduction to the Clang AST](https://clang.llvm.org/docs/IntroductionToTheClangAST.html).

### 3.3 AST is not LLVM IR

The AST represents language semantics: declarations, source types, expressions, and implicit language operations. Clang CodeGen consumes this AST and emits LLVM IR [Clang internals manual](https://clang.llvm.org/docs/InternalsManual.html). The lowering must make implicit source semantics explicit enough for later stages: control flow becomes basic blocks and branches, short-circuit evaluation becomes control flow, lvalues become addresses/loads/stores as appropriate, calls use an ABI-aware signature, and source types are mapped to target-relevant IR types and metadata.

**Inference, bounded by evidence:** AST-to-IR lowering is a semantic compression boundary. Some high-level facts survive in metadata or intrinsics, but later LLVM passes should not be assumed to reconstruct arbitrary C syntax or macro provenance. This follows from the documented source-oriented AST and lower-level, language-independent LLVM IR designs; it is not a promise that every particular fact is discarded.

## 4. LLVM IR and the middle end

### 4.1 Representation and invariants

LLVM IR is a typed, static-single-assignment-based representation available equivalently as in-memory IR, bitcode, and human-readable assembly syntax. A `phi` instruction selects a value according to the predecessor edge and must occur before non-phi instructions in its basic block [LLVM Language Reference](https://llvm.org/docs/LangRef.html). Lattner and Adve's original peer-reviewed LLVM paper explains the design goal: a language-independent, typed, SSA-form common representation usable across compile-, link-, run-, and idle-time transformation [Lattner and Adve 2004](https://doi.org/10.1109/CGO.2004.1281665).

SSA is not merely notation. It gives each SSA value one definition, making def-use relationships explicit; joins require phi-like merging. Cytron et al. provide the foundational dominance-frontier construction and control-dependence account [Cytron et al. 1991](https://doi.org/10.1145/115372.115320). However, frontends often initially represent mutable C locals with stack slots (`alloca`, `load`, `store`) at `-O0`; promotion to SSA registers is performed when legal by transformations such as mem2reg/SROA. Hence “LLVM IR is SSA” does **not** mean “all source variables are immediately SSA virtual registers.” Memory is represented separately and can be mutated.

### 4.2 Pass managers and IR-unit hierarchy

LLVM's new pass manager schedules transformations and analyses over nested IR units: module, call-graph strongly connected component (CGSCC), function, and loop. Analyses can be cached and must be invalidated when transformations make results stale. Adaptors embed, for example, a function-pass manager inside a module pipeline. Grouping passes by IR unit improves locality and can affect optimization opportunities [Using the New Pass Manager](https://llvm.org/docs/NewPassManager.html).

A useful conceptual cycle is:

```text
IR invariant
  → analysis (dominators, alias information, loop structure, call graph, profiles)
  → legality/profitability decision
  → transformation (canonicalize, simplify, inline, vectorize, eliminate, specialize)
  → preserved-analysis declaration / invalidation
  → verifier or next pass
```

Analyses do not normally rewrite IR; transformations do. Yet the executed pipeline is not a fixed textbook list. `PassBuilder` constructs default pipelines for an optimization level and allows front ends, target machines, and plugins to inject passes. Clang also adds feature-driven passes such as sanitizer instrumentation [Using the New Pass Manager](https://llvm.org/docs/NewPassManager.html). The actual pipeline depends on at least LLVM revision, `-O0/-O1/-O2/-O3/-Os/-Oz`, target, LTO mode, profile data, language flags, and instrumentation.

### 4.3 What optimization levels mean—and do not mean

Optimization levels select policy bundles, not single algorithms or stable cross-version specifications. `-O0` prioritizes compile time/debuggability but still requires semantic lowering; `-O2`/`-O3` enable increasingly aggressive profitability choices; size modes alter the objective. The report should compare a specific version's observed IR/assembly rather than assert that `-O2` always runs an immutable named sequence.

Also, optimization preserves the semantics of **defined** source-language executions, not every accidental behavior of an ill-formed or undefined C program. Clang's user manual warns that the optimizer assumes no undefined behavior [Clang user's manual](https://clang.llvm.org/docs/UsersManual.html). A running example used to explain transformations should therefore avoid signed overflow, invalid shifts, out-of-bounds access, uninitialized reads, data races, and other undefined behavior unless the point is specifically to study that contract.

### 4.4 Current pass-manager boundary

Current LLVM documentation states that the LLVM IR optimization pipeline (the middle end) uses the new pass manager, whereas target-dependent backend code generation still uses the legacy pass manager; some LLVM IR passes inserted through target code-generation hooks count as backend codegen passes [Using the New Pass Manager](https://llvm.org/docs/NewPassManager.html). This is a further reason not to equate “LLVM pass” with “middle-end optimization pass.”

## 5. Target backend: LLVM IR to machine instructions

### 5.1 High-level target-independent code-generator sequence

LLVM's code-generator manual documents the following conceptual stages [LLVM Code Generator](https://llvm.org/docs/CodeGenerator.html):

1. **Instruction selection** translates LLVM IR operations into target-specific instructions, initially using virtual registers and respecting calling-convention/target constraints.
2. **Scheduling and formation** orders selected operations and forms `MachineInstr`s.
3. Optional **SSA-form machine-code optimizations** operate before physical register assignment.
4. **Register allocation** maps an unbounded virtual-register program onto the finite physical register file, inserting spill/reload code when needed and eliminating virtual-register references.
5. **Prologue/epilogue insertion** materializes stack-frame setup/teardown and resolves abstract frame locations after stack needs are known.
6. **Late machine-code optimization** cleans up final machine code.
7. **Code emission** lowers machine-code abstractions into assembly text or encoded object bytes.

This list is a conceptual backbone, not a universal exact pass order. Target hooks, optimization level, instruction-selector route, scheduling model, ABI, unwind/debug information, and LLVM version specialize it.

### 5.2 Lowering and legalization precede/participate in selection

LLVM IR is target-independent enough to express operations that a target cannot directly execute: unusual integer widths, vector shapes, intrinsics, atomics, calling conventions, and addressing computations. Backend lowering/legalization rewrites these to supported types/operations or target library calls. It is misleading to say instruction selection is a simple one-IR-instruction/one-opcode lookup.

For the GlobalISel route, the official core pipeline is explicit [GlobalISel pipeline](https://llvm.org/docs/GlobalISel/Pipeline.html):

```text
LLVM IR
  → IRTranslator → generic Machine IR (gMIR)
  → Legalizer → only target-supported operations/types
  → RegisterBankSelect → virtual registers assigned to register banks
  → InstructionSelect → target-specific MIR (no generic instructions remain)
```

GlobalISel works over a whole function and is intended as a reusable alternative to SelectionDAG/FastISel, but its documentation is marked work in progress and describes fallbacks/support variation [GlobalISel overview](https://llvm.org/docs/GlobalISel/). SelectionDAG instead constructs a dependency DAG, combines/legalizes it, matches target patterns, schedules nodes, and emits `MachineInstr`s. A report must not state “LLVM uses GlobalISel” or “LLVM uses SelectionDAG” without naming target, optimization mode, and version. **Selector choice is a configuration observation, not an architecture-wide invariant.**

Foundationally, practical instruction selection often uses tree/DAG pattern matching and dynamic programming. Fraser, Hanson, and Proebsting present a compact code-generator-generator based on such matching [Fraser et al. 1992](https://doi.org/10.1145/151640.151642). This paper explains the algorithmic lineage but does not prove that current LLVM implements that exact system.

### 5.3 Machine IR is not LLVM IR and not final assembly

LLVM's MIR serialization is a human-readable YAML-based testing representation for machine functions. It can embed an LLVM IR module, then serialize machine basic blocks, machine instructions, virtual/physical register operands, live-ins, frame information, and pass properties [MIR reference](https://llvm.org/docs/MIRLangRef.html). MIR is particularly valuable for isolating backend passes with `llc -run-pass`; the format is documented as work in progress, so it should be treated as a testing interface rather than a permanent user ABI.

### 5.4 Scheduling

Instruction scheduling chooses an order consistent with data/control dependencies while accounting for target latency, issue resources, and hazards. Depending on the pipeline, scheduling may occur around selection and/or after register allocation. Its objective can conflict with register pressure: exposing instruction-level parallelism can lengthen live ranges, while reducing pressure can constrain scheduling. Therefore “selection → allocation → scheduling” is not a universal single order; LLVM's own high-level description places SelectionDAG scheduling during selection/formation and permits later scheduling/peephole work.

### 5.5 Register allocation and spilling

Register allocation maps virtual live ranges to a finite, aliased, target-specific physical register set under pre-colored and calling-convention constraints. When simultaneously live values cannot all reside in registers, values are spilled to stack slots and later reloaded. The LLVM manual currently lists Fast, Basic, Greedy (the default optimized allocator), and PBQP allocators and explains that allocation removes virtual registers [LLVM Code Generator](https://llvm.org/docs/CodeGenerator.html).

Chaitin et al. established the classic interference-graph coloring formulation: simultaneously live quantities interfere and cannot receive the same register [Chaitin et al. 1981](https://doi.org/10.1016/0096-0551(81)90048-5). Current LLVM Greedy is not adequately described as “just graph coloring”; it uses live intervals, heuristics, splitting, eviction, and spill-cost machinery. The foundational paper supplies the model, while LLVM documentation supplies the implementation-level claim.

### 5.6 ABI and frame realization

Calls/returns, parameter locations, callee/caller-saved registers, stack alignment, red zones, unwind information, and frame-pointer policy are constrained by the target ABI. Prologue/epilogue insertion can only finalize stack offsets after allocation determines spill slots and saved registers. Thus identical source and even similar LLVM IR can yield different assembly under different triples, ABIs, CPU features, position-independent-code modes, or unwind/debug options.

## 6. Code emission, integrated assembly, and object files

### 6.1 The MC layer

After machine passes, LLVM lowers `MachineFunction`/`MachineInstr` structures into the MC layer. `MCInst` carries a target opcode and operands; `MCStreamer` is an assembler-like interface for labels, sections, directives, data, and instructions. `MCAsmStreamer` prints textual assembly, whereas `MCObjectStreamer` implements integrated assembly and writes an object representation. A target `MCCodeEmitter` encodes `MCInst`s into bytes and relocation/fixup information [LLVM Code Generator, MC layer](https://llvm.org/docs/CodeGenerator.html#the-mc-layer).

This yields two legitimate routes:

```text
MachineInstr → MCInst → MCAsmStreamer → .s → external assembler → .o
MachineInstr → MCInst → MCObjectStreamer + MCCodeEmitter ─────────→ .o
```

The second route is why `clang -c` may never materialize assembly text. The Clang command guide explicitly notes integrated assembly [Clang command guide](https://clang.llvm.org/docs/CommandGuide/clang.html).

### 6.2 What the assembler contributes

An assembler parses mnemonics, operands, labels, and directives; checks target encodings; lays out sections; resolves locally decidable expressions/labels; emits instruction/data bytes; constructs symbol and string tables; and emits relocations for addresses/distances that cannot yet be fixed. An object file is therefore **not merely machine-code bytes**. It is a structured container (commonly ELF, COFF, or Mach-O) containing sections, symbols, relocations, alignment, and often debug/unwind metadata. LLVM's MC layer supports multiple object formats by target [LLVM Code Generator](https://llvm.org/docs/CodeGenerator.html#object-file-format).

### 6.3 Where this task stops and linking begins

The linker consumes objects and libraries, resolves symbol references, chooses final addresses/layout, applies relocations, performs archive extraction and possibly link-time optimization, and emits an executable/shared library. In the driver graph, linking is a subsequent action; it is not part of instruction selection, code emission, or assembly. Some boundaries blur under LTO because objects can contain LLVM bitcode and optimization/code generation can be deferred, but the conceptual responsibilities remain useful.

## 7. Running-example evidence plan

For a single SysY-like C example containing arithmetic, a call, an `if`, and a loop, capture the following **from the same source revision and toolchain**:

1. Source plus explicit target/ABI/optimization flags.
2. `-ccc-print-phases` and `-###`: contrast the driver action graph with actual jobs.
3. `-E`: mark include expansion, macro replacement, conditional removal, and line markers.
4. `-ast-dump -fsyntax-only`: identify declarations, statement/expression structure, inferred types, lvalue-to-rvalue casts, and source ranges.
5. `-O0 -emit-llvm -S`: map AST constructs to blocks, branches, calls, memory operations, and (where present) phi nodes.
6. `-O2 -emit-llvm -S` plus a filtered pass trace: explain only transformations actually observed (for example promotion, folding, CFG simplification, inlining, loop canonicalization/vectorization).
7. Target `.s`: map IR values/control flow to instructions, calling convention, register choices, stack frame, and labels.
8. Object inspection (`llvm-readobj`, `llvm-objdump -dr`): distinguish bytes, sections, symbols, and relocations.
9. Link map or executable disassembly, if linking is covered elsewhere: demonstrate which unresolved object references were resolved.

### Causal questions to ask at every boundary

| Boundary | Ask | Evidence that would falsify a weak explanation |
|---|---|---|
| source → preprocessed tokens | Which spellings were included, excluded, or macro-generated? | Claiming a macro is a runtime function when it has disappeared before parsing |
| tokens → AST | What type/name/implicit-conversion facts were established? | AST node types or diagnostics inconsistent with the proposed parse |
| AST → LLVM IR | How were evaluation order, control flow, objects, and ABI-relevant operations made explicit? | Missing required branch/call/memory effect |
| unoptimized → optimized IR | Which legality fact and profitability policy justified the rewrite? | Undefined-behavior-dependent example or pass trace contradicting attribution |
| LLVM IR → MIR | What was legalized, selected, or turned into a target pseudo-instruction? | Unsupported claim of one-to-one instruction mapping |
| MIR → allocated MIR | Which live ranges interfere, split, spill, or become physical registers? | Final virtual registers after the allocation invariant should hold |
| allocated MIR → object | Which instructions/directives became bytes, symbols, sections, and relocations? | Treating a relocation placeholder as a final runtime address |

## 8. Claims to avoid or qualify

| Tempting claim | Better, evidence-aligned claim |
|---|---|
| “Clang runs five programs.” | The driver constructs five conceptual actions; tool binding may fuse them into one `-cc1` job or use external tools. |
| “Preprocessing happens before lexing.” | Conceptual translation phases begin with preprocessing-token recognition; in Clang lexing and directive/macro processing are interleaved. |
| “A header is pasted as text.” | `#include` contributes a scanned preprocessing-token stream; textual concatenation is only an approximation. |
| “Parsing produces an AST, then semantic analysis annotates it.” | Clang's recursive-descent parser calls Sema incrementally; Sema validates and constructs typed AST nodes. |
| “LLVM IR is machine independent.” | LLVM IR is target-portable but modules carry a target triple/data layout and frontend lowering can encode ABI/target choices. |
| “`-O2` means this fixed pass list.” | `-O2` asks a particular LLVM revision/configuration to build a policy pipeline; inspect the actual run. |
| “The backend uses SelectionDAG.” | LLVM supports SelectionDAG, FastISel, and GlobalISel routes; identify the route for the exact target/mode/version. |
| “Register allocation is graph coloring.” | Interference coloring is foundational; LLVM's production allocators combine live-interval analysis, splitting, spilling, and heuristics. |
| “Assembly is machine code.” | Assembly is textual target syntax; the assembler emits encoded bytes plus sections, symbols, and relocations. |
| “The compiler resolves function addresses.” | The compiler/assembler usually emit symbol references and relocations; the linker or dynamic loader resolves final addresses. |

## 9. Evidence assessment and open uncertainty

* **High confidence:** the driver/action/job distinction; Clang front-end component relationships; LLVM IR/new-PM hierarchy; the documented backend and MC-layer responsibilities. These come from current upstream manuals and a reproducible local driver probe.
* **Configuration-sensitive:** exact pass order, selector choice, allocator choice, calling convention details, assembler integration, and emitted instruction sequence. These must be measured for the report's pinned toolchain.
* **Documentation limitations:** parts of the LLVM code-generator and MIR/GlobalISel manuals explicitly say “work in progress” or leave subsections incomplete. Source and pass traces are stronger evidence for a claim about a specific revision.
* **Historical-paper limitation:** foundational papers explain enduring abstractions but do not establish current LLVM implementation details. Use them for conceptual lineage, not as substitutes for upstream documentation or experiments.

Evidence that would materially revise these notes: a target/version-specific pass trace contradicting the described route; upstream removal of the legacy codegen pass manager; a driver configuration using external preprocessing/assembly; or source evidence showing a current implementation has changed beyond its published manual.

## 10. BibTeX-ready source metadata

```bibtex
@online{ClangCommandGuide,
  author  = {{LLVM Project}},
  title   = {clang---the Clang C, C++, and Objective-C Compiler},
  url     = {https://clang.llvm.org/docs/CommandGuide/clang.html},
  urldate = {2026-09-22}
}

@online{ClangDriverInternals,
  author  = {{LLVM Project}},
  title   = {Driver Design and Internals},
  url     = {https://clang.llvm.org/docs/DriverInternals.html},
  urldate = {2026-09-22}
}

@online{ClangToolchain,
  author  = {{LLVM Project}},
  title   = {Assembling a Complete Toolchain},
  url     = {https://clang.llvm.org/docs/Toolchain.html},
  urldate = {2026-09-22}
}

@online{ClangCommandLineReference,
  author  = {{LLVM Project}},
  title   = {Clang Command Line Argument Reference},
  url     = {https://clang.llvm.org/docs/ClangCommandLineReference.html},
  urldate = {2026-09-22}
}

@online{ClangUsersManual,
  author  = {{LLVM Project}},
  title   = {Clang Compiler User's Manual},
  url     = {https://clang.llvm.org/docs/UsersManual.html},
  urldate = {2026-09-22}
}

@online{ClangInternals,
  author  = {{LLVM Project}},
  title   = {Clang CFE Internals Manual},
  url     = {https://clang.llvm.org/docs/InternalsManual.html},
  urldate = {2026-09-22}
}

@online{ClangASTIntroduction,
  author  = {{LLVM Project}},
  title   = {Introduction to the Clang AST},
  url     = {https://clang.llvm.org/docs/IntroductionToTheClangAST.html},
  urldate = {2026-09-22}
}

@online{GNUCPP,
  author  = {{Free Software Foundation}},
  title   = {The C Preprocessor},
  url     = {https://gcc.gnu.org/onlinedocs/cpp/},
  urldate = {2026-09-22}
}

@online{GNUCPPInitialProcessing,
  author  = {{Free Software Foundation}},
  title   = {The C Preprocessor: Initial Processing},
  url     = {https://gcc.gnu.org/onlinedocs/cpp/Initial-processing.html},
  urldate = {2026-09-22}
}

@online{GNUCPPIncludeOperation,
  author  = {{Free Software Foundation}},
  title   = {The C Preprocessor: Include Operation},
  url     = {https://gcc.gnu.org/onlinedocs/cpp/Include-Operation.html},
  urldate = {2026-09-22}
}

@online{GNUCPPMacroExpansion,
  author  = {{Free Software Foundation}},
  title   = {The GNU C Preprocessor Internals: Macro Expansion Algorithm},
  url     = {https://gcc.gnu.org/onlinedocs/cppinternals/Macro-Expansion.html},
  urldate = {2026-09-22}
}

@online{LLVMLangRef,
  author  = {{LLVM Project}},
  title   = {LLVM Language Reference Manual},
  url     = {https://llvm.org/docs/LangRef.html},
  urldate = {2026-09-22}
}

@online{LLVMNewPassManager,
  author  = {{LLVM Project}},
  title   = {Using the New Pass Manager},
  url     = {https://llvm.org/docs/NewPassManager.html},
  urldate = {2026-09-22}
}

@online{LLVMDebugging,
  author  = {{LLVM Project}},
  title   = {Debugging LLVM},
  url     = {https://llvm.org/docs/DebuggingLLVM.html},
  urldate = {2026-09-22}
}

@online{LLVMOptCommand,
  author  = {{LLVM Project}},
  title   = {opt---LLVM Optimizer},
  url     = {https://llvm.org/docs/CommandGuide/opt.html},
  urldate = {2026-09-22}
}

@online{LLVMCodeGenerator,
  author  = {{LLVM Project}},
  title   = {The LLVM Target-Independent Code Generator},
  url     = {https://llvm.org/docs/CodeGenerator.html},
  urldate = {2026-09-22}
}

@online{LLVMGlobalISelPipeline,
  author  = {{LLVM Project}},
  title   = {GlobalISel: Core Pipeline},
  url     = {https://llvm.org/docs/GlobalISel/Pipeline.html},
  urldate = {2026-09-22}
}

@online{LLVMGlobalISel,
  author  = {{LLVM Project}},
  title   = {Global Instruction Selection},
  url     = {https://llvm.org/docs/GlobalISel/},
  urldate = {2026-09-22}
}

@online{LLVMMIR,
  author  = {{LLVM Project}},
  title   = {Machine IR (MIR) Format Reference Manual},
  url     = {https://llvm.org/docs/MIRLangRef.html},
  urldate = {2026-09-22}
}

@inproceedings{LattnerAdve2004LLVM,
  author    = {Chris Lattner and Vikram Adve},
  title     = {LLVM: A Compilation Framework for Lifelong Program Analysis and Transformation},
  booktitle = {Proceedings of the 2004 International Symposium on Code Generation and Optimization (CGO)},
  pages     = {75--86},
  year      = {2004},
  publisher = {IEEE Computer Society},
  doi       = {10.1109/CGO.2004.1281665},
  url       = {https://doi.org/10.1109/CGO.2004.1281665}
}

@article{CytronEtAl1991SSA,
  author  = {Ron Cytron and Jeanne Ferrante and Barry K. Rosen and Mark N. Wegman and F. Kenneth Zadeck},
  title   = {Efficiently Computing Static Single Assignment Form and the Control Dependence Graph},
  journal = {ACM Transactions on Programming Languages and Systems},
  volume  = {13},
  number  = {4},
  pages   = {451--490},
  year    = {1991},
  doi     = {10.1145/115372.115320},
  url     = {https://doi.org/10.1145/115372.115320}
}

@article{ChaitinEtAl1981RegisterAllocation,
  author  = {Gregory J. Chaitin and Marc A. Auslander and Ashok K. Chandra and John Cocke and Martin E. Hopkins and Peter W. Markstein},
  title   = {Register Allocation via Coloring},
  journal = {Computer Languages},
  volume  = {6},
  number  = {1},
  pages   = {47--57},
  year    = {1981},
  doi     = {10.1016/0096-0551(81)90048-5},
  url     = {https://doi.org/10.1016/0096-0551(81)90048-5}
}

@article{FraserHansonProebsting1992CodeGenerator,
  author  = {Christopher W. Fraser and David R. Hanson and Todd A. Proebsting},
  title   = {Engineering a Simple, Efficient Code-Generator Generator},
  journal = {ACM Letters on Programming Languages and Systems},
  volume  = {1},
  number  = {3},
  pages   = {213--226},
  year    = {1992},
  doi     = {10.1145/151640.151642},
  url     = {https://doi.org/10.1145/151640.151642}
}
```
