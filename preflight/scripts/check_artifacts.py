#!/usr/bin/env python3
"""检查流水线产物的类型与最小不变量。 / Check artifact types and minimal invariants."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def require_text(path: Path, tokens: tuple[str, ...]) -> None:
    """要求文本非空并包含所有标记。 / Require nonempty text containing every token."""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise SystemExit(f"empty artifact: {path}")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(f"{path}: missing {missing}")


def require_riscv_elf(path: Path) -> None:
    """要求 ELF64 小端 RISC-V 可重定位对象。 / Require an ELF64 little-endian RISC-V object."""
    data = path.read_bytes()
    if len(data) < 64 or data[:6] != b"\x7fELF\x02\x01":
        raise SystemExit(f"not ELF64 little-endian: {path}")
    machine = struct.unpack_from("<H", data, 18)[0]
    if machine != 243:  # EM_RISCV
        raise SystemExit(f"wrong ELF machine {machine}, expected EM_RISCV (243): {path}")


def main() -> int:
    """校验预处理、AST、双优化级 IR/汇编和对象。 / Validate preprocessing, AST, two optimization levels, and objects."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--preprocessed", type=Path, required=True)
    parser.add_argument("--ast", type=Path, required=True)
    parser.add_argument("--llvm-o0", type=Path, required=True)
    parser.add_argument("--llvm-o2", type=Path, required=True)
    parser.add_argument("--assembly-o0", type=Path, required=True)
    parser.add_argument("--assembly-o2", type=Path, required=True)
    parser.add_argument("--object", type=Path, action="append", required=True)
    args = parser.parse_args()
    require_text(args.preprocessed, ("int fib", "int sum", "int getint"))
    ast = json.loads(args.ast.read_text(encoding="utf-8"))
    if ast.get("kind") != "TranslationUnitDecl":
        raise SystemExit("AST root is not TranslationUnitDecl")
    require_text(args.llvm_o0, ("define", "@fib", "@main"))
    require_text(args.llvm_o2, ("define", "@fib", "@main"))
    require_text(args.assembly_o0, ("fib:", "main:"))
    require_text(args.assembly_o2, ("fib:", "main:"))
    if args.llvm_o0.read_bytes() == args.llvm_o2.read_bytes():
        raise SystemExit("O0 and O2 LLVM IR unexpectedly match byte-for-byte")
    if args.assembly_o0.read_bytes() == args.assembly_o2.read_bytes():
        raise SystemExit("O0 and O2 assembly unexpectedly match byte-for-byte")
    for path in args.object:
        require_riscv_elf(path)
    print("pipeline artifacts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
