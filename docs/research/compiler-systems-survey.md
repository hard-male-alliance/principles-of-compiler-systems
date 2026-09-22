# Research Notes for *Understanding Compiler Systems*: One Program Across the Entire Toolchain

**Purpose.** This document is the external evidence base and explanatory plan for a survey-style LNCS paper. It deliberately uses one small but structurally rich C program to connect preprocessing, lexical structure, typed syntax, LLVM IR, optimization, target lowering, RV64 machine conventions, ELF object construction, static linking, and loading. It is not a laboratory infrastructure report.

**Research cut-off.** 2026-09-22 (Asia/Singapore).

**Bibliography.** Candidate BibTeX entries are in `compiler-systems-survey.bib`; bracketed keys below refer to those entries.

## 1. Problem definition and evidential discipline

### 1.1 Research object

The paper should answer a single question:

> When one source-level fact passes through a contemporary compiler system, where is that fact preserved, where is it made explicit, where is it encoded only by convention, and where does it disappear because it is no longer needed?

This formulation prevents the paper from becoming a list of commands. The compiler is treated as a sequence of representations with contracts between them, not as a black box and not as a collection of unrelated tools. The official Clang documentation presents preprocessing, parsing and semantic analysis, IR generation, target code generation, assembly, and linking as logical stages; it also warns that stages may be fused in one process [clang-toolchain-2026, clang-command-2026]. Therefore, an emitted `.i`, `.ll`, or `.s` file is an **observation point**, not proof that a separately named operating-system process necessarily ran.

### 1.2 Scope boundary

Included:

1. one factorial program, examined at deliberately chosen observation points;
2. the relation between adjacent representations;
3. both unoptimized and optimized LLVM IR, because they answer different questions;
4. RV64 assembly under an explicitly named ISA and ABI;
5. ELF relocatable objects, symbol resolution, relocation, a statically linked executable, and loading;
6. MLIR progressive lowering as a forward-looking extension of the same representation-centered idea.

Excluded:

- multiple near-duplicate examples;
- CI, CMake, test orchestration, or repository mechanics;
- a `libsysy` implementation or compatibility audit;
- claims about accelerator execution that are not demonstrated;
- presenting version-sensitive instruction sequences as universal compiler truths.

### 1.3 Evidence labels

| Label | Meaning | How it may be written in the paper |
|---|---|---|
| **[S] Specified** | Required or defined by a language, ISA, ABI, or object-format specification. | “The ABI requires …” |
| **[D] Documented** | Stated by upstream LLVM/Clang/MLIR or Linux documentation. | “Clang documents …” |
| **[E] Expected observation** | Mechanistically predicted for the chosen source and flags, but exact output must be checked against the pinned tool version. | “A typical LLVM 23 build emits …” |
| **[I] Interpretation** | A pedagogical or causal explanation connecting artifacts. | “This makes the source-level update visible as …” |

The final paper should replace **[E]** with direct artifact evidence wherever the experiment is actually executed. In particular, exact basic-block names, register allocation, instruction order, and relocation spelling are not stable interfaces.

## 2. The single running example

```c
#define FACT_N 6U

unsigned long factorial(unsigned n) {
    unsigned long acc = 1UL;
    while (n > 1U) {
        acc *= n;
        --n;
    }
    return acc;
}

int main(void) {
    return factorial(FACT_N) != 720UL;
}
```

### 2.1 Why this example is the right size

This source is small enough that every artifact can be printed, but it is not vacuous:

- `#define` creates a visible preprocessing transformation.
- Identifiers, literal suffixes, punctuation, and keywords expose token classes.
- The loop and compound assignment produce a meaningful typed AST and control-flow graph.
- `unsigned` and `unsigned long` force a semantically significant width conversion.
- Two loop-carried variables (`n` and `acc`) produce a compact SSA example with two φ nodes.
- `factorial` is a real call boundary, so instruction selection and the RV64 calling convention are observable.
- The exported `factorial` and `main` definitions become ELF symbols.
- A known input makes interprocedural constant propagation and inlining visible at `-O2`.
- The process exit status is sufficient to check behavior without importing a large I/O subsystem into the case study.

The key design choice is that `factorial` has external linkage rather than `static`. Without link-time optimization, the compiler must normally retain a callable definition for other translation units even if `main` is optimized to `return 0`. This gives one artifact in which the public function body survives while the particular call from `main` may disappear.

### 2.2 Semantic facts to track

| Source fact | Early representation | Middle representation | Late representation |
|---|---|---|---|
| `FACT_N` is a macro | preprocessing identifier and replacement list | only literal `6U` remains | immediate constant or no code after folding |
| `n` is `unsigned` | typed AST node | `i32`, unsigned comparison predicate, zero-extension | 32-bit value discipline in RV64 registers; unsigned branch idiom |
| `acc` is `unsigned long` | typed declaration | `i64` SSA value on LP64 | 64-bit register value and `mul` on an ISA with M |
| loop repeats while `n > 1` | `WhileStmt` | CFG back edge plus φ nodes and conditional branch | branch and backward control transfer, unless transformed |
| `acc *= n` | compound assignment plus implicit cast | `zext i32` followed by `mul i64` | width preparation plus machine multiply |
| call `factorial(6)` | `CallExpr` | LLVM `call`, unless inlined/folded | ABI argument in `a0`; relocation-bearing call before final link |
| success means exit code zero | return expression in `main` | comparison and `zext`, or constant zero | `a0 = 0`, return to startup code, process status |

