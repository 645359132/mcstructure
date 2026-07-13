"""Generate the example structure project and all NetEase support files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "src"
REPOSITORY_SOURCE = HERE.parents[1] / "src"
for source_dir in (SOURCE, REPOSITORY_SOURCE):
    if source_dir.is_dir():
        sys.path.insert(0, str(source_dir))

from example_project import CONFIG, build_structure, export_project  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a structure and export worldgen/ModSDK resources."
    )
    parser.add_argument(
        "--mode",
        choices=("all", "worldgen", "modsdk"),
        default="all",
        help="Select which placement resources to export (default: all).",
    )
    args = parser.parse_args()

    structure = build_structure()
    report = export_project(structure, CONFIG, HERE / "out", mode=args.mode)
    print(
        f"Generated {report.worldgen_pieces} worldgen pieces and "
        f"{report.modsdk_pieces} ModSDK pieces in {report.output_dir}"
    )
    print(f"Dimension ID: {CONFIG.dimension_id}")
    print(f"Structure origin: {CONFIG.world_origin}")
    print(f"Recommended teleport: {report.teleport_command}")


if __name__ == "__main__":
    main()
