# Evidence notes: RV64G, ELF, linking, and loading

## Scope and decision purpose

These notes support a Chinese LLNCS survey that follows one small SysY/C program from generated RV64G assembly through a relocatable ELF object, static archive, linked executable, and Linux process image. The intended reader should be able to point at an instruction, directive, relocation, symbol, section, segment, or mapped page and explain why it exists. The notes therefore emphasize the contracts between stages rather than presenting assembly, ELF, the linker, and the loader as isolated topics.

**Evidence labels used below**

- **Normative:** stated by an ISA/ABI specification.
- **Implementation:** stated by upstream GNU/LLVM/Linux documentation or source.
- **Inference/recommendation:** a synthesis for the report, not a normative requirement.

The safest normative baseline is the ratified **RISC-V ABIs Specification v1.0** (November 2022), whose status page says that it is ratified and immutable. The continuously maintained psABI draft records newer implemented practice, but should be labeled as a development document when it is used. [RISC-V ABI v1.0 status](https://docs.riscv.org/reference/abi/v1.0/index.html), [current psABI](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/).

---

## 1. One continuous case-study spine

A useful case for the main survey is a function such as:

```c
int sum_positive(const int a[], int n) {
    int s = 0;
    for (int i = 0; i < n; ++i)
        if (a[i] > 0) s += a[i];
    return s;
}
```

called by `main`, with input/output supplied by the SysY runtime. It is intentionally ordinary: array addressing exposes byte scaling and loads; the `if` and `for` expose branches and labels; the helper exposes the ABI, prologue/epilogue, arguments and return value; the runtime call remains undefined in the application object and is later resolved from a static archive. A global or string literal may be added if the report needs a concrete `PCREL_HI20`/`PCREL_LO12` pair and `.rodata`. Floating-point should be treated as an optional extension because it makes the LP64D convention and `F`/`D` instructions visible, but it is not necessary to explain the binary pipeline.

Suggested artifact chain:

```text
case.c / case.s
  -> case.o (ET_REL: sections + symbols + relocations)
  +  libruntime.a (archive index + member objects)
  -> case.elf (ET_EXEC or ET_DYN: resolved addresses + program headers)
  -> execve + ELF interpreter (if dynamic)
  -> process image (PT_LOAD mappings, zero-filled tail, stack, entry point)
```

The key conceptual invariant is that **information is progressively committed**:

1. Assembly still names semantic objects (`sum_positive`, `.Lloop`, `putint`).
2. The assembler encodes everything locally decidable and emits relocation records for layout-dependent facts.
3. The static linker resolves the global symbol graph, chooses archive members, lays out output sections, computes addresses, applies relocations, and may relax instruction sequences.
4. The kernel and (for dynamically linked images) the dynamic linker interpret **segments**, not the compiler's source-level abstractions, to form the running image.

This spine avoids a misleading “four unrelated tools” presentation: every downstream stage consumes an explicit data structure produced by the upstream stage.

---

## 2. RV64G: what the target name promises

### 2.1 Composition

**Normative.** `RV64` selects the 64-bit base integer register state (`XLEN=64`). `G` is an abbreviation for `I M A F D Zicsr_Zifencei`: base integer, integer multiply/divide, atomics, IEEE-754 single- and double-precision floating point, CSR access, and instruction-fetch fence. It does **not** include compressed instructions; that target is conventionally `RV64GC`. [ISA naming convention](https://docs.riscv.org/reference/isa/unpriv/naming.html), [RV32/64G listing](https://docs.riscv.org/reference/isa/unpriv/rv-32-64g.html).

| Component | Role visible in a compiler case study |
|---|---|
| `I` / RV64I | integer ALU, branches/jumps, loads/stores, 64-bit registers and addresses |
| `M` | `mul`, `div`, `rem`; useful for arithmetic examples |
| `A` | `lr/sc` and AMOs; normally absent from a single-threaded SysY example |
| `F`, `D` | scalar floating point and separate `f0`–`f31` register file |
| `Zicsr` | CSR instructions; generally operating/runtime territory, not normal SysY code |
| `Zifencei` | instruction-stream synchronization after stores to code |

**Interpretive caution.** An ISA string says which instructions a binary may execute; an ABI name says how independently compiled units interoperate. For general RV64G software, the psABI recommends **LP64D**, but ISA and ABI are not synonyms: a toolchain may generate RV64G instructions under a soft-float LP64 ABI, or use LP64D while avoiding FP operations in a particular function. The psABI recommends LP64D for RV64G. [Current psABI, default ABIs](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_default_abis).

### 2.2 The RV64I facts that matter to a compiler reader

**Normative.** RV64I has 32 integer registers of width 64; `x0` always reads zero. Most integer operations use full `XLEN`. Instructions ending in `W` operate on the low 32 bits and sign-extend the 32-bit result to 64 bits. The compiler/ABI maintain a sign-extension invariant for 32-bit values, including unsigned 32-bit values, so `addw`/`addiw`, `subw`, and word shifts are semantically important when implementing SysY's 32-bit `int`. `lw` sign-extends a 32-bit memory value, `lwu` zero-extends it, and `ld` loads 64 bits. [RV64I specification](https://docs.riscv.org/reference/isa/unpriv/rv64.html).

This provides a high-value source-to-machine explanation:

- `int s += a[i]` will often use `lw` followed by `addw`, not merely the visually similar 64-bit `ld` and `add`.
- An array index is scaled by four for `int[]`, commonly via `slli index, index, 2`, then added to a 64-bit pointer.
- Signed comparisons use `slt`/signed branches; unsigned comparisons use `sltu`/unsigned branches. The language type, not just the bits, selects the comparison relation.
- RISC-V conditional branches compare registers and have no condition-code register. This makes the connection from an LLVM IR `icmp` plus `br` to either a fused branch or `slt` plus branch especially visible.

`AUIPC` adds a sign-extended upper immediate to the address of its own instruction. Paired with `ADDI`, a load/store, or `JALR`, it materializes PC-relative addresses or calls. This pairing is central to RISC-V relocations and relaxation; it is not incidental boilerplate. [RV64I specification](https://docs.riscv.org/reference/isa/unpriv/rv64.html).

### 2.3 Instructions versus assembler pseudoinstructions

**Normative/toolchain convention.** A pseudoinstruction is assembler syntax that expands to one or more real instructions, possibly with relocations. It is not a new hardware opcode. The RISC-V Assembly Programmer's Manual gives, among others: [pseudoinstruction table](https://github.com/riscv-non-isa/riscv-asm-manual/blob/main/src/asm-manual.adoc#-a-listing-of-standard-risc-v-pseudoinstructions)

| Pseudoinstruction | Typical base expansion | Why it matters |
|---|---|---|
| `nop` | `addi x0, x0, 0` | no architectural effect |
| `mv rd, rs` | `addi rd, rs, 0` | register copy |
| `li rd, imm` | one of many sequences | expansion depends on the constant and XLEN |
| `sext.w rd, rs` | `addiw rd, rs, 0` | restores the RV64 32-bit sign-extension invariant |
| `seqz rd, rs` | `sltiu rd, rs, 1` | materializes a Boolean |
| `j label` | `jal x0, label` | unconditional jump without a link |
| `ret` | `jalr x0, 0(ra)` | ABI return through `ra` |
| `call symbol` | `auipc ra, hi`; `jalr ra, lo(ra)` | long-range call plus `R_RISCV_CALL_PLT`, relaxable to `jal` |
| `tail symbol` | `auipc` + `jalr x0, ...` using a temporary | tail call without preserving a new return address |
| `la rd, symbol` | PC-relative pair or GOT access | expansion depends on PIC/non-PIC mode and symbol assumptions |

`li` must not be explained as always `lui`+`addi`: the manual deliberately calls its expansion “myriad sequences,” and a small immediate is one `addi` from `x0`. Likewise, `la` is not a fixed opcode; `.option pic` changes it to a GOT-based access for a preemptible global. This distinction makes a productive experiment: compare source assembly, `objdump -dr` on the object, and `objdump -d` on the executable.

---

## 3. psABI: the interprocedural contract

### 3.1 Integer register convention

**Normative.** The ratified psABI assigns the integer registers as follows. [psABI register convention](https://docs.riscv.org/reference/abi/v1.0/riscv-cc-registers.html)

| Registers | ABI names | Meaning | Preserved across calls? |
|---|---|---|---|
| `x0` | `zero` | immutable zero | n/a |
| `x1` | `ra` | return address | no |
| `x2` | `sp` | stack pointer | yes |
| `x3` | `gp` | global pointer; fixed/unallocatable | fixed |
| `x4` | `tp` | thread pointer; fixed/unallocatable | fixed |
| `x5`–`x7`, `x28`–`x31` | `t0`–`t6` | temporaries | no |
| `x8`–`x9`, `x18`–`x27` | `s0`–`s11` | saved registers | yes |
| `x10`–`x17` | `a0`–`a7` | arguments; `a0`–`a1` also returns | no |

The caller may assume only the callee-saved registers survive. A non-leaf function that needs its incoming `ra` later must therefore save it, normally in its stack frame. A leaf function need not spill `ra`; the absence of a prologue is not evidence that the ABI was ignored.

`gp` and `tp` are not spare temporaries. The standard ABI says procedures should not modify them. If a platform dedicates `gp` to another platform purpose, its ABI must document that choice and toolchain global-pointer relaxation must be disabled. [Current psABI register convention](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_integer_register_convention).

### 3.2 Arguments, results, aggregates, and the stack

**Normative.** The base integer convention provides eight argument registers `a0`–`a7`; `a0` and `a1` are also return registers. Scalars no wider than XLEN use one register when available and otherwise the stack. A 2×XLEN scalar uses a register pair or the stack under the detailed exhaustion rule. Aggregates up to XLEN or 2×XLEN can use one or two registers; larger aggregates are passed by reference. Returns follow the rules for a first named argument of the same type; a large returned object uses caller-provided storage passed as an implicit first argument. [Ratified procedure calling convention](https://docs.riscv.org/reference/abi/v1.0/riscv-cc-procedure-calling-convention.html).

For LP64D, named floating-point values use `fa0`–`fa7` when eligible, with the first two also used for returns. The floating callee-saved registers `fs0`–`fs11` are preserved only for values no wider than ABI_FLEN. Variadic arguments follow the integer rules, an important counterexample to the oversimplification “floats always go in `fa` registers.” [Current psABI floating-point convention](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_hardware_floating_point_calling_convention).

**Normative stack facts:**

- the stack grows toward lower addresses;
- `sp` is aligned to 128 bits (16 bytes) on procedure entry and remains aligned throughout a standard-ABI procedure;
- the first stack-passed argument starts at offset zero from the entry `sp`;
- code must not rely on data below `sp` persisting (there is no x86-64-style red zone);
- a frame pointer is optional; if used, it is `s0`/`x8` and remains callee-saved.

With a conventional frame record, the frame pointer points at the canonical frame address (the `sp` on entry); on RV64 the saved return address is at `fp-8` and the previous frame pointer at `fp-16`. Platforms may allow omitting the frame chain, so optimized code should be interpreted using DWARF call-frame information rather than assuming every function has this exact pattern. [Frame-pointer convention](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_frame_pointer_convention).

### 3.3 What a case-study prologue actually proves

For a non-leaf function that uses `s0` and calls `putint`, a plausible unoptimized pattern is:

```asm
addi sp, sp, -16
sd   ra, 8(sp)
sd   s0, 0(sp)
addi s0, sp, 16
    # body, a0 holds first argument/result
ld   s0, 0(sp)
ld   ra, 8(sp)
addi sp, sp, 16
ret
```

**Inference.** Each line should be explained as satisfying an invariant, not as mandatory syntax. An optimizer may omit `s0`, keep locals in registers, choose a larger aligned frame, shrink-wrap saves, or inline the callee. The durable contract is preservation, arguments/results, and stack alignment—not the visual prologue template.

---

## 4. Assembly directives: metadata and object construction

Assembler directives do not execute on the processor. They tell the assembler how to construct sections, data, symbols, alignment, and target metadata.

The upstream assembly manual lists the portable core relevant to the case study: [RISC-V directives](https://github.com/riscv-non-isa/riscv-asm-manual/blob/main/src/asm-manual.adoc#pseudo-ops).

| Directive family | Object-level effect |
|---|---|
| `.text`, `.data`, `.rodata`, `.bss`, `.section` | select/create an input section |
| `.globl sym`, `.local sym` | set symbol binding/scope |
| `.type sym,@function` / `@object` | classify symbol for ELF tools/linker |
| `.size sym, .-sym` | record the entity size |
| `.align`, `.p2align`, `.balign` | insert/request alignment padding |
| `.byte`, `.half`, `.word`, `.dword`, `.quad` | emit fixed-width data |
| `.string` / `.asciz` | emit a nul-terminated string |
| `.zero n` | emit/declare zero bytes |
| `.comm name,size,align` | create a common symbol |
| `.equ name,value` | define an assembler constant |
| `.option pic` / `nopic` | change address-materialization expansion |
| `.option relax` / `norelax` | enable/disable relaxation annotations for a region |
| `.attribute` | record RISC-V compatibility attributes |
| `.cfi_*` (GNU syntax) | describe stack unwinding in DWARF CFI; not CPU instructions |

RISC-V's `.align n` means power-of-two alignment (`.p2align n`), so `.align 2` means four-byte alignment. Because `.align` semantics vary across architectures, the RISC-V manual recommends explicit `.p2align` or `.balign`. [Alignment directive](https://github.com/riscv-non-isa/riscv-asm-manual/blob/main/src/asm-manual.adoc#align).

**Relaxation-specific subtlety.** In a relaxable region, the assembler emits `R_RISCV_RELAX` and, when necessary, `R_RISCV_ALIGN`. The latter lets the linker delete some padding after earlier instructions shrink while preserving the later alignment. Therefore an object-file disassembly can contain apparently redundant NOPs whose final count is not known until link time. [psABI ELF object files](https://docs.riscv.org/reference/abi/riscv-elf-object-files.html), [assembly `.option relax`](https://github.com/riscv-non-isa/riscv-asm-manual/blob/main/src/asm-manual.adoc#relaxnorelax).

Recommended annotated function skeleton:

```asm
.section .text
.p2align 2
.globl sum_positive
.type sum_positive, @function
sum_positive:
    # body
.Lend:
    ret
.size sum_positive, .-sum_positive
```

`.Lend` is conventionally local and may disappear from a stripped final symbol table; `.globl` makes `sum_positive` available for cross-object resolution; `.type` and `.size` make tools report a function extent rather than merely a numeric label.

---

## 5. ELF as two related views of one file

### 5.1 File types and the crucial section/segment distinction

ELF's header field `e_type` distinguishes at least `ET_REL` (relocatable object), `ET_EXEC` (executable), and `ET_DYN` (shared object or position-independent executable). The same broad container is used at different commitment points in the pipeline.

**Normative.** A section-header table organizes the file for linking and analysis. A program-header table describes segments needed to create a process image. Program headers are meaningful for executables and shared objects, not ordinary relocatable objects. A segment may contain multiple sections, and the loader does not need the conceptual section boundaries to map it. [gABI sections](https://gabi.xinuos.com/elf/03-sheader.html), [gABI program loading](https://gabi.xinuos.com/elf/07-pheader.html).

```text
link-editor view                         loader view
----------------                         -----------
.text  .rodata  .symtab .rela.text  ---> PT_LOAD R-X
.data  .bss     .got    .dynamic    ---> PT_LOAD RW-
                                         PT_DYNAMIC, PT_INTERP, PT_TLS, ...
```

This is the most important correction to a common textbook shortcut: the OS does not generally “load the `.text` section and then the `.data` section.” It maps `PT_LOAD` segments. Section headers can be stripped from a working executable; program headers cannot be omitted if they are needed to construct its image.

### 5.2 Sections and their contracts

Each section header records name, type, flags, address, file offset, size, links to related sections, alignment, and entry size. `SHT_NOBITS` is special: it may have nonzero in-memory size but occupies no bytes in the file. This is why `.bss` consumes memory without bloating the executable. [gABI section header](https://gabi.xinuos.com/elf/03-sheader.html#section-header-table-entry).

Common sections for the report:

| Section | Purpose / caveat |
|---|---|
| `.text` | machine instructions, normally allocatable + executable |
| `.rodata` | immutable constants, normally allocatable + read-only |
| `.data` | initialized writable objects |
| `.bss` | zero-initialized/uninitialized storage, `SHT_NOBITS` |
| `.symtab` + `.strtab` | full link/debug symbol table and its names; often stripped |
| `.dynsym` + `.dynstr` | runtime-visible dynamic symbols and names |
| `.rela.text`, `.rela.data`, ... | relocations for a corresponding input section |
| `.riscv.attributes` | target architecture/stack/other compatibility metadata |
| `.debug_*` | DWARF debug data, generally not allocated into the process image |
| `.eh_frame` | unwind records, potentially runtime-relevant |
| `.got`, `.plt` | indirection structures for position-independent/dynamic linking |

The current RISC-V psABI defines ELF compatibility fields such as `EF_RISCV_RVC` and floating ABI flags, and attributes including `Tag_RISCV_stack_align` and `Tag_RISCV_arch`. A linker should reject incompatible float ABI/RVE inputs. This is a binary-level reason not to mix arbitrary `.o` files merely because all say “RISC-V.” [RISC-V ELF object files](https://docs.riscv.org/reference/abi/riscv-elf-object-files.html), [current psABI attributes](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_attributes).

### 5.3 Symbol tables

**Normative.** An ELF symbol entry contains a name index, value, size, binding/type (`st_info`), visibility (`st_other`), and defining section index (`st_shndx`). `SHN_UNDEF` marks an unresolved reference, `SHN_ABS` an absolute symbol, and `SHN_COMMON` unallocated common storage. [gABI symbol table](https://gabi.xinuos.com/elf/05-symtab.html).

Bindings and key resolution rules:

- `STB_LOCAL`: visible only inside its object; same-named locals in other objects do not collide.
- `STB_GLOBAL`: visible across combined objects; one definition can satisfy another object's undefined reference; duplicate global definitions are normally errors.
- `STB_WEAK`: lower precedence than a global definition; an unresolved weak reference has value zero.
- An archive member is extracted to satisfy an undefined **global** symbol; an undefined weak reference by itself does not cause extraction.

Types include `STT_OBJECT`, `STT_FUNC`, `STT_SECTION`, `STT_FILE`, `STT_COMMON`, and `STT_TLS`. Type and binding are different axes: “global function” is `STB_GLOBAL + STT_FUNC`, not one combined category. Visibility adds a third axis (`DEFAULT`, `HIDDEN`, `PROTECTED`, etc.). [gABI bindings and types](https://gabi.xinuos.com/elf/05-symtab.html#symbol-binding).

### 5.4 Relocation as a deferred expression

**Normative.** Relocation connects symbolic references to definitions. `Elf64_Rela` records:

- `r_offset`: where the result is applied (a section-relative offset in `ET_REL`, a virtual address in an executable/shared object);
- `r_info`: symbol-table index plus processor-specific relocation type;
- `r_addend`: explicit constant addend.

The conceptual calculation uses a symbol value and addend, applies the operation encoded by the relocation type, and writes the appropriate bit field. [gABI relocation](https://gabi.xinuos.com/elf/06-reloc.html).

The RISC-V psABI names useful variables `S` (symbol value), `A` (addend), `P` (place), `B` (loaded object base), `G` (GOT entry offset), and `GOT` (GOT address). Common case-study relocations are: [RISC-V relocation table](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_relocations)

| Relocation | Expression / role |
|---|---|
| `R_RISCV_64` | write `S + A` as 64 bits |
| `R_RISCV_BRANCH` | encode `S + A - P` into a B-type immediate |
| `R_RISCV_JAL` | encode `S + A - P` into a J-type immediate |
| `R_RISCV_CALL_PLT` | PC-relative `AUIPC+JALR` call sequence; the older `CALL` is deprecated |
| `R_RISCV_PCREL_HI20` | upper part of `S + A - P` for `AUIPC` |
| `R_RISCV_PCREL_LO12_I/S` | lower part tied to the corresponding high relocation |
| `R_RISCV_HI20` + `LO12_I/S` | split absolute address |
| `R_RISCV_GOT_HI20` | PC-relative access to a GOT entry |
| `R_RISCV_RELATIVE` | dynamic relocation `B + A` |
| `R_RISCV_JUMP_SLOT` | dynamic resolution of a PLT-associated function |
| `R_RISCV_RELAX` | annotation that a colocated normal relocation is relaxable |

**Subtle but important:** the low relocation in a PC-relative pair refers to a label at the high relocation, not simply the final target symbol. This allows the linker to recover the exact `P` used by the high calculation. Assembly such as:

```asm
.Laddr:
    auipc a0, %pcrel_hi(global)
    addi  a0, a0, %pcrel_lo(.Laddr)
```

should therefore be read as one semantic address construction split across two instruction encodings and two related relocation records.

---

## 6. Static archives and symbol resolution

### 6.1 An archive is not a prelinked object

**Implementation.** GNU `ar` describes an archive as a container of member files. With the `s` modifier it stores an index of symbols defined by relocatable members; this accelerates linking. `ranlib` can add the index, and `nm -s`/`nm --print-armap` displays it. A thin archive stores references to external member files rather than copying all member contents, so it is not self-contained. [GNU `ar`](https://sourceware.org/binutils/docs/binutils.html#ar), [LLVM `ar`](https://llvm.org/docs/CommandGuide/llvm-ar.html).

Thus `libruntime.a` should be described as “a searchable bag of `.o` members plus an index,” not as a merged library image. This distinction explains why unused runtime functions normally do not enter the executable.

### 6.2 Demand-driven extraction and order sensitivity

**Implementation.** GNU `ld` normally searches an archive once, at its command-line position. It extracts members defining currently unresolved symbols introduced by objects already seen. A reference introduced by an object appearing later does not make the linker automatically go backward and rescan. [GNU `ld` archive behavior](https://sourceware.org/binutils/docs/ld.html).

Conceptual algorithm (simplified but useful):

```text
U := set of unresolved strong globals; D := definitions already selected
scan command-line inputs left-to-right:
  ordinary object: add all of it; update D and U
  archive: repeatedly select a member whose definition satisfies U,
           updating D/U, until that archive yields no new member
finish: diagnose remaining non-weak U; diagnose conflicting strong D
```

Consequences suitable for an experiment:

```sh
# Usually works: main.o first creates the unresolved runtime symbols.
clang ... main.o -L. -lsysy -o case.elf

# May fail for a static archive: archive is scanned before main.o needs it.
clang ... -L. -lsysy main.o -o case.elf
```

Circular archive dependencies can be handled with `--start-group ... --end-group`, which repeatedly searches the group until no new unresolved references arise, but GNU documents a significant performance cost. `--whole-archive` instead includes every member and should be scoped with `--no-whole-archive`; it is not the normal fix for ordering errors. [GNU ld group option](https://sourceware.org/binutils/docs/ld/Options.html).

**Resolution precedence.** The gABI specifies that a global definition overrides same-named weak definitions; multiple ordinary global definitions are not allowed; an unresolved weak symbol evaluates to zero. Modern GCC defaults (`-fno-common`) mean tentative C definitions are commonly emitted as regular `.bss` definitions rather than `SHN_COMMON`, so reports should verify actual symbols rather than repeat historic “common symbol” folklore.

---

## 7. Linker work: resolution, layout, relocation, relaxation

### 7.1 A dependency order, not merely a list

A static link can be understood as an iterative dependency problem:

1. Parse input object/archive metadata and check target compatibility.
2. Resolve symbols and extract archive members.
3. Select live input sections (if garbage collection is enabled) and merge/map them into output sections.
4. Assign output addresses and file offsets under a linker script.
5. Create synthetic structures/symbols as needed (GOT, PLT, dynamic table, start/stop symbols, etc.).
6. Evaluate relocations; perform target-specific relaxations; update layout if code shrinks.
7. Emit ELF/program headers, output sections, and optional map/debug information.

Real linkers interleave some steps, but the dependency arrows matter: relaxation needs near-final symbol distances, while relaxation itself changes later addresses.

### 7.2 Layout and linker scripts

**Implementation.** GNU `ld` always uses a linker script; absent `-T`, it uses a built-in default visible with `--verbose`. `SECTIONS` maps input sections to output sections and places them; `MEMORY` models allowed target regions; `PHDRS` controls ELF program headers/segments. [GNU linker scripts](https://sourceware.org/binutils/docs/ld/Scripts.html), [`SECTIONS`](https://sourceware.org/binutils/docs/ld/SECTIONS.html), [`PHDRS`](https://sourceware.org/binutils/docs/ld.html#PHDRS-Command).

For a hosted Linux case study, use the driver and default script, then inspect it; do not replace the platform runtime accidentally by invoking `ld` directly. For a bare-metal extension, a small explicit script is educational:

```ld
MEMORY { ram (rwx) : ORIGIN = 0x80000000, LENGTH = 128M }
SECTIONS {
  .text   : { *(.text .text.*) } > ram
  .rodata : { *(.rodata .rodata.*) } > ram
  .data   : { *(.data .data.*) } > ram
  .bss    : { *(.bss .bss.*) *(COMMON) } > ram
}
```

But this is not a Linux process startup script: it omits the C runtime entry, dynamic metadata, TLS, unwind tables, and platform program-header conventions. Label it as a reduced model rather than a drop-in production replacement.

### 7.3 RISC-V linker relaxation

**Normative.** Linker relaxation simplifies sequences once final placement removes the conservative assumptions made by the compiler/assembler. It is permitted only when an `R_RISCV_RELAX` relocation accompanies a candidate relocation. Related relocations form a group and must be transformed consistently. Because relaxation may delete bytes, code generators must emit relocations needed to repair references affected by the changing layout. [psABI linker relaxation](https://docs.riscv.org/reference/abi/riscv-elf-linker-relaxation.html).

Canonical case:

```asm
# relocatable object, potentially any 32-bit PC-relative call distance
auipc ra, 0        # R_RISCV_CALL_PLT(symbol), R_RISCV_RELAX
jalr  ra, ra, 0

# linked image when target/PLT is in JAL range
jal   ra, symbol
```

The psABI gives the `JAL` reach as roughly ±1 MiB and allows this two-instruction pair to become one. Other relaxations include address/load-store sequences, TLS models, global-pointer addressing, compressed instructions when supported, and alignment padding deletion. The exact set implemented is linker/version dependent; the psABI explicitly permits an implementation to support only part of the relaxation repertoire.

**Evidence strength and caution.** An early RISC-V toolchain tutorial reported about a 7% Linux code-size reduction from relaxation, but that is an old workload/toolchain-specific slide result, not a universal expectation. Use it only as historical motivation, not a promised figure. [2015 RISC-V software ecosystem tutorial](https://riscv.org/wp-content/uploads/2015/02/riscv-software-toolchain-tutorial-hpca2015.pdf).

High-value controlled comparison:

```sh
clang --target=riscv64-linux-gnu -march=rv64g -mabi=lp64d -O1 -c case.c -o case.o
clang --target=riscv64-linux-gnu -fuse-ld=lld case.o ... -Wl,-Map=relax.map -o relax.elf
clang --target=riscv64-linux-gnu -fuse-ld=lld case.o ... -Wl,--no-relax,-Map=norelax.map -o norelax.elf
llvm-objdump -dr case.o
llvm-objdump -d relax.elf
llvm-objdump -d norelax.elf
llvm-size relax.elf norelax.elf
```

Record exact compiler/linker versions: support differs across GNU `ld` and LLD releases. LLVM currently documents RISC-V as a production-quality LLD target and describes its global-pointer relaxation constraints. [LLD overview](https://lld.llvm.org/), [LLVM RISC-V target guide](https://llvm.org/docs/RISCVUsage.html).

---

## 8. From final ELF to a process image

### 8.1 Program headers are the loader contract

**Normative.** Each `Elf64_Phdr` gives a segment type, file offset, virtual address, file and memory sizes, flags, and alignment. For `PT_LOAD`, bytes `[0, p_filesz)` come from the file and the tail up to `p_memsz` is zero-filled. Loadable segments are ordered by virtual address. `p_vaddr` and `p_offset` must be congruent modulo the required alignment/page size. [gABI program header](https://gabi.xinuos.com/elf/07-pheader.html).

Important types:

| Program header | Meaning |
|---|---|
| `PT_LOAD` | bytes/pages mapped into memory with R/W/X flags |
| `PT_INTERP` | path of dynamic program interpreter |
| `PT_DYNAMIC` | dynamic-linking metadata |
| `PT_PHDR` | the program-header table itself in the image |
| `PT_TLS` | thread-local-storage initialization template |
| `PT_NOTE` | auxiliary/vendor notes |
| `PT_GNU_STACK` (Linux extension) | requested stack executability |
| `PT_GNU_RELRO` (GNU/Linux extension) | region made read-only after relocations |

The ordinary explanation of `.bss` now becomes exact: `.bss` is `SHT_NOBITS`, generally placed at the end of a writable `PT_LOAD`; the segment's `p_memsz > p_filesz` tail becomes zero-filled memory.

### 8.2 `execve`, interpreter, and entry

**Linux implementation/documentation.** A successful `execve` replaces the current process image with the new program's initialized/uninitialized data, heap, stack, and text; it does not create a second process. For a dynamically linked ELF executable, Linux uses the `PT_INTERP` pathname to invoke the ELF interpreter. [Linux `execve(2)`](https://man7.org/linux/man-pages/man2/execve.2.html), [Linux `elf(5)`](https://man7.org/linux/man-pages/man5/elf.5.html).

**Normative gABI.** The system loader and dynamic linker cooperate: the interpreter maps required shared objects, performs necessary dynamic relocations/symbol resolution, runs initialization machinery, and transfers control to the program. [gABI dynamic linking](https://gabi.xinuos.com/elf/08-dynamic.html).

The ELF entry `e_entry` normally names `_start`, not C `main`. Startup code receives the initial machine state, arranges libc/runtime initialization, calls `main`, and converts its return into process termination. Therefore “the loader calls `main`” is a pedagogical shortcut and should be corrected in a deep survey.

**Static versus dynamic distinction:**

- A fully static executable has no runtime dependency on a shared-object resolver for ordinary external calls; static-link relocations were already committed.
- A dynamically linked executable retains dynamic metadata and relocations. Function calls may pass through a PLT/GOT mechanism and may be bound eagerly or lazily depending on platform/link options.
- Position-independent `ET_DYN` executables (PIE) have a load base chosen at runtime; `R_RISCV_RELATIVE` computes `B+A` without a symbol lookup.

Do not conflate kernel loading with dynamic linking. The kernel recognizes/maps the ELF and interpreter; user-space dynamic linker code performs shared-library resolution and most dynamic relocations.

---

## 9. Reproducible artifact inspection checklist

Prefer the compiler driver for the final link because it supplies startup objects, default libraries, sysroot, ABI, and linker options. Clang's cross-compilation guide stresses the target triple, CPU/architecture, ABI, and sysroot/toolchain. [Clang cross compilation](https://clang.llvm.org/docs/CrossCompilation.html).

Illustrative commands (adjust sysroot/runtime paths to the actual environment):

```sh
# Show driver decisions rather than guessing hidden startup/link inputs.
clang --target=riscv64-linux-gnu -march=rv64g -mabi=lp64d -### case.c

# Preserve and inspect assembly/object boundaries.
clang --target=riscv64-linux-gnu -march=rv64g -mabi=lp64d -O0 -S case.c -o case.O0.s
clang --target=riscv64-linux-gnu -march=rv64g -mabi=lp64d -O2 -S case.c -o case.O2.s
clang --target=riscv64-linux-gnu -march=rv64g -mabi=lp64d -c case.O0.s -o case.o

# ELF identity, sections, symbols, and relocations of ET_REL.
llvm-readelf -h -S -s -r -A case.o
llvm-objdump -dr --no-show-raw-insn case.o
llvm-nm -n case.o

# Static archive contents and index.
llvm-ar t libruntime.a
llvm-nm -s libruntime.a

# Link using a compiler driver; ask the linker for an auditable map.
clang --target=riscv64-linux-gnu -march=rv64g -mabi=lp64d \
  -fuse-ld=lld case.o path/to/libruntime.a -Wl,-Map=case.map -o case.elf

# Final image: headers, segment mapping, dynamic dependencies, symbols.
llvm-readelf -h -S -l -s -r -d -A case.elf
llvm-objdump -d --source --line-numbers case.elf
llvm-size -A case.o case.elf
```

LLVM documents `llvm-readelf -h/-S/-l/-s/-r` for file header, sections, program headers, symbols, and relocations, while `llvm-objdump -d` disassembles executable sections. [llvm-readelf](https://llvm.org/docs/CommandGuide/llvm-readelf.html), [llvm-objdump](https://llvm.org/docs/CommandGuide/llvm-objdump.html). GNU `readelf` is deliberately independent of BFD and is useful as a second parser when investigating tool bugs. [GNU readelf](https://sourceware.org/binutils/docs/binutils/readelf.html).

Artifact questions that force real understanding:

| Artifact | Question | Expected evidence |
|---|---|---|
| `.s` | Which spellings are pseudo-ops? | expand with object disassembly |
| `.o` | Why are immediates zero/partial? | corresponding `.rela.*` record |
| `.o` | Is `putint` defined? | `UND GLOBAL` symbol plus call relocation |
| `.a` | Which member supplies it? | archive index and member symbol table |
| map file | Which input section/member survived? | output section contribution lines |
| final ELF | Did `AUIPC+JALR` shrink? | linked disassembly vs relocatable object |
| final ELF | Which bytes reach memory? | `readelf -l` section-to-segment map |
| process | Where was it mapped? | `/proc/$pid/maps` or debugger mappings |

For runtime validation on a non-RISC-V host, a Linux-user QEMU command is commonly `qemu-riscv64 -L <riscv-sysroot> ./case.elf` for a dynamically linked binary or `qemu-riscv64 ./case-static.elf` for an appropriately static binary. Treat QEMU as an execution environment, not as evidence about the static ELF structure; validate output separately from artifact inspection.

---

## 10. Strong interpretations, caveats, and likely report pitfalls

1. **The ABI, not visual register choice, is the real function boundary.** Optimization can radically change allocation, frames, and instruction selection while retaining the same externally observable ABI.
2. **Assembly is not yet final machine code when symbols cross section/object boundaries.** The bytes and relocation records together are the assembler's complete answer.
3. **A relocation is typed semantic metadata, not merely “an address hole.”** RISC-V's split, packed immediates require relocation types that understand U/I/S/B/J encodings and paired sequences.
4. **Archives are lazy.** A static library's unused members are not linked just because the `.a` appears on the command line; order and unresolved-symbol state control extraction.
5. **Linking is whole-image reasoning without necessarily being whole-program compilation.** The linker knows final placement and symbol graph, enabling relaxation, but usually lacks the source/IR semantics available to an LTO optimizer.
6. **Sections are not segments.** Sections serve link/edit/debug organization; segments are the execution mapping contract.
7. **`main` is not the ELF entry.** `_start`/runtime startup mediates between the loader's machine state and the language-level function.
8. **RV64G is not RV64GC.** If disassembly contains 16-bit `c.*` instructions, either `C` was enabled in the actual architecture or the build metadata/tool invocation needs explanation.
9. **Do not infer the target solely from a disassembler's chosen aliases.** Use the ELF header/attributes and exact `-march/-mabi`, and optionally request non-alias disassembly when checking real opcodes.
10. **Do not invoke `ld` directly for the main hosted build unless the exercise is specifically about reconstructing startup.** The compiler driver is the production interface; use `-###`/verbose modes and map files to make its work inspectable.

### What would falsify or revise these notes?

- A different execution environment (bare metal, an educational emulator, Linux with musl/glibc, or another OS) changes startup objects, system-call ABI, interpreter path, and default layout without changing the core ISA/psABI rules.
- A different ABI (`LP64` soft-float versus `LP64D`) changes floating argument preservation/passing and ELF flags.
- Tool versions differ in supported relaxations and printed aliases. Keep command output and version strings with the experiment.
- Link-time optimization replaces ordinary ELF object contents with IR/plugin-mediated inputs for part of the link; the final ELF claims remain valid but the intermediate account needs an LTO branch.

---

## 11. Academic context

Andrew Waterman's dissertation documents the design rationale for a small base ISA plus optional extensions and evaluates the compressed extension; it is useful for explaining why RISC-V exposes a regular compiler target rather than for normative encoding details. [Waterman, *Design of the RISC-V Instruction Set Architecture*, UC Berkeley, 2016](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/EECS-2016-1.html).

Celio et al. compare RV64G/RV64GC with other ISAs on SPEC CPU2006 and argue that compressed instructions plus macro-op fusion can preserve a simple ISA while improving code density. This is relevant background, but its benchmark suite and modeled microarchitectural assumptions do not prove that a particular SysY binary or modern core will see the same outcome. It is a Berkeley technical report/CoRR preprint, not a peer-reviewed architecture-conference result. [Celio et al., “The Renewed Case for the Reduced Instruction Set Computer,” 2016](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/EECS-2016-130.html).

John Levine's *Linkers & Loaders* remains a useful conceptual reference for symbol resolution, relocation, static libraries, and loading, but predates RISC-V, PIE-by-default distributions, modern LTO, and today's LLD; use the current gABI/psABI and linker manuals for precise behavior. [Levine, Morgan Kaufmann, 2000](https://linker.iecc.com/).

---

## 12. BibTeX-ready source metadata

```bibtex
@manual{riscv-unpriv-2026,
  title        = {The RISC-V Instruction Set Manual, Volume I: Unprivileged Architecture},
  organization = {RISC-V International},
  year         = {2026},
  month        = jan,
  note         = {Release 20260120},
  url          = {https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf}
}

@manual{riscv-psabi-1,
  title        = {RISC-V ABIs Specification},
  editor       = {Cheng, Kito and Clarke, Jessica},
  organization = {RISC-V International},
  year         = {2022},
  month        = nov,
  version      = {1.0},
  note         = {Ratified},
  url          = {https://docs.riscv.org/reference/abi/v1.0/index.html}
}

@manual{riscv-asm-manual,
  title        = {RISC-V Assembly Programmer's Manual},
  organization = {RISC-V International},
  note         = {Living upstream manual; access date 2026-09-22},
  url          = {https://github.com/riscv-non-isa/riscv-asm-manual}
}

@manual{sysv-gabi-elf-4-3,
  title        = {System V Application Binary Interface: ELF Object File Format},
  organization = {Xinuos},
  version      = {4.3 Draft},
  year         = {2025},
  url          = {https://gabi.xinuos.com/elf.pdf}
}

@manual{gnu-binutils-2-47,
  title        = {GNU Binary Utilities},
  organization = {Free Software Foundation},
  version      = {2.47},
  year         = {2026},
  url          = {https://sourceware.org/binutils/docs/binutils.html}
}

@manual{gnu-ld-2-47,
  title        = {The GNU Linker},
  organization = {Free Software Foundation},
  version      = {2.47},
  year         = {2026},
  url          = {https://sourceware.org/binutils/docs/ld.html}
}

@manual{llvm-riscv-usage,
  title        = {User Guide for RISC-V Target},
  organization = {LLVM Project},
  note         = {Living documentation; access date 2026-09-22},
  url          = {https://llvm.org/docs/RISCVUsage.html}
}

@manual{llvm-lld,
  title        = {LLD -- The LLVM Linker},
  organization = {LLVM Project},
  note         = {Living documentation; access date 2026-09-22},
  url          = {https://lld.llvm.org/}
}

@manual{linux-man-pages-execve,
  title        = {execve(2) -- Linux Manual Page},
  author       = {Kerrisk, Michael and Linux man-pages contributors},
  organization = {Linux man-pages project},
  note         = {Access date 2026-09-22},
  url          = {https://man7.org/linux/man-pages/man2/execve.2.html}
}

@phdthesis{waterman2016riscv,
  author = {Waterman, Andrew},
  title  = {Design of the RISC-V Instruction Set Architecture},
  school = {University of California, Berkeley},
  year   = {2016},
  month  = jan,
  number = {UCB/EECS-2016-1},
  url    = {https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/EECS-2016-1.html}
}

@article{celio2017renewed,
  author  = {Celio, Christopher and Dabbelt, Palmer and Patterson, David A. and Asanovi\'c, Krste},
  title   = {The Renewed Case for the Reduced Instruction Set Computer: Avoiding ISA Bloat with Macro-Op Fusion for RISC-V},
  journal = {Technical Report UCB/EECS-2016-130, EECS Department, University of California, Berkeley},
  year    = {2016},
  doi     = {10.48550/arXiv.1607.02318},
  url     = {https://arxiv.org/abs/1607.02318}
}

@book{levine2000linkers,
  author    = {Levine, John R.},
  title     = {Linkers and Loaders},
  publisher = {Morgan Kaufmann},
  year      = {2000},
  isbn      = {978-1-55860-496-4},
  url       = {https://linker.iecc.com/}
}
```
