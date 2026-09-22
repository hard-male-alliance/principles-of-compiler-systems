# Visual System for the Compiler-Systems Survey

## Status and scope

This note specifies a coherent visual language for the LLNCS survey. It is an
editorial design specification, not a request to decorate the existing draft.
Every proposed figure must replace prose, a weak diagram, or a prose-heavy
table; figures must not simply be appended to an already long manuscript.

The intended reader is learning how one small program changes meaning and
representation while passing through a compiler system. The visual system must
therefore help the reader answer three questions:

1. **What is explicit in this representation?**
2. **Which choice is made here, and which choice remains open?**
3. **What semantic relationship connects this object to the object on either
   side of the boundary?**

This emphasis deliberately moves away from the current manuscript's visual
language of evidence collection. The case is a worked explanatory thread, not
an experiment whose every screenshot must be audited.

## Audit of the current manuscript

The current 55-page PDF contains 4 figures, 26 tables, 19 `lstlisting`
environments, 9 `verbatim` environments, and 7 displayed equation/alignment
environments. This distribution makes the paper read as prose plus inventories.
It does not give the reader durable spatial models of the compiler.

### Existing figures

| Current figure | What the rendered PDF shows | Why it underperforms | Disposition |
|---|---|---|---|
| Fig. 1, pipeline map (p. 6) | A long sentence of stage names inside a framed box | It has no hierarchy, the two provenance paths are described in prose rather than drawn, and the type is too small. A left-to-right list does not show what changes across a boundary. | Replace completely with the compilation atlas below. |
| Fig. 2, assembly CFG (p. 28) | A `tabular` arrangement with arrows between text fragments | The arrows do not define an unambiguous graph; branch targets, merge block, exit, and back edge are not spatially coherent. | Replace with the representation-comparison figure below; do not preserve this pseudo-CFG. |
| Fig. 3, assembler commitment boundary (p. 29) | Four short text rows arranged as an equation | It repeats adjacent prose, does not show how a relocation connects a use, symbol, and definition, and is visually indistinguishable from a table. | Absorb into the ELF/link/load figure below. |
| Fig. 4, MLIR partial order (p. 40) | Four horizontally compressed boxes scaled to text width | `\resizebox` makes the labels barely legible. More importantly, a linear chain contradicts the intended claim that dialects coexist and are not pipeline stages. | Replace with the mixed-abstraction matrix below. |

### Tables and listings

The tables are individually serviceable, but too many cells contain paragraphs
that should be explanatory prose. Several tables encode processes or dependency
structures for which position and connection would be more informative than
rows. Table rules also alternate between raw `\hline` and `booktabs`. The
listings use the same framed, numbered treatment whether the reader must inspect
line identity or merely see a three-line idiom. This flattens visual hierarchy:
the normative SysY program, a decisive SSA fragment, a shell command, and a
minor syntax example all look equally important.

The revised manuscript should use:

- **figures** for structure, transformation, correspondence, and spatial
  relationships;
- **tables** only for lookup or comparison along common attributes;
- **listings** only when exact syntax or instruction order is the object of
  explanation;
- **equations** for semantics, proof obligations, and cost models;
- **prose** for causal explanation and engineering judgment.

## Visual grammar

### Semantic roles, not chapter colors

Use color to encode the role of information, consistently across all figures.
Never assign a different decorative color to every compiler phase.

| Role | Color | Redundant non-color encoding | Meaning |
|---|---|---|---|
| Preserved semantic fact | blue `#0072B2` | thick solid outline | A relation that must survive the transition |
| Newly explicit decision | orange `#E69F00` | pale filled box | A choice or structure made explicit at this layer |
| Deferred decision | purple `#CC79A7` | dashed outline/edge | Information deliberately carried forward for later resolution |
| Constraint or invalid path | vermilion `#D55E00` | cross or dotted boundary | A condition that blocks a transformation or rules out a state |
| Representation/artifact | neutral gray | ordinary thin outline | Syntax, AST, IR, object, or image serving as the carrier |

