# Compiler Frontiers: Evidence Map for an “Understanding Compiler Systems” Survey

> Working language: English. This is a research artifact, not publication prose. Claims are deliberately tagged by epistemic status and paired with primary literature or official production documentation.

## 0. Scope, decision purpose, and evidence policy

This note supports advanced/outlook chapters of a survey that follows one program through a complete compiler toolchain. Its purpose is not to append a catalogue of fashionable techniques, but to answer a harder systems question: **where can a classical pipeline be generalized, validated, specialized, or made adaptive without losing semantic and operational control?**

The map covers: verified compilation and translation validation; superoptimization and equality saturation; profile-guided and machine-learning-guided optimization; polyhedral and heterogeneous compilation; JIT/AOT; full and thin LTO; incremental and reproducible builds; and debugging/security only under explicit compiler error or attacker models.

### Evidence labels

| Label | Meaning |
|---|---|
| **Observed** | Directly reported by a peer-reviewed study or current official implementation documentation. |
| **Inferred** | A synthesis that follows from multiple observations but is not itself established by one experiment. |
| **Hypothesized** | A plausible research direction whose mechanism and falsification conditions should be stated. |
| **Recommended** | A concrete editorial or engineering choice for the survey/case study. |

### Maturity scale

| Level | Interpretation |
|---|---|
| **P5 — routine production** | Stable, documented, broadly deployed; remaining risk is ordinary engineering/measurement. |
| **P4 — production for selected workloads** | Shipping or upstream production support, but requires workload/toolchain discipline. |
| **P3 — deployable specialist technology** | Robust implementation and convincing studies, but narrow domain or nontrivial integration cost. |
| **P2 — research prototype with transferable ideas** | Reproducible artifact or upstream experiment; benefits shown under bounded conditions. |
| **P1 — exploratory** | Promising mechanism, limited validation, rapidly changing semantics or tooling. |

No maturity label is a universal score. It is conditional on source language, target, workload distribution, compile-time budget, and assurance objective.

---

## 1. Integrating the frontiers with one end-to-end case study

Use a small but structurally rich numerical kernel rather than unrelated micro-examples. A suitable running program is a bounded matrix/vector kernel with a reduction and a guarded scalar fallback, called through a separately compiled helper and executed repeatedly with representative and adversarial input sizes. The same source can expose every frontier without pretending that every technique is useful for this tiny program.

| Classical observation point | Frontier question attached to the same artifact | Minimal discriminating experiment |
|---|---|---|
| Source/AST and language semantics | What behavior is the compiler obligated to preserve? | Specify defined inputs; separately show why signed overflow, out-of-bounds access, races, and unsequenced side effects invalidate naïve equivalence tests. |
| High-level loop/tensor IR | Can affine dependence or domain knowledge expose legal reordering, tiling, fusion, or device mapping? | Compare an affine loop nest with a data-dependent bound or indirect access that leaves the polyhedral subset. |
| LLVM IR before/after a pass | Can each optimization result be checked rather than trusting the pass implementation? | Feed the pair to Alive2; record `correct`, counterexample, timeout, or unsupported-feature outcome as distinct results. |
| Optimization search | Can rewrites be explored globally rather than committed greedily? | Construct a small e-graph of algebraic/strength-reduction alternatives; state the extraction cost model and saturation budget. |
| Code generation policy | Can observations or learned policy improve a hard heuristic? | Compare static `-O2/-O3`, representative PGO, deliberately shifted PGO, and—only if infrastructure is available—an MLGO policy. |
| Translation units and link | Which optimizations require cross-module visibility? | Build without LTO, with full LTO, and with ThinLTO; inspect import/inlining and measure build resources as well as runtime. |
| Final binary | What opportunities become visible only after layout and linking? | Apply sample-profile post-link optimization such as BOLT where the object/binary meets its input requirements. |
| Execution | Is the compilation decision fixed before deployment or adapted at run time? | Contrast AOT output with a JIT thought experiment or LLVM ORC prototype; account for warm-up, memory, and deployment policy. |
| Build graph | Can an edit reuse prior work without returning a stale artifact? | Make a semantic edit and a nonsemantic edit; inspect invalidated queries/objects, then compare incremental output against a clean build. |
| Artifact provenance | Can an independent builder reproduce the bits? | Rebuild in two controlled environments; use `diffoscope`-style diagnosis for paths, timestamps, archive order, locale, randomness, and tool versions. |
| Failure investigation | How do we distinguish program bugs, wrong-code bugs, debug-metadata defects, and malicious toolchains? | Use explicit oracles and threat models; do not mix sanitizers, differential testing, translation validation, and DDC as if they prove the same property. |

**Recommended narrative rule.** Each outlook section should return to this one artifact and ask (1) which representation contains the necessary information, (2) what semantic relation is claimed, (3) what observation or cost model drives the choice, (4) where the trusted computing base lies, and (5) what evidence would falsify the benefit or correctness claim. This preserves the “deep systems tour” style while preventing the outlook from becoming disconnected trend reporting.

---

## 2. Verified compilation and translation validation

### 2.1 Two assurance architectures

Let `S` be a source program, `C` the compiler, `T = C(S)` the target program, and `Beh(P)` a set of observable behaviors under a language semantics. An optimizing compiler normally needs a refinement-style theorem, not simple textual equality:

\[
  C(S)=T \Longrightarrow Beh(T) \preceq Beh(S).
\]

The exact direction and relation depend on how undefined behavior, nondeterminism, divergence, I/O traces, and compiler failure are modeled. The distinction matters: “the outputs matched on our examples” is neither compiler correctness nor translation validation.

| Architecture | Proof/checking unit | Principal strength | Principal boundary |
|---|---|---|---|
| **Verified compiler** (CompCert) | For successfully compiled source ASTs produced by the formalized frontend boundary, prove preservation across the modeled and verified pass chain. | Once the proof and assumptions apply, assurance is not limited to tested transformations. | Large proof/semantics engineering cost; proof covers a stated pipeline, not automatically the preprocessor, assembler, linker, libraries, hardware, or every language extension. |
| **Verified translation validator** | Prove a smaller checker sound, then let an arbitrary optimizer propose results and check every result. | Complex heuristic transformation implementation stays outside the trusted proof; demonstrated for scheduling and lazy code motion in the cited CompCert-era case studies. | The checker is normally specific to a transformation family and formal semantics. |
| **Engineering translation validation** (Alive2) | Check a particular source/target IR pair, usually by reduction to SMT. | Can be retrofitted around aggressive, evolving production compilers without verifying their implementations. | Bounded/partial models, solver timeouts, unsupported constructs, and the unverified checker/solver prevent interpreting “not disproved” as universal compiler correctness. |
| **Certifying compilation / proof-carrying code** | Producer ships code plus a certificate; consumer checks it against a published safety policy. | Expensive proof search can remain untrusted while the consumer has a small checker. | Policy-relative safety is not automatically source/target equivalence; proof size, policy design, and certificate production are operational costs. |

### 2.2 CompCert: what is actually established

