# Formal Spine for the Review-Style Revision

Status: design note for the manuscript revision; not manuscript prose.
Scope: add enough programming-languages and compiler theory to explain the
clipped-dot journey without turning the paper into either a verification report
or a miniature formalization project.
Primary manuscript: `report/sections/01-introduction.tex` through
`report/sections/13-conclusion.tex`.

## 1. Diagnosis and editorial decision

The current manuscript has a strong cross-layer case, but its governing question
is too often **“what evidence licenses this claim?”** rather than **“what
mathematical object is this layer manipulating, and why is that representation a
good engineering compromise?”**. A simple lexical count makes the imbalance
visible: the thirteen sections contain roughly 197 occurrences of terms such as
“evidence”, “validation”, “observation”, “reproducibility”, and “oracle”, while
formal display mathematics is concentrated almost entirely in the case definition
and frontier chapter. Section 10 alone has about 30 evidence-related occurrences.

The revision should therefore adopt this editorial rule:

> **Use the case to explain compiler structure, not the compiler infrastructure to
> validate the case.** One compact paragraph may state how an artifact was
> obtained, but the mathematical and conceptual explanation must receive the
> space currently occupied by evidence taxonomies, file sizes, environment
> inventories, and repeated caveats about finite testing.

The right level of formalism is a **formal spine**, not a full mechanization:

1. define one small semantic model for the case;
2. reuse its state and invariant at every representation boundary;
3. introduce exactly the compiler-theory object needed at each layer;
4. give one worked equation, derivation, or proof sketch per major idea;
5. immediately state the engineering compromise that the formal model abstracts
   away.

This produces a CS:APP-style explanation: the reader sees one computation from
several angles, and the notation prevents hand-waving. The paper does **not** need
to prove Clang, LLVM, binutils, glibc, QEMU, or the authored assembly correct.

## 2. The unifying mathematical model

### 2.1 Representations, meanings, and transformations

Let \(R_i\) be the well-formed programs at representation level \(i\), and let

\[
  \llbracket\cdot\rrbracket_i : R_i \to \mathcal P(\mathit{Trace})
\]

map a program to its permitted observable traces. Use two explicitly related
observation boundaries rather than silently mixing source and process semantics:

- \(Obs_{core}\) records `getint`, bytes intentionally emitted through
  `putint`/`putch`, and the return from `main`;
- \(Obs_{proc}\) additionally includes effects introduced by the linked runtime,
  such as the `sylib.c` destructor's timing line on stderr.

The review's semantics follows \(Obs_{core}\). The extra stderr line is a property
of one linked process image, not part of SysY's clipped-dot meaning. Internal loads,
registers, addresses, and block transitions are hidden at both boundaries.

A compiler step is a partial function

\[
  T_i : R_i \rightharpoonup R_{i+1}.
\]

Its semantic obligation is behavioral refinement:

\[
  T_i(P)=Q \quad\Longrightarrow\quad
  \llbracket Q\rrbracket_{i+1}
  \subseteq
  \llbracket P\rrbracket_i .
  \tag{S}
\]

For this deterministic, terminating case on its specified input domain, the two
sets are singletons, so refinement reduces to equality of the output trace. The
set-based statement is nevertheless preferable because it scales to undefined
behavior, nondeterminism, external calls, and compiler-introduced choices. The
direction must be explained rather than treated as universal notation: a target
may choose one behavior allowed by a nondeterministic source, but it may not add a
new observable behavior.

Equation (S) should appear once near the end of Section 1 or at the start of the
repurposed Section 10. Later sections should cite it, not restate competing notions
of “same program”. It also separates two questions that the current prose often
mixes:

- **legality:** is \(Q\) in the refinement set of \(P\)?
- **profitability:** among legal \(Q\), which minimizes a target-dependent cost?

Formally, optimization is

\[
  Q^* \in \arg\min_{Q\in\mathcal F(P)} C(Q;\theta),
  \qquad
  \mathcal F(P)=\{Q\mid
    \llbracket Q\rrbracket\subseteq\llbracket P\rrbracket\},
  \tag{O}
\]

where \(\theta\) denotes the target, workload, and engineering budget. Static
analysis and semantics define the feasible set; heuristics, PGO, MLGO, and hardware
models estimate the cost. This one equation can organize both classical
optimization and the frontier discussion.

### 2.2 The case kernel

Fix

\[
 A=(-4,1,7,3,9,-2,6,5),\qquad
 B=(2,-3,1,4,-1,5,2,3),
\]

and define

\[
 k(n)=\min(8,\max(0,n)),\qquad
 c_i=\min(12,\max(-8,A_iB_i)),
\]

\[
 D(n)=\sum_{i=0}^{k(n)-1}c_i.
 \tag{C}
\]

The important mathematical object is not the six-input oracle. It is the loop
invariant

\[
 \mathcal I(i,acc)\;\equiv\;
 0\le i\le k
 \;\land\;
 acc=\sum_{j=0}^{i-1}c_j
 \;\land\;
 -8i\le acc\le12i.
 \tag{I}
\]

The proof is short enough to present completely:

- initialization: \((i,acc)=(0,0)\) satisfies (I) by the empty-sum convention;
- preservation: if \(i<k\), one iteration computes \(c_i\), then moves to
  \((i+1,acc+c_i)\); because \(-8\le c_i\le12\), all three conjuncts remain true;
