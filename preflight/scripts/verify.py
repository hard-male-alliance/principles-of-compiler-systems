#!/usr/bin/env python3
"""Verify structure and known-answer behavior for captured preflight artifacts.

验证预备实验产物的结构，以及六组独立给定答案的可观察行为。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


CASES: tuple[tuple[int, bytes], ...] = (
    (-1, b"0\n"),
    (0, b"0\n"),
    (1, b"-8\n"),
    (4, b"8\n"),
    (8, b"16\n"),
    (10, b"16\n"),
)

# sylib.c 的 destructor 无条件报告累计计时；本案例未调用计时 API，故值严格为零。
# sylib.c reports accumulated timing unconditionally; this case calls no timer API, so it is exactly zero.
EXPECTED_STDERR = b"TOTAL: 0H-0M-0S-0us\n"


def assert_contains(path: Path, needles: tuple[str, ...]) -> None:
    """Require every semantic marker in a text artifact.

    要求文本产物包含每个语义标记，而不绑定易变的临时名称或指令序列。
    """

    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path.name} lacks markers: {missing}")


def verify_portable(output: Path) -> None:
    """Verify preprocessing, AST, generated IR/assembly, and authored IR.

    验证预处理、AST、生成 IR/汇编和手写 IR 的可检查不变量。
    """

    required = [
        "clipped_dot.i",
        "clipped_dot.ast.json",
        "clipped_dot.O0.ll",
        "clipped_dot.O2.ll",
        "clipped_dot.O0.s",
        "clipped_dot.O2.s",
        "handwritten-ir.rv64.o",
        "capture.json",
    ]
    for name in required:
        path = output / name
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing or empty artifact: {path}")

    preprocessed = (output / "clipped_dot.i").read_text(encoding="utf-8", errors="replace")
    if "VECTOR_LENGTH" in preprocessed or "TERM_MIN" in preprocessed:
        raise AssertionError("case macros were not expanded by preprocessing")
    if "int a[8]" not in preprocessed:
        raise AssertionError("preprocessed source does not expose VECTOR_LENGTH -> 8")

    ast = json.loads((output / "clipped_dot.ast.json").read_text(encoding="utf-8"))
    if ast.get("kind") != "TranslationUnitDecl":
        raise AssertionError("AST root is not TranslationUnitDecl")
    ast_text = json.dumps(ast, ensure_ascii=False)
    for marker in ("clipped_dot", "WhileStmt", "IfStmt", "CallExpr"):
        if marker not in ast_text:
            raise AssertionError(f"AST lacks {marker}")

    for level in ("O0", "O2"):
        assert_contains(output / f"clipped_dot.{level}.ll", ("riscv64", "define", "@clipped_dot", "@getint"))
        assert_contains(output / f"clipped_dot.{level}.s", ("clipped_dot", "getint", "putint"))
    if (output / "clipped_dot.O0.ll").read_bytes() == (output / "clipped_dot.O2.ll").read_bytes():
        raise AssertionError("O0 and O2 IR are unexpectedly identical")


def verify_full(output: Path) -> None:
    """Verify ELF boundaries and execute every implementation under QEMU.

    验证 ELF 边界，并在 QEMU 下执行每一种实现。
    """

    qemu = shutil.which("qemu-riscv64")
    if qemu is None:
        raise AssertionError("full verification requires qemu-riscv64")
    for form in ("c", "sysy", "ir", "asm"):
        object_report = output / f"{form}.object.txt"
        elf_report = output / f"{form}.elf.txt"
        assert_contains(object_report, ("REL (Relocatable file)", "RISC-V", "getint", "putint"))
        assert_contains(elf_report, ("EXEC (Executable file)", "RISC-V", "Entry point address"))
        executable = output / f"clipped-dot-{form}.rv64"
        for value, expected in CASES:
            completed = subprocess.run(
                [qemu, str(executable)],
                input=f"{value}\n".encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode != 0:
                raise AssertionError(f"{form}({value}) exited {completed.returncode}: {completed.stderr!r}")
            if completed.stdout != expected or completed.stderr != EXPECTED_STDERR:
                raise AssertionError(
                    f"{form}({value}): stdout={completed.stdout!r}, stderr={completed.stderr!r}, "
                    f"expected stdout={expected!r}, expected stderr={EXPECTED_STDERR!r}"
                )
    assert_contains(output / "provided-archive.undefined.txt", ("_impure_ptr",))


def main() -> int:
    """Run verification selected by the configured portability mode.

    按已配置的可移植模式运行验证。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("portable", "full"), required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    verify_portable(output)
    if args.mode == "full":
        verify_full(output)
    print(f"verified {args.mode} clipped-dot artifacts")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
