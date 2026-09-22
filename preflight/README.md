# 编译器预备实验 / Compiler preflight experiment

本目录提供一条可复现的纵向切片：同一个 SysY 程序分别以源码、手写 LLVM IR
和手写 RISC-V RV64GC Linux 汇编表示，经预处理、语法树、IR、汇编、目标文件和
链接阶段，最终用共享测试向量比较可观察行为。

This directory provides a reproducible vertical slice. The same SysY program
is represented as source, handwritten LLVM IR, and handwritten RISC-V RV64GC
Linux assembly. It traverses preprocessing, AST, IR, assembly, object, and link
stages, then compares observable behavior with shared test vectors.

## 示例与不变量 / Example and invariants

`src/compiler_tour.sy` 覆盖整数算术、赋值、两路条件、`while` 循环、函数、局部
数组、递归 Fibonacci，以及带副作用的 `&&` 短路求值。输入首先被限制在
`[0, 8]`，既避免递归爆炸也让 8 元素数组的边界成为普通数据约束。

`src/compiler_tour.sy` covers integer arithmetic, assignment, two-way
conditionals, `while`, functions, a local array, recursive Fibonacci, and
side-effecting `&&` short-circuit evaluation. Input is clamped to `[0, 8]`,
making both recursion cost and the eight-element array bound explicit data
invariants.

| 输入 / Input | 第一行：结果 / Result | 第二行：`mark` 次数 / Calls |
|---:|---:|---:|
| -3 | 0 | 0 |
| 0 | 0 | 0 |
| 2 | 11 | 0 |
| 5 | 50 | 1 |
| 20（限制为 8 / clamped to 8） | 197 | 1 |

这些向量同时探测负数、空循环、短路边界、普通递归路径和数组上界。程序只使用
SysY 运行时的 `getint`、`putint` 和 `putch`；最小声明由 Clang 分析时通过
`include/sysy_builtin.h` 注入，不污染 SysY 源码。

The vectors exercise negative input, an empty loop, the short-circuit boundary,
a normal recursive path, and the array limit. The program uses only `getint`,
`putint`, and `putch` from the SysY runtime. Minimal declarations are injected
for Clang analysis through `include/sysy_builtin.h`, without changing the SysY
source.

## 构建与验证 / Build and verification

最低要求：CMake 3.25、Ninja、Python 3.10 和支持 RV64GC 的 Clang。完整 Linux
验证还需要 `riscv64-linux-gnu-gcc` 与 `qemu-riscv64`。

Minimum requirements are CMake 3.25, Ninja, Python 3.10, and Clang with RV64GC
support. Full Linux verification additionally needs `riscv64-linux-gnu-gcc`
with its cross glibc development package (`libc6-dev-riscv64-cross` on Ubuntu),
and `qemu-riscv64`.

```sh
cd preflight
cmake --preset dev
cmake --build --preset dev --target verify
ctest --preset dev
```

`verify` 按实际发现的工具启用能力：

| 环境 / Environment | 生成与检查 / Generated and checked |
|---|---|
| 任意受支持宿主 / any supported host | `.i`、Clang AST JSON、Clang LLVM IR、RV64GC `.s`、三份 RISC-V ELF 对象 |
| POSIX 宿主 / POSIX host | SysY 源码与手写 LLVM IR 的本机链接和行为比较 |
| 有 RISC-V GCC / with RISC-V GCC | 从仓库 `lib/sylib.c` 重建同 ABI runtime，静态链接三种表示 |
| 再有 QEMU user mode / plus QEMU user mode | 三个 RV64GC Linux 程序运行共享向量并逐字节比较输出 |

缺少交叉链接器或 QEMU 时，配置会清楚显示 `NOTFOUND`，相关目标不会创建；这不是
“假成功”。GitHub Actions 的 Ubuntu job 安装真实的交叉工具链并执行完整路径，
Windows job 独立验证前端和 RISC-V 对象生成的可移植性。

If the cross-linker or QEMU is absent, configuration clearly reports
`NOTFOUND` and does not create the corresponding target; this is not a synthetic
success. The Ubuntu GitHub Actions job installs a real cross toolchain and runs
the complete path. The Windows job independently checks frontend and RISC-V
object-generation portability.

