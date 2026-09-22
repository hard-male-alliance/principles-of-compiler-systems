# Preflight Environment and Runtime Compatibility Evidence

**Observed:** 2026-09-22
**Scope:** host toolchains, SysY runtime binaries, cross-target execution, LLNCS PDF production, and CI feasibility.
**Related contracts:** [`preflight-acceptance.md`](preflight-acceptance.md) and [`preflight-architecture.md`](preflight-architecture.md).

This note records reproduced behavior rather than intended behavior. It should be updated when the authoritative CI image or runtime archives change.

## 1. Decision summary

1. **Use Ubuntu Linux as the reproducibility authority.** The local WSL Ubuntu 24.04 environment provides the complete LLVM stage toolset, QEMU user-mode emulators, XeLaTeX/LLNCS, and Poppler. Windows remains a useful authoring and independent compiler environment, but its LLVM installation lacks several standalone IR tools.
2. **The supplied x86-64 runtime is usable through function declarations.** A native program linked with `libsysy_x86.a`; input `21` produced standard output `42` and the runtime timing summary on standard error.
3. **Do not claim that the supplied RISC-V archive is Linux/glibc compatible.** It is an RV64 ELF archive and participates in a matching relocatable link, but the resulting object retains `_impure_ptr`, a newlib-style dependency. This conflicts with treating the README's `riscv64-linux-gnu-gcc` example as already verified.
4. **Build cross runtimes from `lib/sylib.c` with the same Linux cross compiler used for the example.** This removes the newlib/glibc mismatch from the experiment. Preserve a separate audit of the supplied archive rather than hiding the discrepancy.
5. **Do not include `lib/sylib.h` in a client translation unit as currently written.** The header defines nine timing globals. Modern GCC then reports multiple definitions when the prebuilt library is linked. Hand-written LLVM IR and assembly should declare only the runtime functions they call.
6. **Build the Chinese LNCS paper with XeLaTeX.** A Chinese LLNCS smoke document built successfully on both Windows and WSL, was A4, contained extractable Chinese text, and used embedded fonts.

## 2. Observed toolchains

| Capability | Windows host | WSL Ubuntu 24.04.4 |
|---|---|---|
| Clang/LLVM | 22.1.8, `x86_64-pc-windows-msvc` | Ubuntu LLVM 18.1.3 |
| GCC | MSYS2 16.1.0 | Ubuntu GCC 13.3.0 |
| CMake / Ninja | 4.4.0 / 1.13.2 | 3.28.3 / 1.11.1 |
| LLVM stage utilities | `llvm-ar`, `llvm-nm`, `llvm-objdump`, `llvm-readobj`, LLD present; `llvm-as`, `llvm-dis`, `llc`, `opt`, `llvm-config` absent | `llvm-as`, `llvm-dis`, `llc`, `opt`, `llvm-config`, archive/object utilities, and LLD present |
| Cross execution | No QEMU or Linux cross GCC commands found | QEMU user mode 8.2.2 for RISC-V and AArch64; Linux cross GCC/sysroots were not installed |
| TeX | TeX Live 2026, Latexmk 4.88, XeTeX, `llncs.cls`, `ctex.sty` | TeX Live 2023/Debian, Latexmk 4.83, XeTeX, `llncs.cls`, `ctex.sty` |
| PDF inspection | Poppler tools present (`pdftotext` 25.02.0; `pdfinfo` 26.07.0) | Poppler 24.02.0 |

The Windows `latexmk` process emitted a locale fallback warning because `C.UTF-8` was unavailable to its Perl runtime. Compilation still succeeded; this was an environmental warning, not a document failure.

## 3. Runtime binary evidence

### 3.1 Formats and exported interface

`llvm-ar t`, `readelf -h`, and `llvm-nm --defined-only --extern-only` established:

