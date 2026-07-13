import json
from pathlib import Path

import pytest

from scripts.structure_workflow.model import ProjectSpec
from scripts.structure_workflow.runner import build_structure
from scripts.structure_workflow.scaffold import create_work


REPOSITORY = Path(__file__).resolve().parents[1]


def test_example_work_contract_matches_builder() -> None:
    work_dir = REPOSITORY / "workset" / "example_work"
    spec = ProjectSpec.load(work_dir)

    structure = build_structure(work_dir, spec)

    assert structure.size == (96, 48, 96)
    assert spec.builder == "example_project:build_structure"


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
    )

    spec = ProjectSpec.load(work_dir)
    assert spec.namespace == "new_work"
    assert spec.builder == "new_work_project:build_structure"
    assert (work_dir / "BRIEF.md").is_file()
    assert (work_dir / "main.py").is_file()
    assert (work_dir / "src" / "new_work_project" / "build.py").is_file()
    assert not (work_dir / "out").exists()


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
