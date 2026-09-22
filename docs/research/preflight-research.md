# Preflight Research Notes: Understanding the Compiler

**Scope.** External fact-checking for the course task *Preliminary Work -- Understand Your Compiler*, with emphasis on Clang/LLVM, LLVM IR opaque pointers, RV64 assembly/ABI/linking, MLIR progressive lowering, and AscendNPU IR/BiSheng.  These notes are an evidence base for the LLNCS paper, not prose to copy verbatim.

**Cut-off date.** 2026-09-22 (Asia/Singapore).  The latest LLVM release listed by the project on this date is 23.1.1 (released 2026-09-08); LLVM 23.1.2 was scheduled for 2026-09-22 but was not yet listed as released when checked [llvm-home-2026].

**Citation file.** Candidate BibTeX entries are in `docs/research/preflight-references.bib`.  The keys used below refer to that file.

## 1. Research questions, method, and evidence labels

The investigation answers five questions:

1. What does each stage in a modern Clang/LLVM toolchain do, and which commands expose it without confusing a logical phase with a separate process?
2. Which LLVM IR syntax is canonical in current releases, especially after the opaque-pointer migration?
3. Which RV64 ABI, relocation, code-model, and execution-environment constraints must a hand-written SysY-compatible assembly program satisfy?
4. What does MLIR's “progressive lowering” guarantee, and what does it *not* guarantee?
5. What can currently be reproduced for AscendNPU IR VecAdd, and which claims remain documentation-backed rather than device-executed?

Evidence labels used throughout:

| Label | Meaning | Permitted claim strength |
|---|---|---|
| **[O] Observed** | A command, file, HTTP endpoint, or repository state was directly inspected in this workspace on 2026-09-22. | “We observed ... in the stated environment.” |
| **[D] Documented** | An official specification, versioned manual, upstream source, or peer-reviewed paper states the claim. | “The specification/documentation defines/states ...” |
| **[I] Inferred** | A conclusion follows from documented mechanisms but was not directly executed here. | “This suggests/is expected to ...”, with assumptions. |
| **[U] Unverified** | A plausible command or outcome could not be executed in the available environment. | Must not be reported as an experimental result. |

The source hierarchy was: versioned official documentation and specifications; upstream source/tests; peer-reviewed papers; current project documentation; and only then secondary material.  Search snippets were used only to locate primary sources, not as final evidence.

## 2. Environment and version boundary

### 2.1 Directly observed local tools

The local Windows environment contained:

| Tool | Observation |
|---|---|
| `clang`, `clang++` | **[O]** LLVM/Clang 22.1.8, commit `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`, target `x86_64-pc-windows-msvc`. |
| `llvm-objdump` | **[O]** LLVM 22.1.8. |
| `opt`, `llc`, `llvm-as`, `llvm-dis` | **[O]** Not found on `PATH`.  Their commands below are documentation-backed, not locally executed. |
| `riscv64-linux-gnu-gcc`, `riscv64-unknown-elf-gcc`, `qemu-riscv64` | **[O]** Not found on `PATH`. |
| `mlir-opt`, `mlir-translate` | **[O]** Not found on `PATH`. |
| `bishengir-compile`, `bishengir-opt`, `bisheng`, `npu-smi` | **[O]** Not found on `PATH`; no CANN/NPU execution was possible. |

Clang 22.1.8 locally completed preprocessing, raw/preprocessed token dumping, AST dumping, textual LLVM IR generation, assembly generation, object generation, and linking on a small C probe.  All experimental artifacts were kept under the project `.temp` directory.  Generated LLVM IR used `ptr`, as expected for opaque pointers.  This is evidence for LLVM 22.1.8 on this host, not proof for every LLVM 23 build.

### 2.2 Current upstream boundary

- **[D]** The LLVM homepage listed LLVM 23.1.1 as the latest release on the cut-off date [llvm-home-2026].
- **[D]** Version-pinned LLVM/Clang 23.1.0 manuals document the command contracts used below [clang-toolchain-23, clang-command-23, llvm-opt-23].
- **[I]** Patch-level compatibility from 23.1.0 documentation to 23.1.1 is expected but was not locally executed.  The paper should record the exact executable version and help output rather than merely say “LLVM 23.”
- **[D]** MLIR's current website may describe a post-release development snapshot.  Specific pass names and options are not a cross-version stable API; probe the pinned binary with `--help` and record the output [mlir-faq, mlir-release-notes].

## 3. Clang/LLVM compilation pipeline

### 3.1 Logical dataflow and contracts

The official Clang toolchain manual describes the following logical pipeline [clang-toolchain-23]:

