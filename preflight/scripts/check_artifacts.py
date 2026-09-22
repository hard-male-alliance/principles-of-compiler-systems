#!/usr/bin/env python3
"""检查流水线产物的类型与最小不变量。 / Check artifact types and minimal invariants."""

from __future__ import annotations

import argparse
import json
import re
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


def require_riscv_ir(path: Path) -> None:
    """要求 IR 声明 RV64 triple 与 64 位数据布局。 / Require an RV64 triple and 64-bit data layout."""
    text = path.read_text(encoding="utf-8")
    triple = re.search(r'^target triple = "([^"]+)"$', text, re.MULTILINE)
    if triple is None or not triple.group(1).startswith("riscv64-"):
        actual = triple.group(1) if triple else "missing"
        raise SystemExit(f"wrong LLVM IR target triple {actual!r}, expected riscv64: {path}")
    layout = re.search(r'^target datalayout = "([^"]+)"$', text, re.MULTILINE)
    if layout is None or "p:64:64" not in layout.group(1):
        actual = layout.group(1) if layout else "missing"
        raise SystemExit(f"wrong LLVM IR data layout {actual!r}, expected 64-bit pointers: {path}")


def main() -> int:
    """校验前端、双优化级输出与对象证据。 / Validate frontend, dual-level, and object evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--preprocessed", type=Path, required=True)
    parser.add_argument("--tokens", type=Path, required=True)
    parser.add_argument("--ast", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, required=True)
    parser.add_argument("--relocations", type=Path, required=True)
    parser.add_argument("--disassembly", type=Path, required=True)
    parser.add_argument("--asm-object-info", type=Path, required=True)
    parser.add_argument("--asm-symbols", type=Path, required=True)
    parser.add_argument("--asm-relocations", type=Path, required=True)
    parser.add_argument("--asm-disassembly", type=Path, required=True)
    parser.add_argument("--llvm-o0", type=Path, required=True)
    parser.add_argument("--llvm-o2", type=Path, required=True)
    parser.add_argument("--assembly-o0", type=Path, required=True)
    parser.add_argument("--assembly-o2", type=Path, required=True)
    parser.add_argument("--object", type=Path, action="append", required=True)
    args = parser.parse_args()
    require_text(args.preprocessed, ("int factorial", "int clamp_input", "10"))
    require_text(args.tokens, ("identifier 'factorial'", "identifier 'getint'"))
    ast = json.loads(args.ast.read_text(encoding="utf-8"))
    if ast.get("kind") != "TranslationUnitDecl":
        raise SystemExit("AST root is not TranslationUnitDecl")
    require_text(args.llvm_o0, ("define", "@factorial", "@main"))
    require_text(args.llvm_o2, ("define", "@factorial", "@main"))
    require_riscv_ir(args.llvm_o0)
    require_riscv_ir(args.llvm_o2)
    require_text(args.assembly_o0, ("factorial:", "main:"))
    require_text(args.assembly_o2, ("factorial:", "main:"))
    require_text(args.symbols, ("factorial", "getint", "putint"))
    require_text(args.relocations, ("getint", "putint", "putch"))
    require_text(args.disassembly, ("<factorial>", "<main>"))
    require_text(args.asm_object_info, ("Format: elf64-littleriscv", "Arch: riscv64", "Sections ["))
    require_text(args.asm_symbols, ("factorial", "main", "getint", "putint"))
    require_text(args.asm_relocations, ("getint", "putint", "putch"))
    require_text(args.asm_disassembly, ("<factorial>", "<main>"))
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
