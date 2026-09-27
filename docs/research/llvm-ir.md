# LLVM IR evidence notes for the compiler-systems survey

**Scope and decision purpose.** These notes support a case-study chapter that follows one small SysY/C-like program from frontend-emitted LLVM IR through canonicalization and optimization. They explain what each visible IR construct means, which transformations are plausible, and where a student report must not overclaim. The intended LLVM baseline is the rolling LLVM documentation accessed **2026-09-22** (currently advertising LLVM 24.0.0git in generated pages). LLVM IR is a moving target: the report should state the exact `clang --version`, target triple, and commands used for any reproduced listing.

## 1. The shortest defensible mental model

LLVM IR is simultaneously:

1. a typed, target-aware, low-level intermediate language;
2. an in-memory graph of `Module`, `Function`, `BasicBlock`, and `Instruction` objects;
3. a textual assembly syntax (`.ll`) and a compact serialized bitcode format (`.bc`); and
4. the semantic contract between frontends, the target-independent optimizer, and code generation.

The classic LLVM paper describes the key design as a low-level, language-independent, typed SSA representation supporting analysis and transformation across compile time, link time, run time, and idle time [Lattner and Adve 2004]. That historical description remains useful, but current LangRef is authoritative for current syntax and semantics. In particular, old examples with typed pointers such as `i32*` are obsolete: LLVM 17 and later support only **opaque pointers**, written `ptr`; the accessed element type is carried by `load`, `store`, `getelementptr`, and related operations rather than by the pointer type itself ([Opaque Pointers](https://llvm.org/docs/OpaquePointers.html)).

### Representation hierarchy

| Unit | Semantics | Important invariants / traps |
|---|---|---|
| `Module` | Roughly a translation unit: target information, type declarations, globals, function declarations/definitions, aliases, metadata, and module flags. Modules may be linked/merged. | A module's `target datalayout` must match the eventual code generator; omitting it does **not** make the IR target-neutral because optimizers use defaults. |
| Type | Integers of arbitrary bit width, floating point, vectors, arrays, structures, function types, labels, tokens, metadata, and opaque pointers/address spaces. | LLVM memory itself is not typed. A `ptr` does not promise a pointee type; instruction operands state the access type. Source-language type/alias facts require attributes or metadata such as TBAA. |
| `Function` | A signature plus linkage/calling convention/attributes and, for a definition, a CFG of basic blocks. A declaration has no body. | Calling convention, ABI-significant attributes, return/parameter types, and varargs conventions must agree at calls. Attributes are semantic promises, not comments. |
| `BasicBlock` | A straight-line instruction sequence with one entry and one terminating control-transfer instruction; blocks and branch edges form the function CFG. | Every block ends in a terminator. Entry has no predecessors and therefore no PHIs. PHIs must precede non-PHI instructions. |
| SSA value | Function arguments, instruction results, constants, and globals are values; local `%names` are function-scoped and assigned once. | SSA applies to values, not mutable memory. `store` has no SSA result; repeated reads/writes remain possible via pointers. |

Evidence: current LangRef states that modules contain functions, global variables and symbol-table entries; that function bodies are lists of blocks forming a CFG; that each block ends in a terminator; and that the entry block has neither predecessors nor PHIs ([LangRef: High-Level Structure](https://llvm.org/docs/LangRef.html#high-level-structure)).

## 2. A single case study that exposes the central mechanisms

Use a loop reduction over an input array because it connects source variables, addresses, control flow, SSA joins, calls, alias facts, loop optimization, and vectorization without relying on exotic C++ constructs:

```c
int twice(int x) { return x + x; }

int sum_positive(int a[], int n, int scale) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        int x = a[i] * scale;
        if (x > 0)
            sum = sum + twice(x);
        i = i + 1;
    }
    return sum;
}
```

This is SysY-compatible in substance. For a complete report, put input/output calls in `main` and retain this kernel as a separate function so optimization behavior is readable. The illustrative optimized IR below is deliberately normalized and should not be presented as byte-for-byte Clang output:

```llvm
define i32 @twice(i32 %x) memory(none) nounwind {
entry:
  %r = shl i32 %x, 1
  ret i32 %r
}

define i32 @sum_positive(ptr captures(none) readonly %a,
                         i32 %n, i32 %scale) nounwind {
entry:
  %has.work = icmp sgt i32 %n, 0
  br i1 %has.work, label %loop, label %exit

loop:
  %i   = phi i32 [ 0, %entry ], [ %i.next, %latch ]
  %sum = phi i32 [ 0, %entry ], [ %sum.next, %latch ]
  %p   = getelementptr inbounds i32, ptr %a, i32 %i
  %v   = load i32, ptr %p, align 4
  %x   = mul i32 %v, %scale
  %pos = icmp sgt i32 %x, 0
  br i1 %pos, label %then, label %latch

then:
  %t = call i32 @twice(i32 %x)
  %s = add i32 %sum, %t
  br label %latch

latch:
  %sum.next = phi i32 [ %sum, %loop ], [ %s, %then ]
  %i.next = add nuw nsw i32 %i, 1
  %more = icmp slt i32 %i.next, %n
  br i1 %more, label %loop, label %exit

exit:
  %answer = phi i32 [ 0, %entry ], [ %sum.next, %latch ]
  ret i32 %answer
}
```

This listing illustrates structure, not a promise that Clang emits precisely these attributes or flags. For example, `nuw nsw` is only legal if overflow is impossible on every defined execution reaching the instruction; a hand-written frontend must prove that fact or omit the flags.

### Reading the CFG and PHIs

The CFG is:

```text
        entry
       /     \
     loop    exit
    /   \
 then  latch ----> loop
   \     |
    -----+--------> exit
```

At loop entry, `%i` and `%sum` choose their initial values on the edge from `entry` and back-edge values on the edge from `latch`. At `latch`, `%sum.next` selects unchanged `%sum` when the condition is false or updated `%s` after `then`. A PHI is conceptually an **edge selection**, not an executable parallel copy performed in the block. LangRef requires exactly one incoming pair per predecessor and requires PHIs to be at the beginning of a block ([LangRef: `phi`](https://llvm.org/docs/LangRef.html#phi-instruction)). This edge semantics matters when lowering PHIs to machine-level parallel copies and when splitting critical edges.

The dominance rule behind SSA should be stated explicitly: an ordinary definition must dominate every use; a PHI incoming value is considered used on its corresponding predecessor edge. The verifier catches violations. A useful pedagogical contrast is frontend `-O0`-like IR, where source locals are commonly represented by entry-block `alloca`, `store`, and `load`. SSA promotion then makes dataflow explicit:

```llvm
; memory form
%sum.addr = alloca i32, align 4
store i32 0, ptr %sum.addr
%old = load i32, ptr %sum.addr
%new = add i32 %old, %t
store i32 %new, ptr %sum.addr

; after promotion: values and PHIs, no stack traffic for sum
%sum = phi i32 [ 0, %entry ], [ %sum.next, %latch ]
```

## 3. Memory, layout, pointers, and GEP

### SSA values are not memory

LLVM separates an unbounded set of virtual SSA values from allocated objects. `alloca` creates a stack object; global definitions and recognized allocation calls create other objects; `load` and `store` access objects through pointers. Memory can therefore change even though every named SSA result is defined once. Optimizations need alias analysis and explicit memory-effect facts to know whether two accesses or a call can interfere.

For concurrency, LLVM specifies an axiomatic model inspired by C++: valid executions are constrained by program order, synchronization, and a happens-before relation. Atomic `load`, `store`, `cmpxchg`, `atomicrmw`, and `fence` take orderings. `volatile` is for externally observable/special accesses and **does not generally provide inter-thread synchronization** ([LangRef: Memory Model for Concurrent Operations](https://llvm.org/docs/LangRef.html#memory-model-for-concurrent-operations), [Atomic Instructions and Concurrency Guide](https://llvm.org/docs/Atomics.html)). The SysY case study is single-threaded, so an extensive atomic excursus should be framed as scope, not as an explanation of its ordinary loads.

### `target datalayout` is executable compiler knowledge

The data-layout string encodes endianness, pointer size/alignment by address space, integer/vector/aggregate alignment, native integer widths, stack alignment, and related target facts. For example, tokens beginning with `e`/`E` select little/big endian; `p...` describes pointers; `i...`, `f...`, `v...`, and `a...` describe alignments. Optimizations use this data to compute allocation size, struct padding, and legal/efficient accesses. Therefore:

* never hand-copy an x86-64 layout into a RISC-V or ARM module;
* ask Clang/LLVM's target machinery to produce it;
* report both `target triple` and `target datalayout`; and
* do not infer ABI field offsets merely from the source type.

The LangRef warns that the layout must match what the final code generator expects and that even default layout rules introduce target specificity ([LangRef: Data Layout](https://llvm.org/docs/LangRef.html#data-layout)).

### GEP means typed address calculation, not a load

`getelementptr` (GEP) computes an address by walking the layout of a stated source element type. It does not dereference memory. In the case study,

```llvm
%p = getelementptr inbounds i32, ptr %a, i32 %i
%v = load i32, ptr %p, align 4
```

the GEP computes `a + i * alloc_size(i32)` and the separate `load` reads. For a pointer to `{ i32, [40 x i32] }`, indices `0, 1, 17` mean: stay at the pointed-to outer object, select struct field 1, then select array element 17. A struct containing a pointer needs a `load` before indexing through that pointer; a single GEP cannot perform the implicit dereference.

`inbounds` is a semantic promise, not a speed hint. Violating its object-bounds/no-wrap conditions produces poison. A non-`inbounds` GEP may compute an out-of-object address, but dereferencing an address without valid allocation provenance remains invalid. The official GEP guide calls GEP a cornerstone of LLVM's pointer-aliasing model and notes that no static checker can catch all violations ([The Often Misunderstood GEP Instruction](https://llvm.org/docs/GetElementPtr.html); [LangRef: `getelementptr`](https://llvm.org/docs/LangRef.html#getelementptr-instruction)).

### Pointer provenance is more than an integer address

Current LangRef distinguishes the address bits of a pointer from its **provenance**, i.e. authority to access an allocation. An allocated object's bytes may be accessed only through a pointer based on that allocation; merely manufacturing the same numeric address is not a general license to access it. `ptrtoint`, pointer comparisons, captures, lifetime, GEP, alias analysis, and integer-pointer round trips therefore have subtleties that a flat-byte-array explanation misses ([LangRef: Allocated Objects and Pointer Aliasing Rules](https://llvm.org/docs/LangRef.html#allocated-objects)).

Practical caution: opaque pointers removed fake pointee-type semantics, not provenance or access-size semantics. Two identical `ptr` operands used by `store i32` and `load i64` are not the same typed access. Optimizer/plugin code must compare access types and sizes, not just pointer SSA identity ([Opaque Pointers: migration caveat](https://llvm.org/docs/OpaquePointers.html)).

## 4. Calls and attributes: contracts that create optimization power

A `call` identifies a return/signature type, callee pointer, typed arguments, optional calling convention, return/parameter/function attributes, tail-call marker, address space, fast-math flags where applicable, and operand bundles. Direct calls use `@name`; indirect calls use an SSA pointer. `tail` is a hint, whereas `musttail` imposes strict correctness and ABI constraints and must actually be tail-call optimized ([LangRef: `call`](https://llvm.org/docs/LangRef.html#call-instruction)). Exception-capable source operations may require `invoke` with normal and unwind successors rather than `call`.

Attributes should be explained as proof obligations:

| Attribute | Optimizer-visible promise | Misuse consequence / caveat |
|---|---|---|
| `noundef` | Parameter/return representation contains no undef or poison bits. | Passing/returning such bits is undefined behavior; under MemorySanitizer it is ABI-relevant. |
| `nonnull`, `dereferenceable(N)`, `align N` | Pointer address/non-faulting accessible range/alignment facts. | `nonnull` alone does not imply dereferenceability; one-past pointers exist. |
| `captures(none)` | Callee does not capture address or provenance of a pointer argument. | Current syntax is richer than historical `nocapture`; capture can be limited to address, read provenance, return, etc. Do not paste old syntax uncritically. |
| `noalias` (parameter/return) | Specialized allocation-like/non-alias relation defined by LangRef. | It is not a universal C `restrict` synonym; scope and direction matter. |
| `memory(none/read/write/...)` | Constrains externally visible memory effects, optionally by locations such as `argmem`. | Absent attribute means `memory(readwrite)`. A false promise licenses incorrect motion/deletion. |
| `nounwind`, `willreturn`, `nosync`, `nofree` | No LLVM-visible unwind; eventually returns; no inter-thread synchronization; does not free. | These are independent properties. `nounwind` does not say “cannot trap.” |
| `alwaysinline`, `noinline`, `cold`, `optsize`, `minsize` | Optimization policy/cost information. | Mostly policy rather than source semantics, but interaction with recursive calls and target costs remains contextual. |

Current details: [LangRef: Parameter Attributes](https://llvm.org/docs/LangRef.html#parameter-attributes), [Function Attributes](https://llvm.org/docs/LangRef.html#function-attributes). The richer `captures(...)` and `memory(...)` forms are especially important because many older tutorials show `nocapture`, `readnone`, and `readonly` as if those were the whole model.

## 5. Undefined behavior, `undef`, poison, and `freeze`

These concepts must not be collapsed into one “unknown value”:

| Concept | Working semantics | Example and consequence |
|---|---|---|
| Immediate undefined behavior (UB) | Execution has already violated the IR contract; the optimizer need preserve no behavior for that execution. | Dereference invalid/poison pointer; division by zero; reaching an explicit `unreachable` when not otherwise justified. |
| `undef` | Each use may observe an independently chosen unspecified bit pattern. Current LangRef recommends poison instead where possible. | Two uses of the same `undef` need not agree, so ordinary algebraic intuition fails. |
| `poison` | Deferred error/nondeterminism that propagates through most instructions until used in a UB-triggering position. | Signed overflow of `add nsw`; poison as branch condition, call target, or dereferenced pointer triggers immediate UB. `and poison, 0` remains poison. |
| `freeze v` | If `v` is undef/poison, chooses one arbitrary but fixed well-defined value for that freeze result; otherwise identity. | All uses of one frozen result agree. This permits safe speculative transformations where an unconstrained value must not change per use. |

The case study's `%i.next = add nuw nsw ...` illustrates the danger: `nsw`/`nuw` do not request checked arithmetic; they assert no signed/unsigned wrap on defined executions. If wrap occurs, the result is poison, which may later make `%more` and the branch condition poison, causing UB. Frontends must model source-language overflow rules accurately.

Authoritative semantics and examples: [LangRef: Undefined Values](https://llvm.org/docs/LangRef.html#undefined-values), [Poison Values](https://llvm.org/docs/LangRef.html#poison-values), [`freeze`](https://llvm.org/docs/LangRef.html#freeze-instruction). `freeze` returns one arbitrary fixed result per instruction; freezing a poison/undef pointer does not make it dereferenceable.

## 6. Optimization as interacting canonicalizations, not isolated magic tricks

LLVM's default pipeline is a sequence of analyses and transformations organized over modules, call-graph SCCs, functions, and loops. Analyses are cached and invalidated; pipeline order matters because one pass exposes or destroys another's patterns. Current target-independent optimization uses the New Pass Manager, while backend code generation still contains legacy-PM machinery ([Using the New Pass Manager](https://llvm.org/docs/NewPassManager.html)). For observation, prefer pipeline commands that work with the installed release rather than assuming a blog's flags remain stable:

```sh
clang -O0 -Xclang -disable-O0-optnone -S -emit-llvm case.c -o case.raw.ll
opt -S -passes='mem2reg,sroa,instcombine,simplifycfg' case.raw.ll -o case.canon.ll
opt -S -passes='default<O2>' -verify-each case.raw.ll -o case.O2.ll
opt -passes='default<O2>' -debug-pass-manager -disable-output case.raw.ll
clang -O2 -Rpass=loop-vectorize -Rpass-missed=loop-vectorize \
  -Rpass-analysis=loop-vectorize case.c -c
```

Check `opt --print-passes` and `opt --help` for the actual installation. `-Xclang -disable-O0-optnone` is useful for an experiment starting with unoptimized frontend IR because Clang normally marks `-O0` functions `optnone`; document this non-driver-stable `-Xclang` choice.

### Pass-by-pass causal chain

| Pass / family | What it can do in or near the case study | Required preconditions and non-claims |
|---|---|---|
| `mem2reg` | Promotes eligible entry-block scalar allocas used only by loads/stores into pruned SSA, inserting PHIs via dominance frontiers and renaming uses. This turns source-variable stack traffic for `i`/`sum` into loop-carried SSA. | Does not promote escaped addresses, arbitrary heap/global memory, volatile accesses, or general aliasing memory. Official pass docs describe loads/stores-only allocas and pruned SSA construction. |
| SROA (Scalar Replacement of Aggregates) | Splits eligible aggregate allocas into member/slice allocas and often promotes the pieces to SSA. Useful if the case study includes a fixed local array with constant accesses or a frontend-created aggregate temporary. | Dynamic/escaping/overlapping accesses can inhibit scalarization. SROA is broader than `mem2reg`, but still not “remove every array.” |
| InstCombine | Worklist-based, CFG-preserving algebraic and idiom canonicalization; e.g. adjacent adds, constant folding, casts, comparisons, or multiplication-by-power-of-two patterns become preferred forms. `twice(x)` may become a shift after inlining, subject to exact semantics. | Its mission is canonical form and simplification, not guaranteed target speed. Algebraic rewrites are constrained by overflow, poison, and floating-point flags. |
| GVN (Global Value Numbering) | Eliminates fully/partially redundant computations and redundant loads where memory reasoning proves the value unchanged. Repeated `a[i]` loads in the source may collapse after address/value equivalence is established. | A possibly-writing call or aliasing store blocks load elimination unless attributes/alias analysis prove non-interference. “Same textual expression” is insufficient. |
| LICM (Loop-Invariant Code Motion) | Hoists safe loop-invariant computations/loads to a preheader and may sink to exits; can promote must-alias memory with help from alias analysis. | Must preserve traps, poison, memory ordering, and observable behavior. The argument `%scale` is already a loop-invariant SSA value—there is no instruction to hoist. Do not claim every invariant-looking load moves. |
| Inlining + interprocedural attributes | May replace `call @twice` with its body and infer memory/capture/unwind facts, enabling InstCombine and vectorization. | Governed by cost and policy; not guaranteed. Recursive/large/cold boundaries and separate compilation matter. |
| Loop Vectorizer | Widens consecutive loop iterations; often generates runtime alias checks, vector loop, scalar remainder, and reduction code. | Profitability is target-specific and cost-model based. Conditional accumulation needs if-conversion/predication; calls must be inlined or vectorizable; overflow/FP semantics constrain reassociation. A missed vectorization is evidence to diagnose, not automatically a compiler defect. |
| SLP Vectorizer | Packs isomorphic independent scalar operations within a block into vectors. | Distinct from loop vectorization; best suited to straight-line “horizontal” similarity. |

Official pass descriptions: [`mem2reg`, SROA, GVN, InstCombine, LICM](https://llvm.org/docs/Passes.html). LLVM documents two vectorizers: Loop Vectorizer widens loop iterations, SLP packs scalar operations; both use target cost information, and optimization remarks explain success/failure ([Auto-Vectorization in LLVM](https://llvm.org/docs/Vectorizers.html)).

### Why the transformations compose

A defensible causal narrative for this kernel is:

```text
alloca/load/store form
   --mem2reg/SROA--> explicit SSA recurrence and simpler alias surface
   --inlining/attrs--> call side effects disappear or become precise
   --InstCombine/GVN--> canonical arithmetic + redundant values/loads removed
   --loop canonicalization/LICM--> analyzable preheader/latch and invariant work moved
   --LoopVectorize--> costed vector candidate, runtime checks/remainder if needed
   --InstCombine/DCE--> cleanup of generated scaffolding
```

This is an inference about common pipelines, not a fixed ordering guarantee for every LLVM release. The report should use `-debug-pass-manager`, `-print-before/after`, or `-opt-bisect-limit` on the actual toolchain to establish what occurred.

## 7. Verification: what is checked, and what is not

LLVM's verifier checks structural and semantic well-formedness that is statically decidable: types and signatures, terminators, dominance, PHI/predecessor consistency, attribute placement, selected metadata invariants, and many instruction-specific rules. Use:

```sh
llvm-as case.ll -o /dev/null           # parse + verify while assembling
opt -passes=verify -disable-output case.ll
opt -passes='default<O2>' -verify-each -disable-output case.ll
```

`-verify-each` inserts verification after every requested pass and is intended to identify the pass that first creates an invalid module ([`opt` command guide](https://llvm.org/docs/CommandGuide/opt.html#cmdoption-opt-verify-each)). It does **not** prove refinement, source equivalence, absence of UB, correct ABI selection, legal runtime GEP provenance, or preservation of debug-variable truth. The official GEP guide explicitly says there is no checker that can statically find all GEP rule violations.

For transformation correctness, **Alive2** performs bounded translation validation by encoding source/target LLVM IR refinement in SMT. The PLDI 2021 evaluation reported 47 newly reported bugs (28 then fixed) and eight LangRef patches; the method avoids false alarms but bounds resources/loop unrolling and can miss bugs outside its supported/bounded scope [Lopes et al. 2021]. Its memory-model encoding later found 21 new memory-optimization bugs (10 then fixed) while scaling to large intraprocedural workloads [Lee et al. 2021]. Thus:

* verifier success means “well-formed IR,” not “correct optimization”;
* Alive2 success is strong evidence within its modeling and bounds, not universal proof of the entire compiler; and
* execution tests remain valuable but sample behavior and are especially treacherous when the input contains UB.

## 8. Debug information and provenance caveats for the survey

Most source entities vanish or split under optimization. LLVM uses metadata plus debug records (currently the default model) to map optimized values/locations back to source variables and locations. Debug records are interleaved with instructions but are not instructions and do not affect generated code. The older debug-intrinsic model remains for backward compatibility, but one module must not mix the two models ([Source-Level Debugging with LLVM](https://llvm.org/docs/SourceLevelDebugging.html)).

Important interpretation rules:

1. `-g` does not make optimized IR resemble source. Inlining, block merging, tail duplication, promotion, scheduling, vectorization, and register allocation can all produce one-to-many or missing mappings.
2. A variable may legitimately be reported “optimized out.” Preserving a stale value would be worse than dropping location information; pass authors use poison-valued debug records to terminate misleading locations.
3. Debug metadata is not a semantic fence and should not inhibit optimization. Do not infer program behavior from line tables.
4. Source-level provenance (which expression/field/variable produced a value) is distinct from **pointer provenance** (which allocation a pointer may access). The same word is used for different concerns.
5. `llvm-dwarfdump`, `llvm-objdump --source`, and debugger stepping inspect downstream mappings; they do not validate source/IR equivalence by themselves.

The official documentation claims accurate readable source-level state as the goal/contract, but also acknowledges that optimization may prevent modification of variables or calls to optimized-away functions. Treat this as an engineering objective whose fidelity must be measured, not as a guarantee that every source variable is always available.

## 9. Current frontier and calibrated readiness

| Direction | Evidence / observed state | Judgment for a student compiler |
|---|---|---|
| Formal executable LLVM semantics | Vellvm mechanizes a substantial LLVM subset in Rocq/Coq, extracts an interpreter, and differentially tests it against LLVM. Its 2025 experience report emphasizes that LLVM is large, rapidly evolving, nondeterministic, and rich in UB [Beck, Chen, Zdancewic 2025]. A 2024 two-phase memory model reconciles idealized infinite addresses with finite execution, integer-pointer casts, and `undef` [Beck et al. 2024]. | Excellent for understanding why LangRef prose is insufficient for proof. Not a drop-in complete replacement for production LLVM semantics; coverage and version drift must be checked. |
| Translation validation | Alive2 checks individual LLVM transformations without modifying LLVM and has found real optimizer/spec bugs. Crellvm earlier explored compiler-produced witnesses checked by a verified checker [Kang et al. 2018]. | Integrate Alive2 for supported scalar/memory IR tests when practical. Preserve ordinary regression tests and sanitizers; bounded/support limitations matter. |
| Optimization-directed fuzzing | Optimuzz combines directed grey-box fuzzing with translation validation. PLDI 2025 reports 55 new LLVM miscompilation bugs, with 13 patched at paper time, and provides an artifact [Kwon et al. 2025]. | Production-relevant research direction for CI around recently changed optimizations. It complements proof/validation; bug counts do not measure overall compiler defect rates. |
| Explicit vectorization planning | LLVM's VPlan models candidates, cost and materialization, with a roadmap toward richer outer-loop, predication and compositional decisions. Current docs say it already drives LoopVectorize code generation and some VPlan-to-VPlan transforms ([VPlan](https://llvm.org/docs/VectorizationPlan.html)). | Observe generated vector IR and remarks; do not attempt a comparable vectorizer in a small teaching compiler. A clean loop IR and correct alias/overflow facts are the valuable prerequisites. |
| Vector predication and scalable vectors | LLVM's roadmap uses VP intrinsics/masks/explicit vector length to represent modern AVX-512, Arm SVE and RISC-V V behavior, with staged optimizer/codegen integration ([Vector Predication Roadmap](https://llvm.org/docs/Proposals/VectorPredication.html)). | Relevant to the report's RISC-V outlook. Still a roadmap/proposal surface; distinguish implemented facilities from intended native predicated instructions. |
| IR evolution | Opaque pointers are complete; current LangRef has richer pointer capture/provenance and memory effects, debug records, and evolving low-level types. | Pin the LLVM release. Generate IR via APIs/Clang rather than templating textual fragments; run the verifier after every custom pass. |

The strongest competing explanation for reported speedups is often not “this pass is brilliant,” but changed assumptions: UB introduced by the source, stronger attributes, different target CPU/features, benchmark warmup/noise, or an unfair baseline. Any optimization experiment should record inputs, compiler commit/version, target triple/CPU, optimization pipeline, runtime methodology, and emitted code size; inspect remarks and IR before attributing causality.

## 10. Recommended evidence protocol for the final report

1. **Pin the environment:** `clang --version`, `opt --version`, host/target triple, CPU features, OS, linker.
2. **Capture artifacts:** source, preprocessed source, raw `.ll`, selected after-pass snapshots, optimized `.ll`, assembly, object and executable under a repository-local experiment directory.
3. **Verify every IR:** `llvm-as` or `opt -passes=verify`; use `-verify-each` for custom pipelines.
4. **Separate observations from explanations:** “the call disappeared” is observed; “the inliner removed it, enabling InstCombine” requires pass logs/remarks or before/after snapshots.
5. **Control semantics:** run boundary inputs and UBSan where applicable; do not benchmark a source program whose signed overflow/out-of-bounds behavior is undefined.
6. **Measure vectorization rather than assume it:** collect `-Rpass`, `-Rpass-missed`, and `-Rpass-analysis`, then inspect vector and scalar remainder loops.
7. **Avoid version archaeology errors:** translate old typed-pointer examples to opaque pointers and current attributes; cite rolling docs with access date and the reproduced LLVM release.

## 11. Source quality and claim status

* **Observed in current official specification/docs:** module/CFG/type rules, opaque pointers, data layout, GEP, attributes, UB/poison/freeze, pass descriptions, verifier flags, vectorizer behavior, debug-record model.
* **Peer-reviewed empirical claims:** bug counts and tool limits for Alive2, Alive2 memory encoding, and Optimuzz; mechanization scope/methodology for Vellvm.
* **Inference/recommendation:** the proposed case-study pipeline and teaching order. It is a plausible causal chain but must be confirmed against the pinned toolchain.
* **Material uncertainty:** LLVM's rolling documentation changes; textual syntax and pass names/pipelines may drift. Formal models cover subsets and lag upstream. Vectorization profitability varies across targets and releases.

## 12. BibTeX-ready references

```bibtex
@inproceedings{LattnerAdve2004LLVM,
  author    = {Chris Lattner and Vikram Adve},
  title     = {{LLVM}: A Compilation Framework for Lifelong Program Analysis and Transformation},
  booktitle = {Proceedings of the International Symposium on Code Generation and Optimization},
  pages     = {75--86},
  year      = {2004},
  doi       = {10.1109/CGO.2004.1281665},
  url       = {https://llvm.org/pubs/2004-01-30-CGO-LLVM.html}
}

@inproceedings{LopesEtAl2021Alive2,
  author    = {Nuno P. Lopes and Juneyoung Lee and Chung-Kil Hur and Zhengyang Liu and John Regehr},
  title     = {Alive2: Bounded Translation Validation for {LLVM}},
  booktitle = {Proceedings of the 42nd ACM SIGPLAN International Conference on Programming Language Design and Implementation},
  pages     = {65--79},
  year      = {2021},
  doi       = {10.1145/3453483.3454030},
  url       = {https://web.ist.utl.pt/nuno.lopes/pubs.php?id=alive2-pldi21}
}

@inproceedings{LeeEtAl2021LLVMMemory,
  author    = {Juneyoung Lee and Dongjoo Kim and Chung-Kil Hur and Nuno P. Lopes},
  title     = {An {SMT} Encoding of {LLVM}'s Memory Model for Bounded Translation Validation},
  booktitle = {Computer Aided Verification: 33rd International Conference},
  year      = {2021},
  doi       = {10.1007/978-3-030-81688-9_35},
  url       = {https://web.ist.utl.pt/nuno.lopes/pubs.php?id=alive2-mem-cav21}
}

@inproceedings{KangEtAl2018Crellvm,
  author    = {Jeehoon Kang and Yoonseung Kim and Youngju Song and Juneyoung Lee and Sanghoon Park and Mark Dongyeon Shin and Yonghyun Kim and Sungkeun Cho and Joonwon Choi and Chung-Kil Hur and Kwangkeun Yi},
  title     = {Crellvm: Verified Credible Compilation for {LLVM}},
  booktitle = {Proceedings of the 39th ACM SIGPLAN Conference on Programming Language Design and Implementation},
  year      = {2018},
  doi       = {10.1145/3192366.3192377},
  url       = {https://sf.snu.ac.kr/publications/crellvm.pdf}
}

@article{BeckEtAl2024TwoPhaseMemory,
  author  = {Calvin Beck and Irene Yoon and Hanxi Chen and Yannick Zakowski and Steve Zdancewic},
  title   = {A Two-Phase Infinite/Finite Low-Level Memory Model: Reconciling Integer--Pointer Casts, Finite Space, and undef at the {LLVM IR} Level of Abstraction},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {8},
  number  = {ICFP},
  year    = {2024},
  doi     = {10.1145/3674652},
  url     = {https://doi.org/10.1145/3674652}
}

@inproceedings{BeckChenZdancewic2025Vellvm,
  author    = {Calvin Beck and Hanxi Chen and Steve Zdancewic},
  title     = {Vellvm: Formalizing the Informal {LLVM}---Experience Report},
  booktitle = {NASA Formal Methods},
  pages     = {91--99},
  year      = {2025},
  doi       = {10.1007/978-3-031-93706-4_6},
  url       = {https://www.cis.upenn.edu/~stevez/papers/nfm25.pdf}
}

@article{KwonEtAl2025Optimuzz,
  author  = {Jaeseong Kwon and Bongjun Jang and Juneyoung Lee and Kihong Heo},
  title   = {Optimization-Directed Compiler Fuzzing for Continuous Translation Validation},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {9},
  number  = {PLDI},
  articleno = {172},
  numpages  = {24},
  year    = {2025},
  doi     = {10.1145/3729275},
  url     = {https://doi.org/10.1145/3729275}
}

@misc{LLVMLangRef2026,
  author       = {{LLVM Project}},
  title        = {{LLVM} Language Reference Manual},
  year         = {2026},
  howpublished = {Online documentation},
  url          = {https://llvm.org/docs/LangRef.html},
  note         = {Accessed 2026-09-22; rolling main-branch documentation}
}

@misc{LLVMPasses2026,
  author       = {{LLVM Project}},
  title        = {{LLVM}'s Analysis and Transform Passes},
  year         = {2026},
  howpublished = {Online documentation},
  url          = {https://llvm.org/docs/Passes.html},
  note         = {Accessed 2026-09-22}
}

@misc{LLVMVectorizers2026,
  author       = {{LLVM Project}},
  title        = {Auto-Vectorization in {LLVM}},
  year         = {2026},
  howpublished = {Online documentation},
  url          = {https://llvm.org/docs/Vectorizers.html},
  note         = {Accessed 2026-09-22}
}
```

### Primary links not duplicated as BibTeX entries

* LLVM Language Reference: <https://llvm.org/docs/LangRef.html>
* Opaque pointers: <https://llvm.org/docs/OpaquePointers.html>
* GEP guide: <https://llvm.org/docs/GetElementPtr.html>
* Pass catalogue: <https://llvm.org/docs/Passes.html>
* New Pass Manager: <https://llvm.org/docs/NewPassManager.html>
* `opt` command guide: <https://llvm.org/docs/CommandGuide/opt.html>
* Auto-vectorization: <https://llvm.org/docs/Vectorizers.html>
* VPlan: <https://llvm.org/docs/VectorizationPlan.html>
* Source-level debugging: <https://llvm.org/docs/SourceLevelDebugging.html>