```text
C/C++ source
  -> preprocessing (tokens after includes, macros, conditionals)
  -> parsing + semantic analysis (typed AST and diagnostics)
  -> LLVM IR generation
  -> target-independent and target-aware optimization
  -> instruction selection / target code generation
  -> target assembly
  -> relocatable object (assembler)
  -> executable or shared object (linker)
  -> mapped process image (OS loader; outside the linker)
```

Two distinctions matter for the paper:

1. **Logical phase is not necessarily a separate process.**  **[D]** Clang may fuse phases, and it normally uses an integrated assembler where supported.  Intermediate `.i`, `.ll`, and `.s` files are deliberate observation points, not proof that a standalone executable ran for every phase [clang-toolchain-23].
2. **Linking is not loading or execution.**  The linker combines object files and libraries into an image, resolving symbols and applying relocations.  The OS loader maps the executable/shared libraries at run time.  The course text's wording that the linker “executes” machine code should be corrected.

### 3.2 Reproducible command ladder

Use explicit output names and save the exact version, target triple, and flags:

```sh
clang --version
clang -dumpmachine

# 1. Preprocessed source.
clang -E main.c -o main.i

# 2. Preprocessed tokens.  Output is normally on stderr.
clang -Xclang -dump-tokens -fsyntax-only main.c 2> tokens.txt

# 3. Typed AST.  This exact pattern is documented by Clang.
clang -Xclang -ast-dump -fsyntax-only main.c > ast.txt

# 4a. Textual LLVM IR; 4b. LLVM bitcode.
clang -O0 -S -emit-llvm main.c -o main.ll
clang -O0 -c -emit-llvm main.c -o main.bc

# 5. Target assembly.
clang -O0 -S main.c -o main.s

# 6. Relocatable object.
clang -O0 -c main.c -o main.o

# 7. Link.  Use clang++ for C++ so its runtime libraries are selected.
clang main.o -o main

# Reveal the jobs without running them, or print and run them.
clang -### main.c -o main
clang -v main.c -o main
```

`-E`, `-S`, and `-c` are stable driver stage-selection flags [clang-command-23].  `-emit-llvm` plus `-S` emits textual IR; without `-S`, `-c -emit-llvm` emits bitcode [clang-toolchain-23].

#### Frontend diagnostic interface caveat

`-Xclang` forwards an option to Clang's `-cc1` frontend.  **[D]** Clang explicitly classifies the frontend command line as an implementation detail subject to change [clang-toolchain-23].  Therefore:

- `-ast-dump` is reasonable for this exercise because the exact invocation is in official Clang documentation [clang-ast-23].
- `-dump-tokens` is useful but should be labelled a version-pinned diagnostic interface, not a stable user API.
- `-dump-raw-tokens` shows tokens before preprocessing, whereas `-dump-tokens` shows the post-preprocessing token stream.  This difference is pedagogically more useful than treating both as “lexical analysis output.”

### 3.3 Optimization-pass observation with the New Pass Manager

For current LLVM, use `opt` and the textual New Pass Manager pipeline [llvm-opt-23, llvm-new-pm-23]:

```sh
# Discover names actually compiled into this opt binary.
opt --version
opt --print-passes > opt-passes.txt

# Run an explicit pipeline and keep textual IR.
opt -S -passes='mem2reg,instcombine' main.ll -o optimized.ll

# Observe a standard pipeline; dumps are emitted to stderr.
opt -passes='default<O2>' -disable-output \
    -print-before-all -print-after-all main.ll 2> passes.log

# Less noisy: record only changed IR where supported by the pinned version.
opt -passes='default<O2>' -disable-output -print-changed main.ll 2> changes.log
```

The nesting of module, CGSCC, function, and loop passes is part of the pipeline syntax.  `opt --print-passes` is authoritative for the installed build.  The web “Passes” catalogue itself warns that it may be incomplete.

**Experimental confounder.**  Clang-generated `-O0` functions commonly carry `optnone`, which causes many later function passes to be skipped.  For a teaching experiment, either generate an optimized baseline or use the internal, version-pinned option:

```sh
clang -O0 -Xclang -disable-O0-optnone -S -emit-llvm main.c -o main.ll
```

Record this choice, because otherwise “the pass did nothing” may be caused by `optnone`, not by the program structure.

### 3.4 Assembler, object, and linker inspection

Useful observations should distinguish symbolic assembly, relocatable object code, and the linked image:

```sh
clang -c main.s -o main.o
llvm-objdump -dr main.o > main.o.disasm.txt
llvm-nm main.o > main.o.symbols.txt

clang main.o runtime.o -o main
llvm-objdump -dr main > main.disasm.txt
llvm-nm main > main.symbols.txt
```