### 2.3 Target contract

Use one explicit target throughout the machine-level half of the paper:

```text
target triple: riscv64-unknown-linux-gnu
ISA:           rv64gc  (G includes I, M, A, F, D; C is compressed instructions)
ABI:           lp64d
object format: ELF64, little-endian
link mode:     static, non-PIE for the clearest address narrative
```

The C data model must be stated, not assumed. Under the conventional RISC-V LP64 ABI, `unsigned` is 32 bits and `unsigned long` is 64 bits. That target choice explains the IR's `i32`/`i64` distinction and the zero-extension before multiplication. A Windows LLP64 compilation would give `unsigned long` a different width, so host-native IR is not a substitute for target-pinned IR.

## 3. Observation ladder

The following commands form a conceptual observation ladder. Exact options should be verified against the installed version; `clang -###` is useful because the official driver documentation defines it as a way to print the subcommands without executing them [clang-toolchain-2026]. The compiler driver should perform the final link so that startup objects, libraries, target emulation, and linker defaults are selected consistently.

```sh
TARGET=riscv64-unknown-linux-gnu
ARCH=rv64gc
ABI=lp64d

# Record the experiment boundary.
clang --version
clang --target=$TARGET -march=$ARCH -mabi=$ABI -### factorial.c

# Preprocessing and lexical observation.
clang --target=$TARGET -E factorial.c -o factorial.i
clang --target=$TARGET -Xclang -dump-tokens -fsyntax-only factorial.c \
  2> factorial.tokens

# Parsed, semantically analyzed source representation.
clang --target=$TARGET -Xclang -ast-dump -fsyntax-only factorial.c \
  > factorial.ast

# LLVM IR before and after the normal optimization pipeline.
clang --target=$TARGET -march=$ARCH -mabi=$ABI -O0 -S -emit-llvm \
  factorial.c -o factorial.O0.ll
clang --target=$TARGET -march=$ARCH -mabi=$ABI -O2 -S -emit-llvm \
  factorial.c -o factorial.O2.ll

# Optional controlled middle-end observation; available passes are versioned.
opt -S -passes='mem2reg,simplifycfg,instcombine' \
  factorial.O0-for-opt.ll -o factorial.ssa.ll

# Target assembly and relocatable object.
clang --target=$TARGET -march=$ARCH -mabi=$ABI -O2 -S \
  factorial.c -o factorial.rv64.s
clang --target=$TARGET -march=$ARCH -mabi=$ABI -O2 -c \
  factorial.c -o factorial.rv64.o

# Relate object bytes to sections, symbols, instructions, and relocations.
llvm-readelf -h -S -s -r factorial.rv64.o
llvm-objdump -dr --no-show-raw-insn factorial.rv64.o

# Explicit static, non-PIE link for a simple loading story.
clang --target=$TARGET -march=$ARCH -mabi=$ABI -fuse-ld=lld \
  -static -no-pie factorial.rv64.o -o factorial.rv64
llvm-readelf -h -l -s factorial.rv64
llvm-objdump -d factorial.rv64
```

`opt` accepts a textual pass pipeline, but the set and behavior of passes depend on the linked LLVM version [llvm-opt-2026]. A practical complication is that ordinary `-O0` Clang IR may attach `optnone`, which prevents most optimization. A reproducible experiment should either emit IR suitable for explicit `opt` use, remove the attribute in a controlled copy, or compare Clang's direct `-O0` and `-O2` products. The paper should disclose which path it uses rather than quietly mixing them.

## 4. A representation-by-representation interpretation

## 4.1 Source characters, preprocessing tokens, and expanded tokens

The C standard models translation in phases and distinguishes preprocessing tokens from later language tokens [wg14-n3220]. Clang's command guide summarizes the implementation-facing stage as tokenization, macro expansion, include expansion, and directive handling [clang-command-2026]. For this source, the most visible event is:

```text
source spelling:       factorial ( FACT_N )
macro replacement:     factorial ( 6U )
```

The name `FACT_N` does not denote a run-time object, has no address, and never becomes a symbol. It is a rule over preprocessing tokens. Once expanded, the later compiler sees the literal token `6U`; by the AST stage, the macro's definition site can survive only as source-location/provenance metadata useful for diagnostics.

Token output should be read categorically rather than as a character dump:

| Spelling | Token role | Semantic information not yet present |
|---|---|---|
| `unsigned`, `long`, `while`, `return` | keywords | declaration binding and full type relations |
| `factorial`, `n`, `acc`, `main` | identifiers | which declaration each use denotes |
| `1UL`, `6U`, `720UL` | numeric tokens with suffixes | target-specific width after semantic analysis |
| `*=`, `--`, `!=`, `>` | punctuators/operators | operand types and chosen conversions |
| `{`, `}`, `(`, `)`, `;` | punctuators | parse-tree parent/child structure |

