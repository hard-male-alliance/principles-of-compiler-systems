# LNCS 中文论文

本目录包含综述性案例研究《编译系统中的表示演化：从 SysY 源程序到 RV64 ELF 可执行文件》。正文采用 Springer 官方 `llncs` 文档类和 `splncs04` BibTeX 样式；两文件来自 CTAN 的 Springer `llncs` 2.26 发行包（CC BY 4.0），上游说明见 `LLNCS-README.md`。

## 构建

需要 XeLaTeX、BibTeX、`latexmk`，以及 TeX Live/MiKTeX 中的 `ctex`、`booktabs`、`listings`、`hyperref` 等常见宏包。

```sh
cd report
latexmk -r latexmkrc main.tex
```

输出为 `build/main.pdf`。清理命令为 `latexmk -r latexmkrc -C main.tex`。也可在提供 POSIX `make` 的环境中执行 `make` / `make clean`。请勿使用 `geometry` 或手工修改页边距覆盖 LNCS 版式。

## 实验证据与提交

论文中的实验结果来自版本化案例程序、参考 LLVM IR、参考 RV64 汇编及相应结构报告。完整生成和验证命令保存在项目工件文档中，不嵌入论文正文。正式提交前应将匿名作者元数据替换为课程要求的信息，并从干净检出重新构建、检查日志和最终 PDF。

## 上游文件校验

下载日期：2026-09-22；来源：`https://mirrors.ctan.org/macros/latex/contrib/llncs/`。

| 文件 | SHA-256 |
|---|---|
| `llncs.cls` | `E9894C92191FCD195EEF3120A36D2F75B52030EADCBDC3CE146317974654821F` |
| `splncs04.bst` | `F36C3A17E5304A692706359AAFA9DE709395A085E579EB47C027095AEAABDE96` |