The palette is adapted from color-vision-safe scientific practice. Color is
never the sole carrier of meaning: captions and labels say “solid,” “dashed,”
or name the role rather than referring only to hue. Wong's guidance on
color-vision accessibility and later scientific-figure guidance both recommend
such redundancy and grayscale checks.[^wong-color][^crameri-color]

### Shapes and edges

- Rounded rectangle: a representation or artifact.
- Small square tag attached to an artifact: a fact made explicit at that layer.
- Solid arrow: transformation or semantic correspondence.
- Dashed arrow: a deliberately deferred decision or a hand-authored
  correspondence, never “something vaguely related.”
- Double line or brace: boundary governed by an external contract such as the
  language semantics, IR semantics, ISA, ABI, or object format.
- Red cross: illegal transformation or violated precondition. Do not use red
  merely for emphasis.
- A node should contain at most two short lines. Put explanations next to the
  relevant edge rather than in a remote legend.

Direct labels and spatial proximity are important here: research on
split-attention shows why forcing the reader to shuttle between a diagram and a
separate explanatory key can impose avoidable cognitive load, although the
effect depends on task and design.[^split-attention] The design rule is thus not
“put all prose inside the figure,” but “place the shortest necessary explanation
beside the object it explains.”

### Typography and density

- Minimum figure text is `\footnotesize`; `\scriptsize` is prohibited for
  conceptual figures.
- A figure should remain readable at 100% zoom on an A4 page and after grayscale
  printing.
- Use at most 7 primary nodes in one panel. If a process has more steps, group
  them by responsibility rather than shrinking them.
- Prefer a vertical or wrapped two-row layout over a single 12-cm horizontal
  chain.
- Do not use `\resizebox` around TikZ. It hides sizing mistakes and scales text
  below the document's typographic floor.
- Captions state the intellectual takeaway, not merely the depicted nouns.
- Every figure must be introduced by a question in the preceding paragraph and
  followed by the one conclusion the reader should retain.

## Figure program

The core program contains seven figures. Figures V1--V7 form a system: the same
roles, shapes, and two semantic threads recur. The recurring threads are
`a[i] * b[i]` (local computation) and `putint` (cross-component call).

### V1. Compilation atlas: one program, changing obligations

**Placement:** Section 2, replacing current Fig. 1 and most of the subsequent
paragraph explaining solid/dashed paths.

**Question answered:** What changes at each major boundary, and what is carried
forward?

**Layout:** A full-width, two-row TikZ matrix with six columns:

1. source text,
2. typed program,
3. SSA/CFG,
4. target program,
5. relocatable object,
6. process image.

The upper row contains the six neutral artifact boxes. The lower row contains
one short orange tag per column stating the new explicit structure:

`tokens and scopes` → `types and binding` → `data/control dependence` →
`instructions, registers, ABI` → `symbols and relocations` → `virtual addresses
and observable effects`.

A blue ribbon labelled `D(n)` runs underneath all six columns to show the
preserved semantic obligation. Purple dashed notes at the last three boundaries
name genuinely deferred choices: register placement, external symbol address,
and load address. A small brace groups source-to-SSA as **language/IR
semantics**, target as **ISA + ABI**, and the last two columns as **ELF + OS
contracts**. The C observation carrier and hand-written `.ll`/`.S` should appear
as small side-entry arrows, not as main stages.

**Exact caption:**

> **同一个计算在六种表示中拥有不同的显式结构。蓝线表示必须保持的语义关系；橙色标签表示本层新增的决定；紫色虚线表示仍被有意延期的决定。方框是表示边界，而不等同于操作系统进程。**

**Why this is not another flowchart:** Its primary encoding is a matrix of
representation versus commitment, not a line of tool names. It lets the reader
compare columns vertically and follow one invariant horizontally.

### V2. The mathematical case at a glance

**Placement:** Section 2, immediately after the definition of `D(n)`; replace
the three raw number displays and the known-answer table if it survives the
broader revision.

**Question answered:** What exactly does clipping change, and how does the prefix
length select a result?

**Layout:** Two aligned panels.

- **Panel A:** A compact PGFPlots graph of
  `clip(x,-8,12)`: horizontal at -8, diagonal with slope one, then horizontal at
  12. Directly label `lo=-8`, identity region, and `hi=12`; no legend.