- exit: \(i\ge k\) together with \(i\le k\) gives \(i=k\), so
  \(acc=D(n)\);
- safety: \(-64\le acc\le96\), so the case never relies on signed 32-bit
  overflow.

This is the manuscript's reusable proof kernel. The source `while`, LLVM header
`phi` nodes, RV64 loop label, and prospective MLIR reduction all encode the same
recurrence:

\[
 (i,acc)\mapsto(i+1,acc+c_i)\quad\text{while }i<k.
 \tag{R}
\]

The distinction between per-term clipping and saturating the accumulator should be
retained, but stated algebraically. Equation (C) is an ordinary fold under integer
addition over the already-defined sequence \((c_i)\). Its regrouping is legal
because the invariant rules out overflow. In contrast,

\[
 acc_{i+1}=\operatorname{clip}(acc_i+A_iB_i,-8,12)
\]

uses a non-associative binary update, so a parallel reduction tree need not preserve
the sequential result. This is the cleanest case-specific example of semantics
governing optimization legality.

The principal theorem should be stated for the **closed `main` program** and every
32-bit input to `getint`. That choice discharges the array and numeric assumptions
because `main` fixes the arrays and computes \(k\in[0,8]\). If the manuscript also
states a theorem about `clipped_dot` in isolation, it must expose the missing
precondition:

\[
 0\le n\le8,\quad lo\le hi,\quad
 a,b\text{ each designate at least }n\text{ readable }i32\text{ cells},
\]

plus absence of source-level signed overflow in each product and partial sum. A
function signature alone does not establish these facts. This distinction is
particularly important for LLVM `inbounds` and any `nsw` annotations: the closed
program can justify them on its reachable executions even though an arbitrary
external caller could violate the function-level assumptions.

## 3. Section-by-section formal spine

### Section 1 — Introduction: from “evidence chain” to semantic descent

**Keep:** the representation-contract thesis and the distinction between logical
stages and operating-system processes.

**Replace:** the evidence-level table and most methodological disclaimers.

**Add:** a single overview figure and equation (S). The figure should show a
semantic spine through the center:

```text
source state (i, acc)
        | elaboration
typed state + memory
        | CFG/SSA construction
(%i, %acc) at loop header
        | selection/allocation
(t1, t0) at .Lloop
        | assembly/link/load
machine state in a process
```

Each horizontal annotation should answer two questions only: what is made explicit,
and what design decision is deferred. This replaces the current “artifact provenance”
emphasis with a conceptual journey.

Introduce the three dimensions used throughout the paper:

1. **meaning** — the trace semantics that must survive;
2. **information** — which facts are explicit in the current representation;
3. **cost/commitment** — which implementation choices have become fixed.

These are more useful than a catalogue of evidence labels and lead naturally to
the final principles.

### Section 2 — Case study: give the paper its theorem-shaped center

**Keep:** the complete SysY program once, equation (C), and the source-feature
table after substantial compression.

**Add:** invariant (I) and its four-line proof. Include a compact “semantic
passport” table:

| Layer | Loop state | One-step update | Exit observation |
|---|---|---|---|
| SysY | variables `i`, `acc` | source loop body | call `putint(acc)` |
| LLVM | header `%i`, `%acc` | `%i.next`, `%acc.next` | `ret i32 %acc` |
| RV64 | `t1`, `t0` at `.Lloop` | `addiw`, `addw` | result moved to `a0` |
| MLIR view | induction arg, iter arg | `scf.yield`/reduction combiner | scalar result |

**Cut or move:** the six-case oracle, exact stderr behavior, and repeated statements
about what finite testing does not prove. A one-sentence footnote can point to the
companion preflight project. The review's mathematical anchor is the invariant, not
the test table.

If a small testing sidebar remains, note the useful finite quotient: the closed
program's mathematical result depends on raw input only through
\(k=\operatorname{clip}(n,0,8)\), so all 32-bit inputs fall into nine semantic
classes \(k=0,\ldots,8\). The existing six tests cover only
\(k\in\{0,1,4,8\}\); exhaustive coverage of this particular case needs nine prefix
lengths, not \(2^{32}\) raw values. This is an optional bridge between the model and
testing, not a new validation chapter.

### Section 3 — Front end: syntax, typing, and execution meaning

The front-end chapter currently explains many facts well but lacks the formal
objects that distinguish syntax from semantics. Add a deliberately tiny calculus
covering only the case.

#### Abstract syntax

\[
\begin{aligned}
 \tau &::= \mathtt{int}\mid \mathtt{ptr}(\mathtt{int}),\\
 e &::= z\mid x\mid a[e]\mid e_1\odot e_2\mid f(e_1,\ldots,e_m),\\
 s &::= x:=e\mid s_1;s_2\mid
       \mathtt{if}\ e\ \mathtt{then}\ s_1\ \mathtt{else}\ s_2
       \mid \mathtt{while}\ e\ \mathtt{do}\ s .
\end{aligned}
\]

This is abstract syntax, not a replacement SysY grammar. It deliberately erases
parentheses and punctuation after parsing.

Treat preprocessing separately as a token transduction