The object normally contains unresolved external symbols and relocation records; the linked image has a different symbol/relocation state.  Do not infer that every relocation disappears: PIE, shared libraries, and dynamic linking deliberately retain dynamic relocations.

### 3.5 Compatibility audit of commands in the course material

| Course-style command/claim | 2026 judgment | Replacement or qualification |
|---|---|---|
| `clang -E -Xclang -dump-tokens main.c` | **[O]** Still worked in local Clang 22.1.8, but `-E` is redundant/misleading and the option is internal. | `clang -Xclang -dump-tokens -fsyntax-only main.c 2>tokens.txt`. |
| `clang -E -Xclang -ast-dump main.c` | **[O]** Worked locally, but official semantics are clearer without `-E`. | `clang -Xclang -ast-dump -fsyntax-only main.c`. |
| `clang -S -emit-llvm main.c` | Current. | Add `-O0` and `-o main.ll` for reproducibility. |
| `opt -<module name> <test.bc> /dev/null` | Obsolete and malformed.  Legacy `-passname` is superseded; `/dev/null` becomes a second positional input, not an output path. | `opt -passes='passname' -disable-output test.ll`, or add `-S ... -o out.ll`. |
| “`opt` requires `.bc`” | False. | **[D]** `opt` accepts both textual `.ll` and bitcode `.bc` [llvm-opt-23]. |
| `llc -print-before-all -print-after-all a.ll ...` as the primary middle-end experiment | Misleading rather than necessarily removed.  `llc` exposes target-backend/Machine IR work. | Use `opt` for LLVM middle-end passes; use `llc input.ll -filetype=asm -o out.s` or `-filetype=obj` for backend output [llvm-llc-23]. |
| `llvm-as` / `llvm-dis` conversion | Current in a full LLVM tools installation. | Do not imply conversion is required before `opt`. |
| “Clang 15+ supports opaque pointers” | Too weak and temporally misleading. | LLVM 15 made them default; LLVM 17+ removed the typed-pointer mode. |
| linker “executes” the generated code | Incorrect. | Linker builds an image; loader/runtime executes it. |

## 4. LLVM IR opaque pointers

### 4.1 Versioned transition

| LLVM | Supported model | Evidence-backed interpretation |
|---:|---|---|
| 14 | Typed pointers default; opaque pointers opt-in and not production-ready across the pipeline. | Migration release [llvm14-opaque]. |
| 15 | Opaque pointers default; temporary typed-pointer fallback still available. | Transition release [llvm15-opaque]. |
| 16 | Opaque default; typed pointers best-effort and untested. | Final compatibility period [llvm16-opaque]. |
| 17 | Only opaque pointers supported; typed-mode flags and incompatible APIs removed. | Release-note contract [llvm17-release]. |
| 18--23/current | Opaque-only semantic model.  Some legacy textual spellings may still be parsed and immediately canonicalized. | Current LangRef, command references, and parser source [llvm-langref-2026, llvm22-llparser]. |

Strongest defensible wording for the paper:

> Since LLVM 17, opaque pointers are the only supported pointer model.  Current parsers may accept some legacy typed textual spellings as an input-upgrade convenience, but immediately erase the pointee component; this is not a supported typed-pointer mode and must not be treated as a stable textual compatibility contract.

### 4.2 Canonical current syntax

```llvm
define i32 @load_i32(ptr %p) {
entry:
  %v = load i32, ptr %p, align 4
  ret i32 %v
}

define ptr @field(ptr %base) {
entry:
  %q = getelementptr { i32, i64 }, ptr %base, i64 0, i32 1
  ret ptr %q
}
```

- `ptr` denotes a pointer in address space 0; `ptr addrspace(N)` retains a non-default address space.
- Loads/stores carry the accessed value type.
- `getelementptr` carries its source element type.
- Calls carry a function signature; ABI-relevant attributes such as `byval(T)` or `sret(T)` retain explicit types where required.

Opaque pointers remove the pointee type from the *pointer type*.  They do not erase address spaces, data layout, or the types of memory operations.

### 4.3 Direct compatibility probe and engineering consequence

**[O]** Local Clang 22.1.8 rejected `-Xclang -no-opaque-pointers`.  It nevertheless accepted a legacy textual module using `i32*`, and re-emitted it as `ptr`:

```llvm
; legacy input
define i32 @load_old(i32* %p) {
  %v = load i32, i32* %p
  ret i32 %v
}

; canonicalized output
define i32 @load_old(ptr %p) {
  %v = load i32, ptr %p, align 4
  ret i32 %v
}
```