Whitespace and most comments separate tokens but do not become ordinary semantic nodes. Conversely, the absence of whitespace can matter during preprocessing, and macro expansion can change the token stream without creating a textual run-time operation. This is the first important loss of surface form: **characters are reorganized into units that the grammar can consume**.

What to point at in the paper:

1. `FACT_N` exists in the source and token provenance but not in the expanded token stream.
2. `6U` is one numeric token, not the two tokens `6` and `U`.
3. At this stage the compiler recognizes spelling categories, not the loop's control-flow semantics.

## 4.2 Parsing and semantic analysis: the typed AST

The parser reconstructs hierarchical syntax from the linear token stream; semantic analysis binds names, computes types, inserts implicit conversions, and diagnoses ill-formed programs. Clang documents its AST as intentionally close to the written C/C++ source and notes that unreduced parentheses and compile-time constants may remain [clang-ast-2026]. This is why an AST is not merely “high-level IR”: it is a source-faithful, typed representation designed to retain language constructs.

The essential user nodes should resemble:

```text
TranslationUnitDecl
|- FunctionDecl factorial 'unsigned long (unsigned)'
|  |- ParmVarDecl n 'unsigned int'
|  `- CompoundStmt
|     |- VarDecl acc 'unsigned long' = 1UL
|     |- WhileStmt
|     |  |- BinaryOperator '>'
|     |  |  |- ImplicitCastExpr <LValueToRValue> n
|     |  |  `- IntegerLiteral 1U
|     |  `- CompoundStmt
|     |     |- CompoundAssignOperator '*='
|     |     |  |- DeclRefExpr acc
|     |     |  `- ImplicitCastExpr <IntegralCast> n
|     |     `- UnaryOperator '--' prefix
|     `- ReturnStmt acc
`- FunctionDecl main 'int (void)'
   `- ReturnStmt
      `- BinaryOperator '!='
         |- CallExpr factorial(6U)
         `- IntegerLiteral 720UL
```

This is schematic, not a promised byte-for-byte dump. The crucial explanatory fact is the implicit conversion in `acc *= n`:

1. `acc` has type `unsigned long` (64-bit on LP64).
2. `n` has type `unsigned int` (32-bit).
3. The usual arithmetic conversions convert `n` to `unsigned long` for multiplication.
4. The AST can make that conversion explicit even though the source contains no cast.

The AST therefore adds information rather than merely deleting syntax. It answers questions impossible at the token level: which `n` is referenced, whether `>` is signed or unsigned, what `*=` means for these operand types, and whether `factorial(FACT_N)` has a compatible argument.

What the AST still does **not** commit to:

- a particular control-flow graph layout;
- where locals reside in memory or registers;
- a calling convention;
- target instructions;
- final addresses.

## 4.3 Initial LLVM IR: control and effects become explicit

LLVM IR is a low-level, typed, language-independent representation in static single-assignment form for register-like values [lattner-adve-llvm-2004, llvm-langref-2026]. Clang's deliberately conservative `-O0` output commonly lowers mutable source variables through stack slots:

```llvm
; Idealized shape, not literal compiler output.
define i64 @factorial(i32 %n.in) {
entry:
  %n.addr = alloca i32, align 4
  %acc.addr = alloca i64, align 8
  store i32 %n.in, ptr %n.addr, align 4
  store i64 1, ptr %acc.addr, align 8
  br label %while.cond

while.cond:
  %n.cur = load i32, ptr %n.addr, align 4
  %keep.going = icmp ugt i32 %n.cur, 1
  br i1 %keep.going, label %while.body, label %while.end

while.body:
  %acc.cur = load i64, ptr %acc.addr, align 8
  %n.again = load i32, ptr %n.addr, align 4
  %n.wide = zext i32 %n.again to i64
  %product = mul i64 %acc.cur, %n.wide
  store i64 %product, ptr %acc.addr, align 8
  %n.old = load i32, ptr %n.addr, align 4
  %n.next = sub i32 %n.old, 1
  store i32 %n.next, ptr %n.addr, align 4
  br label %while.cond

while.end:
  %answer = load i64, ptr %acc.addr, align 8
  ret i64 %answer
}
```

Five source-to-IR relationships deserve explicit arrows in the paper:

1. `while` becomes named basic blocks, terminators, and a back edge; the keyword itself disappears.
2. `n > 1U` becomes `icmp ugt`, where `u` makes unsigned ordering explicit.
3. the implicit AST conversion becomes an explicit `zext i32 ... to i64`.
4. `acc *= n` decomposes into load, conversion, multiplication, and store.
5. `return acc` becomes a load followed by `ret i64`.

The IR carries a target data layout and target triple. Those module-level declarations are the bridge between target-independent reasoning and concrete size/alignment rules. Opaque `ptr` does not mean that all pointee types are unknown; the load/store instructions themselves carry the accessed value type.

### Undefined behavior and optimization scope

The example intentionally uses unsigned arithmetic. C unsigned multiplication is modulo the type width, so overflow of `acc` is defined rather than undefined. That makes the semantic contract easier to explain: an optimizer may change how the value is computed, but it may not replace a wrapped result with an arbitrary value. In LLVM IR, the plain `mul i64` correspondingly lacks `nsw`/`nuw` promises unless the frontend can prove them.

