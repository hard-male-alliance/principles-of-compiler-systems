# Evidence notes: MLIR progressive lowering and the AscendNPU IR/BiSheng path

## Question and decision purpose

These notes support the report section that contrasts a conventional, mostly single-IR LLVM pipeline with MLIR's multi-level compilation model, then relates that model to the official AscendNPU IR `VecAdd` example and to the report's reduction/dot-product case study. The purpose is explanatory, not to claim an end-to-end experiment that was not performed.

**Evidence labels used below**

- **Observed in source/documentation**: directly stated by, or present in, the cited artifact.
- **Inference**: a consequence that follows from several artifacts but is not asserted verbatim by them.
- **Outlook / proposed mapping**: a technically plausible route for the report's dot product; it must not be presented as an executed Ascend experiment.

Local source inspection was performed on the official GitHub mirror of AscendNPU IR at commit `8d49415f4d75d53dc983353e49b6c99004b0f17c` (2026-09-22 checkout). The repository is a mirror of the canonical GitCode project. No build or device execution was attempted: the working host is Windows and no CANN/Ascend device environment was available.

## 1. What MLIR adds to the compiler design space

The central claim of MLIR is not merely that there are “more IRs.” It supplies a common SSA-based substrate on which domain-specific abstractions can coexist and be transformed without forcing every front end to jump immediately to a machine-oriented representation. The peer-reviewed CGO paper identifies three enabling ingredients: a standardized SSA IR structure, declarative dialect definition, and shared infrastructure for parsing/printing, source locations, passes, and other compiler services. Its evaluation is primarily a design argument plus a survey of applications, not a controlled proof that MLIR always improves generated code or engineering productivity. This is an important calibration for the report: MLIR demonstrates an extensible architecture, while performance remains pipeline- and target-dependent [Lattner et al., CGO 2021](https://doi.org/10.1109/CGO51591.2021.9370308).

### 1.1 Dialects are semantic namespaces, not sequential compiler phases

An MLIR **dialect** defines a namespace containing operations, types, and attributes. Multiple dialects can coexist in one module, so `tensor`, `linalg`, `arith`, `scf`, `memref`, `vector`, `gpu`, and a vendor dialect need not form a rigid stack in which only one is present at a time. The official language reference explicitly permits this coexistence and describes dialect conversion as transformation between or within dialects ([MLIR Language Reference](https://mlir.llvm.org/docs/LangRef/)).

This distinction prevents a common pedagogical error:

| Misleading ladder | More accurate model |
|---|---|
| “tensor IR becomes linalg IR, then affine IR, then SCF IR, then vector IR…” | A module usually contains a changing mixture. A pass may eliminate one family of illegal operations while retaining legal operations from several other dialects. |
| Each dialect is strictly higher or lower than every other dialect. | Dialects capture different concerns: `tensor` versus `memref` is value versus buffer semantics; `linalg` is structured computation; `scf` is structured control; `vector` represents virtual SIMD; `gpu` represents kernel launch and hierarchy. Their relative “level” is partial, not total. |
| Lowering is one irreversible translation. | Lowering is typically a succession of rewrites/conversions; canonicalization and target-specific optimization can occur between conversions. |

The Linalg rationale makes the information-preservation argument particularly clear: lowering too early to loops or CFG form loses properties such as parallel-loop intent or correspondence to a library operation and creates difficult phase-ordering problems. Linalg therefore retains named/structured semantics through transformations such as tiling and fusion ([Linalg rationale](https://mlir.llvm.org/docs/Rationale/RationaleLinalgDialect/)).

### 1.2 Interfaces are the modularity mechanism

Dialects alone could simply move the compiler's giant switch statements into new namespaces. MLIR **interfaces** address that problem by letting analyses and transformations ask semantic questions without knowing every concrete operation class. Operation interfaces describe per-operation capabilities; dialect interfaces cover behavior applying broadly across a dialect. External models allow a transformation library to attach an interface implementation without making the core dialect depend on that transformation ([MLIR Interfaces](https://mlir.llvm.org/docs/Interfaces/)).

Examples relevant to this report include:

- `BufferizableOpInterface`, which tells One-Shot Bufferize how an operation reads, writes, aliases, and rewrites to buffers;
- `DestinationStyleOpInterface`, which captures computations whose output/init operands make update destinations explicit;
- `LinalgStructuredInterface`, which exposes loop/indexing structure for generic tiling, fusion, and vectorization;
- `MemoryEffectOpInterface`, which permits safe reasoning by CSE, DCE, LICM, and schedulers.

AscendNPU IR visibly uses the same mechanism rather than building a separate compiler object model. For example, `hfusion.arange` implements `DestinationStyleOpInterface`, `LinalgStructuredInterface`, `MemoryEffectOpInterface`, and shape reification; HIVM custom operations implement destination style, memory-effect, core-type, pipe, and structured-operation interfaces ([HFusion dialect reference](https://ascendnpu-ir.gitcode.com/en/developer_guide/dialects/hfusion_dialect.html), [HIVM dialect reference](https://ascendnpu-ir.gitcode.com/en/developer_guide/dialects/hivm_dialect.html)). **Inference:** this interface reuse is what allows generic MLIR mechanisms to remain applicable while Ascend-specific semantics are added.

## 2. Rewriting and dialect conversion: the actual mechanics of progressive lowering

Ordinary pattern rewriting expresses a local semantic replacement. **Dialect conversion** adds a global contract: a `ConversionTarget` declares which operations are legal, illegal, or dynamically legal; a set of conversion patterns legalizes illegal operations; and an optional `TypeConverter` changes types and region/block signatures. The driver may use chains of patterns, not only direct source-to-final patterns ([MLIR Dialect Conversion](https://mlir.llvm.org/docs/DialectConversion/)).

Three conversion modes have materially different claims:

| Mode | Success condition | Appropriate use |
|---|---|---|
| Partial conversion | Explicitly illegal operations must be legalized; unspecified operations may remain. | Progressive lowering and mixed-dialect IR. |
| Full conversion | Every operation in scope must be legal for the target. | A phase boundary where residual high-level IR is an error. |
| Analysis conversion | Reports legalizability without committing rewrites. | Diagnostics and planning. |

**Dynamic legality** matters because legality often depends on types or attributes, e.g. an operation may be legal only after its operand/result types have been converted. Recursive legality can declare an entire nested region legal once its owner satisfies a condition. A report should therefore avoid saying “the pass replaces every operation in dialect A with dialect B”; conversion targets express a more precise invariant.

### 2.1 One-to-many type lowering

MLIR's current `TypeConverter` can map one source type to zero, one, or multiple target types. This is **one-to-many (1:N) type conversion**, not merely an operation expanding to several instructions. Materializations bridge temporarily incompatible producer/consumer type systems; when no custom materialization is built, `builtin.unrealized_conversion_cast` can temporarily connect the values. Such casts have no execution semantics and should be reconciled before the final executable boundary ([Dialect Conversion](https://mlir.llvm.org/docs/DialectConversion/), [Builtin dialect](https://mlir.llvm.org/docs/Dialects/Builtin/)).

A concrete example is the LLVM calling convention for memrefs. A ranked memref logically carries an allocated pointer, aligned pointer, offset, sizes, and strides. In an LLVM-dialect function signature, this descriptor may be unbundled into multiple scalar arguments; for an `n`-dimensional memref the signature contains two pointers, an offset, `n` sizes, and `n` strides. This illustrates why 1:N conversion is essential at ABI boundaries ([MLIR LLVM IR target](https://mlir.llvm.org/docs/TargetLLVMIR/)). It should not be confused with Ascend vector splitting, reduction decomposition, or scalar instruction selection; those may also be one-to-many *operation rewrites* but answer different questions.

### 2.2 Why partial lowering remains type-safe

During progressive conversion, an already converted producer can feed an unconverted consumer or vice versa. The conversion framework preserves the original use-site type contract and inserts source or target materializations as required. Conversion fails if a required bridge cannot be constructed. This is more rigorous than textually mixing arbitrary dialects: mixed IR is allowed, but SSA values remain type-correct ([Dialect Conversion](https://mlir.llvm.org/docs/DialectConversion/)).

## 3. The reusable MLIR levels relevant to a reduction or dot product

The following are roles, not a mandatory linear sequence.

| Dialect / mechanism | Semantic payload retained | Typical next decisions |
|---|---|---|
| `tensor` | Immutable/value-semantics shaped values, dimensions, slices, reshapes. No concrete storage identity. | Fusion, tiling, shape reasoning; later bufferization. |
| `linalg` | Structured iteration spaces, indexing maps, parallel/reduction iterator intent, destination-style output. | Tile/fuse/interchange/vectorize, library-call selection, or lower to loops. |
| `affine` | Loops and memory accesses whose bounds/maps are affine; enables polyhedral transformations. | Tiling, dependence analysis, loop transformations; lower to SCF/CFG. |
| `scf` | Structured `for`, `while`, `if`, parallel/reduction control flow. | Lower to `cf`, map parallel structure, scalarize/vectorize. |
| `vector` | Target-independent virtual SIMD and multidimensional vector operations. | Shape/legalization rewrites, target-specific vector dialects/intrinsics, LLVM dialect. |
| `gpu` | Kernel launch, grid/block/thread hierarchy, address spaces, host/device separation. | Outline kernels and lower to target dialect/runtime (e.g. NVVM/ROCDL/SPIR-V); it does not itself parallelize sequential code. |
| `memref` + bufferization | Concrete buffer identity, layout, memory space, loads/stores, allocation. | Lifetime/deallocation, address calculation, ABI lowering. |
| `llvm` dialect | An MLIR representation intentionally close to LLVM IR types, instructions, intrinsics, and ABI. | Mechanical translation to external LLVM IR, then LLVM optimization/code generation. |

Supporting official sources: [Linalg dialect](https://mlir.llvm.org/docs/Dialects/Linalg/), [SCF dialect](https://mlir.llvm.org/docs/Dialects/SCFDialect/), [Vector dialect](https://mlir.llvm.org/docs/Dialects/Vector/), [GPU dialect](https://mlir.llvm.org/docs/Dialects/GPU/), [LLVM dialect](https://mlir.llvm.org/docs/Dialects/LLVM/).

### 3.1 Bufferization is a semantic boundary, not a syntax cleanup

Bufferization converts tensor semantics into memref semantics. Upstream MLIR recommends doing many tile/fuse transformations in tensor form first and bufferizing late, because those transformations are often easier in value semantics. One-Shot Bufferize analyzes tensor SSA use-def chains over a whole function and tries to reuse buffers in place; out-of-place decisions introduce allocations/copies. It is extensible through `BufferizableOpInterface` and can fail on unknown tensor operations unless an explicit unknown-op boundary is permitted ([MLIR Bufferization](https://mlir.llvm.org/docs/Bufferization/)).

This boundary exposes aliasing, lifetime, and ownership. It is therefore where an apparently innocent reduction can acquire significant traffic through copies. The ownership-based deallocation pipeline is preferred over the deprecated buffer deallocation pass. Function-boundary bufferization has restrictions, notably no recursive call graphs in the documented implementation. These are practical constraints, not abstract details.

Memory spaces also become executable constraints. Upstream `memref` permits a memory-space attribute whose meaning is target-defined. GPU compilation maps spaces to target address spaces. AscendNPU IR uses `#hivm.address_space<gm>`, `<ub>`, `<l1>`, and `<l0a/l0b/l0c>` to express the global and on-chip hierarchy. The HIVM `VecAdd` example explicitly copies GM inputs into UB, computes in UB, then stores to GM.

### 3.2 The LLVM dialect boundary

The LLVM dialect is not external LLVM IR. It is an MLIR dialect whose operations/types are required to correspond to LLVM IR semantics (apart from explicitly documented MLIR conveniences). Production of LLVM IR is a two-step process: (1) convert all relevant MLIR to LLVM-translatable dialects, normally the LLVM dialect plus allowed target-specific intrinsic dialects; (2) translate that representation to external LLVM IR. Non-trivial transformations should occur before or during step 1; translation is intended to be simple ([LLVM dialect](https://mlir.llvm.org/docs/Dialects/LLVM/), [LLVM IR target](https://mlir.llvm.org/docs/TargetLLVMIR/)).

Ranked memrefs lower by default to descriptor structs, and function arguments are unbundled under the default convention. A bare-pointer convention exists only under restrictions such as static shapes/default layouts. Thus, “lowering a buffer to `ptr`” is not generally accurate; layout/shape metadata may survive in the ABI.

## 4. AscendNPU IR and the official HIVM `VecAdd`

### 4.1 Architecture observed in official documentation and source

The official architecture divides responsibilities as follows ([AscendNPU IR architecture](https://ascendnpu-ir.gitcode.com/en/introduction/architecture.html)):

- **HFusion** extends Linalg with named structured operations. It provides ecosystem conversion, hardware-independent preprocessing, and automatic fusion/kernel plus host-tiling generation. Preserving named semantics is intentional.
- **HIVM** models NPU computation, movement, and synchronization at tile level, then makes CV-core division, on-chip memory, pipeline, and instruction details explicit.
- **HACC** models heterogeneous asynchronous computing/calling and annotates device entry points, target properties, host helper relationships, and kernel ABI information.
- **Annotation/Scope** carry compiler hints on operands and operations.
- `bishengir-compile` lowers high-abstraction tile operations to low-level, hardware-aware MLIR. The documented `hivmc` stage converts low-level MLIR to LLVM IR, performs low-level LLVM optimization, and emits the operator binary.

The current source tree has explicit conversion components such as `TorchToHFusion` and `HFusionToHIVM`, dialect implementations, `bishengir-opt`, and the `bishengir-compile` driver. Official architecture documentation says the maintained LLVM dependency is based on an Ascend branch of LLVM 19.1.7, while the source build also exposes an LLVM-21 compatibility option. This is evidence of real upstream integration effort, but also of version coupling rather than a claim that arbitrary upstream MLIR snapshots are interchangeable.

### 4.2 What the `VecAdd` program actually shows

The quick-start input is already low-level HIVM/memref IR, not a source-to-HFusion lowering demonstration ([official compilation and execution example](https://ascendnpu-ir.gitcode.com/en/introduction/quick_start/examples.html); [source at inspected commit](https://github.com/Ascend/AscendNPU-IR/blob/8d49415f4d75d53dc983353e49b6c99004b0f17c/bishengir/test/Integration/HIVM/VecAdd/add.mlir)). Its essential dataflow is:

```text
GM arg0 ──hivm.hir.load──▶ UB temporary A ┐
                                          ├─hivm.hir.vadd─▶ UB temporary C
GM arg1 ──hivm.hir.load──▶ UB temporary B ┘                    │
                                                               └─hivm.hir.store─▶ GM arg2
```
All three external buffers are `memref<16xi16, #hivm.address_space<gm>>`. Three local allocations use `#hivm.address_space<ub>`. `hacc.entry` and `hacc.function_kind = DEVICE` identify the kernel entry. Compilation uses:

```bash
bishengir-compile add.mlir -enable-hivm-compile -o kernel.o
```

The CANN host program initializes ACL, selects a device, allocates device memory, copies inputs host-to-device, registers the emitted binary and function, launches it on a stream, synchronizes, copies the output back, and compares sixteen values. Therefore the example covers device compilation **and** the runtime boundary; `kernel.o` is not a standalone host executable.

What it does **not** establish:

1. It does not show source/Torch/Linalg/HFusion to HIVM lowering because its input begins at HIVM.
2. It does not expose the internal pass sequence unless IR-print/debug options are enabled.
3. It validates one fixed `i16[16]` vector addition, not dynamic shapes, reductions, fusion quality, or performance portability.
4. The quick-start expected output is a functional check, not a benchmark.

The official FAQ documents pass-local IR capture, e.g. `--bishengir-print-ir-before=<pass>` and `--bishengir-print-ir-after=<pass>`, and `bishengir-opt` can run an individual pass. These are the appropriate mechanisms for making a progressive-lowering claim inspectable ([AscendNPU IR FAQ](https://ascendnpu-ir.gitcode.com/en/faq/faq.html)).

### 4.3 Memory hierarchy is part of correctness and scheduling

For Atlas A2-class hardware, official documentation lists 32-byte alignment for UB/L1, 512-byte alignment for L0A/L0B/L0C, and 64-byte alignment for BT/FP. `PlanMemory` assigns addresses to `memref.alloc` buffers based on live intervals and hardware constraints, reusing limited on-chip storage while avoiding overwrite and artificial dependencies ([AscendNPU IR memory management](https://ascendnpu-ir.gitcode.com/en/developer_guide/features/plan_memory.html)). This gives a concrete reason for MLIR-level memory spaces: they affect legal placement, DMA operations, alignment, capacity, and scheduling—not merely annotation.

For a dot product, the critical issue is that both input streaming and the partial accumulator must fit an execution strategy. A high-level tensor reduction does not by itself decide chunk sizes, UB residence, cross-core combination, synchronization, or accumulation precision. Those decisions belong in HFusion scheduling/HIVM lowering and must be checked against the exact device generation.

## 5. Outlook: a progressive mapping for the report's dot product

This section is a **proposed explanatory mapping, not an executed pipeline**. It should be marked “outlook” in the paper unless corresponding IR snapshots and device results are later generated.

Assume the kernel computes

\[
s = \sum_{i=0}^{N-1} x_i y_i.
\]

### Stage A — tensor/Linalg semantics

A tensor-level form can express multiplication followed by reduction, or a single `linalg.dot` where supported. A generic structured form has one reduction iterator and indexing maps that read `x[i]`, `y[i]`, and a scalar accumulator. The key retained fact is “this is a dot product/reduction,” rather than merely an arbitrary loop-carried dependence.

This is the stage for algebraic fusion and tiling decisions. Reassociation is not automatically semantics-preserving for IEEE floating point: parallel or vector reduction changes addition order. A report must state whether fast-math/reassociation is permitted and use tolerance-based validation. AscendNPU IR's compilation options explicitly distinguish deterministic reduction behavior from faster multi-core strategies, making this a real semantic/performance choice rather than a footnote ([AscendNPU IR compilation options](https://ascendnpu-ir.gitcode.com/en/user_guide/compile_option.html)).

Ascend-specific high-level route: the current integration guide documents Torch `aten.sum` lowering to `linalg.reduce` plus `arith.addf/addi`, and supplies an HFusion example that multiplies tensors then reduces a dimension. It also documents `bishengir-compile -enable-hfusion-compile=true -enable-hivm-compile=true ...` for this level ([Framework integration](https://ascendnpu-ir.gitcode.com/en/developer_guide/conversion/framework_interface.html)). This is stronger evidence for the report's dot-product outlook than extrapolating only from `VecAdd`.

### Stage B — tiling and branch in the lowering graph

Choose a tile size from vector width, UB capacity, alignment, and expected `N`. Conceptually:

1. partition `[0,N)` into tiles;
2. load `x` and `y` tiles;
3. multiply and locally reduce/vector-accumulate;
4. combine partial sums;
5. handle a masked or scalar tail if `N` is not tile-aligned.

At this point the lowering graph can branch:

- **CPU/general loop route:** Linalg on buffers can lower to `affine.for` when bounds/accesses are affine, or directly to `scf.for`. `affine` is useful only when its restrictions buy dependence/polyhedral transformations; it is not a compulsory waypoint. SCF normally lowers to `cf` before LLVM/SPIR-V.
- **Vector route:** vectorize an inner tile into `vector.transfer_read`, multiply/FMA, and `vector.reduction`; progressively legalize multidimensional/abstract vectors to hardware-supported shapes, then target-specific intrinsics or LLVM dialect.
- **Generic GPU route:** map explicitly parallel loops to `gpu.launch` / `gpu.func`, with block/thread IDs and workgroup/private memory. The upstream default GPU pipelines require already parallel IR; they do not discover parallelism automatically ([GPU dialect](https://mlir.llvm.org/docs/Dialects/GPU/)). Device code then follows a target dialect such as NVVM/ROCDL/SPIR-V, while host launch code becomes runtime calls. This is a conceptual comparison, **not the documented Ascend route**.
- **Ascend route:** retain Linalg/HFusion reduction semantics for automatic fusion/scheduling, then lower to HIVM tile operations with explicit GM↔UB movement, vector/Cube core mapping as appropriate, synchronization, and memory planning. For Ascend 950 Triton paths, the official project also documents reduction decomposition into sub-reductions/layout conversions to use warp-synchronous reduction and avoid global-memory atomics, but that exact Triton pass must not be claimed for the HIVM `VecAdd` path ([Ascend reduction decomposition](https://ascendnpu-ir.gitcode.com/en/developer_guide/features/layout_optimizations.html)).

### Stage C — buffer and memory-space realization

Late bufferization chooses in-place versus out-of-place storage and converts tensor values to memrefs. In a host CPU route, ordinary memory and stack/heap allocations may suffice. In Ascend HIVM, the intended structure is closer to:

```text
memref<... x element, gm> inputs
  └─ tile/chunk load → memref<tile x element, ub>
       └─ vector multiply + local reduction → UB/register-like partial
            └─ combine partials/synchronize as required
                 └─ store scalar result → memref<1 x accumulator, gm>
```

This diagram deliberately does not invent exact HIVM operation names for multiply/reduce or an exact tile size. Those details must come from generated IR for a specific AscendNPU IR version and target.

### Stage D — LLVM-like boundary and binary

For upstream CPU lowering, `memref`, `arith`, `func`, `cf`, and vector operations are converted to LLVM dialect; memrefs become descriptors (or restricted bare pointers), and LLVM dialect translates to external LLVM IR. For Ascend, the documented boundary is low-level MLIR → `hivmc` → LLVM IR optimization → operator binary. “LLVM-like” is the safe description unless an actual dump establishes the precise vendor dialect and ABI at each substage. The host program remains responsible for CANN runtime initialization, allocation/copies, binary registration, launch, synchronization, and result retrieval.

### Evidence required to upgrade the outlook into a result

1. Pin AscendNPU IR, CANN, compiler, target chip, and driver versions.
2. Save source/Torch or HFusion input and every material phase boundary using `bishengir-opt` and pass print options.
3. Show that all residual high-level operations are legal for each claimed boundary; do not infer a pass from a diagram alone.
4. Validate numerical results against a higher-precision reference over zero length (if legal), non-multiple tile sizes, large `N`, cancellation-heavy inputs, NaN/Inf policy, and randomized inputs.
5. Record accumulator type and floating-point flags; compare deterministic and non-deterministic/multi-core modes where applicable.
6. Profile transfer, kernel, and end-to-end time separately after warm-up; report tile/block parameters and memory consumption.

## 6. Practical readiness and limitations

| Dimension | Evidence | Judgment |
|---|---|---|
| Upstream MLIR concepts | Stable, well-documented core model; peer-reviewed architecture paper; extensive dialect and conversion documentation. | Ready for explaining compiler architecture. Exact APIs/pass names are version-sensitive. |
| AscendNPU IR availability | Apache-2.0 source, tests, Sphinx docs, `bishengir-opt`, `bishengir-compile`, Docker/build guidance, CI-oriented tests. | Substantial production-oriented project, not a paper prototype. |
| End-to-end accessibility | Requires matched CANN/ops packages and an Ascend runtime/device for actual execution. Official source build uses CMake ≥3.28, Ninja ≥1.12 and pinned LLVM/Torch-MLIR submodules. | Reproducibility is materially harder than upstream CPU MLIR; binary installation/Docker can reduce build friction but not eliminate device/version coupling. |
| Version matrix | Official matrix maps v1.0.0→CANN 8.5.0, v1.1.0→9.0.0, v1.2.0→9.1.0 and lists supported device families ([version compatibility](https://ascendnpu-ir.gitcode.com/en/introduction/quick_start/version_compatibility.html)). | Reports must pin versions; “works on Ascend” is too broad. |
| Quick-start coverage | Fixed-size HIVM `i16` VecAdd plus CANN host launch. | Excellent minimal runtime anatomy; weak evidence for high-level progressive lowering, dynamic shapes, reduction, or performance. |
| Introspection | Official pass-before/after printing and individual `bishengir-opt` passes. | Sufficient to produce auditable lowering snapshots when the toolchain is installed. |
| Numerical semantics | Deterministic-computing option and documentation acknowledge accumulation-order/precision issues. | Reduction studies need explicit tolerances and semantics; bitwise equality is generally the wrong default. |
| Portability | HFusion is closer to shared Linalg abstractions; HIVM directly represents Ascend memory/core/pipeline details. | Higher layers offer ecosystem reuse; lower layers trade portability for control. This is intentional, not a defect. |
| Upstream drift | Ascend maintains target branches and compatibility switches rather than consuming arbitrary LLVM head. | Expect integration and maintenance cost. Do not copy current upstream pass pipelines into an Ascend report without checking its pinned tree. |

The strongest defensible conclusion is therefore: MLIR's value is its ability to preserve and selectively discharge semantics across a mixed-dialect module; AscendNPU IR is a concrete, open implementation of that approach spanning Linalg-derived HFusion, NPU-specific HIVM, LLVM-based low-level compilation, and CANN runtime. The official VecAdd verifies the lowest visible HIVM/runtime slice. A dot-product narrative through tensor/Linalg/loops/vector/GPU/LLVM-like levels is pedagogically useful, but only the branches actually dumped and executed should be reported as experimental results.

## 7. Recommended report figure and wording

Use a **branching lowering graph**, not a vertical ladder:

```text
source / framework IR
        │
 tensor + linalg/HFusion ── tile/fuse/schedule ──┬─ bufferize → affine/scf → vector → LLVM dialect → CPU
                                                 ├─ explicit parallel mapping → gpu → NVVM/ROCDL/SPIR-V
                                                 └─ HFusion → HIVM (GM/UB/L1/L0, pipes/sync)
                                                                  → hivmc/LLVM IR → Ascend kernel.o
                                                                                         │
                                                      CANN host/runtime ─────────────────┘
```

Suggested calibrated wording:

> MLIR progressive lowering is not a fixed sequence of universal dialects. It is the controlled replacement of operations and types under explicit legality rules while multiple abstractions coexist. In AscendNPU IR, HFusion retains structured tensor semantics for fusion and scheduling, whereas HIVM makes NPU memory movement, on-chip placement, and pipeline behavior explicit. The official VecAdd begins at the latter level; our tensor-to-HIVM dot-product route is an outlook based on the documented integration pipeline, not a completed device experiment.

## Bibliographic metadata

```bibtex
@inproceedings{lattner2021mlir,
  author    = {Chris Lattner and Mehdi Amini and Uday Bondhugula and Albert Cohen and Andy Davis and Jacques A. Pienaar and River Riddle and Tatiana Shpeisman and Nicolas Vasilache and Oleksandr Zinenko},
  title     = {{MLIR}: Scaling Compiler Infrastructure for Domain Specific Computation},
  booktitle = {2021 IEEE/ACM International Symposium on Code Generation and Optimization (CGO)},
  year      = {2021},
  pages     = {2--14},
  publisher = {IEEE},
  doi       = {10.1109/CGO51591.2021.9370308},
  url       = {https://doi.org/10.1109/CGO51591.2021.9370308}
}

@manual{mlirDialectConversion,
  author       = {{LLVM Project}},
  title        = {MLIR Dialect Conversion},
  organization = {LLVM Project},
  url          = {https://mlir.llvm.org/docs/DialectConversion/},
  note         = {Accessed 2026-09-22}
}

@manual{mlirBufferization,
  author       = {{LLVM Project}},
  title        = {MLIR Bufferization},
  organization = {LLVM Project},
  url          = {https://mlir.llvm.org/docs/Bufferization/},
  note         = {Accessed 2026-09-22}
}

@manual{mlirLLVMTarget,
  author       = {{LLVM Project}},
  title        = {LLVM IR Target},
  organization = {LLVM Project},
  url          = {https://mlir.llvm.org/docs/TargetLLVMIR/},
  note         = {Accessed 2026-09-22}
}

@manual{ascendNpuIrArchitecture,
  author       = {{Huawei Ascend Community}},
  title        = {AscendNPU IR Architecture Design},
  organization = {Huawei},
  year         = {2026},
  url          = {https://ascendnpu-ir.gitcode.com/en/introduction/architecture.html},
  note         = {Accessed 2026-09-22; source revision 8d49415f4d75d53dc983353e49b6c99004b0f17c}
}

@manual{ascendNpuIrVecAdd,
  author       = {{Huawei Ascend Community}},
  title        = {AscendNPU IR Compilation and Execution Example},
  organization = {Huawei},
  year         = {2026},
  url          = {https://ascendnpu-ir.gitcode.com/en/introduction/quick_start/examples.html},
  note         = {Accessed 2026-09-22; HIVM VecAdd and CANN runtime host}
}

@software{ascendNpuIrSource,
  author  = {{Huawei Ascend Community}},
  title   = {AscendNPU-IR},
  version = {Git revision 8d49415f4d75d53dc983353e49b6c99004b0f17c},
  year    = {2026},
  url     = {https://github.com/Ascend/AscendNPU-IR},
  license = {Apache-2.0}
}
```
