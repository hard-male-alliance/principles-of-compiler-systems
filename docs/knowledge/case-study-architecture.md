# End-to-End Case-Study Architecture for *Inside a Compiler System*

Status: selected design for the LLNCS survey and its small reproducible companion.
Scope: one clipped dot-product program followed from source to LLVM IR, RV64 assembly, ELF, runtime execution, and an MLIR/AscendNPU IR outlook.
This durable design note is English; the paper is Chinese.

## 1. Decision

Use exactly one semantic fixture: a **bounded-prefix, per-term-clipped integer dot product** over two fixed arrays

```text
A = {-4, 1, 7, 3, 9, -2, 6, 5}
B = { 2,-3, 1, 4,-1,  5, 2, 3}.
```

The program reads `n`, clamps it to `[0,8]`, computes the first `n` products, clamps **each product independently** to `[-8,12]`, sums the clipped terms, and prints the result plus a newline:

```text
D(n) = sum(i = 0 .. clamp(n, 0, 8)-1,
           clamp(A[i] * B[i], -8, 12)).
```

This is not saturating accumulation. Once each independently computed term has been clipped, the addition is an ordinary reduction. Every possible sum lies in `[-64,96]`, so signed `i32` overflow is impossible and reassociation/tree reduction preserves the specified result. Clipping the accumulator after each addition would instead create a non-associative recurrence. The report should use this contrast to show that optimization legality follows from semantics, not from a pass name.

The fixture is small enough for complete authored LLVM IR and RISC-V assembly but exposes aggregate initialization, arrays and pointers, indexing, signed arithmetic, assignments, branches, a loop, a five-argument function, SysY I/O, SSA loop values, ABI calls, relocations, and an MLIR map-plus-reduce view. Factorial/Fibonacci lack those memory and reduction boundaries; matrix multiplication would obscure them with repetition.

## 2. Exact semantic fixture

The normative SysY source is equivalent to:

```c
int clipped_dot(int a[], int b[], int n, int lo, int hi) {
    int acc = 0;
    int i = 0;
    while (i < n) {
        int term = a[i] * b[i];
        if (term < lo) {
            term = lo;
        } else if (term > hi) {
            term = hi;
        }
        acc = acc + term;
        i = i + 1;
    }
    return acc;
}

int main() {
    int a[8] = {-4, 1, 7, 3, 9, -2, 6, 5};
    int b[8] = {2, -3, 1, 4, -1, 5, 2, 3};
    int n = getint();
    if (n < 0) {
        n = 0;
    } else if (n > 8) {
        n = 8;
    }
    int result = clipped_dot(a, b, n, -8, 12);
    putint(result);
    putch(10);
    return 0;
}
```

Keep the names `clipped_dot`, `a`, `b`, `n`, `lo`, `hi`, `term`, `acc`, and `i` stable so prose, IR, assembly labels, tests, and symbols align.

The C observation view has the same executable contract but deliberately includes the
experiment's declaration-and-macro header:

```c
// preflight/src/clipped_dot.c
#include "case_config.h"

// excerpt from preflight/include/case_config.h
#define VECTOR_LENGTH 8
#define TERM_MIN (-8)
#define TERM_MAX 12
```

The three definitions live only in `case_config.h`; they are not duplicated in the C
source. That header also contains only the minimal runtime declarations. The C source
uses its macros for bounds and call arguments.
Thus Clang exposes genuine include, macro, token, AST, IR, and code-generation evidence
without falsely making preprocessing part of SysY. The paper must show this small C/SysY
delta and state that stock Clang is an observation instrument for the shared subset, not
a conforming SysY frontend.

### 2.1 Independent oracle

| `i` | `A[i]` | `B[i]` | product | clipped term | prefix sum |
|---:|---:|---:|---:|---:|---:|
| 0 | -4 | 2 | -8 | -8 | -8 |
| 1 | 1 | -3 | -3 | -3 | -11 |
| 2 | 7 | 1 | 7 | 7 | -4 |
| 3 | 3 | 4 | 12 | 12 | 8 |
| 4 | 9 | -1 | -9 | -8 | 0 |
| 5 | -2 | 5 | -10 | -8 | -8 |
| 6 | 6 | 2 | 12 | 12 | 4 |
| 7 | 5 | 3 | 15 | 12 | 16 |

Mandatory known-answer cases, each with a trailing newline on stdout and exit status
zero:

