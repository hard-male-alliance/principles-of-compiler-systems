# Independent Validation Plan: Compiler-Systems Preflight and LNCS Survey

## 1. Purpose, authority, and present-state caveat

This plan validates the deliverables required by
`docs/预备工作-了解你的编译器.md` independently of implementation claims. The normative local sources are the task document, the SysY 2022 language definition and grammar supplement, the SysY 2022 runtime specification, and the project instructions in `AGENTS.md`. The intended product is one case study represented as SysY, C, authored LLVM IR, and authored RV64 assembly, carried through runtime linking and explained in an LNCS paper.

At plan-writing time (2026-09-22), the checked-out tree contains the task documents, runtime libraries, and `.github/workflows/preflight.yml`, but **does not contain `preflight/` or `report/`**. The root and documentation READMEs nevertheless link to those directories, and the workflow expects them. Therefore no eventual implementation claim is presently verified. This is a missing-deliverable state, not a toolchain failure. Run the plan below after those directories have been added. Keep all generated material under repository-local `.temp/` or `.cache/`.

## 2. Claims to test

| Claim | Independent pass criterion |
|---|---|
| One semantic case study exists | SysY, C, authored LLVM IR, and authored RV64 assembly implement the same clipped dot-product input/output function and cover integer arrays and indexing, arithmetic, assignment, both outcomes of clipping branches, a loop, a user function, and SysY runtime I/O. |
| The compiler pipeline is observable | Reproducible artifacts separately expose preprocessing, tokens/AST, LLVM IR, optimized IR, generated assembly, relocatable object structure, relocation/symbol resolution, and the linked executable. |
| The low-level programs are valid | LLVM accepts the `.ll`; an RV64 assembler accepts the `.s`; both link with an architecture-compatible SysY runtime. |
| Representations are behaviorally equivalent | Every implementation produces the independently specified stdout and exit status for every case below. Agreement alone is insufficient: all implementations could share the same error. |
| The target ABI is respected | Objects and executables are ELF64 little-endian RISC-V; calls, stack alignment, saved registers, integer width/sign behavior, and runtime symbols conform sufficiently to execute under QEMU. |
| Linking is actually demonstrated | Pre-link objects contain undefined runtime symbols and relocations; the final executable is `ET_EXEC` (or documented PIE `ET_DYN`), is runnable, and resolves the intended SysY routines. |
| The controlled compiler comparison is real | The source and target flags remain fixed while only the declared optimization variable changes; the generated artifacts differ in explained, inspectable ways. |
| The report is a reproducible LNCS paper | XeLaTeX/BibTeX build succeeds from a clean tree, the PDF is nonempty A4, required sections and citations are present, and logs contain no unresolved references, missing glyphs, or layout failures. |
| Advanced material is honest | MLIR/AscendNPU IR is clearly labeled as observed, reproduced, inferred, or documentation-based; unavailable tooling is not presented as an executed experiment. |

## 3. Test environment and provenance

Record this before testing:

```sh
git rev-parse HEAD
git status --short
cmake --version
ninja --version
python3 --version
clang --version
llvm-as --version || true
llvm-dis --version || true
llvm-readobj --version
llvm-objdump --version
riscv64-linux-gnu-gcc --version
qemu-riscv64 --version
latexmk --version
xelatex --version
bibtex --version
pdfinfo -v
```

On Ubuntu 24.04, the CI-equivalent dependencies are:

```sh
sudo apt-get update
sudo apt-get install --yes --no-install-recommends \
  clang llvm cmake ninja-build python3 \
  gcc-riscv64-linux-gnu libc6-dev-riscv64-cross qemu-user \
  latexmk poppler-utils texlive-xetex texlive-lang-chinese \
  texlive-latex-extra texlive-fonts-recommended
```

Do not silently substitute `riscv64-unknown-elf-*` for `riscv64-linux-gnu-*`: the former is a bare-metal target and does not provide the Linux startup/libc environment expected by `sylib.c`. Also do not link a host `libsysy_x86.a` or `sylib.so` into an RV64 executable.

## 4. Narrowest high-information workflow

