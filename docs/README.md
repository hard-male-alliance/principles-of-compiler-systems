# 课程文档索引

本目录汇集 SysY 编译器课程的作业要求、语言规范、运行时接口和预备学习材料。原 PDF、Word 和 PowerPoint 内容均已整理为 Markdown；原文中有语义价值的图示存放在 [`assets/`](assets/)。

## 作业要求

1. [上机大作业总体要求](上机大作业总体要求.md)：模块划分、评分、功能要求、提交内容及学术诚信要求。
2. [预备工作：了解你的编译器](预备工作-了解你的编译器.md)：5 分预备作业、报告规范、MLIR 进阶任务和示例程序。

已完成的可复现实验位于 [`../preflight/`](../preflight/README.md)，对应的 LNCS 论文工程位于
[`../report/`](../report/README.md)。方法与验收决策记录在 [`knowledge/`](knowledge/)，外部资料核查记录在
[`research/`](research/)；这些英文笔记保存来源、假设与证据边界，正文则在此基础上形成中文综述。

### 设计与研究记录

- [教程式综述改写架构](knowledge/revision-editorial-brief.md)
- [形式化主线设计](knowledge/revision-formalization-map.md)
- [叙事审计](knowledge/revision-narrative-audit.md)
- [统一视觉系统](knowledge/revision-visual-system.md)
- [教材式写作与可视化最佳实践](research/revision-pedagogy-best-practices.md)
- [报告验收映射](knowledge/report-acceptance.md)
- [贯穿案例与工件架构](knowledge/case-study-architecture.md)
- [独立验证计划](knowledge/validation-plan.md)
- [Clang/LLVM 编译流水线](research/compiler-pipeline.md)
- [LLVM IR 与优化语义](research/llvm-ir.md)
- [RISC-V、ELF 与链接](research/riscv-elf-linking.md)
- [MLIR 与 AscendNPU IR](research/mlir-ascend.md)
- [编译系统研究前沿](research/compiler-frontiers.md)

## SysY 规范

1. [SysY 2022 语言定义](SysY2022语言定义-V1.md)：语法、词法与语义约束。
2. [SysY 文法补充说明](SysY文法补充说明.md)：数组维度、类型转换、浮点常量和运算符等勘误与补充。
3. [SysY 2022 运行时库](SysY2022运行时库-V1.md)：输入输出函数和计时函数接口。

## 编译器与汇编学习材料

- [了解编译器、LLVM IR 与汇编编程](了解编译器-LLVM-IR与汇编编程.md)：编译流水线、LLVM IR、ARM/RISC-V 汇编与 SysY 运行时库链接方法。

## 运行时文件

可链接的静态库、动态库及 `sylib` 源码位于 [`../lib/`](../lib/)，各文件用途与链接示例见 [运行时库文件说明](../lib/README.md)。