\[
  \mathrm{PP}_{E,M}:\mathit{Token}^*\to\mathit{Token}^*,
\]

parameterized by the include environment \(E\) and macro environment \(M\).
`TERM_MIN` disappears before the abstract syntax exists. This single function is
enough to explain why a macro is neither a variable nor an AST node; there is no
need for a long reproducibility discussion about include search paths in the main
narrative.

#### Typing judgments

Use a typing environment \(\Gamma\) and distinguish address-producing lvalues from
ordinary values:

\[
  \Gamma\vdash_L e:\tau
  \qquad\text{and}\qquad
  \Gamma\vdash_R e:\tau.
\]

The three rules that explain the case are sufficient:

\[
\frac{\Gamma(a)=\mathtt{ptr}(\mathtt{int})\quad
      \Gamma\vdash_R i:\mathtt{int}}
     {\Gamma\vdash_L a[i]:\mathtt{int}}
\quad
\frac{\Gamma\vdash_L e:\tau}
     {\Gamma\vdash_R e:\tau}
\quad
\frac{\Gamma\vdash_R e_1:\mathtt{int}\quad
      \Gamma\vdash_R e_2:\mathtt{int}}
     {\Gamma\vdash_R e_1*e_2:\mathtt{int}}.
\]

Instantiate the derivation for `a[i] * b[i]`. This explains, more sharply than an
AST listing alone, why array subscripting yields a location and multiplication
forces two loads. Add one call rule for `clipped_dot(a,b,n,-8,12)` and state that
argument types, not ABI locations, are fixed here.

Do not attempt a complete progress/preservation proof. One sentence should state
the engineering boundary: static typing rules exclude category errors, but do not
by themselves prove array bounds, absence of overflow, or termination. Those facts
come from invariant (I).

#### Operational semantics

Let \(\sigma\) map local variables to integers or addresses and \(\mu\) map
addresses to 32-bit cells. Use standard judgments

\[
 \langle e,\sigma,\mu\rangle\Downarrow v,
 \qquad
 \langle s,\sigma,\mu\rangle\Downarrow(\sigma',\mu').
\]

Rather than printing many generic rules, work one iteration. Under \(i<k\), the
loop body evaluates

\[
 p=\mu(a+4i)\cdot\mu(b+4i),\quad
 c=\min(12,\max(-8,p)),
\]

and changes the store by

\[
 \sigma' = \sigma[i\mapsto i+1,\;acc\mapsto acc+c],
 \qquad \mu'=\mu.
\]

This makes source execution precise while exposing the facts that later become
GEP/load/multiply/select and then RV64 addressing/instructions. It also supports a
short engineering note: Clang interleaves parser and Sema implementation work even
though syntax and typing remain distinct mathematical judgments.

### Section 4 — LLVM IR: CFG, dominance, and SSA as graph structure

Define a control-flow graph as

\[
 G=(V,E,v_{entry}),
\]

where vertices are basic blocks and edges are possible transfers of control. For
the authored kernel:

\[
 V=\{entry,loop,body,exit\},\qquad
 E=\{entry\to loop,loop\to body,body\to loop,loop\to exit\}.
\]

Define dominance exactly:

\[
 u\dom v \iff
 \text{every path from }v_{entry}\text{ to }v\text{ contains }u.
\]

State the relevant facts: `entry` dominates every block; `loop` dominates `body`
and `exit`; `body` does not dominate `exit` because the loop may execute zero
times. This directly explains why a definition in `body` cannot be used at `exit`
without a merge.

SSA well-formedness needs only two rules:

1. each SSA name has one definition;
2. a definition dominates every ordinary use; a \(\phi\)-operand is regarded as
   used on its incoming edge.

Then interpret the two header phis as the recurrence (R):

\[
 \begin{aligned}
 i_{loop}&=\phi(entry:0,\;body:i_{next}),\\
 acc_{loop}&=\phi(entry:0,\;body:acc_{next}).
 \end{aligned}
\]

Add one sentence on dominance frontiers instead of merely citing the SSA paper:

\[
 DF(x)=\{y\mid x\text{ dominates a predecessor of }y
                 \land x\text{ does not strictly dominate }y\}.
\]

For the backedge definition in `body`, \(loop\in DF(body)\), identifying the
header as the merge point. This is enough to connect the graph algorithm to the
actual \(\phi\) nodes without teaching the whole Cytron construction.

**Visualization:** replace the text-only CFG with a combined CFG/dominator-tree
figure. Use solid arrows for CFG edges, a dashed red arrow for the backedge, and a
small inset dominator tree. Annotate the header with invariant (I) and each edge
with the corresponding \(\phi\) choice. This one diagram can replace several
paragraphs.

Memory should remain explicit: SSA governs `%i` and `%acc`, not the cells reachable
through `%a` and `%b`. GEP is address arithmetic; `load` observes memory. State the
`inbounds` obligation as the already-proved inequality \(0\le i<k\le8\), without
reopening a long evidence discussion.

### Section 5 — Optimization: fixed points, legality, and profitability

This section needs the largest theoretical upgrade.

#### Monotone dataflow analysis

Present a classical dataflow framework:

- a lattice \((L,\sqsubseteq,\sqcup,\bot)\) of abstract facts;
- a monotone transfer function \(f_b:L\to L\) for each block;
- one equation per block,