### 4.1 Repository and configuration smoke check

From the repository root:

```sh
test -f preflight/CMakeLists.txt
test -f preflight/CMakePresets.json
test -f preflight/README.md
test -f report/main.tex
test -f report/latexmkrc
test -f report/references.bib
cmake --preset ci -S preflight
cmake --build --preset ci --target verify
ctest --preset ci --test-dir preflight
```

Expected: configure, build, and all tests succeed without writing outside `.temp/`/`.cache/`. The `verify` target must include the representative runtime execution on Linux when the cross compiler and QEMU are present; a target that only checks file existence is insufficient. On Windows, the workflow may limit itself to portable stage generation, but this does not substitute for the Ubuntu RV64 execution job.

Then reproduce the exact CI entry points:

```sh
cmake --preset ci -S preflight
cmake --build --preset ci --target verify
ctest --preset ci --test-dir preflight --output-on-failure
(cd report && latexmk -r latexmkrc -gg main.tex)
```

If the presets are designed to be invoked only from `preflight/`, use the workflow spelling instead and ensure the README says so:

```sh
(cd preflight && cmake --preset ci)
(cd preflight && cmake --build --preset ci --target verify)
(cd preflight && ctest --preset ci --output-on-failure)
```

### 4.2 Primitive compiler-stage reproduction

Do not rely solely on project check scripts. Let `CASE_C`, `CASE_SY`, `CASE_LL`, and `CASE_S` denote the single case-study files discovered from `preflight/README.md`. Preserve the command outputs under `.temp/validation/`:

```sh
mkdir -p .temp/validation
clang -std=c11 -E "$CASE_C" -o .temp/validation/case.i
clang -std=c11 -fsyntax-only -Xclang -dump-tokens "$CASE_C" \
  2> .temp/validation/case.tokens.txt
clang -std=c11 -fsyntax-only -Xclang -ast-dump=json "$CASE_C" \
  > .temp/validation/case.ast.json
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -std=c11 -O0 -S -emit-llvm "$CASE_C" -o .temp/validation/case.O0.ll
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -std=c11 -O2 -S -emit-llvm "$CASE_C" -o .temp/validation/case.O2.ll
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -std=c11 -O0 -S "$CASE_C" -o .temp/validation/case.O0.s
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -std=c11 -O2 -S "$CASE_C" -o .temp/validation/case.O2.s
```

Expected checks:

1. Preprocessed output contains expanded constants/includes and no comments, while retaining meaningful line markers unless `-P` was intentionally requested.
2. Token output contains identifiers and operators used by the case study.
3. The AST parses as JSON with `TranslationUnitDecl` at its root and contains the expected functions, loop, conditional, call expressions, and assignments.
4. Both generated IR files declare an RV64 Linux target triple and a 64-bit pointer data layout; `O0` and `O2` are not byte-identical.
5. Both generated assembly files expose the expected functions and runtime calls; the paper's claimed optimization effect is visible rather than inferred from differing file hashes.

For the authored LLVM IR, validate syntax and both a native quick path and the required target path:

```sh
llvm-as "$CASE_LL" -o .temp/validation/authored.bc
llvm-dis .temp/validation/authored.bc -o .temp/validation/authored.roundtrip.ll
clang -c "$CASE_LL" -o .temp/validation/authored.native.o
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -c "$CASE_LL" -o .temp/validation/authored.rv64.o
```

`llvm-as` may reject an otherwise valid newer IR if installed LLVM major versions differ. Diagnose this as a version/tool mismatch only after `clang -c` with the recorded intended version succeeds. The committed README must state the supported LLVM major version and opaque-pointer expectations.

For authored assembly and the other target objects:

```sh
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -c "$CASE_S" -o .temp/validation/authored-asm.rv64.o
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -std=c11 -O0 -c "$CASE_C" -o .temp/validation/c.rv64.o
clang --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
  -x c -O0 -c "$CASE_SY" -o .temp/validation/sysy.rv64.o
```

The SysY command may require a small declaration-only built-in header supplied by the project, for example `-include preflight/include/sysy_builtin.h`. That header must not implement or alter runtime semantics.