This matches the LLVM 22 parser source: it recognizes legacy `Type *` syntax but constructs an opaque `PointerType`, discarding the pointee [llvm22-llparser].  New teaching material should generate `ptr` directly.

For compiler code, never infer an access type from pointer equality.  The same `%p : ptr` can legally appear in `store i32` and `load i64`; analyses must compare the operation types.  C clients use the explicit-type `*2` builders such as `LLVMBuildLoad2`, `LLVMBuildCall2`, and `LLVMBuildGEP2`.  C++ clients query operation-specific types (`LoadInst::getType`, `GetElementPtrInst::getSourceElementType`, `CallBase::getFunctionType`, and so on) [llvm16-opaque].

### 4.4 Compatibility policy caveat

LLVM's developer policy distinguishes bitcode auto-upgrade support from textual IR.  Textual `.ll` is not a backwards-compatible interchange contract, whereas older bitcode is deliberately auto-upgraded across a substantial version range [llvm-developer-policy].  Therefore, archive source plus the exact compiler version and regenerate canonical `.ll`; do not build a long-lived interface around legacy typed-pointer text.

## 5. RISC-V RV64 ABI, assembly, and linking

### 5.1 First choose the execution environment

The most destructive source of confusion is mixing Linux user-space and bare-metal tools:

| Goal | Compiler family | Link/runtime | Emulator | Correct interpretation |
|---|---|---|---|---|
| RV64 Linux process | `riscv64-linux-gnu-gcc` or Clang with a Linux target/sysroot | glibc/musl and Linux crt objects; dynamic or static Linux ELF | `qemu-riscv64` (user mode), optionally `-L <sysroot>` for dynamic libraries | Same OS ABI, different ISA. |
| RV64 bare-metal program | `riscv64-unknown-elf-gcc` or suitable `*-none-elf` toolchain | newlib/picolibc/custom crt, linker script, trap/exit convention | `qemu-system-riscv64`, Spike, or a board/simulator configured for that runtime | Whole-machine or execution-environment model; no Linux syscall ABI by default. |

**[D]** QEMU user mode launches programs built for another CPU but the same operating system, translating Linux system calls; `-L` sets the guest ELF interpreter/library prefix [qemu-user-2026].  Consequently, `riscv64-unknown-elf-gcc ...; qemu-riscv64 ./a.out` is not a generally valid recipe.  A statically linked *Linux* executable is still a Linux process, while a statically linked bare-metal ELF is still bare metal.  “Static” does not bridge the ABI boundary.

Recommended Linux flow:

```sh
riscv64-linux-gnu-gcc -march=rv64gc -mabi=lp64d -O0 -c main.S -o main.o
riscv64-linux-gnu-gcc -static main.o -L./lib -lsysy_riscv -o main
qemu-riscv64 ./main

# Dynamic alternative: sysroot/interpreter prefix must match the toolchain.
riscv64-linux-gnu-gcc main.o -L./lib -lsysy_riscv -o main
qemu-riscv64 -L /usr/riscv64-linux-gnu ./main
```

Before choosing commands, inspect the supplied SysY library:

```sh
file lib/libsysy_riscv.a
riscv64-linux-gnu-readelf -hW main.o
riscv64-linux-gnu-readelf -A main.o
riscv64-linux-gnu-readelf -rW main.o
```

The archive's object format, ABI, floating-point convention, and libc/runtime assumptions must match the application.

### 5.2 psABI invariants that hand-written assembly must satisfy

The current RISC-V psABI snapshot defines [riscv-psabi-2026]:

| Resource | RV64 integer calling-convention role |
|---|---|
| `a0`--`a7` | Eight argument registers; `a0`--`a1` also return values. |
| `t0`--`t6` | Caller-saved temporaries. |
| `s0`--`s11` | Callee-saved; `s0` may be frame pointer. |
| `ra` | Return address, caller-saved. |
| `sp` | Stack pointer; grows downward. |
| `gp`, `tp` | Fixed/unallocatable by ordinary procedures. |

For the standard RV64 ABI:

- `sp` is aligned to a **128-bit = 16-byte** boundary on procedure entry and remains aligned during standard-ABI execution.
- A callee must restore every callee-saved register it modifies.
- Scalars no wider than XLEN use one argument register when available; larger values/aggregates follow psABI classification rules, not a universal “push right-to-left” rule.
- Integer return values normally use `a0` (and `a1` when needed).
- The floating-point ABI is selected by `-mabi` (`lp64`, `lp64f`, `lp64d`) and must agree across all objects.  ISA availability (`-march`) and calling convention (`-mabi`) are related but distinct.

