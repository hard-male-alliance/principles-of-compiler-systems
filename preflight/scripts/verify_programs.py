#!/usr/bin/env python3
"""比较边界化阶乘各表示的行为。 / Compare bounded-factorial representations."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


CASES = {
    -3: "1\n",
    0: "1\n",
    1: "1\n",
    5: "120\n",
    10: "3628800\n",
    20: "3628800\n",
}


def run(command: list[str], value: int) -> str:
    """运行一个候选程序并返回标准输出。 / Run one candidate and return stdout."""
    result = subprocess.run(
        command,
        input=f"{value}\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{command!r} exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result.stdout.replace("\r\n", "\n")


def main() -> int:
    """验证所有候选在边界与典型输入上等价。 / Verify equivalence on boundary and typical inputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", action="append", nargs="+", required=True)
    args = parser.parse_args()
    for command in args.program:
        if len(command) == 1:
            command[0] = str(Path(command[0]).resolve())
        for value, expected in CASES.items():
            actual = run(command, value)
            if actual != expected:
                raise SystemExit(
                    f"behavior mismatch: command={command!r}, input={value}, "
                    f"expected={expected!r}, actual={actual!r}"
                )
        print(f"behavior: PASS: {' '.join(command)} ({len(CASES)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