| stdin | stdout | Path exercised |
|---:|---:|---|
| `-1` | `0` | lower clamp; zero-trip loop |
| `0` | `0` | lower boundary; zero-trip loop |
| `1` | `-8` | one signed product |
| `4` | `8` | interior prefix |
| `8` | `16` | complete arrays; upper boundary |
| `10` | `16` | upper clamp; complete arrays |

Values outside `[0,8]` collapse to boundary behavior before indexing. All executed indexes therefore satisfy `0 <= i < clamp(n,0,8) <= 8`.
The repository runtime's `after_main` destructor also writes exactly
`TOTAL: 0H-0M-0S-0us\n` to stderr even when no timer API was called. This is observable
runtime behavior and the verifier checks it rather than discarding it.

### 2.2 Cross-layer invariants

1. SysY `int`, LLVM `i32`, and RV64 word operations carry the same signed values for this fixture.
2. Arrays contain eight contiguous 4-byte integers. Parameters carry 64-bit RV64 addresses, not arrays by value.
3. Length clamping precedes `clipped_dot`; its loop test dominates both indexed loads.
4. Product clipping precedes accumulation. There is no accumulator saturation or early exit.
5. Products are in `[-10,15]`, terms in `[-8,12]`, and sums in `[-64,96]`; no source/IR/target arithmetic overflows.
6. Authored IR avoids unjustified `nsw`, `nuw`, `inbounds`, `nonnull`, or `noundef`. Compiler-generated flags are explained as proof obligations.
7. RV64 calls follow LP64D: pointer/integer arguments in `a0`--`a4`, integer result in `a0`, saved registers restored, and `sp` 16-byte aligned at calls.
8. Pre-link objects leave `getint`, `putint`, and `putch` undefined; the runtime link resolves them with repository-specified signatures.
9. SysY, C, authored IR, and authored assembly have byte-identical observations for the six oracle cases.

The last item is finite observational evidence, not universal equivalence proof. The arithmetic table and structural inspection independently guard against a shared bug.

## 3. Representations and filenames

Use stable names:

```text
preflight/src/clipped_dot.sy   # normative SysY
preflight/src/clipped_dot.c    # C/Clang observation view
preflight/ir/clipped_dot.ll    # complete authored LLVM IR
preflight/asm/clipped_dot.S    # complete authored RV64 assembly
```

The LLVM IR defines `clipped_dot` and `main`, uses opaque `ptr`, explicit fixed arrays, `getelementptr`, signed `i32` loads/multiply/add, clipping CFG, and loop `phi` values for `i` and `acc` (or an intentionally explained memory form before `mem2reg`). It declares all runtime calls. The paper labels it separately from generated `-O0`/`-O2` IR.

The assembly implements both functions rather than copying compiler output. It exposes the five-argument ABI call, fixed array layout, signed word loads, clipping branches, loop backedge, register/stack obligations, and runtime calls. Important comments follow the project's bilingual documentation rule.

Generated evidence is flat under the selected preset's artifact directory—normally
`.temp/preflight-rv64/artifacts/`, `.temp/preflight-portable/artifacts/`, or
`.temp/preflight-ci/artifacts/`—rather than beside authored sources. `capture.json`
records mode, commands, target, and oracle.

## 4. Minimal repository/report architecture

Do not turn the survey into an infrastructure project. The existing top-level contract needs only:

```text
.
├── preflight/
│   ├── CMakeLists.txt
│   ├── CMakePresets.json
│   ├── README.md
│   ├── src/clipped_dot.{sy,c}
│   ├── ir/clipped_dot.ll
│   ├── asm/clipped_dot.S
│   ├── include/case_config.h
│   ├── include/sysy_builtin.h   # declarations only, if Clang needs it for .sy
│   └── scripts/                 # narrow stage/test helpers invoked by CMake
├── report/
│   ├── main.tex
│   ├── latexmkrc
│   ├── references.bib
│   ├── sections/
│   ├── figures/
│   └── listings/                # curated excerpts, not raw dump archives
├── lib/
├── docs/knowledge/
└── .github/workflows/preflight.yml
```

CMake/CTest are stable entry points because the repository already commits to cross-platform CMake and GitHub Actions. Preset binary trees and experiments remain in repository-root `.temp/` or `.cache/`. The report builds from checked-in text/figures; raw tokens, AST JSON, binaries, and full disassemblies are evidence, not manuscript dependencies.

## 5. Artifact flow and commands

