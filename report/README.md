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

## 数据注入契约

`generated/experiment-values.tex` 是实验事实进入论文的唯一接口。初稿中的宏全部显示“待实测”；完成实验后应由仓库内脚本依据原始日志生成真实值，而不是直接在正文中填写推测结果。正文所引用的 `artifacts/...` 路径是预定证据布局，相关实验模块实现后再创建。

提交前必须：

1. 据实替换作者、学号、班级、邮箱与分工；
2. 注入工具链版本、目标三元组、测试数与通过数；
3. 补入真实图表并逐项引用原始制品；
4. 根据最终外部研究材料核对和扩充参考文献；
5. 从干净检出重新构建，检查日志与最终 PDF。

## 上游文件校验

下载日期：2026-09-22；来源：`https://mirrors.ctan.org/macros/latex/contrib/llncs/`。

| 文件 | SHA-256 |
|---|---|
| `llncs.cls` | `E9894C92191FCD195EEF3120A36D2F75B52030EADCBDC3CE146317974654821F` |
| `splncs04.bst` | `F36C3A17E5304A692706359AAFA9DE709395A085E579EB47C027095AEAABDE96` |