\[
 IN[b]=\bigsqcup_{p\in pred(b)}OUT[p],
 \qquad OUT[b]=f_b(IN[b]).
 \tag{D}
\]

The desired solution is the least fixed point of the monotone system. A worklist
algorithm repeatedly propagates facts until no component changes. On a finite-height
lattice it terminates; infinite-height numeric domains need widening or another
termination device. This is the conceptual core missing from the present
pass-by-pass narrative.

Use intervals to instantiate (D), without pretending LLVM uses exactly this toy
analysis. In `main`, the transfers are

\[
 [-2^{31},2^{31}-1]
 \xrightarrow{\max(0,\cdot)}[0,2^{31}-1]
 \xrightarrow{\min(8,\cdot)}[0,8].
\]

At the loop header, recurrence (R) and invariant (I) yield the safe over-approximation

\[
 i\in[0,8],\qquad acc\in[-64,96].
\]

The analysis is useful precisely because the fact holds for all paths represented
at the merge, not because a particular execution exhibited it.

Add backward liveness as a second, very compact instantiation that will be reused
for register allocation:

\[
 OUT[b]=\bigcup_{s\in succ(b)}IN[s],\qquad
 IN[b]=USE[b]\cup(OUT[b]\setminus DEF[b]).
 \tag{L}
\]

Do not give another generic algorithm; say that (D) and (L) share the same fixed-point
shape while differing in direction and lattice meaning.

#### Transformation correctness

Use equation (S) to explain legal rewrites. For a local rewrite, a useful proof
obligation is

\[
 Pre(\vec x)\Longrightarrow
 \llbracket e_{before}\rrbracket(\vec x)
 =\llbracket e_{after}\rrbracket(\vec x).
\]

Work two case-specific examples:

1. the branch chain implementing clipping may become
   \(\min(hi,\max(lo,p))\) when \(lo\le hi\) and both expressions have the same
   signed integer semantics;
2. scalar accumulation may become a tree/vector reduction because invariant (I)
   ensures no overflow and ordinary addition is associative on the reachable
   integer range.

Then give the counterfactual: accumulator saturation or IEEE-754 addition without
relaxed rules invalidates the associativity premise. This is a stronger explanation
than naming `InstCombine` and `LoopVectorize`.

Finish with equation (O): after legality has defined the feasible candidates, the
target transform information, code-size policy, and profile decide profitability.
This is where x86 vectorization versus RV64GC scalar code belongs.

**Cut:** the evidence-tier subsection, most version-specific pass attribution
caveats, and the long “reproducible causal experiment” command block. Preserve one
small side box noting that real LLVM analyses are cached and invalidated as the IR
changes.

### Section 6 — Backend: constrained optimization, not lookup

#### Instruction selection as minimum-cost covering

For a tree-shaped IR region, define a target pattern \(p\) by (i) the IR fragment it
matches, (ii) a target instruction sequence, (iii) side conditions, and (iv) cost
\(c(p)\). A classical dynamic program is

\[
 Cost(n)=\min_{p\;matches\;n}
   \left(c(p)+\sum_{u\in frontier(p,n)}Cost(u)\right).
 \tag{IS}
\]

The case supplies concrete patterns:

| IR meaning | RV64 pattern | Side condition |
|---|---|---|
| signed `load i32` to an XLEN register | `lw` | valid aligned address |
| low-32 multiply with sign-extended result | `mulw` | M extension |
| signed compare followed only by branch | `blt`/`bge` | compare result need not be materialized |
| base plus four-byte index | shift/add or pointer induction | element size 4; address semantics preserved |

For every selected pattern require denotational agreement on the relevant machine
state. Explain the engineering boundary immediately: real IR is a DAG/CFG; target
instructions have multiple results, flags, register classes, immediates, and
legalization constraints. SelectionDAG/GlobalISel therefore combine dynamic
programming ideas with rewriting and heuristics; equation (IS) is an explanatory
model, not a claim that LLVM globally solves one tree optimum.

#### Scheduling as a partial-order problem

For each dependence \(u\to v\), a legal schedule obeys

\[
 start(v)\ge start(u)+latency(u),
\]

plus per-cycle resource capacities. Minimizing makespan can increase live ranges;
minimizing register pressure can expose latency. Use the two independent loads
before `mulw` as the case example. This is enough mathematics to explain the
tradeoff without pretending the final order is globally optimal.

#### Register allocation

Construct an interference graph \(H=(V_H,E_H)\) from the liveness solution (L):
two values are adjacent if their live ranges overlap at a point where they cannot
share a physical register. A spill-free allocation is a coloring

\[
 color:V_H\to\mathcal R,
 \qquad (u,v)\in E_H\Longrightarrow color(u)\ne color(v),
 \tag{RA}
\]

subject to register classes and precolored ABI operands. With spills, the objective
becomes minimizing weighted loads/stores and moves, not merely the number of colors.
Global coloring is computationally hard, which is why production allocators use
live intervals, splitting, coalescing, eviction, rematerialization, and heuristics.

Ground (RA) in the case: the kernel's low pressure allows the loop state and loaded
operands to inhabit `t`/`a` registers without spills. Saving `ra` in `main` is **not**
a spill; it is an ABI obligation created by a nested call. This distinction is both
formal (architectural state versus virtual value allocation) and practical.