### 4.3 Object and ABI checks

For each of `c.rv64.o`, `sysy.rv64.o`, `authored.rv64.o`, and `authored-asm.rv64.o`:

```sh
llvm-readobj --file-headers --sections --symbols --relocations OBJECT \
  > .temp/validation/OBJECT.readobj.txt
llvm-objdump --disassemble --symbolize-operands OBJECT \
  > .temp/validation/OBJECT.disassembly.txt
```

Required invariants:

- ELF magic, class `ELF64`, little endian, machine `EM_RISCV` (numeric value 243), and type `ET_REL`.
- Definitions for the case-study functions and `main`.
- Undefined references and call relocations for every used SysY routine (such as `getint`, `putint`, and `putch`) before linking.
- Authored assembly contains no accidental definition that shadows a runtime routine.
- RV64 stack pointer remains 16-byte aligned at each call boundary. Every non-leaf function preserves `ra`; any used `s0`--`s11` register is saved/restored; `sp` is restored on every return path.
- The assembly uses 32-bit integer semantics where SysY requires signed 32-bit `int`. Pay special attention to `mulw`/`addiw` versus full-width operations, sign extension on returns/arguments, signed branch instructions, and division/remainder behavior.
- Address materialization and relocations are compatible with the chosen code model. Do not accept a truncated `R_RISCV_HI20` workaround hidden by fixed local addresses.

### 4.4 Runtime construction and link boundary

The provided `lib/libsysy_riscv.a` has been observed to be incompatible with the Debian glibc RV64 Linux toolchain: linking leaves an unresolved `_impure_ptr`, characteristic of a different C-library environment. Preserve that diagnostic as compatibility evidence, but do not patch around it or present the archive as successfully linked. Rebuild the supplied runtime source with the same target ABI and package it as a target-specific archive:

```sh
riscv64-linux-gnu-gcc -march=rv64gc -mabi=lp64d -std=c11 \
  -c lib/sylib.c -o .temp/validation/sylib.rv64-linux-gnu.o
riscv64-linux-gnu-ar rcs .temp/validation/libsysy_rv64_linux_gnu.a \
  .temp/validation/sylib.rv64-linux-gnu.o
riscv64-linux-gnu-ranlib .temp/validation/libsysy_rv64_linux_gnu.a
```

Validate archive identity and symbols before linking:

```sh
riscv64-linux-gnu-ar t .temp/validation/libsysy_rv64_linux_gnu.a
llvm-nm --undefined-only lib/libsysy_riscv.a | grep -F _impure_ptr
llvm-nm --defined-only .temp/validation/libsysy_rv64_linux_gnu.a | \
  grep -E ' (getint|putint|putch)$'
```

Expected: the rebuilt archive contains only RV64 Linux objects from this run, defines the runtime entry points used by the case study, and introduces no `_impure_ptr` dependency.

Link each representation as a static, non-PIE Linux executable:

```sh
for form in c sysy authored authored-asm; do
  riscv64-linux-gnu-gcc -march=rv64gc -mabi=lp64d -static -no-pie \
    ".temp/validation/${form}.rv64.o" \
    .temp/validation/libsysy_rv64_linux_gnu.a \
    -o ".temp/validation/${form}.rv64"
done
```

Link the authored LLVM IR and handwritten assembly explicitly against the rebuilt target-specific archive as shown above. This is the required runtime-library integration for the Debian RV64 Linux environment. The original `lib/libsysy_riscv.a` compatibility probe is expected to fail with unresolved `_impure_ptr`; that expected diagnostic is not an executable-equivalence candidate and must not make the normal validation job fail.

Inspect final linking:

```sh
llvm-readobj --file-headers --program-headers --symbols \
  .temp/validation/authored-asm.rv64 \
  > .temp/validation/linked.readobj.txt
llvm-objdump --disassemble --symbolize-operands \
  .temp/validation/authored-asm.rv64 \
  > .temp/validation/linked.disassembly.txt
```

Expected: an RV64 executable with program headers and executable entry point; runtime definitions are present in the static symbol table/disassembly; execution does not require a host loader. A dynamically linked alternative is acceptable only if the project records the RV64 sysroot and runs `qemu-riscv64 -L <sysroot> ...` reproducibly.