Pseudo-instructions such as `mv`, `ret`, `call`, `la`, and `lla` are assembler conveniences.  Their expansion may create relocations and may later be shortened by linker relaxation.  The paper should compare both the `.s` input and `objdump -dr` output rather than treating pseudo-instruction spelling as final machine code.

### 5.3 Code models are not synonyms for PIC

| Model | Address formation | Reach | Shared-library/PIE PIC? |
|---|---|---|---|
| `medlow` | Absolute `lui` plus low 12-bit operation | RV32 whole space; on RV64 low and high regions around address zero | No. |
| `medany` | PC-relative `auipc` plus low 12-bit operation | One roughly +/-2 GiB window relative to the instruction | **No**; PC-relative instructions alone do not satisfy ELF interposition semantics. |
| Medium PIC | Local symbols may be PC-relative; non-local/preemptible symbols use GOT/PLT | Medium-model constraints | Yes, subject to the selected ABI/toolchain. |

The RV64 `medlow` ranges are precisely `0x0..0x000000007ffff7ff` and `0xffffffff7ffff800..0xffffffffffffffff`, not a hand-waved “low 2 GB” [riscv-psabi-2026].  `medany` can place one program window anywhere, but the psABI explicitly warns that it is not suitable by itself for ELF shared libraries because of symbol-interposition rules.

Thus `-mcmodel=medany` may be appropriate for a teaching runtime placed near `0x90000000`, but it is not a generic “full 64-bit addressing” mode and not a substitute for `-fPIC`/`-fPIE`.

### 5.4 Relocations and linker relaxation

Representative relocation pairs [riscv-psabi-2026, riscv-asm-manual]:

| Intent | Conservative instruction pattern | Relocations |
|---|---|---|
| Absolute symbol address | `lui` + `addi`/load/store | `R_RISCV_HI20` + `R_RISCV_LO12_I/S` |
| PC-relative symbol address | `auipc` + `addi`/load/store | `R_RISCV_PCREL_HI20` + `R_RISCV_PCREL_LO12_I/S` |
| GOT address | `auipc` + load | `R_RISCV_GOT_HI20` + PC-relative low relocation |
| Function call | `auipc` + `jalr` | Prefer `R_RISCV_CALL_PLT`; `R_RISCV_CALL` is deprecated. |

For a PC-relative pair, the low relocation refers to the local label at the corresponding high relocation, not simply to the final target symbol.  This lets the linker pair the two halves correctly.

Linker relaxation is a cooperation protocol, not recompilation:

1. The compiler/assembler emits a conservative sequence and normal relocations.
2. It marks a candidate with `R_RISCV_RELAX` at the same location.
3. Once layout is known, the linker may replace or delete instructions and updates affected references.

For example, `auipc ra` + `jalr ra` can become one `jal` when the target is in range.  Use the same object twice to isolate the linker's effect:

```sh
riscv64-linux-gnu-gcc main.o -Wl,--no-relax -o no-relax
riscv64-linux-gnu-gcc main.o                  -o relaxed
riscv64-linux-gnu-objdump -dr no-relax > no-relax.txt
riscv64-linux-gnu-objdump -dr relaxed  > relaxed.txt
riscv64-linux-gnu-size no-relax relaxed
```

`--no-relax` is useful as an experimental control, but disabling relaxation is not a correctness requirement for ordinary code.  Conversely, hand-written sequences that violate relocation-pair rules can fail only at link time.

### 5.5 Review of the existing RISC-V recipe

The course recipe combining `riscv64-unknown-elf-gcc`, `-static`, `-Ttext=0x90000000`, and `qemu-riscv64` embeds several unstated assumptions:

- **[D]** `unknown-elf` normally denotes a bare-metal ABI, whereas `qemu-riscv64` is Linux user-mode emulation.
- A custom `-Ttext` address is a linker-layout choice, not a general Linux requirement.  Linux user mode should normally use its standard linker script/PIE policy.
- `-static` only changes library/dynamic-loader dependence; it does not turn bare-metal startup/syscalls into Linux ones.
- The recipe can work only if the particular toolchain/runtime/library combination intentionally supplies a compatible execution convention.  That compatibility must be demonstrated with ELF headers, startup objects, and an actual run, not inferred from the filename.

The paper should either (a) use a consistent Linux GNU tuple plus QEMU user mode, or (b) describe the bare-metal machine, linker script, startup, and termination mechanism explicitly.

## 6. MLIR progressive lowering

### 6.1 Mechanism, not slogan