| File | Archive member | Object format | Machine |
|---|---|---|---|
| `lib/libsysy_x86.a` | `libsysy_x86.o` | ELF64 relocatable, little-endian | AMD x86-64 |
| `lib/libsysy_riscv.a` | `sylib.o` | ELF64 relocatable, little-endian | RISC-V |
| `lib/libsysy_aarch.a` | `libsysy_aarch.o` | ELF64 relocatable, little-endian | AArch64 |
| `lib/sylib.so` | n/a | ELF64 shared object, little-endian | AMD x86-64 |

All four binaries define the documented function set:

```text
getint getch getarray getfloat getfarray
putint putch putarray putfloat putfarray putf
before_main after_main _sysy_starttime _sysy_stoptime
```

They also export the timing globals. `sylib.so` depends on `libc.so.6`; its version table requires at most GLIBC 2.7.

The RISC-V object reports 16-byte stack alignment and an ISA equivalent to RV64 with I, M, A, F, D, and C plus related standard extensions. Its compiler comment identifies GCC 15.1.0 but does not establish the C library ABI. The other embedded compiler comments identify Ubuntu GCC 11.4.0 for AArch64 and Clang 18.1.8 for x86-64.

### 3.2 Native runtime success path

The smoke program deliberately declares the generated-code ABI instead of including the defective header:

```c
extern int getint(void);
extern void putint(int);
extern void putch(int);

int main(void) {
  int x = getint();
  putint(x * 2);
  putch(10);
  return 0;
}
```

Reproduction from the repository root on Linux:

```sh
gcc -std=c17 -Wall -Wextra -Wpedantic runtime_smoke.c \
  lib/libsysy_x86.a -o runtime_static

stdout=$(printf '21\n' | ./runtime_static 2>runtime.stderr)
test "$stdout" = '42'
grep -q '^TOTAL:' runtime.stderr
```

Observed result: the assertions passed. Separating streams is required because the runtime destructor writes its timing summary to standard error.

### 3.3 Cross-target evidence and boundary

Clang 18 and LLD produced static, syscall-only Linux ELF executables for both targets. `qemu-riscv64` returned the deliberately encoded status `42`; `qemu-aarch64` returned `43`. This verifies the local assembler, linker, ELF target, and emulator path without depending on a target libc.

The supplied runtime archives were then tested through a relocatable link:

```sh
clang --target=riscv64-linux-gnu -c runtime_smoke.c -o runtime_riscv.o
ld.lld -r runtime_riscv.o lib/libsysy_riscv.a -o combined_riscv.o
readelf -h combined_riscv.o
llvm-nm --undefined-only combined_riscv.o

clang --target=aarch64-linux-gnu -c runtime_smoke.c -o runtime_aarch64.o
ld.lld -r runtime_aarch64.o lib/libsysy_aarch.a -o combined_aarch64.o
readelf -h combined_aarch64.o
llvm-nm --undefined-only combined_aarch64.o
```

Observed machine types were RISC-V and AArch64 respectively. The RISC-V result retained:

```text
_impure_ptr fprintf gettimeofday printf putchar scanf vfprintf
```

The presence of `_impure_ptr` is evidence of a newlib-style runtime dependency. It is not resolved by a normal glibc Linux link. Therefore:

- **Observed:** target architecture and relocatable-link compatibility.
- **Not observed:** a final Linux/glibc executable linked from the supplied RISC-V archive.
- **Recommended:** rebuild `sylib.c` under the selected `riscv64-linux-gnu` compiler, then perform a static link and QEMU execution in CI.

### 3.4 Reproduced header defect

This client:

```c
#include "sylib.h"
int main(void) { putint(42); putch(10); return 0; }
```

was compiled with:

```sh
gcc -std=c17 -Wall -Wextra -Wpedantic -Ilib header_smoke.c \
  lib/libsysy_x86.a -o header_static
```

