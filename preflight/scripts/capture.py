#!/usr/bin/env python3
"""Capture reproducible compiler-pipeline artifacts for the clipped-dot case.

为截断点积案例捕获可复现的编译流水线产物。Portable mode stops before
target linking; full mode additionally builds and executes Linux RV64GC artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import IO, Sequence


def require_tool(name: str) -> str:
    """Return an executable path or report one actionable missing dependency.

    返回工具路径；缺失时报告一个可操作的依赖错误。
    """

    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"required tool not found on PATH: {name}")
    return path


def run(
    command: Sequence[str],
    *,
    stdout: IO[str] | None = None,
    cwd: Path | None = None,
    commands: list[list[str]],
) -> None:
    """Run one recorded command without a shell.

    不经 shell 执行并记录命令，从而保留参数边界并避免平台相关 quoting。
    """

    rendered = [str(item) for item in command]
    commands.append(rendered)
    subprocess.run(rendered, cwd=cwd, stdout=stdout, check=True, text=True)


def capture_text(
    command: Sequence[str], output: Path, *, commands: list[list[str]]
) -> None:
    """Capture one command's standard output as UTF-8 text.

    将单条命令的标准输出捕获为 UTF-8 文本。
    """

    with output.open("w", encoding="utf-8", newline="\n") as stream:
        run(command, stdout=stream, commands=commands)


def derive_tool(prefix: str, suffix: str) -> str:
    """Resolve a GNU cross-tool sharing the compiler's target prefix.

    解析与交叉编译器共享目标前缀的 GNU 工具。
    """

    candidate = Path(prefix).with_name(f"riscv64-linux-gnu-{suffix}")
    if candidate.exists():
        return str(candidate)
    return require_tool(f"riscv64-linux-gnu-{suffix}")


def main() -> int:
    """Generate portable observations and, when requested, full RV64 artifacts.

    生成可移植观测；在 full 模式下继续生成完整 RV64 目标与可执行文件。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("portable", "full"), required=True)
    parser.add_argument("--clang", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = root / "src" / "clipped_dot.c"
    sysy = root / "src" / "clipped_dot.sy"
    include = root / "include"
    authored_ir = root / "ir" / "clipped_dot.ll"
    authored_asm = root / "asm" / "clipped_dot.S"
    repository = root.parent
    clang = str(Path(args.clang).resolve())
    commands: list[list[str]] = []
    target = ["--target=riscv64-unknown-linux-gnu", "-march=rv64gc", "-mabi=lp64d"]
    common = [clang, "-std=c17", "-Wall", "-Wextra", "-Wpedantic", f"-I{include}"]

    # Portable observations intentionally need neither a target sysroot nor target linker.
    # 可移植观测有意不依赖目标 sysroot 或目标链接器。
    run([*common, "-E", str(source), "-o", str(output / "clipped_dot.i")], commands=commands)
    capture_text(
        [*common, "-fsyntax-only", "-Xclang", "-ast-dump=json", str(source)],
        output / "clipped_dot.ast.json",
        commands=commands,
    )
    for level in ("O0", "O2"):
        run(
            [
                *common,
                *target,
                f"-{level}",
                "-fno-inline",
                "-S",
                "-emit-llvm",
                str(source),
                "-o",
                str(output / f"clipped_dot.{level}.ll"),
            ],
            commands=commands,
        )
        run(
            [
                *common,
                *target,
                f"-{level}",
                "-fno-inline",
                "-S",
                str(source),
                "-o",
                str(output / f"clipped_dot.{level}.s"),
            ],
            commands=commands,
        )

    # Clang's parser/code generator is the compatibility floor for opaque-pointer IR.
    # Clang 的解析器和代码生成器构成 opaque-pointer IR 的最低兼容性检查。
    run(
        [clang, *target, "-c", str(authored_ir), "-o", str(output / "handwritten-ir.rv64.o")],
        commands=commands,
    )
    llvm_as = shutil.which("llvm-as")
    if llvm_as:
        run([llvm_as, str(authored_ir), "-o", str(output / "handwritten.bc")], commands=commands)
        opt = shutil.which("opt")
        if opt:
            run([opt, "-passes=verify", "-disable-output", str(output / "handwritten.bc")], commands=commands)

    if args.mode == "full":
        cross_cc = require_tool("riscv64-linux-gnu-gcc")
        cross_ar = derive_tool(cross_cc, "ar")
        readelf = derive_tool(cross_cc, "readelf")
        objdump = derive_tool(cross_cc, "objdump")
        nm = derive_tool(cross_cc, "nm")
        runtime_obj = output / "sylib.glibc.rv64.o"
        runtime_archive = output / "libsysy-glibc-rv64.a"

        run(
            [
                cross_cc,
                "-std=gnu17",
                "-fcommon",
                "-O2",
                "-march=rv64gc",
                "-mabi=lp64d",
                "-c",
                str(repository / "lib" / "sylib.c"),
                "-o",
                str(runtime_obj),
            ],
            commands=commands,
        )
        run([cross_ar, "rcs", str(runtime_archive), str(runtime_obj)], commands=commands)
        run(
            [*common, *target, "-O0", "-c", str(source), "-o", str(output / "c.rv64.o")],
            commands=commands,
        )
        run(
            [
                clang,
                *target,
                "-std=c17",
                "-x",
                "c",
                "-include",
                str(include / "sysy_builtin.h"),
                "-c",
                str(sysy),
                "-o",
                str(output / "sysy.rv64.o"),
            ],
            commands=commands,
        )
        run(
            [cross_cc, "-march=rv64gc", "-mabi=lp64d", "-c", str(authored_asm), "-o", str(output / "handwritten-asm.rv64.o")],
            commands=commands,
        )

        objects = {
            "c": output / "c.rv64.o",
            "sysy": output / "sysy.rv64.o",
            "ir": output / "handwritten-ir.rv64.o",
            "asm": output / "handwritten-asm.rv64.o",
        }
        for name, obj in objects.items():
            capture_text([readelf, "-h", "-S", "-s", "-r", str(obj)], output / f"{name}.object.txt", commands=commands)
            capture_text([objdump, "-dr", str(obj)], output / f"{name}.disassembly.txt", commands=commands)
            executable = output / f"clipped-dot-{name}.rv64"
            run(
                [
                    cross_cc,
                    "-static",
                    "-no-pie",
                    "-march=rv64gc",
                    "-mabi=lp64d",
                    str(obj),
                    str(runtime_archive),
                    f"-Wl,-Map={output / f'{name}.link.map'}",
                    "-o",
                    str(executable),
                ],
                commands=commands,
            )
            capture_text([readelf, "-h", "-l", "-s", str(executable)], output / f"{name}.elf.txt", commands=commands)
            capture_text([objdump, "-d", str(executable)], output / f"{name}.elf.disassembly.txt", commands=commands)

        # Preserve direct evidence for why the supplied newlib archive is not linked here.
        # 保留直接证据，说明为何此处不链接课程随附的 newlib 归档。
        capture_text(
            [nm, "-u", str(repository / "lib" / "libsysy_riscv.a")],
            output / "provided-archive.undefined.txt",
            commands=commands,
        )

    metadata = {
        "schema": 1,
        "case": "clipped-dot-product",
        "mode": args.mode,
        "target": "riscv64-unknown-linux-gnu/rv64gc/lp64d",
        "oracle": {
            "stdout": {"-1": "0\n", "0": "0\n", "1": "-8\n", "4": "8\n", "8": "16\n", "10": "16\n"},
            "stderr": "TOTAL: 0H-0M-0S-0us\n",
            "exit_status": 0,
        },
        "commands": commands,
        "environment": {"platform": sys.platform, "python": sys.version.split()[0]},
    }
    (output / "capture.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"captured {args.mode} artifacts in {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f"capture failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