### Section 7 — RV64: a small machine semantics and an ABI relation

Model the machine state as

\[
 M=(pc,R,Mem),
\]

where \(R\) maps architectural registers to 64-bit bitvectors. Give only the rules
needed by the case. For example:

\[
 \frac{addr=R[rs]+sext(imm)\quad w=load_{32}(Mem,addr)}
 {(pc,R,Mem)\xrightarrow{\mathtt{lw\ rd,imm(rs)}}
  (pc+4,R[rd\mapsto sext_{64}(w)],Mem)}
\]

and explain that `mulw`/`addw` compute modulo \(2^{32}\) on low words and then sign
extend bit 31. Address arithmetic uses 64-bit operations while source integers use
word operations. This makes the 32/64-bit distinction a semantic fact, not a list of
mnemonics.

At the label `.Lloop`, relate source/IR and machine states by

\[
 \mathcal R_{loop}(i,acc,M)\equiv
 R[t1]=sext_{64}(i)\land R[t0]=sext_{64}(acc)
 \land R[a0]=base_A\land R[a1]=base_B\land R[a2]=k,
 \tag{SIM}
\]

plus the array-layout condition on memory. One assembly loop iteration preserves
`SIM` and realizes recurrence (R). A short prose proof should follow loads,
`mulw`, the two signed branches, `addw`, and `addiw`. This is much more illuminating
than another successful-output statement.

Represent the ABI as a pre/post relation on machine states:

\[
\begin{aligned}
 Pre_{call}:&\quad
 (a0,a1,a2,a3,a4)=(base_A,base_B,k,-8,12),\quad sp\equiv0\pmod{16};\\
 Post_{ret}:&\quad
 a0=D(n),\quad sp'=sp,\quad
 R'[s0\ldots s11]=R[s0\ldots s11].
\end{aligned}
\]

Caller-saved registers may differ. This compact relation explains parameter passing,
stack alignment, callee preservation, leaf-function frame elision, and why independent
objects can interoperate.

**Visualization:** use a split figure: register/stack state at the call boundary on
the left and the loop-state simulation relation on the right. Do not use a generic
register table without showing the case values.

### Section 8 — Assembler and ELF: symbolic evaluation

Replace the “two passes as evidence” framing with a symbolic-expression model. An
object file contains:

\[
 O=(Sections,Symbols,Relocations),
\]

where a symbol initially denotes a `(section, offset)` pair, not a virtual address.
A relocation entry is a typed expression

\[
 r=(P,type,S,A),
\]

with place \(P\), symbol \(S\), and addend \(A\). A link layout turns section-relative
coordinates into addresses, and the relocation type tells the linker how to encode
the resulting value into instruction fields.

For a RISC-V PC-relative call, let

\[
 \Delta=S+A-P,
 \quad hi=\left\lfloor\frac{\Delta+0x800}{2^{12}}\right\rfloor,
 \quad lo=\Delta-hi\cdot2^{12}.
 \tag{REL}
\]

`hi` is placed in the `AUIPC` immediate and the signed 12-bit `lo` in the following
I-type instruction. The `+0x800` compensates for sign extension of the low part.
For `PCREL_LO12_*`, state carefully that the low relocation refers back to the
corresponding high-relocation location; do not teach it as two unrelated holes.

Use `call getint` as the only worked example. Before link, `S` is unresolved and the
object contains `CALL_PLT` plus optional `RELAX`. After layout and symbol resolution,
equation (REL) can be encoded; relaxation may replace the pair by a shorter call if
range and relocation rules permit. The semantic obligation is still “transfer to
the same resolved function with the same link-register effect”.

**Visualization:** draw bytes/bit fields of `AUIPC` and `JALR` above a single
symbolic arc to `getint`, then show the linker substituting \(S\), \(P\), and \(A\).
This is better than a box saying “assembler produces `.o`”.

### Section 9 — Linking and loading: fixed points and memory maps

#### Static archive extraction

Model archive search as a fixed point. Let \(U_j\) be unresolved symbols after step
\(j\). An archive member \(m\) is extracted when

\[
 Def(m)\cap U_j\ne\varnothing,
\]

then

\[
 U_{j+1}=(U_j\setminus Def(m))\cup Ref(m).
 \tag{A}
\]

Iteration stops when no member is newly selected. This immediately explains three
engineering facts:

1. an archive is a searchable collection, not one pre-linked object;
2. order and group rescanning can matter;
3. selecting a member may satisfy one symbol while introducing new requirements.

Instantiate (A): `getint`/`putint`/`putch` cause the SysY runtime member to be
selected, but that member introduces `_impure_ptr`; in the glibc environment the
final \(U^*\) still contains it, so link failure is structurally expected. The
newlib/glibc discussion becomes an example of the algorithm rather than an
evidence narrative.

#### Loader mapping

For a `PT_LOAD` entry, define the initialized process memory succinctly:

\[
 Mem[p_{vaddr}+x]=
 \begin{cases}
 File[p_{offset}+x], & 0\le x<p_{filesz},\\
 0, & p_{filesz}\le x<p_{memsz}.
 \end{cases}
 \tag{LOAD}
\]

