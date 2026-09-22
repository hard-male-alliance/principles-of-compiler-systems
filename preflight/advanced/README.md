# AscendNPU IR VecAdd 静态探索 / Static exploration

`add.mlir` 保存了官方快速入门所示的最小 VecAdd 数据通路（访问日期：
2026-09-22）。它不是通用上游 MLIR：`hacc` 与 `hivm` 是 AscendNPU IR/CANN
工具链提供的方言，普通 `mlir-opt` 无法解析。

`add.mlir` preserves the minimal VecAdd data path shown by the official quick
start (accessed 2026-09-22). It is not standalone upstream MLIR: the `hacc` and
`hivm` dialects are supplied by the AscendNPU IR/CANN toolchain, so ordinary
`mlir-opt` cannot parse it.

## 已观察的 HIVM 静态结构 / Observed HIVM static structure

| 层次 / Layer | 本例中的表示 / Representation | 语义 / Meaning |
|---|---|---|
| 入口契约 / entry contract | `hacc.entry`, `DEVICE` | 标记设备侧 kernel / marks a device kernel |
| 存储层次 / memory hierarchy | `gm` → `ub` | 从全局内存搬运到统一缓冲区 / global memory to unified buffer |
| 向量计算 / vector compute | `hivm.hir.vadd` | 16 个 `i16` 元素相加 / adds 16 `i16` elements |
| 写回 / write-back | `ub` → `gm` | 将结果写回全局内存 / stores the result to global memory |

这说明多级 IR 的价值不只是“换一种语法”：在进入 LLVM IR 之前，内存空间、
搬运和向量操作仍是可优化的领域语义。仓库中的结构检查只验证上述证据仍然存在，
**不等价于方言解析、编译成功或真机执行**。

This illustrates that multi-level IR is more than alternate syntax: memory
spaces, transfers, and vector operations remain domain semantics available for
optimization before LLVM IR. The repository's structural check only preserves
that evidence; it is **not** dialect parsing, successful compilation, or
on-device execution.

## 文档给出的降低边界 / Documented lowering boundaries

官方架构文档描述的总体链路是 `HFusion → HIVM → low-level MLIR → LLVM IR →
算子二进制`。HFusion 最大限度保留 named-operation 高层语义；HIVM 逐步落实
核间映射、片上内存分配及处理单元/同步；随后 `hivmc` 才把低层 MLIR 转换为
LLVM IR 并生成二进制。本仓库的 `add.mlir` 已经位于 HIVM 层，因此它只能作为
这条链路的**一个快照**，不能证明上述阶段已在本地执行。

The official architecture describes `HFusion → HIVM → low-level MLIR → LLVM
IR → operator binary`. HFusion retains named-operation semantics; HIVM makes
core mapping, on-chip memory, processing-unit mapping, and synchronization more
concrete; `hivmc` then converts low-level MLIR to LLVM IR and emits the binary.
The checked-in `add.mlir` is already an HIVM-layer snapshot, so it is evidence
of one level only, not an executed local lowering trace.

## 官方环境与命令 / Official environment and command

官方示例使用 `bishengir-compile add.mlir -enable-hivm-compile -o kernel.o`，
随后用 CANN runtime/AscendCL 构建 host 程序。复现完整路径需要与硬件匹配的
CANN、毕昇编译器、AscendNPU IR 包、驱动和昇腾 NPU；本仓库与 GitHub-hosted
runner 不提供这些依赖，因此没有声称已经上板运行。

The official example invokes
`bishengir-compile add.mlir -enable-hivm-compile -o kernel.o`, then builds a host
program against the CANN runtime and AscendCL. Full reproduction requires a
hardware-compatible CANN release, BiSheng compiler, AscendNPU IR package,
driver, and Ascend NPU. This repository and GitHub-hosted runners provide none
of those dependencies and make no on-device execution claim.

来源 / Sources:

- [AscendNPU IR：运行第一个样例](https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/quick_start/examples_zh.html)
- [AscendNPU IR：架构设计与编译流程](https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/architecture_zh.html)
- [CANN 毕昇编译器](https://www.hiascend.com/cann/bisheng)
