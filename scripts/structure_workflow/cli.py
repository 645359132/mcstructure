"""Command-line interface for scaffolding, building, and validating works."""

from __future__ import annotations

import argparse
from pathlib import Path

from .runner import build_work, print_result, validate_work
from .scaffold import create_work


def _vec3(values: list[int]) -> tuple[int, int, int]:
    return values[0], values[1], values[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage AI-authored structure works.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new = subparsers.add_parser("new", help="create a work contract and source shell")
    new.add_argument("work_dir", type=Path)
    new.add_argument("--project-name")
    new.add_argument("--namespace")
    new.add_argument("--package")
    new.add_argument("--size", type=int, nargs=3, default=(96, 48, 96))
    new.add_argument("--origin", type=int, nargs=3, default=(1024, 56, 1024))
    new.add_argument("--dimension-id", type=int)
    new.add_argument("--dimension-biome")
    new.add_argument(
        "--biome-inherits",
        default="plains",
        help="vanilla biome inherited by the generated NetEase biome",
    )

    build = subparsers.add_parser("build", help="build, export, and validate a work")
    build.add_argument("work_dir", type=Path)
    build.add_argument("--mode", choices=("all", "worldgen", "modsdk"), default="all")

    validate = subparsers.add_parser(
        "validate", help="audit source and existing output"
    )
    validate.add_argument("work_dir", type=Path)

    args = parser.parse_args()
    if args.command == "new":
        fallback = args.work_dir.name
        create_work(
            args.work_dir,
            project_name=args.project_name or fallback.replace("_", " ").title(),
            namespace=args.namespace or fallback,
            package=args.package or f"{fallback}_project",
            size=_vec3(args.size),
            origin=_vec3(args.origin),
            dimension_id=args.dimension_id,
            dimension_biome=args.dimension_biome,
            biome_inherits=args.biome_inherits,
        )
        print(f"Created {args.work_dir.resolve()}")
        print(
            "Next: fill BRIEF.md, ask AI to implement src/, then run the build command."
        )
        return 0
    if args.command == "build":
        print_result(build_work(args.work_dir, mode=args.mode))
        return 0
    validated = validate_work(args.work_dir)
    print(f"Validated {validated} generated files in {args.work_dir.resolve() / 'out'}")
    return 0