with page/alignment and permission constraints stated in prose. Equation (LOAD)
explains sections versus segments and `.bss` zero-fill in one place. Follow control
as `e_entry -> _start -> CRT -> main`, without treating `main` as the ELF entry.

The whole section should emphasize two algorithms—symbol fixed point and segment
mapping—rather than inventorying tool outputs.

### Section 10 — Repurpose from validation report to semantic continuity

The current Section 10 is the clearest manifestation of the wrong genre. Remove or
move to the companion README:

- the 24-execution matrix;
- exact artifact byte sizes;
- the tool-version environment table;
- the clean-checkout checklist;
- repeated distinctions among observed/inferred/assumed claims.

Retitle the chapter approximately **“What remains the same? Semantic continuity
across representations.”** Its job is to compose the earlier models.

Introduce a simulation relation \(\mathcal R_i\) between adjacent machine states.
A forward-simulation proof step has the shape

\[
 \mathcal R_i(s,t)\land s\to_i s'
 \Longrightarrow
 \exists t'.\;t\to_{i+1}^{*}t'\land\mathcal R_i(s',t').
 \tag{F}
\]

Relate (F) to the case, not to a whole-compiler proof:

- source loop state and SSA header values satisfy invariant (I);
- SSA header values and RV64 registers satisfy relation (SIM);
- the ABI pre/post relation connects the function to separately compiled callers;
- relocation and loading preserve the identity of the called runtime symbol and
  its machine address.

Because refinement is transitive,

\[
 P_0\succeq P_1\succeq\cdots\succeq P_m
 \Longrightarrow P_0\succeq P_m.
 \tag{T}
\]

Equation (T) is the conceptual reason compiler architectures use intermediate
languages with local contracts. It does not assert that the manuscript has proved
every arrow. Add one short closing paragraph distinguishing:

- a mathematical explanation/proof for this bounded case (the invariant and
  selected local correspondences);
- testing as a practical smoke check in the companion repository;
- verified compilation or translation validation as research mechanisms for
  mechanizing larger parts of (F).

This is enough. Testing should not remain the paper's narrative climax.

### Section 11 — MLIR: lowering as typed refinement over a partial order

The current chapter correctly rejects a simplistic dialect staircase. Formalize that
insight.

Let a conversion target be a predicate

\[
 Legal_T(op,types,attrs)\in\{true,false\}.
\]

A full conversion succeeds only if

\[
 \forall op\in P'.\;Legal_T(op),
 \tag{M1}
\]

while partial conversion requires this only for operations explicitly declared
illegal and permits unknown/high-level operations to coexist. Crucially, (M1) is a
**syntactic acceptance condition**, not semantic correctness. Every conversion must
also satisfy

\[
 \llbracket P'\rrbracket_{T}
 \subseteq
 \llbracket P\rrbracket_{S}.
 \tag{M2}
\]

Type conversion and materialization construct relations between values when the
source and target types differ; they do not make (M2) automatic.

Avoid saying that lowering simply “loses information”. It simultaneously discards
some structure and commits to new decisions. Use an **information/commitment
matrix** rather than a linear flowchart:

| Representation | Preserved semantic structure | Newly committed decisions |
|---|---|---|
| tensor/linalg | shape, iteration maps, reduction dimension, value semantics | little or no storage identity |
| scf/vector | explicit loop order, iter args, vector lanes | schedule and tail strategy |
| memref/HIVM | layout, address space, transfers, synchronization | storage identity and memory hierarchy |
| LLVM dialect/IR | CFG, scalar/vector ops, explicit addresses | ABI-compatible low-level types |
| object/binary | instructions, symbols, relocations | encodings and most layout choices |

There is no scalar “abstraction height” that totally orders these rows. Bufferization,
for example, forgets pure tensor value semantics while adding aliasing, lifetime, and
layout facts.

Instantiate the case as a sequence of relations:

\[
 \operatorname{reduce}_{i<k}
   (\operatorname{clip}(A_iB_i))
 \rightsquigarrow
 \text{structured map+reduction}
 \rightsquigarrow
 \text{loop with iter-arg}
 \rightsquigarrow
 \text{GM/UB transfers + local reduction}.
\]

At each arrow name the information consumed and the decision fixed. The principal
engineering tradeoff is now precise:

- delaying lowering preserves structure for fusion, tiling, and mapping;
- delaying too long increases dialect/interface surface, compilation cost, and the
  number of semantic combinations a backend must support;
- early lowering reuses mature low-level machinery and simplifies debugging, but may
  make later optimizations reconstruct information unreliably.

The official Ascend VecAdd should remain a concrete illustration of GM/UB transfer,
but delete the repeated evidence calibration. State once that the clipped-dot path
is a design projection, not an executed result.

### Section 12 — Frontiers: one optimization problem, four ways to manage uncertainty

Keep the four-loop philosophical organization, but make equation (O) its center.

- verified compilation and translation validation approximate or certify membership
  in \(\mathcal F(P)\);
- superoptimization and equality saturation enlarge the candidate set;
- static models, profiles, and ML estimate \(C(Q;\theta)\);
- JIT/AOT decide when \(\theta\) becomes known;
- multilevel IR determines which candidate-generating transformations remain
  expressible;