MLIR permits operations from several dialects to coexist in one module/function.  Progressive lowering transforms only the abstractions for which a stage has a meaningful target, retaining others for later stages [mlir-toy-ch5, mlir-cgo-2021].  A representative, not universal, path is:

```text
domain/tensor dialect
 -> Linalg/Affine + Arith + Tensor
 -> bufferization
 -> MemRef + SCF/Affine
 -> CF + LLVM dialect
 -> LLVM IR
 -> object code
```

The important property is the *mixed-dialect transition state*, not a requirement that each stage contain exactly one dialect.

MLIR's Dialect Conversion framework has three main ingredients [mlir-dialect-conversion]:

1. a `ConversionTarget` defining which operations/dialects are legal after the stage;
2. rewrite patterns that legalize illegal operations;
3. an optional `TypeConverter` plus materializations for value/type boundaries.

Conversion modes:

| Mode | Structural guarantee | Suitable use |
|---|---|---|
| Partial conversion | Explicitly illegal operations must be legalized; unknown/not-illegal operations may remain. | Incremental lowering and mixed-dialect stages. |
| Full conversion | Every operation must be legal for the target. | Stage boundary/gate before translation. |
| Analysis conversion | Reports legalizability without applying rewrites. | Diagnostics and planning. |

**Critical epistemic limit.**  Successful conversion and verifier acceptance prove structural/type legality, not semantic equivalence.  Semantics depend on each rewrite pattern.  Differential execution, reference outputs, and targeted tests are still needed.

### 6.2 Inspectable MLIR experiment

```sh
mlir-opt --version
mlir-opt --help > mlir-opt-help.txt
mlir-translate --version
mlir-translate --help > mlir-translate-help.txt

# Parse, verify, and print a round trip.
mlir-opt input.mlir -o 00-roundtrip.mlir

# Explicitly anchored textual pipeline.
mlir-opt input.mlir \
  --pass-pipeline='builtin.module(func.func(cse,canonicalize))' \
  -o 10-opt.mlir

# Pass-by-pass trace.  IR printing goes to stderr.
mlir-opt input.mlir \
  --pass-pipeline='builtin.module(func.func(cse,canonicalize))' \
  --mlir-print-ir-after-all \
  --mlir-print-ir-after-change \
  --mlir-disable-threading \
  --mlir-print-ir-module-scope \
  -o final.mlir 2> pipeline.trace

# Only after the module has been lowered to translatable dialects.
mlir-translate --mlir-to-llvmir lowered-llvm-dialect.mlir -o output.ll
```

The operation anchor in `--pass-pipeline` must match the level on which a pass operates [mlir-pass-management].  `--mlir-print-ir-after-change` must accompany an after/after-all selector.  Module-scope printing should disable threading, as the manual warns.  `--mlir-print-ir-tree-dir=<dir>` is preferable when hundreds of snapshots would otherwise be concatenated.

`mlir-opt` is an experimentation/testing driver, not a complete production compiler driver [mlir-opt-tutorial].  `mlir-translate` does not magically lower arbitrary high-level dialects; it translates only already-supported lower-level operations/interfaces.

### 6.3 Why progressive lowering matters, with calibrated claims

- **[D] Design capability:** high-level structure can remain available to a specialized dialect long enough to use appropriate transformations [mlir-cgo-2021].
- **[I] Engineering benefit:** explicit legality boundaries and reusable dialects can reduce integration cost relative to ad hoc IRs, but the magnitude is project-dependent.
- **Not established:** “more dialects always improve performance” or “lowering is automatically semantics-preserving.”  Extra levels also increase interface surface, materialization casts, pass-order sensitivity, and version coupling.
- **Research connection:** progressive raising shows the complementary problem: after lowering discards structure, reconstructing higher-level operations can be difficult [mlir-progressive-raising-2021].  This supports delaying *irreversible* lowering when a later optimization still needs that structure, not a universal rule to lower everything as late as possible.
- **Frontier:** the Transform dialect makes schedules explicit IR that can be composed, inspected, and tuned [mlir-transform-cgo-2025].  It is a useful outlook topic, not necessary for the basic assignment.

## 7. AscendNPU IR, VecAdd, and BiSheng

### 7.1 What was actually verified

- **[O]** `git ls-remote` against the official GitCode repository succeeded.  On 2026-09-22, GitCode `HEAD/master` was `ad5bc462ceb72443815eb3f025df01fba3fc60d2` and `stable` was `85271f876dd55bd6d6b3dfe66daf13d6392c70ec`.
- **[O]** The official AscendNPU IR documentation and CANN 9.1.0 BiSheng pages returned HTTP 200.
- **[O]** No `bishengir-compile`, `bisheng`, CANN runtime, or NPU device was available locally.
- **[U]** Therefore no claim that `kernel.o` was generated or that VecAdd ran on an NPU is admissible for this environment.  The official expected output is not an experimental result.