## 5. Exact observable-equivalence oracle

### 5.1 Mandatory known-answer cases for the clipped dot-product case study

The selected case study clips an input length to the valid array interval `[0, 8]`, then computes a signed integer dot product over that prefix. The independently established input/output oracle is:

| Case | stdin bytes | expected stdout bytes | expected stderr | exit status | Purpose |
|---|---:|---:|---:|---:|---|
| Negative length | `-1\n` | `0\n` | `TOTAL: 0H-0M-0S-0us\n` | 0 | lower clipping branch; zero loop iterations |
| Zero length | `0\n` | `0\n` | `TOTAL: 0H-0M-0S-0us\n` | 0 | exact lower boundary; zero loop iterations |
| One element | `1\n` | `-8\n` | `TOTAL: 0H-0M-0S-0us\n` | 0 | exactly one iteration, signed multiplication, first array elements |
| Interior length | `4\n` | `8\n` | `TOTAL: 0H-0M-0S-0us\n` | 0 | multiple iterations, array indexing, loop-carried accumulation |
| Full length | `8\n` | `16\n` | `TOTAL: 0H-0M-0S-0us\n` | 0 | exact upper boundary and all array elements |
| Above capacity | `10\n` | `16\n` | `TOTAL: 0H-0M-0S-0us\n` | 0 | upper clipping branch; prevents out-of-bounds access |

These cases jointly exercise both clipping outcomes and the in-range path, zero/one/multiple loop iterations, array address calculation and element loads, a user-defined dot-product call, assignment, signed arithmetic, and runtime input/output. The expected values are the semantic oracle; agreement among implementations is necessary but not sufficient.

Run all four target executables, each linked against the rebuilt RV64 Linux runtime archive:

```sh
for exe in c sysy authored authored-asm; do
  for n in -1 0 1 4 8 10; do
    printf '%s\n' "$n" | qemu-riscv64 ".temp/validation/${exe}.rv64" \
      > ".temp/validation/${exe}.${n}.stdout" \
      2> ".temp/validation/${exe}.${n}.stderr"
    printf '%s %s %s\n' "$exe" "$n" "$?"
  done
done
```

Compare stdout **byte-for-byte** against the table after only normalizing Windows CRLF to LF in a documented test harness. Do not trim arbitrary whitespace. The six numeric values are program results and therefore belong exclusively to stdout. For every fully linked execution, compare stderr independently and require exactly `TOTAL: 0H-0M-0S-0us\n`: `lib/sylib.c` installs `after_main` as a destructor, and it emits this zero-total diagnostic even when the program never calls the timing routines. This runtime diagnostic is expected behavior, not part of the dot-product result and not evidence of a test failure. Require exit status zero separately; matching output from a crashing program is not a pass.

In addition to execution, inspect the authored LLVM IR for two fixed array initializers/globals (or semantically equivalent local arrays), element address computations such as `getelementptr`, signed `i32` multiplication/addition, clipping control flow, loop PHI nodes or explicit loop-carried storage, the user-function call, and runtime declarations/calls. Successful `llvm-as`/`clang -c` and the known-answer runs are mandatory; textual pattern matching alone does not validate the IR.

Inspect the handwritten RV64 assembly for array storage/address materialization, scaled indexing appropriate to 4-byte SysY integers, signed word loads, 32-bit signed arithmetic behavior, clipping branches, a real function call, loop backedge, ABI-compliant stack handling, and calls to the runtime. Successful assembly, relocation/link inspection, and all QEMU known-answer runs are mandatory; compiler-generated assembly cannot substitute for the handwritten file.

Also compile and run the C, SysY-as-C, and authored IR natively as a fast diagnostic, but never count native success as validation of handwritten RV64 assembly, target linking, or the RV64 ABI.

### 5.2 If a different case study is selected