- incremental/reproducible builds govern reuse of the computation that produced
  \(Q^*\).

This makes the technologies consequences of one model rather than a literature
stack. Keep the strongest production examples, but remove the pseudo-precise P1--P5
maturity scoreboard unless a calibrated rubric is defended. A compact table with
columns “changes feasible set / changes cost estimate / changes decision time /
changes reusable state” is more analytical.

For refinement, use traces or simulations consistently; do not alternate among
equality, “improves”, and an undefined \(\preceq\). A CompCert paragraph can explain
that pass-local simulations compose. An Alive2 paragraph can explain that a
validator checks a particular pair rather than proving the optimizer implementation.
These are conceptual contrasts, not a reason to return to evidence taxonomy.

### Section 13 — Conclusion: three principles

The current conclusion is the manuscript's strongest section. Preserve its tone,
but reduce five partly overlapping conclusions to three connected principles:

1. **Meaning is relational.** Adjacent representations need not look alike; they are
   connected by semantics, simulations, ABI relations, and relocation equations.
2. **Representations are budgets of information and commitment.** A good IR exposes
   the facts needed by the next transformation while postponing decisions that would
   destroy useful structure.
3. **Optimization separates possibility from preference.** Semantics defines legal
   candidates; analysis discovers applicable facts; a target/workload cost model
   chooses among them under compilation-time and maintenance constraints.

End with the existing practical injunction to point at a concrete object, but extend
it: identify its mathematical role, the invariant it preserves, and the engineering
choice it encodes.

## 4. A compact formal dependency graph

The revision should make definitions depend on one another rather than introducing
isolated notation:

```text
case function (C)
      |
      +--> loop invariant (I) --> source step (R)
      |                              |
      |                              +--> SSA phi recurrence
      |                              +--> interval facts / vector legality
      |                              +--> RV64 simulation (SIM)
      |
trace semantics --> refinement (S) --> local rewrite legality
                              |       --> instruction-pattern correctness
                              |       --> MLIR conversion correctness (M2)
                              +------> transitive compiler composition (T)

CFG --> dominance --> SSA placement
CFG --> dataflow fixed point (D) --> intervals
                             +----> liveness (L) --> interference graph (RA)

symbolic object --> relocation (REL) --> linked address
undefined set --> archive fixed point (A) --> symbol resolution
program headers --> loader map (LOAD) --> process state
```

If an equation is not connected to this graph, it is probably decorative and should
not enter the manuscript.

## 5. Visual redesign tied to the formal spine

The current text boxes and arrow rows should be replaced by a small, consistent
visual language. Do not create one bespoke visual grammar per chapter.

### 5.1 Encoding

- rounded blue nodes: representations;
- dark arrows: semantics-preserving transformations;
- amber labels: decisions newly fixed;
- green badges: invariants available;
- dashed gray arrows: author projections or possible paths, not executed stages;
- red outlines only for genuine contract violations, never merely “not observed”.

Use the same symbols for source variables, SSA values, and registers in all figures:
\(i/acc\), `%i/%acc`, and `t1/t0`. This visual continuity is more valuable than
decorative icons.

### 5.2 Required figures

1. **Semantic descent map** (Section 1): central recurrence traveling through source,
   AST/typed state, SSA, RV64, object, and process.
2. **Loop invariant strip** (Section 2): initialization, one preservation step, exit;
   include the range bound beneath each state.
3. **CFG plus dominator tree** (Section 4): actual four-block graph, phi edge labels,
   loop invariant at the header.
4. **Fixed-point iteration heatmap** (Section 5): blocks by iteration; interval facts
   grow until stable. Four or five cells suffice.
5. **Backend constraint triptych** (Section 6): IR pattern cover, dependency DAG, and
   interference graph—three views of one loop body.
6. **Typed relocation anatomy** (Section 8): bytes plus `S+A-P`, HI20/LO12 split, and
   possible relaxation.
7. **Archive resolution fixed point and loader map** (Section 9): unresolved-symbol
   set on the left, file-to-memory segments on the right.
8. **MLIR information/commitment matrix** (Section 11): a matrix or two-axis map, not
   a left-to-right staircase.

Graphviz is suitable for CFG, dominator, dependency, and interference graphs; export
vector PDF/SVG with fonts embedded. TikZ is suitable for annotated equations,
bit-fields, stack layouts, and the information matrix. Python/Matplotlib is justified
only for data-driven plots such as the fixed-point heatmap; do not rasterize diagrams
that are naturally vector graphics. Every figure should answer a question that would
otherwise require a paragraph.

## 6. Formalism budget and anti-patterns

### Include

- one semantic function for the case;
- one loop invariant and proof;
- one typing derivation;
- one source-state transition;
- precise CFG/dominance/SSA definitions;
- one dataflow fixed-point system plus liveness reuse;
- one refinement/simulation schema;
- one instruction-selection recurrence;
- one interference-graph condition;
- one ABI pre/post relation;
- one relocation equation and one archive fixed point;
- one MLIR legality/refinement distinction.

### Do not include

