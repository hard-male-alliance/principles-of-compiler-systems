#!/usr/bin/env python3
"""将命令标准输出可靠写入文件。 / Reliably capture command stdout into a file."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    """执行命令，原子替换输出文件。 / Execute a command and atomically replace its output file."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    with temporary.open("wb") as stream:
        result = subprocess.run(command, stdout=stream, check=False)
    if result.returncode != 0:
        temporary.unlink(missing_ok=True)
        return result.returncode
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