GitHub is a mirror and did not necessarily point to the same commit at the observation time.  A reproducible report should cite a GitCode commit rather than mutable `master`.

### 7.2 Official VecAdd dataflow

The current quick start defines a 16-element `i16` vector addition [ascend-vecadd-2026]:

```text
GM input 0 --hivm.hir.load--> UB buffer 0 --\
                                              hivm.hir.vadd --> UB result
GM input 1 --hivm.hir.load--> UB buffer 1 --/                    |
                                                                  +--hivm.hir.store--> GM output
```

The function takes three `memref<16xi16, #hivm.address_space<gm>>` arguments, allocates UB memrefs, and carries HACC attributes identifying a device entry.  The documented compile command is:

```sh
bishengir-compile add.mlir -enable-hivm-compile -o kernel.o
```

The documented host path then loads `kernel.o`, calls `rtDevBinaryRegister` and `rtFunctionRegister`, allocates/copies device buffers, launches with `rtKernelLaunch`, synchronizes, copies back, and compares against `1..16` [ascend-vecadd-2026].  These are **[D] documented steps**, not **[O] local execution**.

### 7.3 AscendNPU IR abstraction levels and source-backed pipeline

The architecture documentation describes [ascend-architecture-2026]:

- **HFusion:** a high-level, Linalg-related layer for hardware-independent named operations, fusion, and preprocessing.
- **HIVM (Hybrid ISA Virtual Machine):** an NPU-aware layer exposing computation, data movement, synchronization, and address-space/memory-hierarchy decisions such as GM, UB, L1, and L0.
- **HACC:** heterogeneous hardware and function-role attributes/contracts.
- Supporting Annotation, Scope, and other dialects.

A cautious pipeline summary is:

```text
ecosystem/front-end IR
 -> HFusion preprocessing/fusion (when enabled)
 -> conversion to HIVM
 -> HIVM scheduling, synchronization, and memory planning
 -> lower-level MLIR
 -> hivmc / LLVM-oriented backend
 -> NPU operator binary
```

**[O, upstream source]** `PassPipeline.cpp` conditionally builds HFusion pipelines, then `buildConvertToHIVMPipeline` and `buildOptimizeHIVMPipeline`.  The conversion source orders HFusion-to-HIVM, optional Triton argument conversion, tensor-to-HIVM, and general conversion passes.  `bishengir-compile` then coordinates `hivmc` and can preserve an optimized HIVM intermediate.  Thus the one-line driver hides multiple pass and backend stages; “input/output are MLIR” applies to an internal lowering layer, whereas `-o kernel.o` requests the final binary path.

For an HIVM input that should skip HFusion, the framework-interface documentation gives a form such as:

```sh
bishengir-compile \
  -enable-hfusion-compile=false \
  -enable-hivm-compile=true \
  -target=Ascend910B1 \
  hivm.mlir -o hivm_kernel.o
```

### 7.4 Observing the Ascend lowering process

The official FAQ exposes version-specific IR-print options [ascend-faq-2026]:

```sh
bishengir-compile input.mlir \
  --bishengir-print-ir-before=hivm-inject-block-sync \
  --bishengir-print-ir-after=hivm-inject-block-sync \
  -enable-hivm-compile -o kernel.o 2> lowering.log
```

Pass names are not stable.  Upstream Triton-Ascend changed a debug dump trigger from `hivm-inject-sync` to `hivm-graph-sync-solver` in 2026.  The experiment must use:

```sh
bishengir-compile --help > bishengir-help.txt
```

and select a pass name from the pinned build.  Generic MLIR `--mlir-print-ir-before-all/after-all` may also be compiled in, but the dedicated `--bishengir-print-ir-before/after=<pass>` options are the documented Ascend interface.  A useful report should show only semantically meaningful boundaries rather than dumping hundreds of near-identical states.

### 7.5 Build/runtime prerequisites and version drift

The current AscendNPU IR build guide documents [ascend-install-2026]:

- CMake >= 3.28 and Ninja >= 1.12; Clang/LLD >= 10 recommended;
- recursive submodules, including pinned LLVM/Torch-MLIR dependencies;
- `./build-tools/build.sh -o ./build --build-type Release` as the recommended build path;
- CANN Toolkit plus the hardware-specific ops package for end-to-end execution;
- `-DLLVM_MAJOR_VERSION_21_COMPATIBLE=ON` for LLVM >= 21 in the documented manual build;
- template-library/end-to-end options requiring the corresponding BiSheng/CANN installation.