This is a useful place to state a general rule: compiler optimization preserves the source language's **defined observable behavior**, not the programmer's preferred sequence of statements. Source constructs that imply no remaining observable distinction may vanish completely.

## 4.4 SSA normalization: assignments become data-flow edges

SSA requires each register-like value to have one static definition. Cytron et al. established the dominance-frontier construction that made SSA practical for general control-flow graphs [cytron-et-al-ssa-1991]. LLVM's `mem2reg`-style promotion removes promotable stack traffic and inserts φ nodes where distinct control-flow paths bring different reaching definitions [llvm-passes-2026].

For the loop, an idealized promoted form is:

```llvm
define i64 @factorial(i32 %n.in) {
entry:
  br label %loop

loop:
  %n = phi i32 [ %n.in, %entry ], [ %n.next, %body ]
  %acc = phi i64 [ 1, %entry ], [ %product, %body ]
  %continue = icmp ugt i32 %n, 1
  br i1 %continue, label %body, label %exit

body:
  %n.wide = zext i32 %n to i64
  %product = mul i64 %acc, %n.wide
  %n.next = sub i32 %n, 1
  br label %loop

exit:
  ret i64 %acc
}
```

A φ node is not a machine instruction that “chooses both inputs.” LLVM defines it as taking the value associated with the predecessor block that just executed, and requires φ nodes to occur at the start of a block [llvm-langref-2026]. The best diagram is therefore edge-based:

```text
                 entry: (%n.in, 1)
                         |
                         v
                 +----------------+
                 | n   = phi(...) |<-------+
                 | acc = phi(...) |        |
                 +----------------+        |
                    | true                 |
                    v                      |
               product, n.next ------------+
                    |
                    | false
                    v
                 return acc
```

The φ nodes are the exact place where source-level mutable variables become explicit data-flow recurrences. This is the conceptual center of the paper: the source says “update `n` and `acc`”; SSA says “the next loop iteration receives new versions on the back edge.”

## 4.5 Optimization: preserving meaning while erasing history

LLVM's default optimization pipeline is a composition of analyses and transformations assembled for an optimization level; it is not a single “optimizer algorithm” [llvm-newpm-2026]. The paper should explain transformations by their semantic role, not claim a version-independent pass order.

| Transformation family | Likely effect on the case study | What becomes easier afterward |
|---|---|---|
| stack promotion / SROA | remove local `alloca`/`load`/`store` traffic | scalar data flow is explicit |
| instruction combining | canonicalize decrement, comparisons, and conversions | matching and later simplification |
| CFG simplification | merge or redirect trivial blocks | fewer branches and φ inputs |
| loop canonicalization | normalize header/latch/exit form | induction and loop analyses |
| inlining | replace `main`'s call with the body when profitable | constant propagation across call boundary |
| constant propagation and dead-code elimination | evaluate the fixed call and delete unused computation in `main` | `main` may reduce to `ret i32 0` |

Two outputs should be contrasted:

1. **`factorial` itself.** Because it has external linkage, its optimized callable definition normally remains in a non-LTO object. Its loop may be canonicalized and its stack slots promoted.
2. **The call inside `main`.** Since the argument is `6` and the expected value is `720`, inlining plus constant evaluation can prove the comparison false and reduce `main` to zero.

This contrast prevents a common misconception: “optimization deleted the factorial algorithm” is true only for the particular closed computation in `main`; the externally callable function may remain because the translation unit's interface is observable by the linker and other code.

Claims requiring caution:

- `-O2` does not guarantee a particular pass sequence as a stable user contract.
- Whether the compiler fully evaluates the loop is an observation, not a language rule.
- With `static factorial`, section garbage collection, or LTO, the standalone function may disappear.
- With sanitizers, profiling, debug constraints, or different targets, code shape changes.

The paper should show a small semantic equivalence table rather than a wall of IR:

| Property | Before optimization | After optimization |
|---|---|---|
| result for `factorial(6)` | 720 modulo `2^64` | same |
| `main` exit status | 0 | 0 |
| source loop visible | yes, via CFG and memory traffic | perhaps only in exported function |
| number of loads/stores | many at `-O0` | often zero for promoted locals |
| source variable names | partly recoverable | often absent except debug metadata |

## 4.6 Instruction selection and RV64 assembly

Instruction selection maps LLVM operations to target-specific machine instructions. LLVM documents SelectionDAG as one such framework and GlobalISel as another; both involve legalization, combining, selection, scheduling, and later register allocation rather than a one-to-one textual substitution [llvm-codegen-2026, llvm-globalisel-2026].

For this example, the explanation should proceed from constraints:

1. **Width legalization.** RV64 integer registers are 64 bits. The C `unsigned` loop counter is logically 32 bits, while `acc` is 64 bits. The backend must preserve the source/IR width semantics even though both may occupy full registers.
2. **Operation availability.** `rv64gc` contains the M extension, whose `MUL` produces the low XLEN bits of a product [riscv-isa-2026]. That matches modulo-`2^64` `mul i64`.
3. **Control lowering.** `icmp` plus `br` can become an unsigned conditional branch (`bltu`/`bgeu`) or an equivalent transformed condition.
4. **Register allocation.** SSA names are unbounded virtual values; assembly uses a finite register file. φ nodes are eliminated into moves, coalescing, or edge-specific assignments before final code.
5. **ABI placement.** Function arguments and return values are not chosen arbitrarily; the psABI assigns them to registers and the stack.

