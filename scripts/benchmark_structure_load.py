"""Benchmark public Structure.load and, optionally, its Python fallback."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from time import perf_counter

from mcstructure import NATIVE_DECODER_AVAILABLE, Structure


def _benchmark(data: bytes, runs: int, *, python_fallback: bool) -> float:
    load = Structure._load_with_nbtx if python_fallback else Structure.load
    start = perf_counter()
    for _ in range(runs):
        load(BytesIO(data))
    return (perf_counter() - start) / runs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--compare-python", action="store_true")
    parser.add_argument("--python-runs", type=int, default=3)
    args = parser.parse_args()
    if args.runs <= 0 or args.python_runs <= 0:
        parser.error("run counts must be positive")

    data = args.structure.read_bytes()
    native_seconds = _benchmark(data, args.runs, python_fallback=False)
    print(f"file: {args.structure}")
    print(f"bytes: {len(data)}")
    print(f"native decoder available: {NATIVE_DECODER_AVAILABLE}")
    print(f"Structure.load: {native_seconds:.9f} seconds/load")
    if args.compare_python:
        python_seconds = _benchmark(data, args.python_runs, python_fallback=True)
        print(f"Python fallback: {python_seconds:.9f} seconds/load")
        print(f"speedup: {python_seconds / native_seconds:.1f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
