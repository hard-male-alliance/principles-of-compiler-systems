#!/usr/bin/env python3
"""静态检查 AscendNPU IR 教学资产。 / Structurally check the AscendNPU IR study asset."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    """验证关键方言结构，但不冒充专用编译器。 / Check structure without impersonating the compiler."""
    parser = argparse.ArgumentParser()
    parser.add_argument("mlir", type=Path)
    args = parser.parse_args()
    text = args.mlir.read_text(encoding="utf-8")
    required = (
        "hacc.entry",
        "#hacc.function_kind<DEVICE>",
        "#hivm.address_space<gm>",
        "#hivm.address_space<ub>",
        "hivm.hir.load",
        "hivm.hir.vadd",
        "hivm.hir.store",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise SystemExit(f"missing required AscendNPU IR structure: {missing}")
    positions = [text.index(op) for op in ("hivm.hir.load", "hivm.hir.vadd", "hivm.hir.store")]
    if positions != sorted(positions):
        raise SystemExit("expected load -> vadd -> store order")
    print("AscendNPU IR static structure: PASS (not a compile/run claim)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