Before running implementations, commit an oracle table with exact stdin, stdout, stderr, and exit status. It must include at least: each conditional outcome, zero iterations, one iteration, several iterations, every semantic boundary introduced by the program, and one arithmetic stress case that stays within defined SysY behavior. Independently derive expected results by hand or a small mathematical reference, not by copying the C program's output. Replace the clipped-dot-product table rather than weakening it into pairwise agreement.

Do not use signed-overflow, division-by-zero, invalid shifts, out-of-bounds arrays, excessive `getarray` length, NaNs, or implementation-dependent character behavior as equivalence cases unless the report explicitly studies those semantics. Undefined behavior cannot be a correctness oracle.

## 6. Artifact-content checks

Automated checks should establish all of the following, not just nonempty files:

| Stage | Structural evidence | Required semantic cross-check |
|---|---|---|
| Preprocessor | `.i` contains expanded case-study constant/declarations | Identify one source spelling that disappeared and its replacement. |
| Lexer | token dump contains identifiers, literals, operators, and control keywords | Relate at least one multi-character operator/keyword to the source. |
| Parser/semantic front end | parseable AST with expected function/call/loop/branch nodes | Explain types and binding of one runtime call and one local value. |
| LLVM IR generation | valid `.ll`, target triple/data layout, function definitions | Trace a source branch, loop-carried value, and runtime call into IR. |
| Optimization | fixed-input `O0` and `O2` artifacts plus metrics | Explain a concrete transformation; mere size difference is insufficient. |
| Code generation | RV64 assembly with expected calls/control flow | Trace IR values/control flow to registers, branches, and ABI calls. |
| Assembly | `ET_REL` object, symbols, relocations, machine code | Show that labels/pseudo-instructions became encoded instructions/relocations. |
| Linking | executable/program headers and resolved runtime code | Show pre-link undefined runtime symbols and post-link resolution. |
| Loading/execution | QEMU command, stdin, stdout/stderr, exit code | Distinguish link success from successful process execution. |

Reject brittle checks that require one exact optimizer instruction sequence or one exact temporary symbol name across compiler releases. Assert semantic and format invariants instead. Conversely, file existence, differing hashes, and all implementations agreeing with one another are too weak.

## 7. LNCS report validation

Build twice from a clean derived-output directory:

```sh
(cd report && latexmk -r latexmkrc -C main.tex)
(cd report && latexmk -r latexmkrc -gg main.tex)
test -s report/build/main.pdf
pdfinfo report/build/main.pdf | tee .temp/validation/pdfinfo.txt
pdftotext -layout report/build/main.pdf .temp/validation/main.txt
test -s .temp/validation/main.txt
```

Machine checks:

```sh
grep -F 'Page size:' .temp/validation/pdfinfo.txt | grep -F '(A4)'
! grep -Eai \
  'undefined (citation|reference)|Citation .* undefined|Reference .* undefined|There were undefined references|Rerun to get cross-references right|Missing character|Overfull \\hbox|Overfull \\vbox|Emergency stop|Fatal error' \
  report/build/main.log
! grep -Eai 'TODO|FIXME|lorem ipsum|anonymous author|replace me' \
  .temp/validation/main.txt
```

Content inspection must verify:

- `\documentclass` uses `llncs`, not a visual imitation; no `geometry` or manual margin override defeats LNCS layout.
- Title, abstract, keywords, introduction, method/work and results, conclusion, and references are present.
- The opening matter clearly states the two-person division of work or contains an explicit, conspicuous placeholder that blocks release until names/contributions are filled. Final submission may not retain anonymous placeholders.
- The complete pipeline is explained without conflating compiler, assembler, linker, loader, and runtime.
- The same case study connects all baseline sections; code listings and tables point to reproducible repository artifacts.
- Citations visible in extracted text correspond to bibliography entries; URLs/DOIs do not overflow columns.
- Figures and tables have captions, are referenced from prose, remain legible at 100% zoom, and do not cross column/page boundaries.
- Chinese glyphs, monospace listings, math, punctuation, headers, and bibliography render correctly. Render every PDF page to images for a visual pass:

```sh
mkdir -p .temp/validation/pages
pdftoppm -png -r 150 report/build/main.pdf .temp/validation/pages/page
```

