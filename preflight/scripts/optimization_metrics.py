#!/usr/bin/env python3
"""报告 O0/O2 文本结构指标，而非性能。 / Report O0/O2 text-structure metrics, not performance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LLVM_MEMORY_OPS = ("alloca", "load", "store")


def llvm_metrics(path: Path) -> dict[str, int]:
    """计算 LLVM IR 的稳定词法代理量。 / Compute stable lexical proxies for LLVM IR."""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_function = False
    instructions = 0
    memory = {opcode: 0 for opcode in LLVM_MEMORY_OPS}
    functions = 0
    for raw in lines:
        line = raw.strip()
        if line.startswith("define "):
            in_function = True
            functions += 1
            continue
        if in_function and line == "}":
            in_function = False
            continue
        if not in_function or not line or line.startswith(";") or line.endswith(":"):
            continue
        instructions += 1
        operation = line.split("=", 1)[-1].strip().split(None, 1)[0]
        if operation in memory:
            memory[operation] += 1
    return {"functions": functions, "instructions": instructions, **memory}


def assembly_metrics(path: Path) -> dict[str, int]:
    """近似统计汇编指令与指令助记符。 / Approximately count assembly instructions and mnemonics."""
    instruction_pattern = re.compile(r"^\s*([A-Za-z][A-Za-z0-9.]*)\s*(?:\s|$)")
    instructions = 0
    mnemonics: set[str] = set()
    directives = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.endswith(":"):
            continue
        if line.startswith("."):
            directives += 1
            continue
        match = instruction_pattern.match(line)
        if match:
            instructions += 1
            mnemonics.add(match.group(1))
    return {
        "approx_instructions": instructions,
        "distinct_mnemonics": len(mnemonics),
        "directives": directives,
    }


def main() -> int:
    """以稳定 JSON 输出静态代理指标。 / Emit static proxy metrics as stable JSON."""
    parser = argparse.ArgumentParser(
        description="Static lexical proxies only; these values are not runtime-performance measurements."
    )
    parser.add_argument("--llvm-o0", type=Path, required=True)
    parser.add_argument("--llvm-o2", type=Path, required=True)
    parser.add_argument("--assembly-o0", type=Path, required=True)
    parser.add_argument("--assembly-o2", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "assembly": {
            "O0": assembly_metrics(args.assembly_o0),
            "O2": assembly_metrics(args.assembly_o2),
        },
        "disclaimer": "Static lexical proxies; not runtime-performance measurements.",
        "llvm_ir": {
            "O0": llvm_metrics(args.llvm_o0),
            "O2": llvm_metrics(args.llvm_o2),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