BiSheng is the CANN heterogeneous compiler entry point, supporting host and AI Core device compilation [bisheng-cann910-2026].  CANN 9.1 documentation uses `.asc` inputs and the current architecture option:

```sh
bisheng source.asc -o output --npu-arch=dav-<npu-architecture>
```

Older 8.x examples used options such as `--cce-soc-version`; do not mix them into a 9.1 command line without versioning the claim.

One concrete documentation-drift example: the VecAdd README names a host target `hivm-vec-add`, while the current CMake/source test uses `bishengir-npu-hivm-vec-add`.  Prefer the pinned source/CMake target or avoid hard-coding the name.

## 8. Recommended experiment claims and falsification tests

| Claim | Evidence to collect | What would falsify/revise it? |
|---|---|---|
| Macro expansion changes the token stream before parsing. | Raw tokens, post-preprocessing tokens, `.i`, and AST from the same source. | Identical tokens despite an active macro/include would indicate the wrong dump phase or inactive directive. |
| An LLVM optimization pass changed IR while preserving program behavior. | Pre/post IR, explicit pass pipeline, verifier result, and differential output over boundary tests. | Different observable output, UB-dependent test, or pass skipped due to `optnone`. |
| Assembly and object code differ because pseudo-instructions and relocations are resolved later. | `.s`, `readelf -rW`, and `objdump -dr` before/after link. | No relocation/pseudo-instruction in the selected example; choose a symbol reference/call that exercises them. |
| Linker relaxation shortened RISC-V code. | Same `.o` linked with and without relaxation; disassembly and size comparison. | No `R_RISCV_RELAX`, target out of range, or toolchain disables relaxation. |
| LLVM opaque pointers remove pointee type, not memory-operation types. | Canonical `.ll` showing `ptr` plus typed load/store/GEP. | A current canonical emitter produces typed pointer types; this would materially contradict LLVM 17+ policy. |
| MLIR lowered progressively through mixed dialects. | Pass-boundary dumps, dialect inventory at each boundary, full-conversion gate. | One monolithic rewrite or unrecorded pipeline; then “progressive” is merely a narrative label. |
| Ascend VecAdd ran correctly. | Pinned repository/CANN versions, actual command logs, NPU identification, exit status, and captured result comparison. | Only documentation expected output or absence of CANN/NPU; then the claim must remain unverified. |

## 9. Reproducibility checklist for the LLNCS report

Record at minimum:

1. OS, architecture, compiler/tool versions, target triple, and exact commands.
2. Source and runtime-library hashes; for Ascend, Git commit, CANN version, device model, driver/firmware, and `bishengir-compile --help` snapshot.
3. Inputs and outputs for each phase, including stderr for token/pass dumps.
4. Optimization level and whether `optnone`, debug information, LTO, PIE/PIC, static linking, and linker relaxation are enabled.
5. For RISC-V: compiler tuple, `-march`, `-mabi`, code model, sysroot, linker, and QEMU user/system mode.
6. Behavioral oracle, test inputs (including boundaries), exit code, and repeated results where timing is measured.
7. Separate statements for **observed**, **inferred**, and **unverified** results.  Never present an official quick-start's expected output as a local measurement.
8. Keep command output concise in the paper; archive full logs as reproducibility artifacts.

## 10. Bottom-line judgments

1. **Clang is a driver over a logical pipeline, not evidence that each phase is a separate executable.**  Use named intermediate outputs and `-###` to expose the execution plan.
2. **The course's legacy `opt -<pass>` recipe should be replaced by `-passes=...`; `.ll` is a first-class `opt` input.**
3. **Current LLVM IR is opaque-pointer IR.**  Legacy typed text may be upgraded on input, but new work must use `ptr` and explicit operation types.
4. **A RISC-V binary is meaningful only relative to an ABI and execution environment.**  Do not combine a bare-metal compiler tuple with Linux QEMU user mode without demonstrated compatibility.
5. **`medany` is PC-relative, not generic shared-library PIC; linker relaxation is observable only after linking.**
6. **MLIR progressive lowering supplies composable legality/type-conversion machinery, not automatic semantic preservation or performance.**
7. **AscendNPU IR provides a credible, inspectable multi-level case study, but the current workspace lacks CANN/NPU tools.**  Report its architecture and source-backed pipeline as documented/inspected evidence; reserve “executed successfully” for a real pinned device run.