- **Panel B:** An eight-column worked strip. Each column contains `a_i b_i` on
  top, the clipped term below, and a running prefix-sum polyline at the bottom.
  The changed terms (-9, -10, 15) use orange fill and the prefix selected by
  `k=clip(n,0,8)` is indicated by a movable-looking brace. This is a worked
  example, not an empirical result chart.

**Exact caption:**

> **案例计算的两次限制发生在不同对象上：输入决定前缀长度 (k)，逐项截断决定每个加数；蓝色折线给出 (k=0,\ldots,8) 时的前缀和。**

**Implementation:** PGFPlots is justified only for Panel A and the prefix line;
the value strip is a TikZ matrix. Use explicit coordinates so the figure has no
runtime data dependency.

### V3. From syntax to typing judgment

**Placement:** Section 3, after the parser/Sema discussion; replace the
prose-heavy “semantic analysis result and downstream obligation” table.

**Question answered:** What does a front end add beyond recognizing grammar?

**Layout:** A two-panel worked derivation for `a[i] * b[i]`.

- **Panel A:** A small concrete-syntax/AST tree. Leaves are `a`, `[`, `i`, `]`,
  `*`, and the mirrored `b[i]`. Interior nodes are `ArraySubscriptExpr` and
  multiplication. Gray nodes show syntax; orange tags show the resolved
  declaration and type.
- **Panel B:** A compact typing derivation ending in
  `Γ ⊢ a[i] * b[i] : int`. The premises make array-to-pointer conversion,
  integer index, lvalue-to-rvalue conversion, and integer multiplication
  explicit. A blue arrow maps the typed expression to the later pair of address
  computations, loads, and multiply in IR.

**Exact caption:**

> **解析给出表达式的树形结构，语义分析把名字、类型与隐式转换附着到同一结构；这些判断随后约束地址计算、载入和乘法的 IR 生成。**

This figure should carry the mathematical typing content; the surrounding prose
should explain why a production compiler often combines these logical duties.

### V4. One loop seen as control flow and data flow

**Placement:** Section 4, replacing the current assembly pseudo-CFG in Section 7
and reducing repeated block-by-block listings. Cross-reference it later from the
assembly chapter.

**Question answered:** Why does SSA need both a graph and `phi` values, and how
does the same loop later retain its shape without retaining source variables?

**Layout:** A true CFG at left and a synchronized value-flow overlay at right.
Use four named blocks: `entry`, `loop`, `body`, `exit`. The loop block contains
`i = phi [0,entry], [i+1,body]` and
`acc = phi [0,entry], [acc+term,body]`. The body contains load–multiply–clip.
Solid black edges are CFG edges; blue curved edges are loop-carried values.
Beside the body, a small three-row correspondence maps:

- `i` → scaled addresses → RV64 pointer increments,
- `term` → compare/select or branches → selected register value,
- `acc` → loop-carried SSA value → `addw` accumulator.

Do not reproduce full IR or assembly inside the nodes. Refer to the nearby
listing for exact syntax.

**Exact caption:**

> **循环同时是一张控制流图和一组跨回边的数据依赖：$\phi$ 节点表达“来自哪条前驱边的值”，而后端可以把索引归纳改写为指针递增，只要这些依赖保持不变。**

### V5. Optimization as a conditional commuting diagram

**Placement:** Opening third of Section 5, replacing the evidence-ranking table
and several listings that merely show before/after syntax.

**Question answered:** In what precise sense is an optimization allowed, and why
does legality not imply profitability?

**Layout:** A commuting square on the left and an engineering decision funnel on
the right.

Left square:

```
        transform T
    P --------------> P'
    |                  |
 [[·]]               [[·]]
    v                  v
 behavior(P, x) == behavior(P', x)
          for x satisfying A
```

The assumption box `A` names bounds, overflow semantics, alias information, and
reduction laws for this case. A vermilion crossed branch shows the alternative
“saturate the accumulator after every addition,” for which arbitrary reassociation
does not follow.

The right funnel has three gates: **semantically legal**, **representable on the
target**, and **profitable under the cost model**. Candidate scalarization,
vectorization, and predication choices may stop at different gates. This makes
the formal/engineering distinction visible instead of treating the optimizer as
either theorem prover or bag of passes.

