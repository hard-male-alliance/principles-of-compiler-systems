# 中文：论文构建入口；所有派生文件均留在 report/build。
# English: Paper build entry point; all derived files stay in report/build.
.PHONY: all clean

all:
	latexmk -r latexmkrc main.tex

clean:
	latexmk -r latexmkrc -C main.tex