- **Observed.** CompCert is a realistic optimizing C compiler whose core compilation from a typed CompCert C AST to assembly AST is mechanically proved in Coq/Rocq. The current official documentation explicitly describes multiple intermediate languages and pass-by-pass semantic-preservation proofs. It targets ARM/AArch64, PowerPC, RISC-V, and x86 families. Sources: [CompCert overview](https://compcert.org/), [commented proof development](https://compcert.org/doc/), and Leroy’s peer-reviewed overview (CACM 2009, DOI below).
- **Observed boundary, often lost in summaries.** The official manual states that preprocessing, some elaboration/presimplification, textual assembly production, assembling, and linking are outside the principal verified core; the manual estimates roughly 90% of compiler algorithms are proved and names the remaining categories. Therefore “CompCert proves source file to executable correct” is too strong without additional validated components and environmental assumptions. Source: [CompCert manual, trustworthy compiler and structure](https://compcert.org/man/manual001.html).
- **Observed.** The semantic-preservation theorem is conditional on successful compilation and on the source semantics. The target behavior may refine an allowed source behavior. Programs invoking C undefined behavior do not receive the intuitive “same result” guarantee students often assume.
- **Inferred.** CompCert’s greatest pedagogical value here is architectural: intermediate languages are proof interfaces. Each lowering makes a smaller semantic claim, and whole-pipeline assurance is obtained by composition. This mirrors the ordinary compiler pipeline but turns “phase correctness” into an explicit theorem.
- **Maturity: P4 for safety-critical embedded C, P2–P3 as a replacement for general-purpose GCC/Clang workloads.** It is commercially supported and used in high-assurance contexts, but language coverage, optimization repertoire, surrounding toolchain trust, certification objectives, and ecosystem constraints make adoption workload-specific.
- **Observed adversarial audit of the trusted base.** Monniaux and Boulmé enumerate ways an incorrect executable can still arise despite the verified core: mismatches between formal and actual source/target models, front-end/printer/assembler/ABI boundaries, extraction/runtime/tooling, and interfaces to external algorithms. This is the right counterweight to slogan-level claims. Source: “The Trusted Computing Base of the CompCert Verified Compiler,” ESOP 2022, DOI `10.1007/978-3-030-99336-8_8`, [preprint](https://arxiv.org/abs/2201.10280).

### 2.3 Alive/Alive2: validation attached to an evolving optimizer

- **Observed.** Alive introduced a domain-specific language and automated verification for LLVM peephole optimizations; Alive2 validates LLVM IR transformations and was designed and deployed against LLVM. The PLDI 2021 paper calls it *bounded* translation validation and reports finding numerous LLVM bugs. Primary source: [Alive2 PLDI 2021 landing page](https://web.ist.utl.pt/nuno.lopes/pubs.php?id=alive2-pldi21), DOI `10.1145/3453483.3454030`.
- **Mechanism.** A validator encodes source and target executions as formulas and asks an SMT solver for a counterexample to refinement. On a counterexample it can produce concrete values that turn a semantic dispute into a reproducible compiler bug. A proof is relative to the validator’s LLVM semantics, memory model, loop bound/unrolling strategy, and supported features.
- **Observed limitation.** “Bounded” is substantive: loops and some state spaces cannot simply be exhausted. Timeouts and unsupported semantics are neither correctness proofs nor miscompilation evidence. Reports must keep four outcomes separate: validated, refuted with counterexample, unknown/timeout, and unsupported.
- **Inferred production position.** Alive2 is highly mature as an optimization-development and regression-validation instrument, but not a transparent certificate for every end-to-end Clang build. It complements fuzzing: fuzzing finds executions that differ; translation validation reasons over a modeled input space for a particular transform.
- **Maturity: P3–P4 inside LLVM optimization engineering; P2 for whole-program executable assurance.**

### 2.4 Verified validators and proof-carrying code

- **Observed.** Pnueli, Siegel, and Singerman introduced translation validation as a posteriori checking of a compiler run (TACAS 1998, DOI `10.1007/BFb0054170`). Tristan and Leroy later mechanically verified validators for instruction scheduling (POPL 2008, DOI `10.1145/1328438.1328444`) and lazy code motion (PLDI 2009, DOI `10.1145/1542476.1542512`). The latter adds checks such as anticipability so moving a potentially failing operation cannot turn divergence into a crash.
- **Inferred.** This architecture is attractive when the transformation/search algorithm changes often but the acceptance relation is compact and stable. The optimizer may be heuristic and untrusted; only accepted outputs inherit the checker theorem.
- **Observed.** Necula’s proof-carrying code (PCC) lets the code consumer publish a safety policy and check a producer-supplied proof locally. Foundational PCC further minimizes trusted axioms/checking machinery. Sources: Necula, POPL 1997, DOI `10.1145/263699.263712`, [paper](https://www.cs.tufts.edu/comp/150CMP/papers/necula97pcc.pdf); Appel, LICS 2001, [paper](https://www.cs.princeton.edu/~appel/papers/fpcc.pdf).
- **Maturity:** verified pass-specific validators P3–P4 inside formal toolchains; PCC P2 for contemporary general compiler deployment despite high conceptual maturity. The durable pattern is untrusted expensive search plus small trusted checking.

### 2.5 Editorial experiment and falsification criteria

For the running kernel, save LLVM IR immediately before and after a simple transformation, then invoke Alive2. Include one deliberately invalid rewrite (for example, one that mishandles poison/overflow preconditions). A useful report records the exact LLVM/Alive2 revisions and solver, because IR semantics change.

The chapter should be revised if any of the following evidence appears: the example relies on undefined behavior; the validator does not support the relevant operation; a solver timeout is presented as validation; or a source-to-executable claim silently crosses unverified preprocessing/linking/runtime components.

---

## 3. Superoptimization and equality saturation

### 3.1 Separate three ideas that are often conflated

1. **Superoptimization** searches a program space for a semantically equivalent program minimizing a cost.
2. **Equality saturation** repeatedly adds equivalent expressions to an e-graph without committing to a rewrite order, then extracts one expression under a cost model.
3. **Solver-aided optimization discovery** can use synthesis to discover a rewrite offline, after which humans or validators integrate it into a conventional compiler.

The first asks for the best program within a bounded search space. The second changes the representation of rewrite search. Neither guarantees real hardware optimality: the answer is only as good as the semantics, search boundary, and cost model.

### 3.2 STOKE and Souper

- **Observed.** STOKE formulates loop-free x86-64 binary optimization as stochastic search and uses a cost combining correctness and performance; the ASPLOS 2013 prototype found sequences competitive with strong compilers and some expert assembly on evaluated kernels. Source: Schkufza, Sharma, and Aiken, “Stochastic Superoptimization,” ASPLOS 2013, DOI `10.1145/2451116.2451150`; [Microsoft Research publication page](https://www.microsoft.com/en-us/research/publication/stochastic-superoptimization/).
- **Observed limitation.** Stochastic search sacrifices completeness; practical correctness mechanisms rely on bounded tests and formal checks whose assumptions must be stated. Search cost grows sharply with sequence/state complexity. The [STOKE repository](https://github.com/StanfordPL/stoke) is an inactive research artifact, not a maintained production optimizer.
- **Observed.** Souper synthesizes optimizations for LLVM’s integer SSA fragments. Its authors report that compiler releases incorporated Souper-discovered optimizations manually, while an automated Souper pass reduced the evaluated Clang binary size. Source: Sasnauskas et al., “Souper: A Synthesizing Superoptimizer,” arXiv:1711.04422 and [repository](https://github.com/google/souper).
- **Inferred production lesson.** The durable pattern is **offline discovery → independent validation → conventional rewrite**, not placing an unbounded search in every build. This amortizes solver/search cost and preserves predictable compilation. Archived or inactive repositories further support classifying STOKE/Souper as idea generators rather than drop-in defaults.
- **Maturity: P2 as online optimizers; P3 as offline optimization-discovery tools.**

### 3.3 E-graphs and `egg`

- **Observed.** An e-graph compactly represents a congruence relation over expressions. Equality saturation delays destructive choice: rewrites add equivalent nodes until a resource/iteration condition, after which extraction optimizes a stated cost. The `egg` paper contributes rebuilding and e-class analyses and reports strong results across three case studies. Source: Willsey et al., “egg: Fast and Extensible Equality Saturation,” POPL 2021, DOI `10.1145/3434304`; [conference page](https://popl21.sigplan.org/details/POPL-2021-research-papers/23/egg-Fast-and-Extensible-Equality-Saturation).
- **The central risk is not rewrite ordering but growth.** Equality saturation removes phase-ordering for represented equalities by retaining alternatives; it does not remove the need for termination control. Rewrite sets can explode the e-graph, and extraction itself may be difficult under global costs, sharing, register pressure, target scheduling, or nonlinear objectives.
- **Semantic preconditions remain first-class.** Algebraic equalities may fail for IEEE floating point, overflow, poison/undef, memory aliasing, exceptions, or effects. An e-graph library maintains congruence; it does not automatically prove domain-specific rewrites sound.
- **Observed production bridge.** Recent Cranelift/Wasmtime work uses an e-graph-based optimization framework adapted to production constraints, with an acyclic representation and fuel/resource bounds rather than naïve unconstrained saturation. The accepted Cranelift RFC and current Wasmtime implementation show that e-graph ideas can ship after changing the algorithm to meet deterministic compile-time and memory budgets.
- **Maturity: `egg`-style general equality saturation P2–P3; constrained e-graph rewriting in Cranelift P4 for its supported optimization domain.**

The production citation is the [accepted Bytecode Alliance Cranelift e-graph RFC](https://github.com/bytecodealliance/rfcs/blob/main/accepted/cranelift-egraph.md), together with the current [Cranelift implementation/documentation](https://github.com/bytecodealliance/wasmtime/tree/main/cranelift). The RFC reports encouraging compile-time and runtime measurements on two motivating Wasm workloads, but that is design evidence, not a broad independent benchmark. Crucially, Cranelift does **not** simply run the general `egg` library to full saturation: it uses an acyclic e-graph embedded in a conventional CFG, ISLE rules, optimization fuel, effect boundaries, heuristic costs, and extensive fuzzing.

Three research boundaries deserve explicit mention:

1. **Matching:** relational e-matching recasts pattern search as database joins and can substantially reduce matching cost. Source: Zhang et al., POPL 2022, DOI `10.1145/3498696` (consult the corrigendum).
2. **Extraction:** optimal extraction with global sharing/cycles is not a trivial tree walk. Goharshady, Lam, and Parreaux prove general hardness results and develop algorithms for sparse/low-treewidth cases: OOPSLA 2024, DOI `10.1145/3689801`.
3. **Analysis + rewriting:** `egglog` combines equality saturation with Datalog/lattice analyses so side information can participate declaratively. Source: Zhang et al., PLDI 2023, DOI `10.1145/3591239`. This is a promising P1–P2 substrate, not yet evidence of universal production compilation.

### 3.4 Case-study use

Use a pure integer subexpression from the running kernel. Show a local greedy path and an e-graph containing alternative factorizations/strength reductions. Annotate every rewrite with its arithmetic domain and overflow assumptions. Extract once with an instruction-count model and once with a target-sensitive latency/code-size model. If choices differ, the experiment makes a crucial point: equality is semantic, but “best” is empirical and target-dependent.

Do **not** claim that equality saturation solves compiler phase ordering in general. It solves ordering among admitted equality rewrites inside a bounded representation; legality analyses, lowering choices, effects, profitability, and resource limits remain.

---

## 4. Profile-guided and machine-learning-guided optimization

### 4.1 PGO as a causal loop, not a compiler flag

The correct abstraction is:

\[
\text{program + build} \rightarrow \text{instrument/sample} \rightarrow
\text{workload executions} \rightarrow \text{profile} \rightarrow
\text{rebuild/relink/rewrite} \rightarrow \text{evaluation}.
\]

- **Observed.** Clang supports instrumentation-based and sample-based PGO. Profiles influence branch/layout, inlining, and other decisions; the official manual warns that profiling inputs must represent typical behavior because unexercised or disproportionately exercised code can receive poor decisions. Source: [Clang User’s Manual, Profile Guided Optimization](https://clang.llvm.org/docs/UsersManual.html#profile-guided-optimization).
- **Observed.** AutoFDO converts low-overhead hardware sampling profiles for GCC/LLVM use and was motivated by reducing the deployment friction of instrumentation. Google reported substantially broader internal adoption and production improvements in its CGO 2016 evaluation. Primary source: Chen et al., “AutoFDO: Automatic Feedback-Directed Optimization for Warehouse-Scale Applications,” CGO 2016, DOI `10.1145/2854038.2854044`, [paper PDF](https://research.google.com/pubs/archive/45290.pdf).
- **Observed.** BOLT is a post-link binary optimizer that uses execution profiles to change code layout and other binary-level properties. Its CGO 2019 study evaluates Meta/Facebook data-center workloads and open-source compilers; BOLT is now in LLVM, and LLVM’s own build documentation composes PGO, ThinLTO, and BOLT. Sources: Panchenko et al., “BOLT,” CGO 2019, DOI `10.1109/CGO.2019.8661201`; [LLVM advanced builds](https://llvm.org/docs/AdvancedBuilds.html).
- **Observed.** Propeller performs profile-guided relinking for warehouse-scale applications, targeting layout while fitting distributed build infrastructure. Source: Shen et al., ASPLOS 2023, DOI `10.1145/3575693.3575727`.

### 4.2 The actual threat to validity is distribution shift

Let `P_train(x)` be the profile workload distribution and `P_deploy(x)` deployment. PGO optimizes an empirical objective under `P_train`; benefit under deployment is an inference that depends on similarity between these distributions. Code-version/profile mismatch adds another axis.

**Recommended evaluation:** define at least three workload sets: training, held-out in-distribution evaluation, and intentionally shifted evaluation. Report runtime distributions and tail behavior, code size, build/profile collection cost, and cold-start effects. A single train-and-test-on-the-same-run number is optimistically biased.

**Maturity:** instrumentation and sample PGO P5 for performance-sensitive production; post-link BOLT P4 because binaries, profiles, relocation/debug information, and deployment tooling must satisfy operational constraints.

### 4.3 ML-guided optimization: replace a heuristic, not semantics

- **Observed.** LLVM MLGO provides infrastructure for replacing selected compiler heuristics with learned policies. Current official documentation names inlining-for-size and greedy register-allocation eviction integrations and explains that training orchestration is external to LLVM. Source: [LLVM MLGO documentation](https://llvm.org/docs/MLGO.html).
- **Observed.** Trofin et al. integrated a learned inlining-for-size policy into LLVM and reported up to 7% size reduction relative to `-Oz` on evaluated tasks, together with cross-target/time generalization experiments. This is evidence for one decision and objective, not evidence that ML generally supersedes optimizer design. Source: “MLGO: a Machine Learning Guided Compiler Optimizations Framework,” 2021, arXiv:2101.04808; [Google Research record](https://research.google/pubs/mlgo-a-machine-learning-guided-compiler-optimizations-framework/).
- **Mechanism.** The compiler exposes an observation/state, an action set, and a reward/objective. A production model needs deterministic, low-overhead inference; feature/version compatibility; a safe fallback; monitoring for quality drift; and correctness-independent integration. The learned policy should normally choose among already legal actions. If ML generates transformations, independent validation becomes much more important.
- **Inferred.** ML is strongest when the legality is conventional but profitability has a high-dimensional, workload-dependent cost surface. It is weakest where labels/rewards are noisy, target coverage changes quickly, compile-time is strict, or the model can exploit benchmark artifacts.
- **Hypothesis worth testing.** A learned policy may complement—not replace—PGO: static program features describe what code is; profiles describe how deployed code behaves. The hypothesis fails if a strong PGO-aware baseline matches the model on held-out projects/targets or if inference/training/maintenance cost outweighs gains.
- **Maturity: MLGO infrastructure and upstream advisor integrations P3; organization-specific deployed models may reach P4 only where deployment evidence is cited; broad phase ordering or generative optimization P1–P2.** Upstream integration does not mean that a generally applicable pretrained policy ships in every LLVM build.

### 4.4 Baseline fairness checklist

| Question | Why it matters |
|---|---|
| Is the baseline the current compiler heuristic at the same revision and compile-time budget? | Old or under-tuned baselines exaggerate ML benefit. |
| Are training and test projects disjoint, including forks/near-duplicates? | Leakage makes generalization claims meaningless. |
| Is the profile collection budget equal? | An ML+autotuning system may secretly consume far more measurement. |
| Are model inference, feature extraction, failed compilations, and binary size counted? | Deployment cost is part of the system objective. |
| Are multiple architectures and compiler revisions held out? | Portability and temporal drift are core compiler realities. |
| Are regressions/tails shown rather than only geometric means? | A compiler policy is applied to heterogeneous programs; catastrophic outliers matter. |

---

## 5. Polyhedral and heterogeneous compilation

### 5.1 What the polyhedral model buys—and what it assumes

For a **static-control part** (SCoP), loop iteration domains and memory accesses are represented with affine integer constraints/functions. Dependences become relations over integer points, and schedules become affine maps. This exposes legality for transformations such as interchange, fusion/fission, skewing, tiling, parallelization, and locality optimization.

- **Observed.** Pluto demonstrated an end-to-end automatic polyhedral parallelizer/locality optimizer driven by integer-linear optimization for affine loop nests. Source: Bondhugula et al., “A Practical Automatic Polyhedral Parallelizer and Locality Optimizer,” PLDI 2008, pp. 101–113, DOI `10.1145/1375581.1375595`; [project repository](https://github.com/bondhugula/pluto).
- **Observed production bridge.** LLVM Polly applies polyhedral analysis/optimization to suitable LLVM regions; MLIR’s Affine and Linalg ecosystems preserve higher-level loop/tensor structure so transformations need not reconstruct it after lowering. Sources: [Polly](https://polly.llvm.org/) and [MLIR dialect documentation](https://mlir.llvm.org/docs/Dialects/).
- **Scope condition.** Data-dependent loop bounds, indirect/subscripted accesses, opaque calls, alias uncertainty, irregular control, and effects can exclude or fragment a region. Runtime guards and speculative versioning may recover cases, but their overhead and correctness conditions are part of the result.
- **Inferred.** The polyhedral model is most useful as a precise island inside a heterogeneous compiler, not as a universal whole-program representation. It is production-capable when the workload naturally exposes affine dense loops and when target-specific profitability is supplied; automatic optimal scheduling remains hard.
- **Maturity: P3–P4 in dense numerical domains and explicit affine IR; P2–P3 for general automatic parallelization of arbitrary C/C++.**

### 5.2 MLIR: multi-level IR as an information-retention strategy

- **Observed.** MLIR supplies extensible dialects, operation/type/attribute interfaces, pattern rewriting, and dialect conversion so domain structure can be retained and lowered progressively. The peer-reviewed system paper positions this as infrastructure for domain-specific computation and heterogeneous targets. Source: Lattner et al., “MLIR: Scaling Compiler Infrastructure for Domain Specific Computation,” CGO 2021, pp. 2–14, DOI `10.1109/CGO51591.2021.9370308`; [official citation/FAQ](https://mlir.llvm.org/getting_started/Faq/).
- **Observed.** Official MLIR rationale explicitly combines SSA-style IR ideas with polyhedral concepts and says progressive lowering can target specialized accelerators; the LLVM target documentation describes partial conversion where converted and unconverted dialects coexist. Sources: [MLIR rationale](https://mlir.llvm.org/docs/Rationale/Rationale/) and [LLVM IR target](https://mlir.llvm.org/docs/TargetLLVMIR/).
- **Mechanistic interpretation.** A single low-level IR forces later passes to rediscover tensor shapes, layouts, parallel dimensions, sparsity, and accelerator operations after information loss. Multiple dialects instead make these semantics explicit until a lowering decision is ready. The cost is a larger semantic surface: dialect contracts, conversion legality, bufferization, ABI boundaries, and cross-dialect canonicalization must be engineered.
- **Counterweight.** “Progressive lowering” is not automatically compositional correctness. Dialect semantics are often less formal than LLVM IR semantics, and a pipeline can be locally well-typed yet choose poor layouts or incompatible conventions. Verification across mixed dialects is an active frontier.
- **Maturity: MLIR infrastructure P4; individual dialect stacks range P1–P5.** Never transfer the maturity of MLIR core to every downstream accelerator compiler.

### 5.3 Representative heterogeneous stacks

| System | Core abstraction and evidence | Maturity judgment |
|---|---|---|
| **XLA** | Graph/tensor compiler used by major ML framework stacks; performs target-specific optimization and code generation. Official architecture: [OpenXLA/XLA](https://openxla.org/xla). | P4 for documented supported framework/backend combinations; broad P5 claims require deployment-specific evidence. It is not a general C compiler. |
| **TVM** | End-to-end tensor compiler with explicit separation of computation and schedule; research showed competitive CPU/GPU/accelerator code generation. Chen et al., OSDI 2018, [USENIX paper](https://www.usenix.org/conference/osdi18/presentation/chen). | P3–P4; powerful auto-scheduling and deployment stack, with integration and tuning costs. |
| **IREE** | MLIR-based compiler/runtime designed for deployable ML across CPUs/GPUs/accelerators, with explicit HAL/runtime layers. Official docs: [IREE](https://iree.dev/). | P3 as a production-oriented open stack; a specific backend/model may justify P4 only with deployment evidence. Empirical literature is narrower than mature LLVM CPU compilation. |
| **AscendNPU IR** | MLIR ecosystem/hardware abstraction for Huawei Ascend; relevant because the course task explicitly asks students to inspect dialect lowering. Official docs: [VecAdd quick start](https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/quick_start/examples_zh.html). | Treat as platform-specific P2–P4 pending exact version, hardware access, documented supported ops, and reproducible experiment. Do not infer general MLIR maturity from one tutorial. |
| **Halide** | Separates an image-processing algorithm from its schedule. Source: Halide PLDI 2013, DOI `10.1145/2499370.2462176`. | P4–P5 in established image-pipeline deployments; this maturity does not transfer to all algorithm/schedule DSLs. |
| **Tiramisu** | Multi-level polyhedral DSL exposing loop transforms, data layout, and communication. Source: Tiramisu CGO 2019, DOI `10.1109/CGO.2019.8661197`. | P2–P3 evaluated research system; strong conceptual/benchmark evidence, not broad production evidence. |
| **Ansor** | Hierarchical schedule-space sampling, evolutionary search, learned cost model, and task scheduling over tensor subgraphs. Source: Zheng et al., OSDI 2020, [paper](https://www.usenix.org/conference/osdi20/presentation/zheng). | P2–P3 evaluated auto-scheduling technique; reported gains are hardware/search-budget and distribution dependent. |

### 5.4 A disciplined lowering trace

For the running kernel, preserve a table at every IR boundary:

| Boundary | Invariant to record | Typical decision |
|---|---|---|
| Tensor/domain dialect → `linalg`/structured ops | Shape, element type, reduction dimensions, purity | Fusion, tiling, library selection |
| Structured ops → `scf`/`affine` + `vector` | Iteration space, dependence legality, vector lanes | Loop ordering, tile sizes, vectorization |
| Tensor → `memref` (bufferization) | Ownership, aliasing, layout, address space | Allocation, copies, in-place update |
| GPU/NPU mapping | Workgroup/thread or device hierarchy, memory spaces | Mapping, promotion, synchronization |
| LLVM dialect → LLVM IR | ABI, concrete pointers/layout, target intrinsics | Calling convention, instruction selection handoff |

**Recommended experiment:** keep the mathematics constant and vary only a tile/vector/mapping parameter. Measure compile time, transfer time, cold start, steady-state throughput, and memory. This distinguishes a good representation from a good schedule. The compiler system needs both.

### 5.5 Evidence that prevents a triumphalist account

- A 2024 survey and independent evaluation of general-purpose polyhedral compilers reports both speedups and correctness/robustness failures; tiling can improve locality while increasing branches, and limited parallelism or many fork/join regions can erase benefits. Source: Thangamani, Loechner, and Genaud, *ACM TACO* 21(4), article 72, DOI `10.1145/3674735`. This is stronger maturity evidence than quoting only favorable original Pluto benchmarks.
- The MLIR Transform dialect makes target/workload-specific transformation strategy itself an IR, improving composability and precise control. Source: Lücke et al., CGO 2025, DOI `10.1145/3696443.3708922`. It relocates schedule engineering; it does not eliminate it.
- StableHLO is a versioned operation/serialization boundary, not a promise of equal floating-point results or equal performance on every backend. Sources: [StableHLO specification](https://openxla.org/stablehlo/spec) and [compatibility documentation](https://github.com/openxla/stablehlo/blob/main/docs/compatibility.md).

---

## 6. JIT, AOT, and hybrid compilation

### 6.1 Treat timing of knowledge as the design axis

| Strategy | Knowledge available | Main benefit | Main cost/risk |
|---|---|---|---|
| **AOT** | Source, static target, optional offline profiles | Predictable startup/deployment; optimization cost paid once; simple artifact management | Cannot specialize to late types/values/microarchitecture without multiversioning; profile can become stale. |
| **JIT** | Runtime types, hotness, actual target, dynamic linkage/state | Adaptive specialization and deoptimization; only hot code needs expensive optimization | Warm-up latency, memory/CPU overhead, nondeterministic performance, executable-memory policy, runtime complexity. |
| **Hybrid/tiered** | Cheap early execution plus later profile | Balances startup and peak performance | More state transitions, code versions, metadata, and difficult testing/debugging. |

- **Observed production example.** Android ART uses interpretation, JIT, AOT, and profile-guided compilation in combination. Official documentation states that JIT complements AOT to improve runtime performance while reducing storage/update costs; compilation filters such as profile-guided modes make the trade-off operationally explicit. Sources: [ART JIT](https://source.android.com/docs/core/runtime/jit-compiler) and [ART configuration](https://source.android.com/docs/core/runtime/configure).
- **Observed infrastructure.** LLVM ORC is a modular JIT API supporting JIT linking, LLVM IR compilation, eager/lazy materialization, concurrent compilation, and cross-process/architecture arrangements. JITLink models runtime linking over object graphs. Sources: [ORCv2 design](https://llvm.org/docs/ORCv2.html) and [JITLink](https://llvm.org/docs/JITLink.html).
- **Inferred.** JIT versus AOT is not a contest with one winner. It is a placement problem: when do types, values, hot paths, target features, and deployment constraints become known, and how expensive is it to revise code after that point?
- **Maturity:** AOT P5; managed-runtime tiered JIT P5; LLVM ORC P4 as infrastructure, with maturity varying by object format/architecture; bespoke JIT for a new language P2–P4 depending runtime semantics.

### 6.2 Measurement contract

Never compare AOT steady-state throughput to JIT throughput after an undisclosed warm-up. Report separately:

1. process startup and first response;
2. interpreter/baseline tier time;
3. compilation CPU time and peak memory;
4. time/requests to steady state;
5. steady-state throughput/latency and tail latency;
6. code-cache size and invalidation/deoptimization events;
7. artifact size and installation/update cost.

For the small case study, a conceptual ORC trace is enough if building a credible JIT would dominate the assignment. The pedagogical objective is to make symbol materialization, compilation, runtime linking, and code memory visible—not to claim a speedup on a toy kernel.

---

## 7. LTO, ThinLTO, and post-link optimization

### 7.1 Visibility versus scalability

- **Observed.** Conventional full LTO merges bitcode modules into one combined module, exposing cross-translation-unit inlining and whole-program analysis but consuming substantial time/memory and impeding incremental parallel work.
- **Observed.** ThinLTO stores compact summaries, creates a combined summary index at link time, makes global decisions such as importing, and runs parallel per-module backends. LLVM officially describes it as scalable and incremental. Source: [Clang ThinLTO documentation](https://clang.llvm.org/docs/ThinLTO.html).
- **Peer-reviewed evidence.** Johnson, Amini, and Li report the design and evaluation in “ThinLTO: Scalable and Incremental LTO,” CGO 2017, pp. 111–121, DOI `10.1109/CGO.2017.7863733`, [paper](https://storage.googleapis.com/gweb-research2023-media/pubtools/4743.pdf).
- **Inferred.** ThinLTO is a classic systems compromise: a cheap summary makes the normal unit of compilation mostly independent while selectively importing the information/body needed for profitable global optimization. It does not make every whole-program analysis equally precise, and imports can expand invalidation.
- **Maturity:** full LTO P5 for release builds that can afford resources; ThinLTO P5 for large LLVM-family production builds; exact linker/platform features vary.

### 7.2 Relating compiler-time and binary-time views

LTO sees typed/SSA program structure and can change computations and calls. Post-link optimizers see final addresses, alignments, assembled libraries, and measured binary layout. Their opportunities overlap but are not identical. LLVM explicitly documents composing PGO, ThinLTO, and BOLT; this is evidence against presenting them as mutually exclusive alternatives.

**Recommended case-study matrix:**

| Build | Expected extra visibility | Measure/inspect |
|---|---|---|
| Separate `-O2` | Within one translation unit | Baseline build/runtime; retained call boundary |
| Full LTO | All linked bitcode bodies | Cross-module inline/devirtualization; peak link time/RSS |
| ThinLTO | Global summary + selective imports | Imported functions, parallel backends, cache hits, incremental rebuild |
| ThinLTO + PGO | Global structure + observed hotness | Hot import/inlining/layout; profile mismatch |
| ThinLTO + PGO + BOLT | Adds final-binary layout evidence | Code layout, I-cache/branch metrics, post-link time and binary requirements |

Use multiple source files even though the computation is small; otherwise LTO has nothing meaningful to demonstrate.

---

## 8. Incremental and reproducible builds

### 8.1 These optimize different relations

**Incrementality** asks whether unchanged results can be reused after an edit without producing a stale artifact. **Reproducibility** asks whether fixed declared inputs and environment yield bit-for-bit identical artifacts across builds. A build may be incremental but nondeterministic, or reproducible only as a clean build.

### 8.2 Incremental computation inside compilers and build systems

- **Observed.** `rustc` represents compilation as queries and persists prior results plus a dependency DAG. Its red-green algorithm can mark a query green when inputs are green or when recomputation produces the same result, avoiding unnecessary propagation. Source: [Rust compiler development guide](https://rustc-dev-guide.rust-lang.org/queries/incremental-compilation.html).
- **Observed theory.** Mokhov, Mitchell, and Peyton Jones decompose build systems into task, scheduler, dependency, and caching choices and relate real systems in “Build Systems à la Carte: Theory and Practice,” *Journal of Functional Programming* 30 (2020), e11, DOI `10.1017/S0956796820000088`; [publication page](https://www.microsoft.com/en-us/research/publication/build-systems-a-la-carte/).
- **Correctness invariant.** The cache key and dependency graph must be sensitive to every observation that can change the action's semantic result: source/generated contents or declared identities, compiler/linker/tool/plugin versions, flags, target, relevant environment, and dependency results. This does not require invalidation merely because an identical dependency was rebuilt. Missing an observationally relevant input creates a false cache hit; conservative over-approximation loses performance.
- **Inferred.** The compiler and external build system are two layers of the same incremental-computation problem. Coarse file/module caches provide simple isolation; fine query caches save more work but enlarge the dependency-tracking and serialization correctness surface.
- **Maturity:** file/module incremental builds and content-addressed caches P5; fine-grained compiler queries P4 in systems such as Rust, Swift, and IDE compilers; general always-correct dynamic dependency discovery P2–P3.

### 8.3 Reproducible builds and their actual guarantee

- **Observed.** Reproducible-builds.org defines a reproducible build around identical output from the same source, build instructions, and environment; guidance covers timestamps, paths, locale/timezone, ordering, randomness, archive metadata, and environment capture. Sources: [documentation hub](https://reproducible-builds.org/docs/) and [`SOURCE_DATE_EPOCH` specification](https://reproducible-builds.org/specs/source-date-epoch/).
- **Observed.** `SOURCE_DATE_EPOCH` standardizes a source-derived timestamp so tools need not embed wall-clock time. It addresses one variability channel, not the entire environment.
- **Peer-reviewed synthesis.** Lamb and Zacchiroli explain reproducible builds as an integrity mechanism and survey real-world challenges: “Reproducible Builds: Increasing the Integrity of Software Supply Chains,” *IEEE Software* 39(2), 2022, pp. 62–70, DOI `10.1109/MS.2021.3073045`.
- **Security inference with limits.** Independent matching builds provide evidence that a distributed binary corresponds to declared source/build inputs. They do **not** prove that the source is benign, the compiler semantics are correct, two builders are independent, or the runtime environment/hardware is trustworthy. A compromised common toolchain can reproduce the same malicious artifact.
- **Maturity:** deterministic compiler/archive/linker techniques P5; ecosystem-wide bit-for-bit reproducibility P3–P5 depending language, distribution, and environment discipline; bootstrappable trust chains remain P2–P3.

### 8.4 Combined acceptance test

For each meaningful edit `e` and environment `E`, compare:

\[
  Artifact(incremental(e), E) \stackrel{?}{=} Artifact(clean(e), E),
\]

then repeat the clean build under a separately instantiated but declared-equivalent environment `E'`:

\[
  Artifact(clean(e), E) \stackrel{?}{=} Artifact(clean(e), E').
\]

The first equation tests invalidation/cache correctness; the second tests reproducibility. When bits differ, diagnose rather than normalize blindly: nondeterminism can reveal undeclared inputs or data races in build tools.

---

## 9. Debugging and security under explicit models

This section must not use “secure compiler” as a catch-all. Each method answers a different model.

| Model | Adversary/error | Oracle or property | Appropriate technique | What it does **not** establish |
|---|---|---|---|---|
| Wrong-code compiler bug | Nonmalicious bug in optimizer/backend; generated program differs on defined source behavior | Cross-compiler/optimization output agreement or semantic refinement | Csmith-style differential testing, EMI, Alive2, verified compiler | Absence of bugs outside generated/modelled cases |
| Debug-metadata defect | Optimizer/compiler emits missing or misleading mapping/variable information | Stated source-level observability relation for an execution | Debug-info validation and differential debugger testing | Program semantic correctness or full recovery of optimized-away state |
| “Trusting Trust” toolchain attack | Compiler binary maliciously recognizes source/compilers and injects payload, potentially self-propagating | Correspondence between compiler source and executable under diversity assumptions | Diverse double compilation (DDC) | Benign source, benign independent compiler, or safety of all dependencies |
| Spatial/temporal memory defect | Executed path performs a supported out-of-bounds or lifetime violation | ASan shadow/redzone/allocator invariant | AddressSanitizer | Protection against a capable attacker; completeness for unexecuted/unsupported defects |
| Uninitialized-value use | Executed computation consumes data whose initialization taint is absent | MSan initialization/taint invariant | MemorySanitizer | General memory safety or detection of paths not executed |
| Selected undefined behavior | Executed operation violates one of the enabled checks (e.g., signed overflow, null/misaligned access) | UBSan check-specific invariant | UndefinedBehaviorSanitizer | Absence of all language UB; checks not enabled or paths not executed |
| Control-flow hijack | Attacker corrupts an indirect control transfer despite other defenses | Runtime target belongs to an allowed equivalence class/set | Compiler/linker CFI instrumentation | Memory safety, data-only attack prevention, or perfect precision under coarse type classes |
| Build substitution/tampering | Distributed artifact differs from artifact generated from declared inputs | Bit equality from independent reproducible builds | Reproducible builds + signed provenance/transparency | Correct compiler/source or independence if all builders share compromise |

### 9.1 Wrong-code discovery: Csmith and EMI

- **Observed.** Csmith generates deterministic C programs while avoiding executed undefined behavior and dependencies on unspecified behavior, then uses differential execution across compilers/configurations. The original three-year study reported more than 325 previously unknown compiler bugs. This is historical evidence that language-aware random generation can reach optimizer corner cases, not a current defect-rate estimate. Source: Yang et al., PLDI 2011, DOI `10.1145/1993498.1993532`, [author PDF](https://users.cs.utah.edu/~regehr/papers/pldi11-preprint.pdf).
- **Why the oracle works.** A disagreement is meaningful only if the generated source has a defined, deterministic relevant behavior and all implementations are compared under compatible conditions. Majority vote does not logically identify the faulty compiler, and correlated bugs or a shared runtime can agree incorrectly.
- **Observed.** Equivalence Modulo Inputs (EMI) profiles a program on input set `I`, constructs variants whose behavior must agree on `I`—for example by pruning unexecuted code—and checks the compiler’s self-consistency. Eleven months of experiments produced 147 confirmed unique GCC/LLVM reports in the original study. Source: Le, Afshari, and Su, PLDI 2014, DOI `10.1145/2594291.2594334`, [paper](https://www.vuminhle.com/pdf/pldi14-emi.pdf).
- **Boundary.** EMI equivalence is only modulo the selected inputs; it is a metamorphic testing oracle, not a whole-input proof. Csmith and EMI are complementary: the former explores defined language-feature combinations, while the latter perturbs structure around concrete executions to stress optimizer decisions.
- **Maturity: P4 as compiler CI/fuzzing methodologies; not certification.** Preserve seed, source, flags, target, compiler revisions, reducer, and the final regression test.

### 9.2 The Trusting Trust attack and diverse double compilation

- **Attacker model.** The attacker controls the compiler executable. It recognizes a victim program and injects a payload; it also recognizes compiler source and injects the trigger/payload into the next compiler binary. Published source can remain clean while a malicious binary self-propagates. Source: Thompson, “Reflections on Trusting Trust,” *CACM* 27(8), 1984, DOI `10.1145/358198.358210`.
- **Observed countermeasure.** Diverse double compilation (DDC) first uses a causally independent trusted compiler to compile the relevant parent/compiler source, then uses that result to compile the putative compiler source, and compares the result with the compiler under examination. Under Wheeler’s assumptions, bit identity establishes correspondence between examined source and binary and breaks the hidden self-regeneration chain. Source: Wheeler, ACSAC 2005, DOI `10.1109/CSAC.2005.17`, [author paper](https://dwheeler.com/trusting-trust/wheelerd-trust.pdf).
- **Assumptions.** The diverse compiler must correctly implement the relevant compilation; all effective sources/tools/libraries/flags/environment must be controlled; nondeterminism must be removed; and diversity must not share the same compromise. DDC does not show that source is benign or that the compiler never miscompiles ordinary programs.
- **Maturity: P3 for high-assurance release audits, P1–P2 for routine per-commit use.** The obstacle is operationally diverse, reproducible bootstrapping of a large toolchain—not the abstract comparison.

### 9.3 Compiler-enforced runtime checks: do not merge detectors with mitigations

**Control-flow integrity (CFI).** The attacker already has a memory-corruption primitive and attempts to redirect an indirect call, jump, or return. Compiler/linker instrumentation checks that the runtime destination belongs to a statically/dynamically allowed set. The property assumes the checks/code/metadata cannot simply be modified or bypassed. Source: Abadi et al., CCS 2005, DOI `10.1145/1102120.1102165`, [Microsoft Research record](https://www.microsoft.com/en-us/research/publication/control-flow-integrity-principles-implementations-and-applications/).

- CFI is only as precise as its target equivalence classes/CFG approximation; it permits redirection to another allowed target and does not stop data-only corruption.
- Forward edges and returns are different. A protected shadow stack can enforce a stronger backward-edge property than broad type-based labels.
- **Observed production evidence.** Clang documents CFI modes and their LTO/visibility constraints, while KCFI avoids the LTO requirement for the kernel-oriented design. Android documents kernel CFI/KCFI deployment. Sources: [Clang CFI](https://clang.llvm.org/docs/ControlFlowIntegrity.html), [CFI design](https://clang.llvm.org/docs/ControlFlowIntegrityDesign.html), [Android KCFI](https://source.android.com/docs/security/test/kcfi).
- **Maturity: P4–P5 for supported production threat models/platforms; never a claim of memory safety.**

**Sanitizers.** AddressSanitizer (ASan) instruments memory accesses and allocator/object layout to detect supported errors on executed paths; the original study reported roughly 73% average slowdown and more than 300 Chromium bugs. Source: Serebryany et al., USENIX ATC 2012, [paper](https://www.usenix.org/conference/atc12/technical-sessions/presentation/serebryany). Current [Clang ASan documentation](https://clang.llvm.org/docs/AddressSanitizer.html) explicitly warns that its runtime was not designed as a hardened security boundary. UndefinedBehaviorSanitizer similarly checks selected executed operations, with configurable recover/trap modes; it does not prove absence of undefined behavior. Source: [Clang UBSan documentation](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html).

**Recommended wording:** sanitizers are mature dynamic defect detectors for tests/fuzzing (and selective production trapping where documented); CFI constrains one exploitation consequence after a memory-corruption bug. Neither substitutes for memory-safe semantics/design.

### 9.4 Optimized debug information as an observability contract

Optimization legitimately eliminates variables, merges/reorders instructions, and inlines frames; therefore equality with an unoptimized debugger trace is too strong. The real defect is metadata that violates a stated observation contract—for example, it claims a wrong variable value/location or misleading frame—not every `optimized out` result.

- **Observed.** Li et al. define actionable program/location-variable observations so debugger comparison avoids semantically invalid inspections; their PLDI 2020 framework found confirmed GCC/LLVM and Rust debug-information bugs. Source: “Debug Information Validation for Optimized Code,” DOI `10.1145/3385412.3386020`, [paper](https://faculty.cc.gatech.edu/~qzhang414/papers/pldi20_yuanbo1.pdf).
- **Observed.** Debug² compares optimized/unoptimized debugger traces under carefully chosen invariants over lines, frames, and arguments, finding bugs across LLVM/LLDB, GCC/GDB, and rustc/LLDB. This establishes that the relevant system is compiler + linker + debug format + debugger, not one component. Source: Di Luna et al., ASPLOS 2021, DOI `10.1145/3445814.3446695`, [preprint](https://arxiv.org/abs/2011.13994).
- **Maturity:** emitting optimized DWARF/CodeView is P5; systematic invariant-based validation is P2–P4 depending toolchain. Preserve reduced failures and distinguish unavailable truth from false metadata.

### 9.5 Integrated failure case study

One small C/C++ function can contain an indirect callback and a latent out-of-bounds write:

1. **Meaning:** use defined random/metamorphic variants to test compiler semantic consistency.
2. **Provenance:** pose a Thompson trigger and explain why clean source plus self-rebuild is insufficient; DDC introduces an independent normalization path.
3. **Enforcement:** ASan detects the executed overwrite during testing; CFI rejects only an out-of-class indirect destination under its release threat model.
4. **Observability:** compile `-O2 -g`; distinguish a legitimately eliminated local from an incorrect DWARF location.

The case study should never actually introduce or test malicious modifications in the course repository; it is an explanatory error/attacker model and a literature-grounded validation design.

---

## 10. Cross-frontier synthesis: one compiler, four control loops

The frontiers become coherent when organized by which uncertainty they control:

| Loop | Question | Representative mechanisms | Failure mode if loop is omitted |
|---|---|---|---|
| **Semantic assurance loop** | Did the transformation preserve the specified behaviors? | CompCert proofs, Alive2, fuzzing/differential testing | Fast wrong code; unjustified trust in phase composition |
| **Search/profitability loop** | Which legal program is best under a resource/cost objective? | E-graphs, superoptimization, polyhedral schedules, cost models, MLGO | Greedy phase-order traps or optimization for a surrogate that misses hardware reality |
| **Empirical adaptation loop** | Does deployed behavior match static assumptions? | PGO, JIT/tiering, post-link optimization | Optimizing cold paths; stale profiles; poor warm-up/tail behavior |
| **Artifact/build loop** | Can results be reused and independently reconstructed? | ThinLTO summaries/cache, query incrementality, hermetic/reproducible builds | Slow iteration, stale cache hits, or unverifiable source-to-binary provenance |

### 10.1 Important connections

1. **Search needs assurance.** Superoptimization, equality saturation, polyhedral scheduling, and learned transformations enlarge the search space; translation validation or proof-carrying rewrites can keep correctness risk from scaling with aggressiveness.
2. **Profiles and learned policies need versioned provenance.** The program revision, IR schema, target, compiler revision, feature extractor, and workload population are semantic inputs to an optimization decision even if ordinary build systems do not encode them all.
3. **Multi-level IR improves optimization and complicates validation.** Preserving abstraction enables better schedules, but every dialect boundary adds semantics that must be specified for end-to-end assurance.
4. **Incrementality fights global visibility.** Full LTO wants one global optimization unit; fast edits want small independent units. ThinLTO’s summary/import design is a concrete compromise rather than a universal solution.
5. **Reproducibility strengthens but does not replace toolchain trust.** Bit-identical artifacts enable comparison and accountability; verified compilation or translation validation addresses semantic correctness; DDC addresses one malicious self-hosting compiler attack. They compose because their claims are different.
6. **JIT and PGO are two placements of feedback.** Offline PGO moves runtime evidence into the next AOT build; JIT moves compilation toward the running process. Hybrid systems choose feedback latency rather than choosing “static” or “dynamic” once and for all.

### 10.2 Production-versus-frontier matrix

| Direction | Academic promise | Strongest production evidence | Main unresolved risk | Overall maturity |
|---|---|---|---|---|
| Verified compilation | Machine-checked semantic preservation across a verified compiler core | CompCert in high-assurance embedded C | Unverified surroundings, language/ecosystem breadth, proof maintenance | P4 narrow / P2–P3 general |
| Translation validation | Retrofittable assurance for aggressive passes | Alive2 in LLVM development/CI workflows | Model/feature coverage, loops, solver cost, whole-toolchain gap | P3–P4 |
| Superoptimization | Discover code beyond hand-written peepholes | Offline discovery feeding LLVM/MSVC rewrites | Search explosion, cost-model realism, maintenance of prototypes | P2 online / P3 offline |
| Equality saturation | Avoid destructive rewrite ordering; modular rewrite systems | `egg` ecosystem; constrained e-graph optimization in Cranelift/Wasmtime | Growth, extraction, effects and conditional equalities | P2–P4 by design |
| PGO and binary optimization | Optimize for actual workload and final layout | Clang/GCC PGO, AutoFDO, BOLT/Propeller | Workload drift, profile/version mapping, operations cost | P4–P5 |
| ML-guided heuristics | Learn complex profitability policies | LLVM MLGO integrations | Leakage/drift, training cost, regression tails, interpretability | P2–P4 per decision |
| Polyhedral optimization | Exact dependence reasoning and schedule synthesis | Pluto/Polly/MLIR affine-based stacks | Affine applicability and target profitability | P3–P4 in regular kernels |
| Heterogeneous/multi-level IR | Retain domain semantics through accelerator lowering | MLIR ecosystem, XLA, TVM, IREE/vendor stacks | Dialect semantics/composition, schedule portability, fast hardware churn | P3–P5 by stack |
| JIT/AOT hybrid | Adapt late while bounding startup | JVM/.NET/ART; LLVM ORC infrastructure | Warm-up, runtime footprint, executable-memory/deployment policy | P5 managed runtimes, P4 infra |
| ThinLTO | Whole-program benefit with parallel, cacheable backends | LLVM/Clang production toolchains | Import invalidation and platform/linker differences | P5 |
| Incremental compilation | Recompute only semantically affected queries | Rust/Swift/IDE query systems and modern build caches | Dependency completeness and cache compatibility | P4–P5 |
| Reproducible builds | Independent source-to-binary verification | Major distributions/toolchain support | Complete environment capture; common-mode compromise | P3–P5 by ecosystem |

### 10.3 Recommended ordering for the survey outlook

1. **Correctness first:** define semantic preservation; compare proof, validation, and testing.
2. **Optimization-space expansion:** superoptimization/e-graphs and polyhedral scheduling.
3. **Evidence-driven profitability:** PGO, post-link optimization, then ML-guided decisions.
4. **Representation and hardware diversity:** MLIR progressive lowering and accelerator stacks.
5. **When compilation occurs:** AOT, JIT, tiering, and feedback placement.
6. **How compilation scales and becomes accountable:** LTO/ThinLTO, incremental and reproducible builds.
7. **Failure and attacker models:** wrong-code, debug metadata, Trusting Trust, sanitizers/CFI—with no generic “security” bucket.

This ordering follows a causal dependency: legality before profitability, representation before lowering, execution feedback before build/artifact operations, and explicit models before security claims.

---

## 11. Evidence-quality cautions for the final manuscript

1. **Benchmark gains are local evidence.** Preserve benchmark suite, hardware, compiler revision, baseline flags, repetitions/uncertainty, and training/profile split. Do not transplant a percentage into the running example.
2. **A framework’s existence is not adoption evidence.** Upstream code and official documentation establish availability; production case studies establish use; neither alone proves broad superiority.
3. **Unsupported/timeout is not validated.** This is essential for solver-backed tools.
4. **Defined behavior is the input contract.** Differential compiler testing without eliminating undefined/unspecified behavior produces false bug reports; this is precisely why Csmith’s generator design matters.
5. **Cost models are hypotheses.** Instruction count, static latency, code size, and measured runtime can choose different outputs. Extraction or scheduling must state the objective.
6. **Profiles and models age.** Version and provenance them as build inputs; evaluate drift rather than treating training as a one-time phase.
7. **Do not conflate determinism, reproducibility, provenance, and correctness.** They are complementary relations over artifacts and processes.
8. **Do not claim every MLIR pipeline is “MLIR-verified” or production-ready.** Core infrastructure maturity does not propagate automatically to dialect semantics and vendor lowering passes.
9. **Prefer one falsifiable experiment per technique.** A failed/neutral result with understood mechanism is more valuable than screenshots of successful commands.

---

## 12. Bibliography-ready primary and official sources

The following entries are intentionally close to BibTeX. URLs point to a primary paper, publisher record, or official project documentation. Before publication, normalize venue macros and verify page ranges against the publisher export.



### 12.1 Verification, validation, compiler testing, trust, and observability

```bibtex
@article{Leroy2009CompCert,
  author  = {Xavier Leroy},
  title   = {Formal Verification of a Realistic Compiler},
  journal = {Communications of the ACM},
  volume  = {52}, number = {7}, pages = {107--115}, year = {2009},
  doi     = {10.1145/1538788.1538814},
  url     = {https://xavierleroy.org/publi/compcert-CACM.pdf}
}

@article{Leroy2009Backend,
  author  = {Xavier Leroy},
  title   = {A Formally Verified Compiler Back-end},
  journal = {Journal of Automated Reasoning},
  volume  = {43}, number = {4}, pages = {363--446}, year = {2009},
  doi     = {10.1007/s10817-009-9155-4}
}

@inproceedings{MonniauxBoulme2022CompCertTCB,
  author    = {David Monniaux and Sylvain Boulm{\'e}},
  title     = {The Trusted Computing Base of the {CompCert} Verified Compiler},
  booktitle = {Programming Languages and Systems (ESOP)},
  series    = {Lecture Notes in Computer Science}, volume = {13240},
  pages     = {204--233}, year = {2022},
  doi       = {10.1007/978-3-030-99336-8_8},
  url       = {https://arxiv.org/abs/2201.10280}
}

@inproceedings{PnueliSiegelSingerman1998TranslationValidation,
  author    = {Amir Pnueli and Michael Siegel and Eli Singerman},
  title     = {Translation Validation},
  booktitle = {Tools and Algorithms for the Construction and Analysis of Systems (TACAS)},
  series    = {Lecture Notes in Computer Science}, volume = {1384},
  pages     = {151--166}, year = {1998},
  doi       = {10.1007/BFb0054170}
}

@inproceedings{TristanLeroy2008Scheduling,
  author    = {Jean-Baptiste Tristan and Xavier Leroy},
  title     = {Formal Verification of Translation Validators: A Case Study on Instruction Scheduling Optimizations},
  booktitle = {Proceedings of the 35th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages},
  pages     = {17--27}, year = {2008},
  doi       = {10.1145/1328438.1328444}
}

@inproceedings{TristanLeroy2009LazyCodeMotion,
  author    = {Jean-Baptiste Tristan and Xavier Leroy},
  title     = {Verified Validation of Lazy Code Motion},
  booktitle = {Proceedings of the 30th ACM SIGPLAN Conference on Programming Language Design and Implementation},
  pages     = {316--326}, year = {2009},
  doi       = {10.1145/1542476.1542512}
}

@inproceedings{LopesEtAl2015Alive,
  author    = {Nuno P. Lopes and David Menendez and Santosh Nagarakatte and John Regehr},
  title     = {Provably Correct Peephole Optimizations with {Alive}},
  booktitle = {Proceedings of the 36th ACM SIGPLAN Conference on Programming Language Design and Implementation},
  year      = {2015},
  doi       = {10.1145/2737924.2737965},
  url       = {https://web.ist.utl.pt/nuno.lopes/pubs.php?id=alive-pldi15}
}

@inproceedings{LopesEtAl2021Alive2,
  author    = {Nuno P. Lopes and Juneyoung Lee and Chung-Kil Hur and Zhengyang Liu and John Regehr},
  title     = {{Alive2}: Bounded Translation Validation for {LLVM}},
  booktitle = {Proceedings of the 42nd ACM SIGPLAN International Conference on Programming Language Design and Implementation},
  pages     = {65--79}, year = {2021},
  doi       = {10.1145/3453483.3454030},
  url       = {https://users.cs.utah.edu/~regehr/alive2-pldi21.pdf}
}

@inproceedings{Necula1997PCC,
  author    = {George C. Necula},
  title     = {Proof-Carrying Code},
  booktitle = {Proceedings of the 24th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages},
  pages     = {106--119}, year = {1997},
  doi       = {10.1145/263699.263712}
}

@inproceedings{Appel2001FoundationalPCC,
  author    = {Andrew W. Appel},
  title     = {Foundational Proof-Carrying Code},
  booktitle = {16th Annual IEEE Symposium on Logic in Computer Science},
  pages     = {247--256}, year = {2001}, doi = {10.1109/LICS.2001.932501},
  url       = {https://www.cs.princeton.edu/~appel/papers/fpcc.pdf}
}

@inproceedings{YangEtAl2011Csmith,
  author    = {Xuejun Yang and Yang Chen and Eric Eide and John Regehr},
  title     = {Finding and Understanding Bugs in {C} Compilers},
  booktitle = {Proceedings of the 32nd ACM SIGPLAN Conference on Programming Language Design and Implementation},
  pages     = {283--294}, year = {2011},
  doi       = {10.1145/1993498.1993532}
}

@inproceedings{LeAfshariSu2014EMI,
  author    = {Vu Le and Mehrdad Afshari and Zhendong Su},
  title     = {Compiler Validation via Equivalence Modulo Inputs},
  booktitle = {Proceedings of the 35th ACM SIGPLAN Conference on Programming Language Design and Implementation},
  pages     = {216--226}, year = {2014},
  doi       = {10.1145/2594291.2594334}
}

@article{Thompson1984TrustingTrust,
  author  = {Ken Thompson}, title = {Reflections on Trusting Trust},
  journal = {Communications of the ACM}, volume = {27}, number = {8},
  pages   = {761--763}, year = {1984}, doi = {10.1145/358198.358210}
}

@inproceedings{Wheeler2005DDC,
  author    = {David A. Wheeler},
  title     = {Countering Trusting Trust through Diverse Double-Compiling},
  booktitle = {21st Annual Computer Security Applications Conference},
  pages     = {33--48}, year = {2005}, doi = {10.1109/CSAC.2005.17},
  url       = {https://dwheeler.com/trusting-trust/wheelerd-trust.pdf}
}

@inproceedings{LiEtAl2020DebugInfo,
  author    = {Yuanbo Li and Shuo Ding and Qirun Zhang and Davide Italiano},
  title     = {Debug Information Validation for Optimized Code},
  booktitle = {Proceedings of the 41st ACM SIGPLAN International Conference on Programming Language Design and Implementation},
  year      = {2020}, doi = {10.1145/3385412.3386020}
}

@inproceedings{DiLunaEtAl2021Debuggers,
  author    = {Giuseppe Antonio Di Luna and Davide Italiano and Luca Massarelli and Sebastian {\"O}sterlund and Cristiano Giuffrida and Leonardo Querzoni},
  title     = {Who's Debugging the Debuggers? Exposing Debug Information Bugs in Optimized Binaries},
  booktitle = {Proceedings of the 26th ACM International Conference on Architectural Support for Programming Languages and Operating Systems},
  pages     = {1034--1045}, year = {2021}, doi = {10.1145/3445814.3446695}
}
```

### 12.2 Search-based and equality-based optimization

```bibtex
@inproceedings{Massalin1987Superoptimizer,
  author    = {Henry Massalin}, title = {Superoptimizer: A Look at the Smallest Program},
  booktitle = {Proceedings of the Second International Conference on Architectural Support for Programming Languages and Operating Systems},
  pages     = {122--126}, year = {1987}, doi = {10.1145/36177.36194}
}

@inproceedings{SchkufzaSharmaAiken2013Stoke,
  author    = {Eric Schkufza and Rahul Sharma and Alex Aiken},
  title     = {Stochastic Superoptimization},
  booktitle = {Proceedings of the Eighteenth International Conference on Architectural Support for Programming Languages and Operating Systems},
  pages     = {305--316}, year = {2013}, doi = {10.1145/2451116.2451150}
}

@misc{SasnauskasEtAl2017Souper,
  author        = {Raimondas Sasnauskas and Yang Chen and Peter Collingbourne and Jeroen Ketema and Gratian Lup and Jubi Taneja and John Regehr},
  title         = {Souper: A Synthesizing Superoptimizer},
  year          = {2017}, eprint = {1711.04422}, archivePrefix = {arXiv}, primaryClass = {cs.PL},
  url           = {https://arxiv.org/abs/1711.04422}
}

@inproceedings{TateEtAl2009EqualitySaturation,
  author    = {Ross Tate and Michael Stepp and Zachary Tatlock and Sorin Lerner},
  title     = {Equality Saturation: A New Approach to Optimization},
  booktitle = {Proceedings of the 36th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages},
  pages     = {264--276}, year = {2009}, doi = {10.1145/1480881.1480915}
}

@article{WillseyEtAl2021Egg,
  author  = {Max Willsey and Chandrakana Nandi and Yisu Remy Wang and Oliver Flatt and Zachary Tatlock and Pavel Panchekha},
  title   = {egg: Fast and Extensible Equality Saturation},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {5}, number = {POPL}, articleno = {23}, pages = {1--29}, year = {2021},
  doi     = {10.1145/3434304}
}

@article{ZhangEtAl2022RelationalEMatching,
  author  = {Yihong Zhang and Yisu Remy Wang and Max Willsey and Zachary Tatlock},
  title   = {Relational E-matching},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {6}, number = {POPL}, articleno = {35}, pages = {1--22}, year = {2022},
  doi     = {10.1145/3498696}
}

@article{ZhangEtAl2023Egglog,
  author  = {Yihong Zhang and Yisu Remy Wang and Oliver Flatt and David Cao and Philip Zucker and Eli Rosenthal and Zachary Tatlock and Max Willsey},
  title   = {Better Together: Unifying Datalog and Equality Saturation},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {7}, number = {PLDI}, articleno = {125}, pages = {468--492}, year = {2023},
  doi     = {10.1145/3591239}
}

@article{GoharshadyLamParreaux2024Extraction,
  author  = {Amir Kafshdar Goharshady and John Chun Kit Lam and Lionel Parreaux},
  title   = {Fast and Optimal Extraction for Sparse Equality Graphs},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {8}, number = {OOPSLA2}, articleno = {361}, pages = {2551--2577}, year = {2024},
  doi     = {10.1145/3689801}
}
```

### 12.3 Feedback-directed and learned optimization

```bibtex
@inproceedings{ChenLiMoseley2016AutoFDO,
  author    = {Dehao Chen and David Xinliang Li and Tipp Moseley},
  title     = {{AutoFDO}: Automatic Feedback-Directed Optimization for Warehouse-Scale Applications},
  booktitle = {Proceedings of the 2016 International Symposium on Code Generation and Optimization},
  pages     = {12--23}, year = {2016}, doi = {10.1145/2854038.2854044}
}

@inproceedings{PanchenkoEtAl2019BOLT,
  author    = {Maksim Panchenko and Rafael Auler and Bill Nell and Guilherme Ottoni},
  title     = {{BOLT}: A Practical Binary Optimizer for Data Centers and Beyond},
  booktitle = {2019 IEEE/ACM International Symposium on Code Generation and Optimization},
  pages     = {2--14}, year = {2019}, doi = {10.1109/CGO.2019.8661201}
}

@inproceedings{ShenEtAl2023Propeller,
  author    = {Han Shen and Krzysztof Pszeniczny and Rahman Lavaee and Snehasish Kumar and Sriraman Tallam and Xinliang David Li},
  title     = {Propeller: A Profile Guided, Relinking Optimizer for Warehouse-Scale Applications},
  booktitle = {Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2},
  pages     = {617--631}, year = {2023}, doi = {10.1145/3575693.3575727}
}

@article{TrofinEtAl2021MLGO,
  author  = {Mircea Trofin and Yundi Qian and Eugene Brevdo and Zinan Lin and Krzysztof Choromanski and Xinliang David Li},
  title   = {{MLGO}: A Machine Learning Guided Compiler Optimizations Framework},
  journal = {arXiv preprint arXiv:2101.04808}, year = {2021},
  url     = {https://arxiv.org/abs/2101.04808}
}

@inproceedings{MendisEtAl2019Ithemal,
  author    = {Charith Mendis and Alex Renda and Saman Amarasinghe and Michael Carbin},
  title     = {Ithemal: Accurate, Portable and Fast Basic Block Throughput Estimation using Deep Neural Networks},
  booktitle = {Proceedings of the 36th International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research}, volume = {97}, pages = {4505--4515}, year = {2019},
  url       = {https://proceedings.mlr.press/v97/mendis19a.html}
}

@inproceedings{CumminsEtAl2022CompilerGym,
  author    = {Chris Cummins and Bram Wasti and Jiadong Guo and Brandon Cui and Jason Ansel and Sahir Gomez and Somya Jain and Jia Liu and Olivier Teytaud and Benoit Steiner and Yuandong Tian and Hugh Leather},
  title     = {{CompilerGym}: Robust, Performant Compiler Optimization Environments for {AI} Research},
  booktitle = {2022 IEEE/ACM International Symposium on Code Generation and Optimization},
  year      = {2022}, doi = {10.1109/CGO53902.2022.9741258}
}
```

### 12.4 Polyhedral, multi-level, and heterogeneous compilation

```bibtex
@article{Feautrier1992AffineSchedulingII,
  author  = {Paul Feautrier},
  title   = {Some Efficient Solutions to the Affine Scheduling Problem. Part II: Multidimensional Time},
  journal = {International Journal of Parallel Programming},
  volume  = {21}, number = {6}, pages = {389--420}, year = {1992},
  doi     = {10.1007/BF01379404}
}

@inproceedings{BondhugulaEtAl2008Pluto,
  author    = {Uday Bondhugula and Albert Hartono and J. Ramanujam and P. Sadayappan},
  title     = {A Practical Automatic Polyhedral Parallelizer and Locality Optimizer},
  booktitle = {Proceedings of the 29th ACM SIGPLAN Conference on Programming Language Design and Implementation},
  pages     = {101--113}, year = {2008}, doi = {10.1145/1375581.1375595}
}

@article{ThangamaniLoechnerGenaud2024Survey,
  author  = {Arun Thangamani and Vincent Loechner and St{\'e}phane Genaud},
  title   = {A Survey of General-purpose Polyhedral Compilers},
  journal = {ACM Transactions on Architecture and Code Optimization},
  volume  = {21}, number = {4}, articleno = {72}, pages = {1--26}, year = {2024},
  doi     = {10.1145/3674735}
}

@inproceedings{LattnerEtAl2021MLIR,
  author    = {Chris Lattner and Mehdi Amini and Uday Bondhugula and Albert Cohen and Andy Davis and Jacques Pienaar and River Riddle and Tatiana Shpeisman and Nicolas Vasilache and Oleksandr Zinenko},
  title     = {{MLIR}: Scaling Compiler Infrastructure for Domain Specific Computation},
  booktitle = {2021 IEEE/ACM International Symposium on Code Generation and Optimization},
  pages     = {2--14}, year = {2021}, doi = {10.1109/CGO51591.2021.9370308}
}

@inproceedings{RaganKelleyEtAl2013Halide,
  author    = {Jonathan Ragan-Kelley and Connelly Barnes and Andrew Adams and Sylvain Paris and Fr{\'e}do Durand and Saman Amarasinghe},
  title     = {Halide: A Language and Compiler for Optimizing Parallelism, Locality, and Recomputation in Image Processing Pipelines},
  booktitle = {Proceedings of the 34th ACM SIGPLAN Conference on Programming Language Design and Implementation},
  pages     = {519--530}, year = {2013}, doi = {10.1145/2499370.2462176}
}

@inproceedings{BaghdadiEtAl2019Tiramisu,
  author    = {Riyadh Baghdadi and Jessica Ray and Malek Ben Romdhane and Emanuele Del Sozzo and Abdurrahman Akkas and Yunming Zhang and Patricia Suriana and Shoaib Kamil and Saman Amarasinghe},
  title     = {Tiramisu: A Polyhedral Compiler for Expressing Fast and Portable Code},
  booktitle = {2019 IEEE/ACM International Symposium on Code Generation and Optimization},
  pages     = {193--205}, year = {2019}, doi = {10.1109/CGO.2019.8661197}
}

@inproceedings{ChenEtAl2018TVM,
  author    = {Tianqi Chen and Thierry Moreau and Ziheng Jiang and Lianmin Zheng and Eddie Yan and Haichen Shen and Meghan Cowan and Leyuan Wang and Yuwei Hu and Luis Ceze and Carlos Guestrin and Arvind Krishnamurthy},
  title     = {{TVM}: An Automated End-to-End Optimizing Compiler for Deep Learning},
  booktitle = {13th USENIX Symposium on Operating Systems Design and Implementation},
  pages     = {578--594}, year = {2018},
  url       = {https://www.usenix.org/conference/osdi18/presentation/chen}
}

@inproceedings{ZhengEtAl2020Ansor,
  author    = {Lianmin Zheng and Chengfan Jia and Minmin Sun and Zhao Wu and Cody Hao Yu and Ameer Haj-Ali and Yida Wang and Jun Yang and Danyang Zhuo and Koushik Sen and Joseph E. Gonzalez and Ion Stoica},
  title     = {Ansor: Generating High-Performance Tensor Programs for Deep Learning},
  booktitle = {14th USENIX Symposium on Operating Systems Design and Implementation},
  pages     = {863--879}, year = {2020},
  url       = {https://www.usenix.org/conference/osdi20/presentation/zheng}
}

@inproceedings{LuckeEtAl2025TransformDialect,
  author    = {Martin Paul L{\"u}cke and Oleksandr Zinenko and William S. Moses and Michel Steuwer and Albert Cohen},
  title     = {The {MLIR} Transform Dialect: Your Compiler Is More Powerful Than You Think},
  booktitle = {Proceedings of the 23rd ACM/IEEE International Symposium on Code Generation and Optimization},
  pages     = {241--254}, year = {2025}, doi = {10.1145/3696443.3708922}
}
```

### 12.5 Compilation time, optimization scope, and build systems

```bibtex
@article{Aycock2003JIT,
  author  = {John Aycock}, title = {A Brief History of Just-in-Time},
  journal = {ACM Computing Surveys}, volume = {35}, number = {2}, pages = {97--113}, year = {2003},
  doi     = {10.1145/857076.857077}
}

@article{ArnoldEtAl2005AdaptiveOptimization,
  author  = {Matthew Arnold and Stephen J. Fink and David Grove and Michael Hind and Peter F. Sweeney},
  title   = {A Survey of Adaptive Optimization in Virtual Machines},
  journal = {Proceedings of the IEEE}, volume = {93}, number = {2}, pages = {449--466}, year = {2005},
  doi     = {10.1109/JPROC.2004.840305}
}

@inproceedings{JohnsonAminiLi2017ThinLTO,
  author    = {Teresa Johnson and Mehdi Amini and Xinliang David Li},
  title     = {{ThinLTO}: Scalable and Incremental {LTO}},
  booktitle = {2017 IEEE/ACM International Symposium on Code Generation and Optimization},
  pages     = {111--121}, year = {2017}, doi = {10.1109/CGO.2017.7863733}
}

@article{MokhovMitchellPeytonJones2020BuildSystems,
  author  = {Andrey Mokhov and Neil Mitchell and Simon Peyton Jones},
  title   = {Build Systems {\`a} la Carte: Theory and Practice},
  journal = {Journal of Functional Programming}, volume = {30}, articleno = {e11}, year = {2020},
  doi     = {10.1017/S0956796820000088}
}

@inproceedings{ErdwegLichterWeiel2015PlutoBuild,
  author    = {Sebastian Erdweg and Moritz Lichter and Manuel Weiel},
  title     = {A Sound and Optimal Incremental Build System with Dynamic Dependencies},
  booktitle = {Proceedings of the 2015 ACM SIGPLAN International Conference on Object-Oriented Programming, Systems, Languages, and Applications},
  pages     = {89--106}, year = {2015}, doi = {10.1145/2814270.2814316}
}

@article{LambZacchiroli2022ReproducibleBuilds,
  author  = {Chris Lamb and Stefano Zacchiroli},
  title   = {Reproducible Builds: Increasing the Integrity of Software Supply Chains},
  journal = {IEEE Software}, volume = {39}, number = {2}, pages = {62--70}, year = {2022},
  doi     = {10.1109/MS.2021.3073045}
}
```

### 12.6 Compiler-enforced runtime checks

```bibtex
@inproceedings{AbadiEtAl2005CFI,
  author    = {Mart{\'i}n Abadi and Mihai Budiu and {\'U}lfar Erlingsson and Jay Ligatti},
  title     = {Control-Flow Integrity},
  booktitle = {Proceedings of the 12th ACM Conference on Computer and Communications Security},
  pages     = {340--353}, year = {2005}, doi = {10.1145/1102120.1102165}
}

@inproceedings{SerebryanyEtAl2012ASan,
  author    = {Konstantin Serebryany and Derek Bruening and Alexander Potapenko and Dmitry Vyukov},
  title     = {{AddressSanitizer}: A Fast Address Sanity Checker},
  booktitle = {2012 USENIX Annual Technical Conference},
  pages     = {309--318}, year = {2012},
  url       = {https://www.usenix.org/conference/atc12/technical-sessions/presentation/serebryany}
}
```

### 12.7 Official living documentation (record access date in the final `.bib`)

```bibtex
@manual{CompCertManual,
  title = {The {CompCert C} Verified Compiler: Documentation and User's Manual},
  organization = {CompCert Project}, url = {https://compcert.org/man/}
}
@manual{LLVMInstCombineGuide,
  title = {{InstCombine} Contributor Guide}, organization = {LLVM Project},
  url = {https://llvm.org/docs/InstCombineContributorGuide.html}
}
@manual{LLVMMLGO,
  title = {Machine Learning Guided Optimization ({MLGO})}, organization = {LLVM Project},
  url = {https://llvm.org/docs/MLGO.html}
}
@manual{ClangPGO,
  title = {Clang Compiler User's Manual: Profile Guided Optimization}, organization = {LLVM Project},
  url = {https://clang.llvm.org/docs/UsersManual.html#profile-guided-optimization}
}
@manual{ClangThinLTO,
  title = {{ThinLTO}}, organization = {LLVM Project},
  url = {https://clang.llvm.org/docs/ThinLTO.html}
}
@manual{LLVMORCv2,
  title = {{ORC} Design and Implementation}, organization = {LLVM Project},
  url = {https://llvm.org/docs/ORCv2.html}
}
@manual{MLIRRationale,
  title = {{MLIR} Rationale}, organization = {LLVM Project},
  url = {https://mlir.llvm.org/docs/Rationale/Rationale/}
}
@manual{MLIRLLVMTarget,
  title = {{LLVM IR} Target}, organization = {LLVM Project},
  url = {https://mlir.llvm.org/docs/TargetLLVMIR/}
}
@manual{AndroidART,
  title = {Configure {ART}}, organization = {Android Open Source Project},
  url = {https://source.android.com/docs/core/runtime/configure}
}
@manual{RustcIncremental,
  title = {Incremental Compilation}, organization = {Rust Project},
  url = {https://rustc-dev-guide.rust-lang.org/queries/incremental-compilation.html}
}
@manual{ReproducibleBuildsDocs,
  title = {Reproducible Builds Documentation}, organization = {Reproducible Builds Project},
  url = {https://reproducible-builds.org/docs/}
}
@manual{SourceDateEpoch,
  title = {{SOURCE_DATE_EPOCH} Specification}, organization = {Reproducible Builds Project},
  url = {https://reproducible-builds.org/specs/source-date-epoch/}
}
@manual{ClangCFI,
  title = {Control Flow Integrity}, organization = {LLVM Project},
  url = {https://clang.llvm.org/docs/ControlFlowIntegrity.html}
}
@manual{ClangASan,
  title = {AddressSanitizer}, organization = {LLVM Project},
  url = {https://clang.llvm.org/docs/AddressSanitizer.html}
}
@manual{AscendNPUIRVecAdd,
  title = {AscendNPU IR VecAdd Quick Start}, organization = {AscendNPU IR Project},
  url = {https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/quick_start/examples_zh.html}
}
@manual{CraneliftEGraphRFC,
  title = {Cranelift E-graph Optimizer Request for Comments}, organization = {Bytecode Alliance},
  url = {https://github.com/bytecodealliance/rfcs/blob/main/accepted/cranelift-egraph.md}
}
@manual{OpenXLAXLAArchitecture,
  title = {{XLA} Architecture}, organization = {OpenXLA Project},
  url = {https://openxla.org/xla/architecture}
}
@manual{StableHLOSpecification,
  title = {{StableHLO} Specification}, organization = {OpenXLA Project},
  url = {https://openxla.org/stablehlo/spec}
}
@manual{IREEDocumentation,
  title = {{IREE} Documentation}, organization = {IREE Project},
  url = {https://iree.dev/}
}
```

---

## 13. Compact recommendation to the manuscript author

A defensible closing judgment is:

> Compiler research is not converging on one replacement for the classical pipeline. It is adding explicit semantic checkers around transformations, richer intermediate representations before irreversible lowering, larger but resource-bounded search spaces for optimization, and feedback loops that move information between deployment and compilation. The production frontier advances when a technique states its semantics and threat/error model, exposes its resource budget and fallback, fits incremental/reproducible build contracts, and survives distribution shift on real workloads.

For the LLNCS manuscript, cite only the subset actually discussed in prose. Keep this evidence file broader than the final bibliography so later editors can replace a frontier paragraph without restarting literature search.