An illustrative optimized body may have this *shape*:

```asm
factorial:
    li      a1, 1
    li      a2, 2
    bltu    a0, a2, .Ldone
.Lloop:
    # zero-extend the 32-bit logical n if required by the chosen invariant
    mul     a1, a1, a0
    addiw   a0, a0, -1
    bgeu    a0, a2, .Lloop
.Ldone:
    mv      a0, a1
    ret
```

This listing is pedagogical. A real compiler may change the loop test, use different registers, exploit known sign-extension invariants of RV64 word operations, schedule instructions differently, or emit compressed encodings. The paper must annotate observed output, not force it to match the sketch.

### ABI facts to point at

The ratified RISC-V psABI defines [riscv-psabi-1.0]:

- `a0`--`a7` (`x10`--`x17`) as argument registers; `a0` and `a1` also carry return values;
- `ra` (`x1`) as the return-address register and not preserved across calls;
- `sp` (`x2`) as callee-preserved and 128-bit (16-byte) aligned on procedure entry;
- `s0`--`s11` as callee-saved and `t0`--`t6` as temporaries;
- an optional frame pointer in `s0`/`x8`.

Consequences for the example:

- `factorial` receives `n` in `a0` and returns `unsigned long` in `a0`.
- An optimized leaf `factorial` may need no stack frame and need not save `ra` because it makes no call.
- A non-leaf `main` normally must preserve its return address before calling `factorial`, unless the call is removed or transformed.
- `ret` is an assembler pseudoinstruction for an indirect jump through `ra`; `call factorial` is also a pseudoinstruction that may expand to a PC-relative instruction pair.

The ABI is a contract between separately compiled components. The ISA says what `jalr`, `mul`, loads, stores, and branches do; the ABI says which registers mean “argument,” “return value,” “saved across calls,” and how the stack is aligned. Confusing these levels makes assembly explanations brittle.

## 4.7 Assembly to an ELF relocatable object

The assembler turns mnemonics, labels, directives, and pseudoinstructions into section contents plus metadata. An ELF relocatable object is not just “binary assembly.” It is a structured container whose section view exists primarily for linking [elf-gabi-2025, linux-elf-2026].

Expected high-value fields for `factorial.rv64.o`:

| ELF component | Role in this example |
|---|---|
| ELF header | identifies ELF64, little-endian RISC-V, and `ET_REL` |
| `.text` | encoded instructions for `factorial` and `main` |
| `.symtab` | symbol records, including global definitions and local labels |
| `.strtab` | spellings referenced by symbol-table entries |
| `.rela.text` | relocations for instruction fields whose final values are not yet known |
| `.riscv.attributes` | target/ABI attributes used for compatibility checks |
| `.eh_frame` (toolchain-dependent) | unwind metadata and possible relocations |

Three values that look similar must be distinguished:

1. an **assembly label** names a location while assembling;
2. an **ELF symbol** records a name, binding, type, section index, and section-relative value;
3. a **final virtual address** is assigned only after the linker lays out output sections/segments.

For a call whose distance is unknown during assembly, the object carries both placeholder instruction bits and a relocation record. RISC-V commonly represents a general call with an `AUIPC`/`JALR` pair and a call relocation; the psABI defines the RISC-V-specific relocation semantics and permits linker relaxation when a shorter encoding suffices [riscv-psabi-1.0]. Thus, “the assembler failed to finish the instruction” is the wrong interpretation. The assembler intentionally emits a relocatable claim:

```text
At offset P in .text, rewrite designated instruction fields so that they
refer to symbol S with addend A according to relocation type R.
```

`llvm-objdump -dr` is the best bridge view because it places disassembly and relocations together. `llvm-readelf -s -r` provides the table view. A screenshot or listing should highlight the same call site in both tools.

## 4.8 Static linking: names become addresses

The linker's central jobs are **symbol resolution** and **relocation**, together with section selection and layout. LLD's design description explains the traditional archive algorithm: an archive member is extracted when it defines a symbol currently required by the link [lld-design-2026]. For the selected source, the most instructive cross-object edge comes from normal C startup:

```text
startup object defines:        _start
startup object requires:       main
factorial.rv64.o defines:      main, factorial
linker resolves:               startup's main reference -> our main
linker chooses addresses:      output text/data layout
linker applies relocations:    instruction/data fields -> assigned addresses
output entry point:            _start, not main
```

This is enough to teach library extraction and symbol resolution without analyzing any course-specific runtime library. If the driver links a fully static executable, it may also select libc support objects; those are toolchain inputs, not the intellectual center of the case study.

The paper should distinguish four artifacts:

| Artifact | ELF type | Addresses complete? | Intended consumer |
|---|---|---:|---|
| compiler/assembler output | `ET_REL` | no | linker |
| non-PIE executable | usually `ET_EXEC` | link-time virtual addresses assigned | loader |
| PIE executable | usually `ET_DYN` | load bias still chosen at run time | loader + dynamic machinery as applicable |
| shared object | `ET_DYN` | relocation/binding may remain | loader/dynamic linker |

