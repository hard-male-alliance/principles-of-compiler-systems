# 边界化阶乘编译纵览 / Bounded-factorial compiler tour

本目录只研究一个实例：输入小于 0 时取 0，大于 10 时取 10，再由独立
`factorial` 函数用 `while` 计算阶乘并经 SysY runtime 输出。C、SysY、手写
opaque-pointer LLVM IR 与手写 RV64GC 汇编保持相同可观察行为。

This directory studies one case only: clamp input to `[0, 10]`, compute the
factorial in an independent `factorial` function with `while`, and print through
the SysY runtime. C, SysY, handwritten opaque-pointer LLVM IR, and handwritten
RV64GC assembly have the same observable behavior.

## 复现 / Reproduce

依赖 CMake 3.25、Ninja、Python 3.10、Clang 和 LLVM `readobj`/`objdump`。完整
Linux 路径另需 `riscv64-linux-gnu-gcc`、交叉 glibc 与 `qemu-riscv64`。

Requires CMake 3.25, Ninja, Python 3.10, Clang, and LLVM `readobj`/`objdump`.
The full Linux path additionally requires `riscv64-linux-gnu-gcc`, its cross
glibc, and `qemu-riscv64`.

```sh
cd preflight
cmake --preset dev
cmake --build --preset dev --target verify
ctest --preset dev
```

仅生成阶段材料 / Generate stage evidence only:

```sh
cmake --build --preset dev --target pipeline optimization_metrics
```

所有生成物位于 `.temp/preflight-build/generated/`。
All generated artifacts are in `.temp/preflight-build/generated/`.

## 产物索引与阅读问题 / Artifact index and reading questions

| 阶段 / Stage | 产物 / Artifact | 看什么 / What to inspect |
|---|---|---|
| 源程序 / source | `src/bounded_factorial.{c,sy}` | 宏、声明和 SysY runtime 调用如何围绕同一算法组织 |
| 预处理 / preprocessing | `bounded_factorial.i` | `FACTORIAL_LIMIT` 已替换为 `10`，注释和 `#define` 已消失 |
| 词法 / lexing | `bounded_factorial.tokens.txt` | 关键字、标识符、常量、运算符如何成为 token 流 |
| 语法/语义 / syntax & semantics | `bounded_factorial.ast.json` | 函数、`if`、`while`、调用与隐式转换的树结构 |
| LLVM IR | `bounded_factorial.O{0,2}.ll` | O0 的显式内存操作与 O2 的 SSA/控制流变化 |
| 指令选择 / instruction selection | `bounded_factorial.O{0,2}.s` | LLVM 操作如何映射为 RV64GC 指令与伪指令 |
| 汇编 / assembly | `{c,sysy,ir,asm}.rv64.o` | 四个输入表示都成为 ELF64 RISC-V 可重定位对象 |
| 对象结构 / object structure | `c.object.txt` | ELF header、section 边界及代码/元数据分离 |
| 符号 / symbols | `c.symbols.txt` | `factorial` 已定义，`getint`/`putint`/`putch` 尚未定义 |
| 重定位 / relocations | `c.relocations.txt` | 外部调用为何要留给链接器修补地址 |
| 机器码 / machine code | `c.disassembly.txt` | 指令字节、地址、基本块和符号标签的对应关系 |
| 链接 / linking | `{c,sysy,ir,asm}.rv64` | runtime、启动代码与 libc 合并后的静态 Linux ELF |
| 执行 / execution | `native_equivalence`, `riscv_equivalence` | 共享 6 个输入是否逐字节得到相同输出 |

共享向量覆盖 `-3, 0, 1, 5, 10, 20`，期望输出依次为 `1, 1, 1, 120,
3628800, 3628800`。`optimization_metrics` 输出文本结构指标，仅用于定位 O0/O2
表示差异，不是性能基准。

The shared vector covers `-3, 0, 1, 5, 10, 20`, expecting `1, 1, 1, 120,
3628800, 3628800`. `optimization_metrics` reports textual structural metrics
to locate O0/O2 representation changes; it is not a performance benchmark.

## 展望 / Outlook

`advanced/add.mlir` 是 AscendNPU IR 多级降低的最小静态材料，用来说明领域操作、
存储空间和数据搬运可在 LLVM IR 之前保持为显式语义。它属于展望，不是本实例
已经执行的编译阶段；当前 CI 不声称完成 CANN 编译或 NPU 真机运行。

`advanced/add.mlir` is minimal static material for AscendNPU IR multi-level
lowering. It illustrates how domain operations, memory spaces, and transfers can
remain explicit before LLVM IR. It is outlook material, not an executed stage
of this case study; CI makes no CANN-compilation or on-device claim.
