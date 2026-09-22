# AscendNPU IR 展望 / AscendNPU IR outlook

`add.mlir` 保存官方 VecAdd 示例的最小 HIVM 方言片段，只用于展望多级中间表示
（multi-level intermediate representation）：`gm → ub` 数据搬运、`vadd` 领域
计算和 `ub → gm` 写回在进入 LLVM IR 前仍然显式。

`add.mlir` preserves a minimal HIVM-dialect fragment from the official VecAdd
example. It is outlook material for multi-level intermediate representation:
`gm → ub` transfer, domain-level `vadd`, and `ub → gm` write-back remain explicit
before LLVM IR.

仓库检查仅确认这份静态材料结构未丢失。普通 `mlir-opt` 不包含 `hacc`/`hivm`
方言；完整路径需要 CANN、毕昇编译器、驱动和昇腾 NPU。因此本项目不声称已解析
该方言、生成算子二进制或完成真机运行。

The repository check only confirms that this static structure remains present.
Ordinary `mlir-opt` does not ship the `hacc`/`hivm` dialects. The full path needs
CANN, BiSheng, a driver, and Ascend hardware; this project therefore claims no
dialect parsing, operator binary, or on-device execution.

来源 / Sources:

- [AscendNPU IR：运行第一个样例](https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/quick_start/examples_zh.html)
- [AscendNPU IR：架构设计与编译流程](https://ascendnpu-ir.gitcode.com/zh_cn/sources/introduction/architecture_zh.html)
