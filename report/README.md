# 《深入理解编译系统》LLNCS 报告

本目录是预备作业的中文综述论文工程。正文使用 Springer `llncs` 文档类，唯一贯穿案例是
SysY 截断点积；对应源码、LLVM IR、RV64GC 汇编和可复现实验位于 [`../preflight/`](../preflight/)。

## 构建

需要 XeLaTeX、BibTeX、`latexmk`，以及包含 `llncs.cls` 与 `splncs04.bst` 的 TeX 发行版：

```sh
cd report
latexmk -r latexmkrc main.tex
```

PDF 输出为 `report/build/main.pdf`。清理生成物：

```sh
latexmk -r latexmkrc -C main.tex
```

## 提交前必须修改

1. 在 `main.tex` 中把两位作者、学号、班级与小组占位符替换为真实信息。
2. 核对“作者分工”表，并确保两位组员都在课程平台提交同一份 PDF。
3. 先执行 `preflight` 的完整验证，再从干净目录重建论文并检查日志和渲染页。

本仓库不复制 Springer 模板文件；构建环境直接使用 TeX Live 提供的 `llncs` 包，避免维护
一份易过期的模板副本。