生成物位于仓库内的 `.temp/preflight-build/generated/`：

- `compiler_tour.i`：预处理结果 / preprocessed source;
- `compiler_tour.ast.json`：Clang 抽象语法树（Abstract Syntax Tree, AST）;
- `compiler_tour.O{0,2}.ll`：同一源码在两个受控优化级别生成的 LLVM IR;
- `compiler_tour.O{0,2}.s`：同一源码在两个受控优化级别降低的 RV64GC 汇编;
- `compiler_tour.from-source.{ll,s}`：兼容保留的 O0 副本 / compatibility O0 copies;
- `compiler_tour.from-{source,ir,asm}.o`：三条路径的 RISC-V ELF 对象;
- `runtime.rv64.o`：从仓库源码按当前 GNU/Linux ABI 重建的 SysY runtime;
- `{source,ir,asm}.rv64`：与该 runtime 静态链接的 Linux 程序（仅完整环境）。

仓库附带的 `libsysy_riscv.a` 保留作课程原始材料，但它的 C library 来源与当前
GNU/Linux sysroot 不可由仓库元数据证明（其未解析符号还呈现 newlib 特征）。直接
把它和 glibc 交叉工具链混用会使实验依赖偶然 ABI 兼容。因此权威验证从同仓库的
`lib/sylib.c` 重建 runtime；源码侧只注入三个 `extern` 风格声明，也避开
`lib/sylib.h` 在头文件中定义计时全局量所造成的多重定义风险。手写汇编通过
`%hi/%lo` 访问 `ticks`，故 RV64 链接显式使用 `-static -no-pie`。

The bundled `libsysy_riscv.a` remains useful as original course material, but
the repository metadata cannot establish its C-library provenance against the
current GNU/Linux sysroot (its unresolved symbols also show newlib traits).
Mixing it directly with a glibc cross toolchain would make the experiment rely
on accidental ABI compatibility. The authoritative check therefore rebuilds
the runtime from this repository's `lib/sylib.c`. Source compilation injects
only three extern-style declarations, avoiding the multiple definitions caused
by timer globals defined in `lib/sylib.h`. Because handwritten assembly accesses
`ticks` via `%hi/%lo`, RV64 linkage explicitly uses `-static -no-pie`.

## 阶段边界 / Stage boundaries

| 阶段 / Stage | 本实验中的职责 / Responsibility here |
|---|---|
| 预处理器 / preprocessor | 注入最小函数声明，展开注释与预处理指令 |
| 编译器前端 / compiler frontend | 解析、类型检查并形成 AST |
| 中端与后端 / middle end and backend | 形成 LLVM IR，并选择 RV64GC 指令 |
| 汇编器 / assembler | 编码指令、符号与重定位为 ELF 可重定位对象 |
| 链接器 / linker | 解析 SysY runtime 符号，合并启动代码与 libc，生成静态 Linux ELF |

手写 IR 刻意保持目标无关的 `i32` 语义；手写汇编遵守 RISC-V ELF psABI 的整数
调用约定、16 字节栈对齐和 callee-saved 寄存器规则。结构检查还直接读取 ELF
header，要求 `e_machine == EM_RISCV`，避免只凭扩展名判断对象类型。

The handwritten IR intentionally retains target-independent `i32` semantics.
The assembly follows the RISC-V ELF psABI integer calling convention, 16-byte
stack alignment, and callee-saved register rules. The structural test reads the
ELF header and requires `e_machine == EM_RISCV`, rather than trusting a filename.

## 受控优化对照 / Controlled optimization comparison

`pipeline` 从**同一份** `compiler_tour.sy` 分别以 `-O0` 和 `-O2` 生成文本 LLVM
IR 与 RV64GC 汇编。`check_artifacts.py` 要求四份文件非空、包含预期函数，并要求
每类 O0/O2 结果不逐字节相同。`optimization_metrics.py` 再以稳定 JSON 报告词法
结构代理量（lexical structural proxies）：函数体内 IR 指令行、
`alloca/load/store` 数量，以及汇编指令行近似数、指令助记符种类数和 directive
行数。