- a complete SysY grammar or complete dynamic semantics;
- progress/preservation proofs for SysY;
- a mechanized proof of the authored LLVM or assembly program;
- pseudo-formal notation for every compiler pass;
- a theorem claiming full end-to-end correctness of the real toolchain;
- repeated warnings that the report does not prove such a theorem;
- formal symbols that are never instantiated on `clipped_dot`;
- mathematical decoration for straightforward tool invocation.

The formalism should occupy roughly 15--20% of the revised body and should reduce,
not increase, total length by replacing repeated prose.

## 7. Engineering tradeoffs that must accompany the mathematics

| Formal object | What it clarifies | What production compilers compromise |
|---|---|---|
| typing judgment | local static meaning of syntax | diagnostics, recovery, extensions, and parser/Sema interleaving matter to users |
| operational semantics | what execution step means | real languages include UB, libraries, concurrency, exceptions, and volatile effects |
| dominance/SSA | where definitions can reach uses | memory needs alias/effect models; maintaining canonical form has compile-time cost |
| lattice fixed point | why iterative analysis converges | precision competes with time/memory; widening and sparse formulations trade guarantees |
| refinement/simulation | what “same program” should mean | full proofs are expensive; production mixes testing, validators, assertions, and conservative fallbacks |
| pattern covering | why selection is not textual substitution | DAGs, register classes, immediates, legalization, and phase coupling defeat global optimality |
| graph coloring | the finite-register constraint | heuristic allocation, splitting, and rematerialization dominate exact coloring at scale |
| ABI relation | independent compilation contract | varargs, aggregates, TLS, unwind, and platform variants expand the real relation |
| relocation algebra | deferred address computation | relaxation and paired relocations make layout iterative and target-specific |
| dialect legality + refinement | why mixed IR can be well formed | conversion coverage, interface maintenance, compile time, and diagnostic quality bound extensibility |

Every mathematical subsection should end with one such paragraph. That is how the
paper avoids both extremes: superficial literature stacking and formal theory
detached from systems reality.

## 8. Recommended sources and bibliography additions

Prefer primary papers or official specifications. Several required sources already
exist in the bibliography: Cytron et al. on SSA (`llvm-cytron1991`), Chaitin et al.
on coloring (`llvm-chaitin1981`), LLVM LangRef/code-generation documentation,
CompCert, Alive2, the MLIR paper and documentation, the RISC-V psABI, and the System V
ABI. Add the following only where the corresponding formal idea is actually used:

1. Gordon D. Plotkin, *A Structural Approach to Operational Semantics*, DAIMI
   FN-19, Aarhus University, 1981; reprinted in *Journal of Logic and Algebraic
   Programming* 60--61 (2004), 17--139. Use for the transition-system style in
   Section 3.
2. Andrew K. Wright and Matthias Felleisen, “A Syntactic Approach to Type
   Soundness,” *Information and Computation* 115(1), 1994, 38--94,
   DOI `10.1006/inco.1994.1093`. Cite only if the prose mentions the standard
   progress/preservation discipline; the manuscript itself need not prove it.
3. Gary A. Kildall, “A Unified Approach to Global Program Optimization,” POPL
   1973, 194--206, DOI `10.1145/512927.512945`. Use for monotone dataflow fixed
   points.
4. Thomas Lengauer and Robert E. Tarjan, “A Fast Algorithm for Finding Dominators in
   a Flowgraph,” *TOPLAS* 1(1), 1979, 121--141,
   DOI `10.1145/357062.357071`. Use only if algorithmic dominance computation is
   discussed; the definition itself needs no historical citation.
5. Alfred V. Aho and Stephen C. Johnson, “Optimal Code Generation for Expression
   Trees,” STOC 1975, 207--217, DOI `10.1145/800116.803770`. Use for equation (IS)
   and explicitly delimit the tree-machine model.
6. Lal George and Andrew W. Appel, “Iterated Register Coalescing,” POPL 1996,
   208--218, DOI `10.1145/237721.237777`. Use if the revised backend explains
   simplify/coalesce/freeze/spill beyond the existing Chaitin reference.

The official RISC-V psABI gives the relocation formulas and paired-relocation rules;
do not source those formulas from tutorials. The official LLVM loop terminology
documents Loop Simplify and LCSSA invariants. The MLIR dialect-conversion and LLVM
target documents explicitly distinguish partial/full legality and progressive
conversion. The CompCert sources state semantic preservation through composed
simulations. These production/academic pairings satisfy the manuscript's need to
connect mathematical structure to real compiler engineering.

## 9. Recommended revision order

1. Rewrite Sections 1--2 around (S), (C), (I), and (R).
2. Add syntax/typing/semantics to Section 3 and CFG/dominance/SSA to Section 4.
3. Replace the evidence-centered optimization narrative with (D), legality, and (O).
4. Add backend constraint models (IS), scheduling, (L), and (RA).
5. Connect source and RV64 states with (SIM), then explain ABI, relocation, archive
   resolution, and loading through their equations.
6. Repurpose Section 10 as the composition chapter using (F) and (T).
7. Rebuild Section 11 around (M1)/(M2) and the information/commitment matrix.
8. Compress Section 12 using (O), then let Section 13 state the three principles.
9. Only after the prose stabilizes, build the eight vector figures; otherwise diagram
   geometry will encode a chapter structure that is still changing.

This order preserves the single-writer boundary by chapter range and gives later
sections a stable notation to reuse.
