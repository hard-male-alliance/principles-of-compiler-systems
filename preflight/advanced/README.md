# AscendNPU IR VecAdd 静态探索 / Static exploration

`add.mlir` 保存了官方快速入门所示的最小 VecAdd 数据通路（访问日期：
2026-09-22）。它不是通用上游 MLIR：`hacc` 与 `hivm` 是 AscendNPU IR/CANN
工具链提供的方言，普通 `mlir-opt` 无法解析。

`add.mlir` preserves the minimal VecAdd data path shown by the official quick
start (accessed 2026-09-22). It is not standalone upstream MLIR: the `hacc` and
`hivm` dialects are supplied by the AscendNPU IR/CANN toolchain, so ordinary
`mlir-opt` cannot parse it.

## 可观察的渐进式降低 / Observable progressive lowering

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
- [CANN 毕昇编译器](https://www.hiascend.com/cann/bisheng)
