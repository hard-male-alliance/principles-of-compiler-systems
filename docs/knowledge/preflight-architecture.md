# Preflight Compiler Study: Experiment and Repository Architecture

**Status:** proposed implementation contract  
**Scope:** the course task “Preliminary Work — Know Your Compiler,” including the
SysY/C case, hand-written LLVM IR, hand-written RV64 and AArch64 assembly,
runtime linking, evidence capture, tests, the LNCS report, and CI.  
**Authority:** Linux on GitHub Actions is the grading/reproducibility authority.
Windows is a supported authoring and inspection environment, not a substitute
execution oracle for Linux ELF targets.

## 1. Decision summary

Use one small, behaviorally specified SysY program as the semantic center of
the experiment, then implement the same contract four ways:

1. the authored SysY source;
2. a C oracle used to expose Clang's compilation stages;
3. one target-neutral, opaque-pointer LLVM IR module written by hand; and
4. hand-written assembly for both RV64 Linux (`rv64gc/lp64d`) and AArch64 Linux.

Every executable consumes the same input corpus and must produce byte-identical
standard output and exit with status zero. Standard error is captured but is
not part of the semantic oracle because the supplied SysY runtime emits timing
diagnostics from a destructor. This single contract prevents four ad-hoc demos
from drifting into four different experiments.

CMake owns the dependency graph and public developer interface. A small Python
standard-library runner owns portable process execution, exact stream capture,
hashing, metadata, and result comparison. No shell pipeline is the source of
truth. Generated evidence is written only below the preset build directory and
is uploaded as a CI artifact; authored sources and golden answers remain in the
repository.

The authoritative pipeline uses GNU/Linux cross toolchains and QEMU Linux user
emulation. The old course-note use of `riscv64-unknown-elf-gcc` should **not** be
copied: the supplied runtime calls libc and Linux facilities, and its RISC-V
archive is an ELF64 little-endian RISC-V object with double-float ABI flags. The
correct toolchain family is `riscv64-linux-gnu-*`.

## 2. Evidence and constraints already present in this repository

### 2.1 Observed facts

The current repository contains documentation plus these supplied runtime
artifacts:

| Artifact | Locally observed format | Architectural consequence |
|---|---|---|
| `lib/libsysy_x86.a` | ELF64 x86-64 relocatable member | Runnable only in a compatible Linux x86-64 environment, not native Windows |
| `lib/libsysy_riscv.a` | ELF64 little-endian RISC-V; `EF_RISCV_RVC` and `EF_RISCV_FLOAT_ABI_DOUBLE` | Compile/link as `rv64gc` + `lp64d`; do not mix with a soft-float ABI |
| `lib/libsysy_aarch.a` | ELF64 little-endian AArch64 | Compile/link for AArch64 Linux GNU ABI |
| `lib/sylib.c`, `lib/sylib.h` | libc, `gettimeofday`, constructor/destructor, I/O functions | Requires a hosted Linux C environment; stderr contains timing output |

These facts must be rechecked automatically by a `preflight-doctor` target,
not assumed forever. The check should inspect the archive headers and fail the
strict Linux preset on an architecture/ABI mismatch.

The present Windows machine has Clang, CMake, Ninja, and TeX Live, but does not
have the complete LLVM command suite, either Linux cross GCC, or QEMU user-mode
executables. That is why Windows can provide fast frontend/report feedback but
cannot issue the final green verdict.

### 2.2 External specifications that constrain the design