**Exact caption:**

> **优化首先要求语义图在假设 (A) 下交换；通过合法性门槛后，目标特性与成本模型才决定是否采用该改写。合法不等于有利，未采用也不等于不可证明。**

### V6. Object, link, and load: where an unresolved call goes

**Placement:** Across Sections 8–9, replacing current Fig. 3 and at least one of
the section/segment comparison tables.

**Question answered:** How can an instruction exist before the callee address is
known, and how do link-time and load-time views differ?

**Layout:** Three nested-container panels connected left-to-right.

1. **Relocatable object:** Draw `.text`, `.rela.text`, and `.symtab` as stacked
   regions. A call-site dot in `.text` connects to an `R_RISCV_CALL` entry, then
   to undefined symbol `putint` in `.symtab`.
2. **Link:** Draw an archive member containing the definition of `putint`, the
   merged output sections, and the resolved edge. Mark relaxation as an optional
   orange rewrite after layout, not as a separate pipeline stage.
3. **Load:** Draw `PT_LOAD` segments mapped into a simplified virtual address
   space. A brace distinguishes file sections (linker's organization) from
   segments (loader's mapping unit). A short arrow from entry point through
   runtime startup to `main` prevents the false impression that the kernel calls
   `main` directly.

Use a single call as the narrative spine. Do not include numeric sizes unless a
number explains alignment or relocation width; the object-inspection inventory
belongs in prose or an appendix.

**Exact caption:**

> **对 \texttt{putint} 的调用从“带类型的未决引用”变为链接后的地址关系，再随可装载段进入进程映像；节、符号、重定位和段分别服务于不同的决定。**

### V7. MLIR as a mixed-abstraction state, not a staircase

**Placement:** Section 11, replacing current Fig. 4.

**Question answered:** How can progressive lowering preserve the right
high-level facts without requiring a module-wide phase change?

**Layout:** A 4×3 matrix rather than a horizontal chain. Rows are **computation**,
**data**, **control**, and **target commitment**. Columns are three snapshots,
not stages:

| | Structured snapshot | Mixed snapshot | Target-oriented snapshot |
|---|---|---|---|
| Computation | `linalg` reduction + clipped map | `vector` + residual `linalg` | target intrinsics / LLVM dialect |
| Data | `tensor` values | tensor and `memref` coexist | buffers, address spaces |
| Control | implicit iteration domain | `scf.forall` / `scf.for` | branches and calls |
| Target | shape/layout attributes | vector width and memory space | ABI and device-specific operations |

Use connected orange cells to show newly explicit decisions and retain a blue
outline around facts still represented structurally. Two arrows labelled
**rewrite under interfaces** and **legalize under conversion target** connect the
snapshots. A dashed arrow bypassing the mixed snapshot is crossed out and
labelled “premature information loss,” not “invalid in every implementation.”

**Exact caption:**

> **渐进式降低改变的是模块中各种抽象的组成比例：计算、数据、控制和目标约束可以按不同节奏显式化；接口与合法性条件使混合表示仍可组合。**

## Optional synthesis figure

If the conclusion still needs a visual anchor after prose revision, add one
compact control-loop figure rather than an eighth pipeline. Place three questions
at the vertices of a triangle: **what information is preserved**, **how a
transformation is chosen**, and **how semantic and engineering constraints are
discharged**. Put PGO/MLGO, equality saturation, verified compilation,
heterogeneous lowering, and JIT/AOT around the edge they primarily modify. The
caption should state that frontier methods change one or more control variables;
they are not disconnected trends. Omit this figure if the revised conclusion is
already concise—the seven core figures are sufficient.

## Table and listing policy

### Tables to keep

Keep a table only if a reader is likely to compare cells in the same row or scan
one attribute down a column. Good candidates include:

- RV64 instruction/semantic responsibility;
- pseudo-instruction versus expansion caveats;
- MLIR rewrite/conversion/analysis guarantees;
- frontier technique versus controlled object and deployment maturity.

Use `booktabs` consistently (`\toprule`, `\midrule`, `\bottomrule`), no vertical
rules, sentence fragments rather than paragraphs, and no more than four columns
in the LLNCS measure. If a cell requires more than about three printed lines,
move the reasoning into prose.

### Tables to remove or transform

- Remove evidence-level taxonomies from the main narrative. They serve the old
  audit framing rather than the revised survey.
- Replace source-fact-to-mechanism and semantic-analysis-result tables with V1
  and V3.
- Replace known-answer tables with V2.
- Absorb section/segment timing and assembler commitment tables into V6.
- Move exact tool versions, file sizes, and reproducibility checklists to a
  compact appendix or repository README if retained at all.

### Listings

Define three listing roles rather than one universal “evidence” style:

1. **Normative program:** framed, line-numbered, `\small`; used once for the SysY
   case.
2. **Explanatory fragment:** no frame, no line numbers, 3–12 lines,
   `\footnotesize`; accompanied by 1–3 margin-like callouts using circled tags.
3. **Command/inspection snippet:** light gray background, no syntax color, no
   line numbers; use only when the command itself teaches an interface.

Do not show both a long listing and a table that paraphrases it. A figure may use
short exact fragments, but it should point to a nearby listing rather than copy
it at unreadable size.

## LaTeX implementation guidance

### Dependencies

TikZ is sufficient for structural diagrams; PGFPlots has a clear payoff only for
the clipping function and prefix-sum line. No Python or JavaScript generator is
needed because the figures are semantic diagrams with carefully controlled
labels, not large data-driven plots. Keeping them in LaTeX preserves fonts,
vector output, references, and one-command CI builds.

Add only:

```tex
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{
  arrows.meta,backgrounds,calc,decorations.pathreplacing,
  fit,matrix,positioning
}
```

The official TikZ manual recommends matrices for aligned diagram elements and
chains for systematic sequences; the proposed layouts use matrices because
alignment and comparison matter more than automatically creating another
chain.[^tikz-matrix][^tikz-chain] `arrows.meta` is the maintained configurable
arrow-tip library.[^tikz-arrows]

### Shared style vocabulary

Centralize styles in `preamble.tex`; individual figures must not invent their
own colors, corner radii, arrowheads, and font sizes.

```tex
% Visual semantics / 视觉语义：颜色始终由线型或形状冗余编码。
\definecolor{semblue}{HTML}{0072B2}
\definecolor{decisionorange}{HTML}{E69F00}
\definecolor{deferredpurple}{HTML}{CC79A7}
\definecolor{constraintred}{HTML}{D55E00}
\definecolor{artifactgray}{HTML}{6B7280}

\tikzset{
  vis/artifact/.style={
    draw=artifactgray, rounded corners=1.2pt, line width=.45pt,
    fill=black!2, align=center, inner sep=3.5pt, font=\footnotesize
  },
  vis/decision/.style={
    draw=decisionorange!85!black, fill=decisionorange!13,
    rounded corners=1.2pt, align=center, inner sep=3pt,
    font=\footnotesize
  },
  vis/semantic/.style={draw=semblue, line width=.9pt},
  vis/deferred/.style={
    draw=deferredpurple!85!black, dashed, line width=.7pt
  },
  vis/constraint/.style={
    draw=constraintred, densely dotted, line width=.8pt
  },
  vis/edge/.style={
    -{Stealth[length=1.8mm,width=1.25mm]}, line width=.55pt
  },
  vis/label/.style={font=\footnotesize, align=center},
  vis/note/.style={font=\footnotesize, align=left, text=black!85}
}
```

Use `matrix of nodes` for V1, V2's value strip, and V7. Use `fit` and the
background layer only to group already aligned objects; do not draw large boxes
first and squeeze content into them. The TikZ manual documents `fit`,
`backgrounds`, and `positioning` as complementary tools for such grouped
diagrams.[^tikz-fit]

For V2, configure PGFPlots for a quiet explanatory plot:

```tex
\begin{axis}[
  width=.43\linewidth, height=4.0cm,
  axis lines=middle, ticks=none, clip=false,
  xlabel={$x$}, ylabel={$\operatorname{clip}(x,-8,12)$},
  every axis plot/.append style={semblue, very thick}
]
```

Do not use a colormap; the quantity is one-dimensional and direct labels are
clearer. PGFPlots should not be introduced into non-quantitative diagrams merely
for consistency.[^pgfplots]

### Float behavior and page economy

- Prefer `[tbp]`; avoid `[H]`, which can create large white holes in an LLNCS
  manuscript.
- Keep each figure at `0.94\linewidth` or less without scaling text.
- A core figure should occupy roughly 0.35–0.55 page including caption.
- Each added figure must remove at least one redundant table, listing, or 2–4
  explanatory paragraphs. The target is a shorter and more visual paper, not a
  longer paper with illustrations.
- Keep figure source near its first conceptual use. If the TikZ grows beyond
  roughly 70 lines, move it to `report/figures/<name>.tex` and `\input` it.
- Figure source is production code: use short semantic node names, define styles
  once, and comment only non-obvious layout constraints.

## Quality gates

Visual correctness is not proven by a successful LaTeX build. For each revised
figure:

1. Build from a clean `report/build` directory using the repository's normal
   `latexmk` path.
2. Reject all overfull boxes, missing glyphs, undefined references, and package
   warnings that affect output.
3. Render the figure page at 150 dpi and inspect it at 100% scale.
4. Render or convert the same page to grayscale. Every role must remain
   distinguishable by line style, fill value, shape, or direct label.
5. Verify that no conceptual figure uses text smaller than `\footnotesize`.
6. Ask a cold reader to state the figure's one-sentence takeaway using only the
   figure and caption. If the answer becomes a list of boxes, the figure lacks an
   argument.
7. Inspect surrounding pages: a float must not precede the paragraph that poses
   its question, strand a heading, or leave a half-empty page.
8. Check that textual claims and figure labels use the same technical terms
   (`section` versus `segment`, semantic legality versus profitability, dialect
   versus stage). A beautiful diagram with a changed ontology is a regression.

## Recommended implementation order

1. Define the shared visual styles and implement V1. It establishes the grammar
   against which all later figures are judged.
2. Implement V2 and V3; these anchor the mathematical and PL foundations early,
   before the reader reaches implementation detail.
3. Implement V4 and V5 together so the SSA explanation, formal optimization
   condition, and engineering trade-off use consistent symbols.
4. Implement V6 and delete both obsolete assembler/linker diagrams and redundant
   inventory tables.
5. Implement V7 without `\resizebox`; if it does not fit at `\footnotesize`,
   simplify labels rather than scale the figure.
6. Perform the table/listing pass only after the figures settle. This prevents
   deleting an explanation before its replacement exists.
7. Run the visual quality gates over the complete PDF, not just isolated figure
   previews.

## References for the design choices

[^wong-color]: Bang Wong, “Color blindness,” *Nature Methods* 8, 441 (2011), https://doi.org/10.1038/nmeth.1618.
[^crameri-color]: Timothy B. Plante and Mary Cushman, “Choosing color palettes for scientific figures,” *Research and Practice in Thrombosis and Haemostasis* 4(2), 176–180 (2020), https://doi.org/10.1002/rth2.12308.
[^split-attention]: Mareike Florax and Rolf Ploetzner, “What contributes to the split-attention effect? The role of text segmentation, picture labelling, and spatial proximity,” *Learning and Instruction* 20(3), 216–224 (2010), https://doi.org/10.1016/j.learninstruc.2009.02.021.
[^tikz-matrix]: PGF/TikZ Manual, “Matrices and Alignment,” https://tikz.dev/tikz-matrices.
[^tikz-chain]: PGF/TikZ Manual, “Chains,” https://tikz.dev/library-chains.
[^tikz-arrows]: PGF/TikZ Manual, “Arrows,” https://tikz.dev/tikz-arrows.
[^tikz-fit]: PGF/TikZ Manual, “A Petri-Net for Hagen” (use of `fit`, `backgrounds`, and `positioning`), https://tikz.dev/tutorial-nodes.
[^pgfplots]: Christian Feuersänger, *Manual for Package PGFPlots*, https://ctan.org/pkg/pgfplots.