GNU ld reported multiple definitions for `_sysy_start`, `_sysy_end`, `_sysy_l1`, `_sysy_l2`, `_sysy_h`, `_sysy_m`, `_sysy_s`, `_sysy_us`, and `_sysy_idx`. These objects are defined in `sylib.h` and again in the archive. This is an implementation defect, not a missing dependency. A future production correction should declare the variables `extern` in the header and retain exactly one definition in `sylib.c`; until then, generated artifacts should use external function declarations rather than include the header.

## 4. LLNCS document evidence

A minimal document using the repository's `report/llncs.cls`, `ctex`, Chinese title/body text, abstract, keywords, a section, and mathematics was built with:

```sh
cd report
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
pdfinfo main.pdf | grep -E 'Pages:|Page size:|PDF version:'
pdftotext main.pdf - > /tmp/report.txt
test -s /tmp/report.txt
pdffonts main.pdf
```

The smoke build succeeded on both the Windows TeX Live and WSL TeX Live installations. The generated document was A4, Chinese text was recoverable with `pdftotext`, and fonts were embedded. This supports XeLaTeX as the canonical engine; it does not establish that every later revision of the full paper is layout-correct, so CI and final visual review remain necessary.

## 5. CI implementation guidance

Pin `ubuntu-24.04`, print tool versions, and install the required Linux packages explicitly:

```sh
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  clang lld llvm cmake ninja-build qemu-user \
  gcc-riscv64-linux-gnu gcc-aarch64-linux-gnu \
  latexmk texlive-xetex texlive-lang-chinese texlive-latex-extra \
  texlive-fonts-recommended poppler-utils
```

Required validation layers:

1. **Native runtime:** compile against `libsysy_x86.a`; assert exit status, stdout, and timing stderr independently.
2. **LLVM stages:** generate textual IR with `clang -S -emit-llvm`, assemble/disassemble with `llvm-as`/`llvm-dis`, and generate target assembly/object code. Assert semantics and stable structural properties, not byte-identical compiler output across versions.
3. **Cross runtime rebuilt from source:** use one cross toolchain for `sylib.c`, the example object, final static link, and QEMU execution.
4. **Supplied-archive audit:** run `readelf` and `llvm-nm`; surface `_impure_ptr` as a diagnostic rather than masking it with linker flags.
5. **Paper:** run XeLaTeX with `-halt-on-error`; verify nonzero page count, extractable text, and embedded fonts; upload the PDF and logs even when a later check fails.

Cross-runtime commands expected in the Linux job:

```sh
mkdir -p build

riscv64-linux-gnu-gcc -O2 -c lib/sylib.c -o build/sylib-riscv64.o
riscv64-linux-gnu-ar rcs build/libsysy-riscv64-linux.a build/sylib-riscv64.o
riscv64-linux-gnu-gcc -static build/example-riscv64.o \
  build/libsysy-riscv64-linux.a -o build/example-riscv64
printf '21\n' | qemu-riscv64 build/example-riscv64

aarch64-linux-gnu-gcc -O2 -c lib/sylib.c -o build/sylib-aarch64.o
aarch64-linux-gnu-ar rcs build/libsysy-aarch64-linux.a build/sylib-aarch64.o
aarch64-linux-gnu-gcc -static build/example-aarch64.o \
  build/libsysy-aarch64-linux.a -o build/example-aarch64
printf '21\n' | qemu-aarch64 build/example-aarch64
```

## 6. Remaining uncertainty and falsification conditions

The local environment did not contain Linux cross GCC/sysroots, so final glibc-linked RISC-V and AArch64 runtime execution was not reproduced locally. CI closes that gap only if it rebuilds the runtime and executes the final binaries under QEMU.

Revise the RISC-V incompatibility judgment if a documented toolchain can link the supplied archive into a final executable and run the common behavior corpus without unresolved `_impure_ptr` or ABI emulation. Revise the header judgment only after a client including `sylib.h` links cleanly with modern GCC defaults and the runtime library, without `-fcommon` or multiple-definition suppression.