```text
clipped_dot.c
  ├─ clang -E ───────────────> preprocessed source
  ├─ Clang frontend ─────────> tokens + typed AST
  ├─ clang -O0/-O2 -emit-llvm> generated IR comparison
  └─ clang -O0/-O2 -S ──────> generated RV64 comparison

src/clipped_dot.sy ── declaration-only Clang probe ──> independent source object
ir/clipped_dot.ll ─── verify/codegen ────────────────> authored-IR object
asm/clipped_dot.S ─── RISC-V assembler ─────────────> authored-assembly object
lib/sylib.c ───────── cross GCC/ar ─────────────────> libsysy-glibc-rv64.a

each case object + rebuilt runtime + cross startup/libc
  ── cross GCC link driver ─────────────────────> RV64 Linux executable
  ── readobj/nm/objdump/map ────────────────────> ELF/link evidence
  ── qemu-riscv64 + six inputs ────────────────> observations
```

Human-transcription edges and executed-tool edges must be visually distinct in the paper.

Public UX:

```sh
cd preflight
cmake --preset ci
cmake --build --preset ci --target verify
ctest --preset ci --output-on-failure

cd ../report
latexmk -r latexmkrc -gg main.tex
```

Representative raw observations remain visible in the README/appendix. The following
spellings assume the repository root and the `rv64` preset's actual output directory;
`capture.py` invokes the same operations with argument arrays:

```sh
clang -std=c17 -Wall -Wextra -Wpedantic -Ipreflight/include \
  -E preflight/src/clipped_dot.c -o .temp/preflight-rv64/artifacts/clipped_dot.i
clang -std=c17 -Wall -Wextra -Wpedantic -Ipreflight/include \
  -fsyntax-only -Xclang -ast-dump=json preflight/src/clipped_dot.c \
  > .temp/preflight-rv64/artifacts/clipped_dot.ast.json
clang -std=c17 -Wall -Wextra -Wpedantic -Ipreflight/include \
  --target=riscv64-unknown-linux-gnu -march=rv64gc -mabi=lp64d \
  -O0 -fno-inline -S -emit-llvm preflight/src/clipped_dot.c \
  -o .temp/preflight-rv64/artifacts/clipped_dot.O0.ll
clang -std=c17 -Wall -Wextra -Wpedantic -Ipreflight/include \
  --target=riscv64-unknown-linux-gnu -march=rv64gc -mabi=lp64d \
  -O2 -fno-inline -S -emit-llvm preflight/src/clipped_dot.c \
  -o .temp/preflight-rv64/artifacts/clipped_dot.O2.ll
clang --target=riscv64-unknown-linux-gnu -march=rv64gc -mabi=lp64d \
  -c preflight/ir/clipped_dot.ll \
  -o .temp/preflight-rv64/artifacts/handwritten-ir.rv64.o
llvm-as preflight/ir/clipped_dot.ll \
  -o .temp/preflight-rv64/artifacts/handwritten.bc
opt -passes=verify -disable-output .temp/preflight-rv64/artifacts/handwritten.bc
riscv64-linux-gnu-gcc -march=rv64gc -mabi=lp64d \
  -c preflight/asm/clipped_dot.S \
  -o .temp/preflight-rv64/artifacts/handwritten-asm.rv64.o
riscv64-linux-gnu-readelf -h -S -s -r \
  .temp/preflight-rv64/artifacts/handwritten-asm.rv64.o
```

Pin or record the intended LLVM major version: pass names and IR syntax are versioned interfaces. A helper reports an actionable version mismatch rather than silently skipping verification.

### 5.1 Runtime archive compatibility is a linker result

The supplied `lib/libsysy_riscv.a` is ELF64 little-endian RISC-V LP64D, but that does **not** make it compatible with Debian/Ubuntu's glibc RV64 environment. Its undefined symbols include `_impure_ptr`, a newlib-family dependency not supplied by glibc. A `riscv64-linux-gnu-gcc -static` link consequently fails despite matching machine type and calling convention.

Preserve `provided-archive.undefined.txt`, produced by
`riscv64-linux-gnu-nm -u`, as direct evidence for the expected link incompatibility. It
demonstrates the difference between ISA, processor ABI, and C-library ABI; do not
fabricate `_impure_ptr` or call it a compiler bug. For successful Linux/QEMU execution,
the actual build recompiles the repository's same runtime source with the selected glibc
cross toolchain:

```sh
riscv64-linux-gnu-gcc -std=gnu17 -fcommon -O2 -march=rv64gc -mabi=lp64d \
  -c lib/sylib.c -o .temp/preflight-rv64/artifacts/sylib.glibc.rv64.o
riscv64-linux-gnu-ar rcs \
  .temp/preflight-rv64/artifacts/libsysy-glibc-rv64.a \
  .temp/preflight-rv64/artifacts/sylib.glibc.rv64.o
riscv64-linux-gnu-gcc -march=rv64gc -mabi=lp64d -static -no-pie \
  .temp/preflight-rv64/artifacts/handwritten-asm.rv64.o \
  .temp/preflight-rv64/artifacts/libsysy-glibc-rv64.a \
  -Wl,-Map=.temp/preflight-rv64/artifacts/asm.link.map \
  -o .temp/preflight-rv64/artifacts/clipped-dot-asm.rv64
```

Use the compiler driver for startup objects/libc; do not invoke `ld` directly or substitute an x86 archive. The report can say it links the provided SysY runtime **implementation/API rebuilt for glibc RV64** and must separately report the prebuilt archive's `_impure_ptr` incompatibility.

## 6. Traceability matrix

| Requirement | `clipped_dot` evidence | Paper | Acceptance |
|---|---|---|---|
| Preprocessor | include, three macros, `.i`, line markers | §3 | macros visibly expand; C/SysY boundary explicit |
| Lexing/parsing | preprocessed spelling and captured AST for initializers, unary minus, subscripts, loop, clipping | §3 | explain that `-4` is unary `-` plus literal; show actual AST nesting |
| Semantic analysis | array/function types, scopes, one isolated invalid mutation | §3 | show a real diagnostic and violated rule |
| Compiler IR | generated `-O0` IR/CFG | §4 | account for mutable `i`, `term`, `acc` and merges |
| LLVM IR programming | authored `.ll` | §4 | verifier accepts; linked result passes oracle |
| Optimization | controlled `-O0`/`-O2`, remarks | §4/§7 | distinguish legality from profitability; cite observed change |
| Code generation | generated RV64 mapped to IR | §5 | explain addressing, signed loads/arithmetic, branches/call |
| RISC-V programming | authored `.S`, ABI/stack diagram | §5 | assembles, passes inspection and execution |
| Assembler | ELF sections/symbols/relocations/disassembly | §6 | follow a runtime `call` through a relocation |
| Linker/runtime | archive symbols, expected incompatibility, rebuilt runtime, map | §6 | explain `_impure_ptr`; resolve intended symbols successfully |
| Equivalence | six cases over C, SysY-as-C, IR, assembly | §7 | exact stdout/stderr/status match independent oracle |
| MLIR/Ascend | map-clamp-reduce model and official VecAdd observation | §8 | label executed/documented/inferred claims |
| Scientific report | LLNCS structure, figures, tables, references | all | clean XeLaTeX/BibTeX PDF |

## 7. LLNCS chapter skeleton

1. **Introduction:** representation-contract thesis, questions, one-program method, target/tool versions.
2. **Program and journey map:** full SysY listing once, mathematical function, oracle table, invariants, central provenance figure.
3. **Characters to typed program:** C preprocessing probe; lexical reading; captured AST; scope/type checks; initialization; array-to-pointer passage; diagnostic; SysY/C boundary.
4. **Typed structure to LLVM IR:** blocks, explicit memory/addressing, GEP, loop `phi`, runtime declarations, authored/generated labels, focused `-O0`/`-O2` narrative.
5. **LLVM IR to RV64:** instruction selection, `i32` on RV64, scaled indexing, clipping, allocation, five-argument ABI, stack frame, authored/generated comparison.
6. **Assembly to process:** pseudo-instructions, ELF sections/symbols/relocations, archive extraction, `_impure_ptr` mismatch, runtime rebuild, symbol resolution, relaxation, QEMU/loader boundary.
7. **Equivalence and controlled variation:** six-case oracle, structural checks, optimizer remarks, test/QEMU limits.
8. **Beyond one low-level IR:** MLIR map/reduce structure, progressive lowering, dialect legality/type conversion, bufferization, official Ascend VecAdd comparison.
9. **Discussion and limitations:** tiny fixed workload, compiler-version instability, behavioral evidence versus proof, no real-hardware performance claim.
10. **Conclusion:** synthesize the representation-contract model; no new result.

