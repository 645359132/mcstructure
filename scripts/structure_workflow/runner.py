"""Load AI-authored builders, export their result, and audit generated files."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
import importlib
from itertools import islice
import json
import os
from pathlib import Path
import sys
from typing import Callable, TypeVar

from mcstructure import Structure, StructurePlan
from mcstructure._fast_nbt import read_structure_size

from .exporter import ExportMode, ExportReport, export_project
from .model import ProjectSpec


BuildArtifact = Structure | StructurePlan
Builder = Callable[[], BuildArtifact]
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class BuildResult:
    spec: ProjectSpec
    report: ExportReport
    validated_files: int


@dataclass(frozen=True, slots=True)
class _StructureCheck:
    path: Path
    expected_size: tuple[int, int, int]
    identifier: str


def _validation_worker_count(workers: int | None) -> int:
    if workers is not None:
        if workers <= 0:
            raise ValueError("validation workers must be positive")
        return workers
    return min(16, max(4, os.cpu_count() or 1))


def _run_parallel(
    items: Iterable[T], function: Callable[[T], object], *, workers: int
) -> None:
    """Run I/O checks with bounded pending futures to keep validation memory low."""
    iterator = iter(items)
    if workers == 1:
        for item in iterator:
            function(item)
        return
    with ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix="structure-validation"
    ) as executor:
        pending: set[Future[object]] = {
            executor.submit(function, item)
            for item in islice(iterator, workers * 2)
        }
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                future.result()
            pending.update(
                executor.submit(function, item)
                for item in islice(iterator, len(done))
            )


def _repository_root(work_dir: Path) -> Path:
    for candidate in (work_dir, *work_dir.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
            return candidate
    raise ValueError(f"cannot locate repository root from {work_dir}")


def _check_python_sources(work_dir: Path) -> None:
    paths = [work_dir / "main.py", *(work_dir / "src").rglob("*.py")]
    missing = [str(path) for path in paths[:1] if not path.is_file()]
    if missing:
        raise ValueError(f"missing required source: {', '.join(missing)}")
    if not (work_dir / "src").is_dir():
        raise ValueError(f"missing source directory: {work_dir / 'src'}")
    for path in paths:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")


def load_builder(work_dir: Path, spec: ProjectSpec) -> Builder:
    """Import the zero-argument builder declared by project.json."""
    work_dir = work_dir.resolve()
    _check_python_sources(work_dir)
    root = _repository_root(work_dir)
    for path in (work_dir / "src", root / "src", root):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)
    module_name, function_name = spec.builder.split(":", 1)
    module = importlib.import_module(module_name)
    builder = getattr(module, function_name, None)
    if not callable(builder):
        raise ValueError(f"builder is not callable: {spec.builder}")
    return builder


def build_structure(work_dir: Path, spec: ProjectSpec) -> BuildArtifact:
    builder = load_builder(work_dir, spec)
    structure = builder()
    if not isinstance(structure, (Structure, StructurePlan)):
        raise TypeError(
            f"{spec.builder} returned {type(structure).__name__}, expected Structure "
            "or StructurePlan"
        )
    if structure.size != spec.structure_size:
        raise ValueError(
            f"builder returned {structure.size}, expected {spec.structure_size}"
        )
    return structure


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid generated JSON {path}: {error}") from error


def _validate_json_file(path: Path) -> None:
    _load_json(path)


def _validate_structure_file(check: _StructureCheck) -> None:
    try:
        with check.path.open("rb") as file:
            actual_size = read_structure_size(file)
    except (OSError, ValueError) as error:
        raise ValueError(
            f"invalid generated structure {check.identifier} at {check.path}: {error}"
        ) from error
    if actual_size != check.expected_size:
        raise ValueError(
            f"piece {check.identifier} has size {actual_size}, "
            f"manifest says {check.expected_size}"
        )


def validate_output(
    work_dir: Path,
    spec: ProjectSpec,
    *,
    deep: bool = True,
    workers: int | None = None,
) -> int:
    """Audit generated output, optionally reopening every file for deep checks."""
    worker_count = _validation_worker_count(workers)
    output_dir = work_dir / "out"
    manifest_path = output_dir / "project_manifest.json"
    placements_path = output_dir / "placements.json"
    if not manifest_path.is_file() or not placements_path.is_file():
        raise ValueError("output is incomplete; run the build command first")

    json_paths = sorted(output_dir.rglob("*.json"))
    json_path_set = set(json_paths)
    json_parent_counts = Counter(path.parent for path in json_paths)
    manifest = _load_json(manifest_path)
    placements_root = _load_json(placements_path)
    if not isinstance(manifest, dict) or not isinstance(placements_root, dict):
        raise ValueError("generated manifests must contain JSON objects")

    validated_structures = 0
    structure_checks: list[_StructureCheck] = []
    expected_structure_paths: set[Path] = set()
    for mode in ("worldgen", "modsdk"):
        placements = placements_root.get(mode)
        if not isinstance(placements, list):
            raise ValueError(f"placements.{mode} must be an array")
        for placement in placements:
            if not isinstance(placement, dict):
                raise ValueError(f"placements.{mode} entries must be objects")
            try:
                name = placement["name"]
                namespace = placement["structure_namespace"]
                offset = tuple(placement["offset"])
                size = tuple(placement["size"])
                identifier = placement["identifier"]
            except (KeyError, TypeError) as error:
                raise ValueError(
                    f"malformed {mode} placement: {placement!r}"
                ) from error
            if identifier != f"{namespace}:{name}":
                raise ValueError(f"invalid structure identifier: {identifier}")
            if len(offset) != 3 or len(size) != 3:
                raise ValueError(f"invalid placement vectors for {identifier}")
            if any(value < 0 for value in offset) or any(value <= 0 for value in size):
                raise ValueError(f"invalid placement bounds for {identifier}")
            if any(
                start + length > limit
                for start, length, limit in zip(offset, size, spec.structure_size)
            ):
                raise ValueError(f"placement exceeds logical canvas: {identifier}")
            if size[0] * size[1] * size[2] > 65_536:
                raise ValueError(f"piece exceeds 65,536 blocks: {identifier}")
            path = output_dir / "structures" / str(namespace) / f"{name}.mcstructure"
            expected_structure_paths.add(path)
            if deep:
                structure_checks.append(_StructureCheck(path, size, identifier))
            validated_structures += 1

        expected_count = manifest.get(f"{mode}_pieces")
        if expected_count != len(placements):
            raise ValueError(f"{mode} piece count differs between generated manifests")

    structure_root = output_dir / "structures"
    actual_structure_paths = (
        set(structure_root.rglob("*.mcstructure"))
        if structure_root.is_dir()
        else set()
    )
    missing_structures = sorted(
        expected_structure_paths - actual_structure_paths, key=str
    )
    if missing_structures:
        raise ValueError(f"missing structure file: {missing_structures[0]}")

    if deep:
        already_loaded = {manifest_path, placements_path}
        _run_parallel(
            (path for path in json_paths if path not in already_loaded),
            _validate_json_file,
            workers=worker_count,
        )
        _run_parallel(
            structure_checks,
            _validate_structure_file,
            workers=worker_count,
        )

    worldgen = placements_root["worldgen"]
    if worldgen:
        features_dir = output_dir / "netease_features"
        rules_dir = output_dir / "netease_feature_rules"
        if json_parent_counts[features_dir] != len(worldgen):
            raise ValueError("worldgen feature count does not match placement count")
        if json_parent_counts[rules_dir] != len(worldgen):
            raise ValueError(
                "worldgen feature-rule count does not match placement count"
            )
        expected_dimension = (
            output_dir / "netease_dimension" / f"dm{spec.dimension_id}.json"
        )
        if expected_dimension not in json_path_set:
            raise ValueError(f"missing dimension definition: {expected_dimension}")
        dimension_root = _load_json(expected_dimension)
        dimension_info = (
            dimension_root.get("netease:dimension_info")
            if isinstance(dimension_root, dict)
            else None
        )
        dimension_components = (
            dimension_info.get("components")
            if isinstance(dimension_info, dict)
            else None
        )
        biome_sources = (
            dimension_components.get("netease:biome_source")
            if isinstance(dimension_components, dict)
            else None
        )
        biome_source = (
            biome_sources[0]
            if isinstance(biome_sources, list) and biome_sources
            else None
        )
        biome_pool = (
            biome_source.get("pool") if isinstance(biome_source, dict) else None
        )
        if biome_pool is None:
            raise ValueError(f"malformed dimension biome source: {expected_dimension}")
        if biome_pool != [{"biome_type": spec.dimension_biome, "weight": 1}]:
            raise ValueError("dimension biome source differs from project.json")
        expected_biome = (
            output_dir
            / "netease_biomes"
            / spec.dimension_biome_namespace
            / f"{spec.dimension_biome}.json"
        )
        if expected_biome not in json_path_set:
            raise ValueError(f"missing biome definition: {expected_biome}")
        biome_root = _load_json(expected_biome)
        biome = (
            biome_root.get("minecraft:biome") if isinstance(biome_root, dict) else None
        )
        description = biome.get("description") if isinstance(biome, dict) else None
        components = biome.get("components") if isinstance(biome, dict) else None
        if not isinstance(description, dict) or not isinstance(components, dict):
            raise ValueError(f"malformed biome definition: {expected_biome}")
        if description.get("identifier") != spec.dimension_biome:
            raise ValueError("generated biome identifier differs from project.json")
        if description.get("inherits") != spec.biome_inherits:
            raise ValueError("generated biome inheritance differs from project.json")
        for tag in (spec.dimension_biome_namespace, spec.dimension_biome):
            if components.get(tag) != {}:
                raise ValueError(f"generated biome is missing required tag: {tag}")
    if placements_root["modsdk"]:
        modsdk_path = output_dir / "place_with_modsdk.py"
        compile(modsdk_path.read_text(encoding="utf-8"), str(modsdk_path), "exec")

    return len(json_paths) + validated_structures


def build_work(work_dir: Path, *, mode: ExportMode = "all") -> BuildResult:
    work_dir = work_dir.resolve()
    spec = ProjectSpec.load(work_dir)
    structure = build_structure(work_dir, spec)
    report = export_project(structure, spec, work_dir / "out", mode=mode)
    validated_files = validate_output(work_dir, spec, deep=False)
    return BuildResult(spec, report, validated_files)


def validate_work(
    work_dir: Path, *, deep: bool = True, workers: int | None = None
) -> int:
    work_dir = work_dir.resolve()
    spec = ProjectSpec.load(work_dir)
    build_structure(work_dir, spec)
    return validate_output(work_dir, spec, deep=deep, workers=workers)


def print_result(result: BuildResult) -> None:
    print(
        f"Generated {result.report.worldgen_pieces} worldgen pieces and "
        f"{result.report.modsdk_pieces} ModSDK pieces in {result.report.output_dir}"
    )
    print(f"Validated files: {result.validated_files}")
    print(f"Dimension ID: {result.spec.dimension_id}")
    print(f"Structure origin: {result.spec.world_origin}")
    print(f"Recommended teleport: {result.report.teleport_command}")


def run_work_entry(work_dir: Path) -> int:
    parser = argparse.ArgumentParser(
        description="Build this AI-authored structure and deterministic support files."
    )
    parser.add_argument("--mode", choices=("all", "worldgen", "modsdk"), default="all")
    args = parser.parse_args()
    result = build_work(work_dir, mode=args.mode)
    print_result(result)
    return 0
