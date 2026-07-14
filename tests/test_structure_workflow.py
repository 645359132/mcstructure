import json
from pathlib import Path

import pytest

from mcstructure import Block, Structure, StructurePlan

import scripts.structure_workflow.exporter as workflow_exporter
import scripts.structure_workflow.runner as workflow_runner
from scripts.structure_workflow.exporter import export_project
from scripts.structure_workflow.model import ProjectSpec
from scripts.structure_workflow.runner import build_structure, validate_output
from scripts.structure_workflow.scaffold import create_work


REPOSITORY = Path(__file__).resolve().parents[1]


def test_structure_split_is_lazy(monkeypatch: pytest.MonkeyPatch) -> None:
    structure = Structure((32, 8, 32), Block("minecraft:stone"))
    real_structure = workflow_exporter.Structure
    created_piece_sizes: list[tuple[int, int, int]] = []

    def tracked_structure(
        size: tuple[int, int, int], fill: Block | None = Block("minecraft:air")
    ) -> Structure:
        created_piece_sizes.append(size)
        return real_structure(size, fill)

    monkeypatch.setattr(workflow_exporter, "Structure", tracked_structure)
    pieces = workflow_exporter._split(
        structure,
        (16, 8, 16),
        name_prefix="piece",
        structure_namespace="test",
    )

    assert created_piece_sizes == []
    assert iter(pieces) is pieces
    placement, piece = next(pieces)
    assert created_piece_sizes == [(16, 8, 16)]
    assert placement.offset == (0, 0, 0)
    assert piece.size == (16, 8, 16)


def test_runner_accepts_recorded_structure_plan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spec = ProjectSpec(
        schema_version=1,
        project_name="Recorded Work",
        namespace="recorded_work",
        structure_name="landmark",
        builder="recorded_work:build_structure",
        structure_size=(32, 8, 32),
        world_origin=(1024, 64, 1024),
        dimension_id=700_000_004,
        dimension_mod_id="recorded_work",
        dimension_biome="recorded_work_plains",
    )
    plan = StructurePlan(spec.structure_size, Block("minecraft:air"))
    plan.set_blocks((0, 0, 0), (31, 1, 31), Block("minecraft:stone"))
    monkeypatch.setattr(workflow_runner, "load_builder", lambda *_: lambda: plan)

    assert build_structure(tmp_path, spec) is plan


def test_export_project_accepts_recorded_structure_plan(tmp_path: Path) -> None:
    spec = ProjectSpec(
        schema_version=1,
        project_name="Recorded Export",
        namespace="recorded_export",
        structure_name="landmark",
        builder="recorded_export:build_structure",
        structure_size=(32, 8, 32),
        world_origin=(1024, 64, 1024),
        dimension_id=700_000_005,
        dimension_mod_id="recorded_export",
        dimension_biome="recorded_export_plains",
    )
    plan = StructurePlan(spec.structure_size, Block("minecraft:air"))
    plan.set_blocks((0, 0, 0), (31, 1, 31), Block("minecraft:stone"))

    report = export_project(plan, spec, tmp_path / "out", mode="worldgen")

    assert report.worldgen_pieces == 4
    assert report.modsdk_pieces == 0
    assert validate_output(tmp_path, spec) > 0


def test_example_work_contract_matches_builder() -> None:
    work_dir = REPOSITORY / "workset" / "example_work"
    spec = ProjectSpec.load(work_dir)

    structure = build_structure(work_dir, spec)

    assert structure.size == (96, 48, 96)
    assert spec.builder == "example_project:build_structure"
    assert spec.biome_inherits == "plains"


def test_scaffold_creates_only_source_contract_not_generated_output(
    tmp_path: Path,
) -> None:
    work_dir = tmp_path / "new_work"

    create_work(
        work_dir,
        project_name="New Work",
        namespace="new-work",
        package="new-work-project",
        size=(64, 32, 64),
        origin=(1024, 64, 1024),
        dimension_id=700_000_001,
        dimension_biome="new_work_plains",
        biome_inherits="plains",
    )

    spec = ProjectSpec.load(work_dir)
    assert spec.namespace == "new_work"
    assert spec.builder == "new_work_project:build_structure"
    assert spec.biome_inherits == "plains"
    assert (work_dir / "BRIEF.md").is_file()
    assert (work_dir / "main.py").is_file()
    assert (work_dir / "src" / "new_work_project" / "build.py").is_file()
    assert not (work_dir / "out").exists()


def test_scaffold_uses_recorded_plan_for_memory_heavy_canvas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    work_dir = tmp_path / "large_work"

    create_work(
        work_dir,
        project_name="Large Work",
        namespace="large_work",
        package="large_work_project",
        size=(1024, 128, 1024),
        origin=(4096, 64, 4096),
        dimension_id=700_000_006,
        dimension_biome="large_work_plains",
    )

    source = (work_dir / "src" / "large_work_project" / "build.py").read_text(
        encoding="utf-8"
    )
    spec = ProjectSpec.load(work_dir)
    monkeypatch.setattr(workflow_runner, "_repository_root", lambda _: REPOSITORY)
    result = build_structure(work_dir, spec)

    assert "StructurePlan" in source
    assert isinstance(result, StructurePlan)
    assert result.operation_count == 1


def test_contract_rejects_oversized_piece(tmp_path: Path) -> None:
    work_dir = tmp_path / "bad_work"
    work_dir.mkdir()
    data = {
        "schema_version": 1,
        "project_name": "Bad Work",
        "namespace": "bad_work",
        "structure_name": "landmark",
        "builder": "bad_work:build_structure",
        "structure_size": [128, 64, 128],
        "world_origin": [1024, 64, 1024],
        "dimension_id": 700000002,
        "dimension_mod_id": "bad_work",
        "dimension_biome": "bad_work_plains",
        "modsdk_piece_size": [64, 64, 64],
    }
    (work_dir / "project.json").write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="65,536"):
        ProjectSpec.load(work_dir)


def test_worldgen_export_includes_valid_custom_biome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = ProjectSpec(
        schema_version=1,
        project_name="Biome Work",
        namespace="biome_work",
        structure_name="landmark",
        builder="biome_work:build_structure",
        structure_size=(16, 8, 16),
        world_origin=(1024, 64, 1024),
        dimension_id=700_000_003,
        dimension_mod_id="biome_work",
        dimension_biome="dm700000003_roofed_forest",
        biome_inherits="roofed_forest",
    )
    structure = Structure(spec.structure_size, Block("minecraft:stone"))

    export_project(structure, spec, tmp_path / "out", mode="worldgen")

    biome_path = (
        tmp_path
        / "out"
        / "netease_biomes"
        / "dm700000003"
        / "dm700000003_roofed_forest.json"
    )
    biome_root = json.loads(biome_path.read_text(encoding="utf-8"))
    biome = biome_root["minecraft:biome"]
    assert biome["description"] == {
        "identifier": "dm700000003_roofed_forest",
        "inherits": "roofed_forest",
    }
    assert biome["components"]["dm700000003"] == {}
    assert biome["components"]["dm700000003_roofed_forest"] == {}

    def unexpected_full_load(*args: object) -> None:
        raise AssertionError("generated-piece validation must not fully decode NBT")

    monkeypatch.setattr(Structure, "load", unexpected_full_load)
    assert validate_output(tmp_path, spec) > 0

    def unexpected_header_read(*args: object) -> None:
        raise AssertionError("fresh-output validation must not reopen structure files")

    monkeypatch.setattr(workflow_runner, "read_structure_size", unexpected_header_read)
    assert validate_output(tmp_path, spec, deep=False) > 0