`pipeline` emits textual LLVM IR and RV64GC assembly at `-O0` and `-O2` from
the **same** `compiler_tour.sy`. `check_artifacts.py` requires all four files to
be nonempty, retain expected functions, and differ between O0 and O2.
`optimization_metrics.py` emits stable JSON lexical structural proxies: IR
instruction lines and `alloca/load/store` counts inside function bodies, plus
approximate assembly instruction lines, distinct mnemonics, and directive
lines.

本机实际观测如下；数字取决于编译器版本，所以脚本输出才是复现实验时的权威记录：

| 环境 / Environment | 指标 / Proxy | O0 | O2 | 结构变化 / Structural change |
|---|---|---:|---:|---:|
| Windows, Clang 22.1.8 | IR `alloca/load/store` 合计 | 59 | 24 | -35 (-59.3%) |
| Windows, Clang 22.1.8 | IR 指令行 | 119 | 137 | +18 (+15.1%) |
| Windows, Clang 22.1.8 | RV64 汇编指令行近似数 | 156 | 102 | -54 (-34.6%) |
| Ubuntu 24.04, Clang 18.1.3 | IR `alloca/load/store` 合计 | 59 | 25 | -34 (-57.6%) |
| Ubuntu 24.04, Clang 18.1.3 | IR 指令行 | 119 | 161 | +42 (+35.3%) |
| Ubuntu 24.04, Clang 18.1.3 | RV64 汇编指令行近似数 | 156 | 104 | -52 (-33.3%) |

更细看 Windows/Clang 22 的 O2：`alloca` 从 10 降为 1，`load` 从 29 降为
11，`store` 从 20 降为 12；Ubuntu/Clang 18 的前三项分别为 1、11、13。
这符合 mem2reg、标量替换和寄存器化减少显式内存流量的结构特征。然而 O2 的 IR
指令行反而增加，说明内联、循环变换或控制流改写可以用更多 IR 表达更适合后端的
程序。单看文本行数不能推出运行更快。

Looking more closely, O2 under Windows/Clang 22 reduces `alloca` from 10 to 1,
`load` from 29 to 11, and `store` from 20 to 12. The corresponding Ubuntu/
Clang 18 counts are 1, 11, and 13. This is structurally consistent with
promotion, scalar replacement, and registerization reducing explicit memory
traffic. Yet O2 has *more* IR instruction lines, since inlining, loop
transformation, or control-flow rewriting may use more IR to expose a form that
is friendlier to the backend. Text size alone does not imply faster execution.

> **解释边界 / Interpretation boundary:** 这些计数是静态文本代理，不是动态
> 指令数、代码尺寸、延迟、吞吐量或真实性能测量。没有运行基准，因此这里不作
> 任何性能提升声明。These counts are static textual proxies, not dynamic
> instruction counts, code size, latency, throughput, or measured performance.
> No benchmark was run, so no speedup claim is made.

## 进阶材料 / Advanced material

`advanced/` 保存 AscendNPU IR 官方 VecAdd 的最小静态研究资产，并解释
`gm → ub → vadd → gm` 的领域语义。其检查只保证材料结构完整；由于 CI 没有
CANN、毕昇专用编译器、驱动和昇腾 NPU，项目明确不声称完成方言编译或真机运行。

`advanced/` contains a minimal static study artifact based on the official
AscendNPU IR VecAdd example and explains its `gm → ub → vadd → gm` domain
semantics. Its check preserves structure only. Without CANN, the specialized
BiSheng compiler, driver, and Ascend NPU, no dialect-compilation or on-device
execution claim is made.

## 主要参考 / Primary references

- [Clang Command Line Reference](https://clang.llvm.org/docs/ClangCommandLineReference.html)
- [LLVM Language Reference Manual](https://llvm.org/docs/LangRef.html)
- [RISC-V ELF psABI](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/)
- [CMake Presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html)
- [QEMU User Mode](https://www.qemu.org/docs/master/user/)
- [AscendNPU IR VecAdd 快速入门](https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/quick_start/examples_zh.html)

本目录文档所列在线来源访问日期均为 2026-09-22。
Online sources listed by this directory were accessed on 2026-09-22.