- Claims are labeled consistently as observed, inferred, or prospective. In particular, documentation-derived MLIR/Ascend discussion is not phrased as a locally executed result.
- The contribution statement, runtime-link evidence, equivalence result table, limitations, and both-students-must-submit reminder are not lost during editorial compression.

## 8. CI and compatibility checks

The GitHub Actions matrix should exercise:

1. Ubuntu 24.04: full RV64 object generation, static linking, QEMU execution, CTest, and LNCS build.
2. Windows: portable configuration and stage generation supported by installed Clang/CMake/Python; target execution may be omitted only when explicitly reported as unexercised.

Audit the workflow paths and commands against the real tree. Current `.github/workflows/preflight.yml` assumes `preflight/` and `report/`, invokes the presets from inside `preflight/`, and checks PDF size, A4 metadata, extractable text, and selected log errors. Extend or retain those checks rather than duplicating them in an unrelated script. A green Windows job does not compensate for a skipped Linux execution job, and a green paper job does not validate factual consistency with generated artifacts.

Compatibility risks to check explicitly:

- LLVM opaque-pointer syntax versus the chosen compiler major version.
- Clang integrated assembler acceptance versus GNU assembler acceptance.
- `rv64gc` with `lp64d` consistently used in compiler, assembler, runtime, and linker.
- Static archive member ABI/architecture. The supplied `lib/libsysy_riscv.a` is expected to expose the incompatible `_impure_ptr` dependency under Debian glibc; the rebuilt `.temp/validation/libsysy_rv64_linux_gnu.a` must contain RV64 Linux objects and link cleanly.
- PIE defaults differing by distribution; use `-no-pie` if the report claims `ET_EXEC`.
- `main` and runtime interfaces using C-compatible symbol names and signatures.
- Windows path quoting and Python text newline handling.
- TeX Live package/version differences and Chinese font fallback.
- QEMU user-mode timing not being reported as native RV64 performance.

## 9. Failure classification and verdict format

Classify failures before assigning blame:

| Class | Example | Treatment |
|---|---|---|
| Implementation defect | Wrong result only in authored assembly; stack not restored | Product fails the affected claim. Preserve command, input, stdout/stderr, exit code, and disassembly excerpt. |
| Test defect | Harness trims significant spaces that the oracle requires | Repair the isolated harness without weakening the contract; rerun all candidates. |
| Environment failure | Cross libc package unavailable; TeX engine missing | Record exact command/diagnostic and mark the check unavailable, not passed. CI on the declared environment remains authoritative. |
| Version incompatibility | `llvm-as` older than the authored IR dialect while supported `clang -c` succeeds | Record both versions and supported command; do not mislabel valid IR as semantically wrong. |
| Flakiness | Inconsistent timeout or output across repeated identical runs | Investigate resource/runner conditions; one successful rerun does not establish a pass. |
| Ambiguous requirement | Alternative case study changes output contract | Require the authors to publish an exact oracle before equivalence validation; all structural checks can proceed meanwhile. |

Final validation report template:

```text
Revision: <git SHA>
Environment: <OS and exact tool versions>
Commands: <verbatim commands or committed log path>

Claim                         Expected                 Observed                 Verdict
Pipeline stage artifacts      <invariants>             <paths/findings>         PASS/FAIL
SysY/C/IR/RV64 equivalence    <oracle cases>           <per-form results>       PASS/FAIL
Runtime linking               <symbols/ELF/run>        <evidence>               PASS/FAIL
LNCS source and PDF           <build/content/layout>   <evidence>               PASS/FAIL
Advanced section truthfulness <status labels>          <evidence>               PASS/FAIL

Coverage limits: <unexecuted paths and why>
Written artifacts: <tests/fixtures/logs created under the repository>
Supported overall verdict: PASS / FAIL / PARTIALLY VERIFIED
```

The overall verdict is **PASS** only when the full Ubuntu RV64 workflow, all known-answer cases for every representation, runtime archive linkage, structural stage checks, and clean LNCS build all pass. MLIR/NPU execution may remain explicitly unavailable if the course-permitted documentation-based outlook is accurately labeled, but it must not be counted as reproduced execution.