For a clean introductory experiment, `-static -no-pie` removes dynamic symbol binding from the main narrative. It does **not** imply that “static linking is always non-PIE”; static PIE exists. The exact ELF type and presence/absence of `PT_INTERP` must be observed with `readelf`, not inferred only from a flag.

### Linker relaxation as a cross-stage optimization

RISC-V linker relaxation is a valuable counterexample to a rigid front-end/middle-end/back-end separation. The compiler/assembler may emit a general relocatable call sequence; after global layout makes the distance known, the linker can replace it with a shorter form if the psABI permits it. This is optimization driven by information available only after separate compilation. It also explains why object disassembly can differ from final executable disassembly even when no source or LLVM optimization changed.

## 4.9 Loading and execution: segments replace sections

The linker does not execute the program. ELF executable/shared files statically describe programs; the operating system creates a process image using the program header table and its segments [elf-gabi-2025]. Linux `execve` replaces the current process image with a new one; for a dynamically linked ELF it also invokes the named interpreter, whereas the deliberately static case has no dynamic interpreter [linux-execve-2026].

The explanatory chain should be:

1. `execve` validates the executable and reads its ELF/program headers.
2. `PT_LOAD` entries describe byte ranges to map, their virtual addresses, memory sizes, alignment, and permissions.
3. File-backed bytes form code/read-only/data mappings; any `p_memsz > p_filesz` tail is zero-filled (the usual mechanism behind `.bss`).
4. The kernel prepares the initial stack and process state according to the platform contract.
5. Control transfers to the ELF entry address `_start`.
6. Startup code establishes the language runtime context and eventually calls `main`.
7. `main` returns zero for this example; startup code converts that into process termination status.

The most important visual distinction is:

```text
Link-time section view                    Run-time segment view
----------------------                    ---------------------
.text       executable bytes  ---+        PT_LOAD  R-X  code/rodata
.rodata     constants          ---|
.data       initialized data   ---+----->  PT_LOAD  RW-  data
.bss        zero-fill size     ---|
.symtab     linker metadata       +--X     usually not mapped/needed to run
.strtab     names                 +--X     usually not mapped/needed to run
```

Sections answer “how should tools classify and combine file contents?” Segments answer “what should the loader map into memory with which permissions?” They overlap in bytes but serve different views. This is the cleanest final transformation in the paper: source-level functions are no longer the loader's unit; loadable ranges and an entry address are.

## 5. The end-to-end transformation ledger

This table can become the paper's central figure or a two-page spread.

| Stage | Primary structure | Newly explicit | Deliberately lost or deferred | Best question to ask |
|---|---|---|---|---|
| source text | characters and directives | programmer intent and names | nothing yet | What did the programmer write? |
| preprocessed tokens | linear token stream | macro result, included tokens | macro spelling as executable entity | What text reaches the parser? |
| typed AST | source-shaped hierarchy | binding, types, implicit casts | whitespace/comments; target layout still deferred | What does the language mean? |
| initial LLVM IR | CFG, memory effects, typed operations | branches, loads/stores, widths | `while`, `*=`, most source syntax | What operations/effects implement the meaning? |
| SSA/optimized IR | def-use graph and canonical CFG | loop recurrences, proven constants | mutable-variable history, dead computations | Which distinctions still affect behavior? |
| machine IR / assembly | finite registers and target operations | legal target ops, calling convention actions | SSA names and most high-level types | How can this target execute it? |
| relocatable ELF | sections, symbols, relocations | encoded bytes and unresolved address obligations | final virtual addresses | What remains for the linker? |
| linked ELF | laid-out output and program headers | resolved symbols, entry, segment plan | most relocation/link metadata for static case | What can the loader instantiate? |
| process image | mapped segments and machine state | permissions, addresses, initial execution context | most section boundaries and symbol names | What does the processor actually execute? |

This ledger supports a deeper thesis: compilation is not a monotonic descent from “rich” to “poor.” Each representation discards irrelevant distinctions while adding facts needed by the next consumer. The AST adds language meaning; SSA adds data-flow explicitness; the object file adds symbolic address obligations; the executable adds a load map.

## 6. MLIR progressive lowering as the outlook

### 6.1 Why LLVM IR is not always the right first IR

LLVM IR is highly effective for scalar, control-flow, memory, and target-independent machine-like optimization, but lowering a domain operation too early can destroy the structure needed for domain transformations. The peer-reviewed MLIR design argues for extensible dialects and multiple abstraction levels so that domain, algorithmic, memory, and hardware structure can coexist and be lowered over time [lattner-et-al-mlir-2021].

The factorial example does not *need* MLIR in production. That is precisely why it is pedagogically useful as an outlook: the same loop can show the mechanism without claiming that MLIR improves this scalar program.

### 6.2 A conceptual factorial path

One plausible, non-normative path is:

```text
C typed AST
   |
   v
func.func + arith + scf
  - function/type structure
  - typed constants and multiplication
  - structured while loop with loop-carried values
   |
   | lower structured control flow
   v
func.func + arith + cf
  - explicit blocks, branches, block arguments
   |
   | convert types/ops to LLVM dialect
   v
LLVM dialect
  - LLVM-compatible functions, integer ops, branches
   |
   | translate
   v
LLVM IR -> existing optimization and RV64 backend
```

The official MLIR LLVM target documentation explicitly describes conversion as progressive: most passes convert one dialect while leaving unrelated dialect operations present, with type-conversion materializations bridging temporarily mixed representations [mlir-llvm-target-2026]. The dialect conversion framework formalizes this with [mlir-dialect-conversion-2026]:

- a **conversion target** declaring operations/dialects legal or illegal;
- **rewrite patterns** replacing illegal operations with legal ones;
- an optional **type converter** and materializations;
- partial, full, and analysis conversion modes.

MLIR's Toy tutorial demonstrates mixed dialects during partial lowering rather than demanding one giant AST-to-LLVM translation [mlir-toy-lowering-2026]. For the factorial loop, `scf.while` can retain structured loop regions and loop-carried values longer; lowering to `cf` turns that structure into blocks and branches similar to the LLVM SSA explanation.

### 6.3 What progressive lowering does and does not promise

| Supported conclusion | Unsupported overclaim |
|---|---|
| Different abstractions may coexist in one module/function during conversion. | Every program follows one canonical dialect ladder. |
| Legality and rewrite patterns make conversion obligations explicit. | Any set of dialects automatically composes without interface work. |
| High-level structure may be retained until relevant transformations finish. | Retaining structure automatically produces faster code. |
| LLVM dialect/translation can reuse LLVM optimization and backends. | MLIR replaces LLVM or makes backend design unnecessary. |
| Progressive lowering is valuable for heterogeneous/domain compilers. | It is justified overhead for every small scalar C compiler. |

### 6.4 Research frontier and engineering judgment

The academically important idea is not “more IRs are always better,” but **representation timing**: an abstraction should survive exactly until transformations needing it are complete, then lower through explicit contracts. The production risk is dialect and conversion proliferation. Every boundary needs legality definitions, type conversions, tests, diagnostics, and version management. Thus the outlook should recommend MLIR when a system has multiple domains or hardware levels whose structure LLVM IR would erase too soon—not because multi-level IR is fashionable.

## 7. Proposed paper architecture

The narrative should resemble a systems text's guided dissection rather than a lab report.

| Paper section | Central question | Anchor artifact |
|---|---|---|
| 1. Introduction | Why follow one program rather than enumerate tools? | full transformation pipeline figure |
| 2. Case and method | Which facts will be tracked, under what target contract? | 11-line source + fact ledger |
| 3. Front end | How do characters acquire grammar, binding, and type? | macro/token/AST triptych |
| 4. IR and optimization | How do mutation and control become SSA, and what can disappear? | `-O0`, promoted SSA, `-O2` comparison |
| 5. RV64 code generation | How do typed operations become legal instructions under an ABI? | annotated assembly and register table |
| 6. Object, link, load | How do unresolved names become mapped executable addresses? | object relocation paired with final disassembly; sections/segments figure |
| 7. MLIR outlook | What if one low-level IR erases domain structure too early? | progressive-lowering ladder |
| 8. Conclusion | Which facts survived, transformed, or vanished? | condensed end-to-end ledger |

### 7.1 Recommended figures

1. **Representation river:** one horizontal pipeline with the dominant data structure under each stage.
2. **Mutation-to-SSA diagram:** source assignments on the left, two loop φ nodes on the right.
3. **Call site through time:** LLVM `call` -> assembly `call` pseudo -> object relocation -> relaxed final instruction.
4. **Sections versus segments:** link view and load view of the same bytes.
5. **MLIR outlook:** structured dialect -> CFG dialect -> LLVM dialect -> LLVM IR.

Each figure should answer one causal question. Avoid screenshots whose only message is “the tool produced a lot of text.”

### 7.2 Terminology discipline

- Say **front end**, **middle end**, **back end**, **assembler**, **linker**, **loader** only when the corresponding contract is meant.
- Say **LLVM IR basic block** rather than “assembly block.”
- Say **virtual register / SSA value** for LLVM names and **physical register** for `a0`, `ra`, etc.
- Say **relocatable object** for `.o`, not “executable machine code file.”
- Say **section** in the link view and **segment** in the loading view.
- Say **entry point `_start`** rather than “the loader starts at `main`.”
- Treat `call`, `ret`, and some address constructions as assembler pseudos when applicable.

## 8. Validity threats and discriminating checks

| Threat | Why it matters | Strong check |
|---|---|---|
| tool-version drift | LLVM pass pipelines and printed syntax evolve | record full version; regenerate all artifacts together |
| target drift | host compilation may use a different C data model and object format | pin triple, ISA, ABI, and inspect ELF header/attributes |
| optimization attribution | a changed instruction may result from several interacting passes | compare controlled pass checkpoints; phrase attribution cautiously |
| debug/sanitizer contamination | instrumentation changes CFG, calls, stack frames, and sections | build the explanatory artifacts without instrumentation; disclose flags |
| PIE/static ambiguity | driver defaults vary by distribution/toolchain | inspect ELF type and program headers, not flags alone |
| pseudo/real instruction confusion | printed assembly need not equal encoded instruction count | compare `.s` with `objdump -dr` and final executable disassembly |
| source-semantics mistake | signedness or undefined behavior can invalidate an optimization story | use unsigned arithmetic; explain modulo semantics and IR flags |
| cross-stage false identity | names/lines do not map one-to-one after optimization | track semantic facts, not line numbers |