* Clang is a driver over distinct preprocessing, compilation, assembly, and
  linking stages; its official command guide defines the stop modes and stage
  model used here: [Clang command guide](https://clang.llvm.org/docs/CommandGuide/clang.html).
* A cross compilation must state its target triple explicitly; otherwise Clang
  assumes the host and failures often surface only at assembly or linking:
  [Clang cross-compilation guide](https://clang.llvm.org/docs/CrossCompilation.html).
* LLVM modules carry a target triple, and LLVM's language reference is the
  semantic authority for the hand-written IR:
  [LLVM Language Reference](https://llvm.org/docs/LangRef.html).
* RV64 has eight integer argument registers `a0`–`a7`, returns integer values in
  `a0`/`a1`, preserves `s0`–`s11`, and requires 128-bit stack alignment on
  standard procedure entry:
  [RISC-V ELF psABI calling convention](https://github.com/riscv-non-isa/riscv-elf-psabi-doc/blob/master/riscv-cc.adoc).
* AArch64 requires `SP mod 16 = 0` when the stack is accessed and at public
  interfaces:
  [AAPCS64](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst).
* QEMU Linux user mode executes a program built for another CPU while
  translating its Linux system calls; its `-L` option selects a guest library
  prefix. Static test executables avoid that dynamic-loader dependency:
  [QEMU user-mode documentation](https://www.qemu.org/docs/master/user/).
* Checked-in `CMakePresets.json` is intended for project-wide workflows, while
  local `CMakeUserPresets.json` should remain untracked:
  [CMake Presets manual](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html).
* GitHub distinguishes caches (reusable acceleration inputs) from artifacts
  (job results retained for inspection). Stage evidence is an artifact, never a
  cache:
  [GitHub dependency caching concepts](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching).
* `llncs` is Springer's official proceedings class, and the official
  documentation explicitly asks authors not to override its page geometry or
  spacing:
  [LLNCS class documentation](https://tug.ctan.org/macros/latex2e/contrib/llncs/llncsdoc.pdf),
  [Springer LNCS author resources](https://www.springer.com/gp/computer-science/lncs/forthcoming-proceedings).

## 3. Repository shape and ownership

The following tree cleanly separates authored claims, executable specifications,
orchestration, and derived evidence.

```text
.
├── CMakeLists.txt
├── CMakePresets.json
├── cmake/
│   ├── PreflightStages.cmake       # add_custom_command graph helpers
│   └── toolchains/                 # only if a real CMake compile target is added
├── experiments/
│   └── preflight/
│       ├── README.md               # human entry point and one-command workflows
│       ├── manifest.json           # versioned experiment/test specification
│       ├── include/
│       │   └── experiment_config.h # visible include/macro for preprocessing study
│       ├── src/
│       │   ├── feature_tour.sy     # canonical SysY presentation
│       │   ├── feature_tour.c      # C oracle and frontend-stage subject
│       │   ├── feature_tour.ll     # hand-written opaque-pointer LLVM IR
│       │   ├── riscv64/
│       │   │   └── feature_tour.S  # hand-written RV64 GNU assembly
│       │   └── aarch64/
│       │       └── feature_tour.S  # hand-written AArch64 GNU assembly
│       ├── tests/
│       │   ├── empty.in
│       │   ├── empty.out
│       │   ├── nominal.in
│       │   ├── nominal.out
│       │   ├── clamp.in
│       │   ├── clamp.out
│       │   ├── signed.in
│       │   ├── signed.out
│       │   ├── zero_continue.in
│       │   ├── zero_continue.out
│       │   ├── early_break.in
│       │   └── early_break.out
│       └── scripts/
│           ├── doctor.py           # capability + archive ABI validation
│           ├── run_stage.py        # argv execution and evidence record
│           ├── run_cases.py        # exact behavioral oracle
│           ├── collect_metrics.py  # structural metrics, not interpretation
│           └── render_report_data.py
├── report/
│   ├── main.tex                    # \documentclass[runningheads]{llncs}
│   ├── sections/*.tex
│   ├── references.bib
│   ├── figures/                    # authored diagrams only
│   ├── generated/                  # generated .tex/.pdf inputs; ignored
│   └── third_party/llncs/          # exact upstream class/BST + license/checksum
├── lib/                            # preserve the existing external contract
└── .github/workflows/preflight.yml
```

### Ownership rules

* `*.sy`, the hand-written `*.ll`, and hand-written `*.S` files are source.
  They must never be overwritten by a compiler target.
* `*.i`, token dumps, ASTs, compiler-generated IR/assembly, objects,
  executables, disassembly, run logs, metrics, manifests, and the report PDF are
  derived. They belong below `build/<preset>/`, not beside source files.
* Golden `*.out` files are authored behavior specifications. Updating one must
  be reviewed as a semantic change, not accepted automatically because current
  executables agree.
* `lib/` filenames and public symbols are an existing course contract. Do not
  rename or rebuild the supplied archives silently. A separately built runtime
  may exist as an explicit comparison variant, not as a replacement.
* `report/generated/` contains only machine-produced LaTeX fragments copied
  from a successful experiment result. Authors edit narrative and captions,
  never measurements embedded in generated fragments.

## 4. The semantic center: one program, one contract

### 4.1 Feature coverage

`feature_tour` should deliberately cover course-relevant language features
without becoming an algorithm benchmark:

| Construct | How it is exercised | What it exposes downstream |
|---|---|---|
| global constant and global variable | modulus and bias | symbol binding, `.rodata`/`.data`, relocation |
| integer arithmetic and remainder | per-element transform | LLVM integer instructions, RV64/AArch64 ALU instructions |
| assignment and local scope | loop accumulator and a nested temporary | allocas at `-O0`, SSA promotion under optimization |
| `if` / `else` | sign normalization and input clamping | conditional branches and CFG joins |
| `while` | bounded array-processing loop | loop back-edge and optimization metadata |
| function definition/call | `transform(value, weight)` | calling convention, prologue/epilogue, linker symbols |
| one-dimensional array | maximum eight input values | indexed addressing / `getelementptr` |
| `continue` and `break` | zero element and sum threshold | multiple loop exits and CFG shape |
| runtime I/O | `getint`, `putint`, `putch` | undefined symbols, archive extraction, final linkage |
| preprocessor-only C wrapper | include, object macro, function macro, conditional compilation | visible difference between SysY and the C preprocessing experiment |

Keep the numeric domain explicit. Clamp `n` to `[0, 8]`; use test values small
enough that all signed 32-bit operations are defined. Do not use `INT_MIN`
absolute value, overflowing multiplication, or language-dependent negative
remainder as “edge tests.” Undefined behavior would destroy the oracle rather
than enrich it.

The SysY source and C oracle may differ only in the preprocessor wrapper and
runtime declarations required by C. The function bodies should remain
line-for-line comparable where the grammars overlap. Put the contract and
input domain in bilingual documentation comments in both sources.

### 4.2 Test corpus

Each test case must isolate a meaningful control-flow path:

| Case | Required property |
|---|---|
| `empty` | lower clamp or zero-length path, no loop body |
| `nominal` | several positive values, ordinary loop completion |
| `clamp` | input length above eight is clamped; exactly eight values consumed |
| `signed` | negative value takes normalization branch |
| `zero_continue` | zero triggers `continue` without an accidental infinite loop |
| `early_break` | accumulated result crosses threshold and takes `break` |

The runner writes input bytes directly to stdin, captures stdout and stderr
separately, records the exit code, and compares stdout exactly with the golden
file. Expected files use UTF-8 and LF endings. Do not call `.strip()` and do not
normalize arbitrary whitespace: a missing newline or extra space is observable
program behavior.

### 4.3 Executable variants

The minimum equivalence set is:

| Variant | Build path | Execution path |
|---|---|---|
| C oracle, x86-64 | Clang C → object; link `libsysy_x86.a` | native Linux |
| hand IR, x86-64 | validate/assemble IR → object; link `libsysy_x86.a` | native Linux |
| hand IR, RV64 | Clang/LLVM target object; GNU cross driver links `libsysy_riscv.a` | `qemu-riscv64` |
| hand assembly, RV64 | GNU assembler via cross driver; static GNU link | `qemu-riscv64` |
| hand IR, AArch64 | Clang/LLVM target object; GNU cross driver links `libsysy_aarch.a` | `qemu-aarch64` |
| hand assembly, AArch64 | GNU assembler via cross driver; static GNU link | `qemu-aarch64` |

The authored SysY file is not treated as executable until this repository has a
SysY compiler. The C oracle is therefore a clearly labeled surrogate, not
evidence that an independent SysY compiler accepted the source.

## 5. Stage graph and artifact contract

### 5.1 Canonical stage directories

Use lexically sortable stage numbers under
`build/<preset>/evidence/<variant>/`:

```text
00-source/       source snapshot, manifest excerpt, SHA-256
10-preprocess/   .i plus a report-normalized excerpt
20-frontend/     tokens.txt, ast.txt, ast.json
30-ir/           O0.ll, O2.ll, .bc, verifier log
40-codegen/      compiler-generated target .s
50-object/       .o, headers, sections, symbols, relocations, disassembly
60-link/         executable ELF, link map, headers, symbols, disassembly
70-run/          per-case stdin/stdout/stderr/status/result JSON
80-metrics/      long-form CSV + JSON and a provenance manifest
```

The numeric directory is the conceptual stage, not evidence that one monolithic
driver command produced every file. Each record contains the exact argv used.
This makes integrated and separately invoked compiler stages distinguishable.

### 5.2 Stage commands

The implementation should use the driver for normal compilation and official
LLVM tools for inspection/validation. Representative Linux commands follow;
the runner must pass them as an argv array rather than through `sh -c`.

```text
# Driver plan and preprocessing
clang -### -std=c17 -I experiments/preflight/include -I lib feature_tour.c
clang -E   -std=c17 -I experiments/preflight/include -I lib feature_tour.c -o feature_tour.i

# Frontend observations (diagnostic streams must be captured deliberately)
clang -fsyntax-only -Xclang -dump-tokens ... feature_tour.c
clang -fsyntax-only -Xclang -ast-dump ... feature_tour.c
clang -fsyntax-only -Xclang -ast-dump=json ... feature_tour.c

# Compiler-generated LLVM IR at distinct optimization levels
clang -S -emit-llvm -O0 ... feature_tour.c -o feature_tour.O0.ll
clang -S -emit-llvm -O2 ... feature_tour.c -o feature_tour.O2.ll

# Hand-written IR validation
llvm-as feature_tour.ll -o feature_tour.bc
opt -passes=verify -disable-output feature_tour.bc

# LLVM backend observations
llc -O0 -mtriple=riscv64-unknown-linux-gnu -mattr=+m,+a,+f,+d,+c feature_tour.bc -o feature_tour.riscv64.s
llc -O0 -mtriple=aarch64-unknown-linux-gnu feature_tour.bc -o feature_tour.aarch64.s

# Hand assembly and static hosted-Linux linkage
riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d feature_tour.S -o feature_tour.o
riscv64-linux-gnu-gcc -static -no-pie -march=rv64gc -mabi=lp64d feature_tour.o lib/libsysy_riscv.a -o feature_tour.elf
aarch64-linux-gnu-gcc -c -march=armv8-a feature_tour.S -o feature_tour.o
aarch64-linux-gnu-gcc -static -no-pie -march=armv8-a feature_tour.o lib/libsysy_aarch.a -o feature_tour.elf
```

For LLVM-IR-to-cross-object commands, invoke Clang with the explicit
`--target=...` and ISA/ABI flags, then use the corresponding GNU cross compiler
driver for the final hosted link. The GNU driver supplies the correct Linux
startup objects, libc, libgcc, and linker configuration. Do not invoke `ld`
directly unless the experiment is specifically studying everything a driver
adds.

Record object and executable differences with `llvm-readelf`/`llvm-readobj`,
`llvm-nm`, `llvm-size`, and `llvm-objdump`. These tools are expressly intended
to inspect object files and final linked images:
[LLVM command guide](https://llvm.org/docs/CommandGuide/),
[llvm-readelf](https://llvm.org/docs/CommandGuide/llvm-readelf.html), and
[llvm-objdump](https://llvm.org/docs/CommandGuide/llvm-objdump.html).

### 5.3 Linker study

Always retain both object and final-executable symbol/relocation/disassembly
views. The paper can then demonstrate, rather than merely assert:

* runtime functions are undefined in the student object but defined after
  archive extraction and linkage;
* relocations in `.o` are resolved or transformed in the executable;
* `_start`, C runtime startup, libc, constructor/destructor machinery, and
  additional sections appear only after the link; and
* linker relaxation may change RISC-V code between object disassembly and final
  disassembly.

Generate a link map with `-Wl,-Map,<path>`. Optionally add a named
`riscv64-no-relax` experimental variant using `-Wl,--no-relax`; do not make it
the default merely to hide linker behavior.

Static Linux ELFs are the normative run products because they make QEMU's guest
loader independent of a sysroot. A dynamic-link variant is pedagogically useful
but optional; if included, run it with QEMU `-L /usr/<triple>` and record both
`PT_INTERP` and dynamic dependencies.

## 6. CMake architecture

### 6.1 Principles

Use CMake 3.28 or later and Ninja. The top-level experiment project may use
`project(... LANGUAGES NONE)` because one build tree deliberately orchestrates
three target architectures and uses explicit compiler executables. Pretending
there is one CMake C compiler would encode the wrong data model. If future
production C++ tools are added, put them in a normal C++23 target and enable CXX
then; do not globally fake a compiler toolchain.

Define explicit outputs and dependencies with `add_custom_command(OUTPUT ...)`,
then aggregate them with small targets. Do not use recursive globs, always-run
shell scripts, or one opaque `preflight-all` command that CMake cannot
incrementally reason about.

Suggested public targets:

```text
preflight-doctor          validate tools, runtime archives, and manifest
preflight-frontend        produce .i, tokens, AST, generated O0/O2 IR
preflight-ir              validate hand IR and build native/cross IR variants
preflight-riscv64         assemble, link, inspect, and run RV64 variants
preflight-aarch64         assemble, link, inspect, and run AArch64 variants
preflight-test            execute all equivalence cases (also exposed via CTest)
preflight-evidence        collect provenance and structural metrics
preflight-report-data     render validated results into LaTeX fragments
report                    build the LNCS PDF after validated report data
preflight-all             dependency-only umbrella, no hidden work
```

The helper `preflight_add_stage()` should own one primary output, declare every
source/tool/config dependency, put secondary files in `BYPRODUCTS`, set a
meaningful `COMMENT`, and use `VERBATIM`. Short helpers are preferable to a
generic mini build language.

### 6.2 Presets

Commit `CMakePresets.json` using schema version 6 (workflow presets require
CMake 3.25+) and keep `CMakeUserPresets.json` ignored.

| Preset/workflow | Purpose | Missing-tool policy |
|---|---|---|
| `linux-authoritative` | Ninja tree at `build/linux-authoritative`; all targets and report | configure/doctor failure |
| `windows-observe` | native frontend, static archive inspection, script tests, and local report | capability recorded; cross run targets unavailable, never reported as passed |
| `preflight-ci` workflow | configure → `preflight-all` → CTest | strict |
| `report-local` workflow | report authoring with last validated/generated data | may use checked evidence snapshot only if clearly marked |

Tool paths should be cache variables (`PREFLIGHT_CLANG`, `PREFLIGHT_LLVM_AS`,
`PREFLIGHT_RISCV_CC`, and so on). CI supplies exact paths such as versioned LLVM
binaries; developers override them in `CMakeUserPresets.json`, never by editing
project presets.

## 7. Runner, manifests, and data model

### 7.1 Why a small runner is justified

CMake is a good dependency graph but a poor cross-platform stream-capture and
JSON engine. PowerShell and POSIX shell differ in redirection, quoting, exit
status, executable suffixes, and timing. One Python runner removes these
special cases instead of adding branches to every command.

The runner must remain deliberately small:

* use `subprocess.run` with an argv list, never `shell=True`;
* accept explicit cwd, stdin file, stdout file, stderr file, and metadata path;
* preserve raw output bytes;
* return the child status unless an expected nonzero result was declared;
* write metadata atomically via a temporary file in the same build directory;
* use monotonic time only for elapsed-duration observations; and
* never delete outside its explicit build-tree root.

### 7.2 Versioned experiment manifest

`manifest.json` should contain stable semantics, not machine paths:

```json
{
  "schema_version": 1,
  "program": "feature_tour",
  "domain": {"n_min": 0, "n_max": 8},
  "cases": [
    {"id": "nominal", "stdin": "tests/nominal.in", "stdout": "tests/nominal.out"}
  ],
  "variants": [
    {"id": "c-x86_64", "runner": "native"},
    {"id": "ir-riscv64", "runner": "qemu-riscv64"},
    {"id": "asm-riscv64", "runner": "qemu-riscv64"},
    {"id": "ir-aarch64", "runner": "qemu-aarch64"},
    {"id": "asm-aarch64", "runner": "qemu-aarch64"}
  ]
}
```

Validate unknown/missing keys and unique IDs early. Paths are repository-relative
and may not escape the preflight subtree. Tool argv and build paths belong in
the result manifest produced by CMake/runner, not in this source manifest.

### 7.3 Per-command and aggregate provenance

Each stage record should contain:

* schema version and stage/variant ID;
* argv as an array, cwd relative to the repository, and selected environment;
* tool path plus `--version` output;
* target triple, ISA, ABI, optimization level, and link mode;
* Git commit and dirty flag;
* SHA-256 for all declared inputs and outputs;
* exit status and elapsed nanoseconds; and
* host OS/architecture, locale, timezone, and CI run identity when available.

Do not claim that elapsed time or absolute output paths are reproducible. Keep
them in raw provenance but exclude them from semantic comparisons and stable
report snapshots.

### 7.4 Metrics

Use long-form data so new dimensions do not force a new table schema:

```text
program,variant,target,opt,case,metric,value,unit,method,status
feature_tour,clang-c,riscv64,O0,,object_bytes,1234,byte,stat,observed
feature_tour,hand-asm,riscv64,none,nominal,semantic_match,1,bool,exact-stdout,observed
```

Collect at least source/preprocessed/IR/assembly/object/executable byte counts,
ELF section sizes (`text`, `data`, `bss`), functions/basic blocks/IR instruction
counts, undefined/defined symbol counts before and after linkage, and semantic
pass counts. A compile or run duration may be collected as median and median
absolute deviation after warmups, but it must be labeled exploratory.

Never compare QEMU wall-clock times across RV64 and AArch64 as if they measured
the target architectures. They mostly measure different emulator paths and a
noisy shared CI host. Instruction counts and section sizes are suitable
structural observations; real-hardware runtime claims require a separate
controlled benchmark design.

## 8. Reproducibility policy

### 8.1 What “reproducible” means here

The primary guarantee is **semantic and evidentiary reproducibility**: from a
recorded source revision and environment, another run can reproduce the stage
graph, exact commands, observations, and expected behavior. Byte-identical ELF
files across toolchain releases are not promised.

For stable outputs:

* set `LC_ALL=C`, `LANG=C`, and `TZ=UTC` in the authoritative job;
* derive `SOURCE_DATE_EPOCH` from the source commit, not wall time;
* avoid `__DATE__`, `__TIME__`, random temporary names in reported data, and
  embedded absolute paths;
* use `-ffile-prefix-map=<repo>=.` and `-fdebug-prefix-map=<repo>=.` for variants
  that carry file/debug paths;
* use deterministic archives and disable optional linker build IDs for the
  byte-comparison experiment (`-Wl,--build-id=none`), while retaining a normal
  pedagogical link variant if desired;
* sort rows and object lists explicitly before serialization; and
* record, rather than conceal, exact compiler/linker/QEMU/LaTeX versions.

`SOURCE_DATE_EPOCH` is a standardized mechanism for replacing volatile build
timestamps with a source-related timestamp:
[Reproducible Builds timestamp guidance](https://reproducible-builds.org/docs/timestamps/).

### 8.2 Environment levels

1. **Required now:** pin the GitHub runner label to `ubuntu-24.04`, install named
   packages, use versioned LLVM executable names, and record package/tool
   versions in every artifact.
2. **Stronger later:** run the authoritative job in an OCI image pinned by
   digest and publish its Dockerfile/package lock. This enables closer binary
   reproduction but adds maintenance cost that is not necessary to establish
   the course claims.
3. **Not sufficient:** a README list of approximate commands without captured
   versions, target triples, or input/output hashes.

## 9. GitHub Actions design

Use two jobs rather than pretending all hosts have equivalent capabilities.

### 9.1 `host-smoke` matrix

Run on `ubuntu-24.04` and `windows-latest`:

1. checkout;
2. install/select CMake, Ninja, and Python;
3. configure the host-appropriate preset;
4. run manifest/runner unit tests, CMake configuration, and the doctor; and
5. on Windows, optionally compile the local LNCS report if TeX is available,
   but do not download a huge TeX distribution merely for the smoke job.

The Windows result proves that project orchestration and authoring helpers do
not accidentally depend on Bash. It does not claim that Windows produced or
ran Linux RV64/AArch64 binaries.

### 9.2 `linux-authoritative`

Run on `ubuntu-24.04` and install:

* CMake/Ninja/Python;
* a complete, version-selected Clang/LLVM tool suite;
* `gcc-riscv64-linux-gnu`, `binutils-riscv64-linux-gnu`;
* `gcc-aarch64-linux-gnu`, `binutils-aarch64-linux-gnu`;
* `qemu-user`; and
* `latexmk` plus the TeX Live packages needed by `llncs`, BibTeX, listings,
  graphics, and Chinese text.

Then execute only the public workflow:

```text
cmake --workflow --preset preflight-ci
```

Upload, even after a failed validation, the available `evidence/`, CTest logs,
LaTeX log, tool-version manifest, and (on success) `report.pdf`. Give the
artifact a revision-qualified name and a finite retention period. GitHub's
artifact action supports explicit retention and immutable artifact IDs:
[actions/upload-artifact](https://github.com/actions/upload-artifact).

Use a read-only default token (`contents: read`), add no deployment credentials,
and pin third-party actions to reviewed full commit hashes. Do not cache evidence
or generated report data. A dependency cache is optional acceleration; a clean
cache miss must still produce a complete result.

This full job is the required branch check. The smoke matrix is valuable
portability evidence but cannot override a failed authoritative job.

## 10. LNCS report pipeline

### 10.1 Typesetting contract

Use the official class directly:

```tex
\documentclass[runningheads]{llncs}
...
\bibliographystyle{splncs04}
```

Vendor a specific unmodified official `llncs.cls`/`splncs04.bst` release with
its license, upstream URL, version, and checksum, or pin the TeX environment
that supplies it. Do not copy snippets from an unofficial template. Do not use
`geometry`, manual text-width/height changes, negative vertical spacing, or
custom heading/caption redefinitions that defeat the LNCS layout.

For a Chinese report, prefer a deterministic pdfLaTeX + `CJKutf8` setup if the
submission requirement includes pdfLaTeX compatibility. If XeLaTeX + `xeCJK`
is selected instead, pin an open CJK font and record the engine/font versions;
do not silently fall back to a machine-specific Windows font.

Use `listings`, not `minted`, unless shell escape and Pygments are intentionally
added and pinned. Build with:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

### 10.2 Paper structure driven by evidence

The report should include:

1. title, authors, explicit two-person contribution statement, abstract, and
   keywords;
2. introduction and research questions;
3. experimental object, semantic contract, environment, and reproducibility;
4. observed preprocessing/frontend/IR/code-generation/assembly/link stages;
5. hand-written IR design and verifier evidence;
6. RV64 and AArch64 ABI mapping and runtime linkage;
7. equivalence results and structural measurements;
8. limitations (C is a SysY surrogate; QEMU is not hardware performance;
   generated compiler output is version-dependent);
9. optional MLIR/AscendNPU IR exploration clearly separated from verified base
   results; and
10. conclusion and references.

Tables in the result section are generated from successful JSON/CSV evidence.
Code/IR/assembly excerpts are bounded, line-numbered snapshots with a source
hash in the caption or appendix; the full artifacts remain attached to CI.
This prevents stale numbers and giant unreviewable listings in the paper.

## 11. CTest and acceptance criteria

Expose tests by layer so failures point to one boundary:

| Label | Acceptance criterion |
|---|---|
| `schema` | manifest and every generated result validate; IDs and paths are safe/unique |
| `ir` | hand IR assembles and passes `opt -passes=verify` |
| `abi` | runtime archive formats/flags match declared targets; assembly respects stack/callee-save rules |
| `link` | all normative variants link statically; expected runtime symbols resolve |
| `semantic` | every executable × case returns zero and stdout exactly equals golden bytes |
| `evidence` | required stage outputs exist, are nonempty, and have hashes/provenance |
| `report` | LaTeX/BibTeX completes without undefined citations/references or fatal warnings |

Completion means all six layers pass in `linux-authoritative`, the PDF is built
from the same run's validated evidence, and both PDF and evidence bundle are
uploaded. A Windows-only green build, manually executed command, or visually
plausible output is not completion.

## 12. Implementation slices and integration order

These slices minimize broken intermediate states and support small commits:

1. **Contract:** add SysY/C sources, golden cases, `manifest.json`, and runner
   unit tests. Review expected outputs independently.
2. **Native LLVM path:** add hand IR, verifier, C/IR native linking, and exact
   equivalence tests.
3. **RV64 path:** add assembly, ABI checks, static link, QEMU execution, object
   vs executable inspection, and equivalence tests.
4. **AArch64 path:** add the symmetric implementation and tests, reusing the
   same manifest/runner rather than cloning scripts.
5. **Stage evidence:** implement frontend dumps, generated optimization/codegen
   variants, link maps, metrics, and the aggregate provenance manifest.
6. **CMake/presets:** expose the stable target/workflow interface and Windows
   observe preset.
7. **Report:** add official pinned LNCS assets, evidence-to-LaTeX rendering,
   narrative, bibliography, and PDF checks.
8. **CI:** add cross-platform smoke plus authoritative Linux job, upload failure
   evidence, and make the Linux job required.

Commit after each slice passes its available local tests. Do not commit generated
build trees. Since the project requires PR-based integration, work on the
current feature branch, push small coherent commits, and merge only after the
authoritative workflow succeeds.

## 13. Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Separate unrelated examples for C, IR, RV64, and AArch64 | No meaningful equivalence claim; report becomes a collection of anecdotes |
| Treat compiler output as the “hand-written” IR/assembly | Does not satisfy the programming task and hides design understanding |
| Put generated `.ll`, `.s`, `.o`, and logs beside sources | Stale artifacts are easily mistaken for authored truth and pollute reviews |
| A monolithic Bash/Make script | Poor Windows behavior, opaque incremental dependencies, fragile stream redirection |
| `riscv64-unknown-elf-gcc` with the supplied runtime | Bare-metal toolchain conflicts with a runtime that expects hosted libc/Linux behavior |
| Direct `ld` final links | Omits startup files, libc/libgcc selection, and ABI defaults the compiler driver owns |
| Dynamic cross executables as the only test | Couples tests to guest loader/sysroot paths; static ELFs are simpler and more portable under QEMU |
| Compare RV64 vs AArch64 QEMU wall time | Confounds program, emulator, host scheduling, and implementation quality |
| Make Windows failures silently skip cross tests | Converts missing evidence into false success |
| Hand-copy measurements into LaTeX | Results go stale and lose provenance |
| Override LNCS margins/spacing to fit more content | Violates the class contract and makes the PDF nonconforming |

## 14. Material risks and mitigations

| Risk | Consequence | Mitigation / falsifying check |
|---|---|---|
| Supplied archive ABI differs from assumed compiler flags | link error or silent calling-convention mismatch | doctor inspects ELF machine/flags; compile probe; fail strict preset |
| Hand IR depends on an LLVM syntax version | verifier or codegen failure after toolchain change | pin major LLVM in CI; opaque-pointer IR; record version; verifier is a hard gate |
| Assembly violates callee-save or stack alignment rules | sporadic libc/runtime failures | follow psABI/AAPCS64, ABI-focused review, multiple call paths and tests |
| C oracle accidentally uses behavior outside SysY semantics | false equivalence claim | keep overlapping bodies simple; document the surrogate; inspect domain and UB |
| Static cross link cannot find compatible libc/start files | CI link failure | install GNU Linux cross compiler packages and link through their driver |
| Runtime destructor makes stderr vary | flaky golden comparison | compare exact stdout + exit code; retain stderr as observation only |
| QEMU accepts behavior that real hardware would reject | overclaim about target validity | frame result as Linux-user emulation; optionally validate on real ISA runner later |
| Tool updates alter AST/IR/assembly text | noisy snapshots | treat stage text as versioned observation, not golden semantics; record versions/hashes |
| CI timing noise appears as a performance claim | invalid conclusion | median/MAD only for exploratory within-variant repeats; no cross-ISA speed claim |
| Report can build from stale generated data | internally inconsistent paper | `report` depends on successful current evidence manifest and source hashes |
| Windows path/quoting assumptions leak into scripts | local authoring breaks | argv-based Python runner; matrix smoke; repository-relative paths |

## 15. Definition of done

The architecture is realized when a fresh authoritative runner can execute one
documented workflow and produce:

* verified hand-written LLVM IR;
* assembled and linked hand-written RV64 and AArch64 programs;
* native and cross-architecture semantic equivalence over the complete corpus;
* preserved preprocessing, frontend, IR, assembly, object, linker, and run
  evidence with exact provenance;
* machine-generated result tables with appropriately qualified claims;
* a conforming `llncs` PDF built from that evidence; and
* a downloadable CI evidence bundle that lets a reviewer inspect how every
  reported result was obtained.

Anything less should be described precisely as partial capability, never
collapsed into a generic “build passed.”