Appendices may contain complete authored IR/assembly, commands/versions, and contribution statement. Main text includes only claim-bearing excerpts.

## 8. MLIR/Ascend outlook

The exact case has a faithful structured interpretation:

```text
tensor<8xi32> A, B
  -> elementwise multiply
  -> elementwise clamp to [-8,12]
  -> zero/mask lanes whose index >= clamp(n,0,8)
  -> associative i32 sum reduction
```

An upstream MLIR sketch can express fixed tensors and map/clamp/mask with `arith` inside `linalg.generic`, then use `linalg.reduce` or a reduction iterator. Progressive snapshots should show tensor/linalg form, bufferization to `memref`, loops in `scf`, branches in `cf`, LLVM dialect, and LLVM IR. The bound makes tree/vector reduction legal; whether a pinned compiler chooses it is a cost-model observation.

Legal does not mean profitable: eight elements are an educational fixture, not an NPU benchmark. When CANN/BiSheng is available, reproduce the official AscendNPU IR VecAdd quick start as a control for its documented high-level tile -> lower-level MLIR -> `hivmc`/LLVM -> device-binary path, then compare abstraction boundaries with this map-clamp-reduce case. Do not invent vendor syntax, assert direct SysY ingestion, or claim unexecuted hardware results. Mark facts as executed, documentation-backed, inferred, or proposed.

## 9. Validation gates and implementation order

Validation ladder:

1. Clang parses the C view and the SysY-compatible view with declaration-only builtins if needed.
2. LLVM verifies `.ll`; an RV64 assembler accepts `.S`.
3. Objects are ELF64 little-endian RISC-V with compatible `rv64gc/lp64d`, expected undefined symbols, and conforming stack/register use.
4. `provided-archive.undefined.txt` preserves the prebuilt archive's `_impure_ptr` dependency and explains the expected glibc link incompatibility; `lib/sylib.c` is rebuilt with the case toolchain.
5. C, SysY-as-C, authored IR, and authored assembly pass all six QEMU cases.
6. Relocations/symbols resolve as expected in the final executable.
7. The LLNCS PDF builds cleanly without unresolved citations/references or missing glyphs.

Ubuntu CI is authoritative for glibc RV64/QEMU. Windows may check portable Clang stages and CMake but cannot substitute for target execution. Record versions/commands; do not assert unstable instruction offsets or basic-block names.

Implementation order: freeze the four semantic views and oracle; capture frontend/O0/O2 evidence; verify and test authored IR; assemble/inspect/test authored RV64; capture the prebuilt archive's undefined symbols and the successful rebuilt-runtime link; write around observed artifacts; add MLIR snapshots; independently validate a clean checkout.

## 10. Evidence base

Use primary specifications for mechanisms and peer-reviewed work for architecture:

* Clang toolchain phases: <https://clang.llvm.org/docs/Toolchain.html>.
* LLVM IR semantics: <https://llvm.org/docs/LangRef.html>.
* LLVM opaque pointers and GEP: <https://llvm.org/docs/OpaquePointers.html>, <https://llvm.org/docs/GetElementPtr.html>.
* RISC-V psABI: <https://riscv-non-isa.github.io/riscv-elf-psabi-doc/>; cite a pinned revision.
* GNU assembler RISC-V relocations: <https://sourceware.org/binutils/docs/as/RISC_002dV_002dModifiers.html>.
* System V ELF ABI: <https://refspecs.linuxfoundation.org/elf/gabi4+/contents.html>.
* C. Lattner and V. Adve, “LLVM: A Compilation Framework for Lifelong Program Analysis & Transformation,” CGO 2004, DOI `10.1109/CGO.2004.1281665`.
* C. Lattner et al., “MLIR: Scaling Compiler Infrastructure for Domain Specific Computation,” CGO 2021: <https://arxiv.org/abs/2002.11054>.
* MLIR dialect conversion/LLVM target: <https://mlir.llvm.org/docs/DialectConversion/>, <https://mlir.llvm.org/docs/TargetLLVMIR/>.
* AscendNPU IR architecture: <https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/compiler/AscendNPUIR/docs/source/en/introduction/architecture.md>.
* Repository-local SysY 2022 language/grammar/runtime documents, `sylib.c`, and archives are normative assignment evidence.

Tool output proves what one pinned build did; specifications establish permitted behavior. The survey needs both and should preserve negative evidence such as `_impure_ptr` when it explains a real boundary.
