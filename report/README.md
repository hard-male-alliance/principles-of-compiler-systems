# LNCS 中文实验报告

本目录是“预备工作——了解你的编译器”的论文工程。正文采用 Springer 官方 `llncs` 文档类和 `splncs04` BibTeX 样式；两文件来自 CTAN 的 Springer `llncs` 2.26 发行包（CC BY 4.0），上游说明见 `LLNCS-README.md`。

## 构建

需要 XeLaTeX、BibTeX、`latexmk`，以及 TeX Live/MiKTeX 中的 `ctex`、`booktabs`、`listings`、`hyperref` 等常见宏包。

```sh
cd report
latexmk -r latexmkrc main.tex
```

输出为 `build/main.pdf`。清理命令：

```sh
latexmk -r latexmkrc -C main.tex
```

也可在提供 POSIX `make` 的环境中执行 `make` / `make clean`。请勿使用 `geometry` 或手工修改页边距覆盖 LNCS 版式。

## 实验证据与提交

论文中的实验结果来自 `preflight/` 的版本化程序、测试驱动与结构检查；可复现命令列于论文附录。提交前唯一需要人工填写的内容是两位作者的姓名、学号及真实分工。填写后应从干净检出重新构建并检查日志与最终 PDF，不要直接修改构建目录中的派生文件。

## 上游文件校验

下载日期：2026-09-22；来源：`https://mirrors.ctan.org/macros/latex/contrib/llncs/`。

| 文件 | SHA-256 |
|---|---|
| `llncs.cls` | `E9894C92191FCD195EEF3120A36D2F75B52030EADCBDC3CE146317974654821F` |
| `splncs04.bst` | `F36C3A17E5304A692706359AAFA9DE709395A085E579EB47C027095AEAABDE96` |
