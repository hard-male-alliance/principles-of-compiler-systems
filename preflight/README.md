# 截断点积编译器预备实验 / Clipped-Dot Compiler Preflight

本目录把一个 **SysY 2022 截断点积**案例沿 C 前端、LLVM IR、RV64GC 汇编、
ELF 对象、静态链接与 QEMU 执行贯通。它不是第二套构建框架：CMake 只负责选择
`portable` 或 `full` 模式，两个短 Python 驱动分别负责捕获和验证。

This directory carries one **SysY 2022 clipped-dot product** through a C front end,
LLVM IR, RV64GC assembly, ELF objects, static linking, and QEMU execution. CMake only
selects a mode; two focused Python drivers own capture and verification.

## 单一语义契约 / One semantic contract

`src/clipped_dot.sy`、`src/clipped_dot.c`、`ir/clipped_dot.ll` 和
`asm/clipped_dot.S` 实现相同程序。程序将输入 `n` 限制到 `[0,8]`，然后计算
前 `n` 对数组元素的乘积；每个乘积先限制到 `[-8,12]`，再累加。它覆盖赋值、
有符号整数算术、嵌套条件、零次/多次循环、数组、用户函数，以及 `getint`、
`putint`、`putch` 运行时调用。

独立给定答案（精确 stdout，退出码必须为零）：

| stdin | stdout | 覆盖点 |
|---:|---:|---|
| `-1` | `0` | 输入下界截断、零次循环 |
| `0` | `0` | 精确下界、零次循环 |
| `1` | `-8` | 一次循环、单项下界截断 |
| `4` | `8` | 多次循环与单项上界截断 |
| `8` | `16` | 完整数组 |
| `10` | `16` | 输入上界截断 |

`lib/sylib.c` 的 `after_main` destructor 会无条件向 stderr 写出累计计时。本案例没有
调用计时 API，因此六组执行都必须得到精确的
`TOTAL: 0H-0M-0S-0us\n`；验证器既不丢弃也不静默过滤这项真实运行时行为。

## 运行 / Run

任何平台只需 Clang 15+（支持 opaque pointers）、CMake 3.25+、Ninja 和
Python 3.10+：

```sh
cd preflight
cmake --preset portable
cmake --build --preset portable --target verify
ctest --preset portable
```

Linux 完整验证另需 `gcc-riscv64-linux-gnu`、`binutils-riscv64-linux-gnu` 和
`qemu-user`：

```sh
cd preflight
cmake --preset rv64
cmake --build --preset rv64 --target verify
ctest --preset rv64
```

CI 使用 `ci` preset：Linux 检测到工具后自动进入 `full` 模式，Windows 自动保持
`portable`，因此 Windows 配置**不会**要求 RV64 链接器或 QEMU。需要确定性时用
`rv64`（缺工具即给出清晰配置错误）或 `portable`，不要依赖自动检测。

## 产物与证据 / Artifacts and evidence

所有派生产物位于仓库内 `.temp/preflight-*/artifacts/`：

| 边界 | 代表产物 | 可检查事实 |
|---|---|---|
| 预处理 | `clipped_dot.i` | `VECTOR_LENGTH`、上下界宏已经替换 |
| 语法/语义前端 | `clipped_dot.ast.json` | 函数绑定、类型、循环、分支、调用 |
| LLVM 生成与优化 | `clipped_dot.O0.ll`, `.O2.ll` | 固定源码/目标，只改变优化级别 |
| 指令选择 | `clipped_dot.O0.s`, `.O2.s` | RV64GC 调用、分支与访存 |
| 手写 IR | `handwritten-ir.rv64.o`, 可选 `.bc` | opaque-pointer IR 被 Clang 接受；存在时亦经 `llvm-as`/`opt` |
| 汇编/对象 | `*.rv64.o`, `*.object.txt`, `*.disassembly.txt` | ELF64 RISC-V、符号、重定位与机器码 |
| 链接 | `*.link.map`, `*.elf.txt` | 目标文件的未定义运行时符号在静态可执行文件中得到解析 |
| 加载/执行 | `clipped-dot-*.rv64` | 四种表示均经 QEMU 对六组 oracle 逐字节验证 |
| 复现记录 | `capture.json` | 模式、目标、命令参数和基础环境 |

结构检查刻意不锁死优化器的临时符号或某一条具体指令；这能在不同 LLVM 版本间
保持有意义的兼容性，同时仍检查目标三元组、函数、运行时调用和 ELF 边界。

## 运行时归档边界 / Runtime archive boundary

课程随附的 `lib/libsysy_riscv.a` 面向 newlib，其未定义符号表含 `_impure_ptr`；
Ubuntu 的 `riscv64-linux-gnu-gcc` 使用 glibc，直接静态链接会失败。完整模式因此以
同一仓库的 `lib/sylib.c`、同一 `rv64gc/lp64d` ABI 构建
`libsysy-glibc-rv64.a`。`provided-archive.undefined.txt` 保存对原归档执行
`riscv64-linux-gnu-nm -u` 的直接证据；这不是把不兼容静默掩盖为“自动回退”。

The supplied archive targets newlib and imports `_impure_ptr`, whereas the Ubuntu
Linux cross toolchain is glibc-based. Full mode therefore rebuilds `lib/sylib.c` into
a glibc-compatible RV64 static archive with the same ISA/ABI and records the original
archive's undefined symbols explicitly.

## 文件职责 / File ownership

- `include/case_config.h`：C 观察载体的宏与最小运行时声明；不实现语义。
- `include/sysy_builtin.h`：仅帮助通用 C 前端把 SysY 内建函数解析为声明。
- `scripts/capture.py`：执行实际工具并保存原始证据；不用 shell 拼接命令。
- `scripts/verify.py`：把结构不变量与给定答案分开验证，避免“彼此相同即正确”。

完整执行证明了所列样例上的可观察一致性，而不是对所有输入的形式化等价证明。