Three particularly discriminating experiments:

1. Change `FACT_N` from a macro to a `const unsigned` object. If the explanation is correct, preprocessing behavior changes even when later constant folding yields similar machine code.
2. Change `factorial` from external to `static`. If the linkage explanation is correct, the optimized standalone definition becomes eligible for deletion.
3. Compare object and executable disassembly at the call site. If relocation/relaxation is active, the final encoding may be shorter or otherwise patched after object emission.

These are not extra examples for grading; they are small falsification probes for the causal account.

## 9. Source quality map

| Topic | Preferred source | Authority | Specific use | Caveat |
|---|---|---|---|---|
| C tokens and conversions | WG14 N3220 [wg14-n3220] | public working draft closely tracking ISO C | translation phases, tokens, unsigned semantics | cite as draft, not as freely licensed final ISO text |
| Clang phases | Clang toolchain/command guides [clang-toolchain-2026, clang-command-2026] | upstream official | logical stages, driver observation flags | fused stages mean artifacts are observation points |
| AST | Clang AST introduction [clang-ast-2026] | upstream official | source-faithful AST and dump method | dump spelling is implementation/version-sensitive |
| LLVM IR/φ | LangRef [llvm-langref-2026] | upstream normative documentation | instruction and φ semantics | not a C semantics specification |
| SSA theory | Cytron et al. [cytron-et-al-ssa-1991] | peer-reviewed TOPLAS classic | dominance frontiers and practical SSA construction | LLVM implementation details differ from the original algorithm |
| LLVM architecture | Lattner and Adve [lattner-adve-llvm-2004] | peer-reviewed CGO paper | why typed SSA IR supports analysis/transformation | historical LLVM differs from current LLVM |
| optimization passes | LLVM pass/new-PM docs [llvm-passes-2026, llvm-newpm-2026] | upstream official | transformation roles and pipeline composition | exact default pipeline is unstable |
| instruction selection | LLVM code generator docs [llvm-codegen-2026, llvm-globalisel-2026] | upstream official | legalization, selection frameworks, scheduling | documentation includes evolving implementation details |
| RV64 instructions | RISC-V unprivileged ISA [riscv-isa-2026] | ratified official specification | instruction semantics and extension membership | ISA alone does not define calling convention |
| calling convention/relocations | RISC-V psABI 1.0 [riscv-psabi-1.0] | ratified official specification | registers, stack alignment, ELF relocations/relaxation | distinguish ratified 1.0 from moving development draft |
| ELF | Xinuos ELF specification [elf-gabi-2025] | maintained gABI-format specification | headers, sections, symbols, relocations, segments | processor details come from psABI |
| Linux loading | Linux man-pages [linux-elf-2026, linux-execve-2026] | maintained platform documentation | actual Linux ELF/`execve` behavior | Linux behavior is not every ELF operating system |
| linker implementation | LLD design [lld-design-2026] | upstream production linker | archive extraction and linker mental model | design document admits some age; verify output empirically |
| multi-level IR | MLIR CGO paper [lattner-et-al-mlir-2021] | peer-reviewed primary paper | motivation and design space | paper's promise is broader than any one production deployment |
| progressive lowering | MLIR conversion/LLVM target docs [mlir-dialect-conversion-2026, mlir-llvm-target-2026] | upstream official | legality, partial/full conversion, mixed dialects | APIs and pass names evolve |

## 10. Conclusions supported by the evidence

1. **The most faithful organizing principle is representation change, not command enumeration.** The official toolchain model identifies stages, while the artifacts reveal the contracts between them.
2. **Compilation both removes and creates information.** Macro spelling, source loops, and mutable variables disappear; types, CFG edges, SSA dependencies, relocation obligations, and segment permissions become explicit at later stages.
3. **Optimization is best understood as proof-driven forgetting.** Once the compiler proves that `factorial(6) != 720` is false under defined unsigned semantics, the call and loop inside `main` no longer carry observable information.
4. **ISA, ABI, object format, linker, and loader are distinct layers.** RV64 instructions do not say where arguments live; the ABI does. Assembly labels are not final addresses; symbols and relocations mediate the link. Sections are not the loader's mapping unit; segments are.
5. **MLIR generalizes the same lesson.** The central design choice is when to discard an abstraction. Progressive lowering makes that timing and the legality of intermediate mixtures explicit, but it introduces real conversion and maintenance costs.

The paper should end by returning to the original 11-line program: the final process contains no macro named `FACT_N`, no `WhileStmt`, and usually no variable named `acc`; nevertheless, their required behavior survives as a chain of typed operations, data dependencies, target conventions, relocated instruction fields, and mapped executable bytes. That is the sense in which one can “understand the compiler system” by pointing at each representation and explaining what it now knows.
