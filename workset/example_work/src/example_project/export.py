"""Export one logical build for NetEase worldgen and ModSDK placement."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
from typing import Any, Literal

import numpy as np
from mcstructure import Block, Structure

from .config import ProjectConfig, Vec3


ExportMode = Literal["all", "worldgen", "modsdk"]


@dataclass(frozen=True, slots=True)
class Placement:
    name: str
    offset: Vec3
    size: Vec3
    structure_namespace: str

    @property
    def identifier(self) -> str:
        return f"{self.structure_namespace}:{self.name}"


@dataclass(frozen=True, slots=True)
class ExportReport:
    output_dir: Path
    worldgen_pieces: int
    modsdk_pieces: int
    teleport_command: str


def _json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _empty_palette_index(structure: Structure) -> int | None:
    air = Block("minecraft:air")
    for index, block in enumerate(structure.palette):
        if block == air:
            return index
    return None


def _split(
    structure: Structure,
    piece_size: Vec3,
    *,
    name_prefix: str,
    structure_namespace: str,
) -> list[tuple[Placement, Structure]]:
    empty_index = _empty_palette_index(structure)
    built: list[tuple[Placement, Structure]] = []
    size_x, size_y, size_z = structure.size
    step_x, step_y, step_z = piece_size
    for y0 in range(0, size_y, step_y):
        for z0 in range(0, size_z, step_z):
            for x0 in range(0, size_x, step_x):
                x2 = min(x0 + step_x, size_x)
                y2 = min(y0 + step_y, size_y)
                z2 = min(z0 + step_z, size_z)
                region = structure.structure[x0:x2, y0:y2, z0:z2]
                if empty_index is not None and not np.any(region != empty_index):
                    continue
                actual_size = (x2 - x0, y2 - y0, z2 - z0)
                piece = Structure(actual_size, None)
                piece._palette = structure._palette.copy()
                piece.structure = region.copy()
                name = f"{name_prefix}_x{x0:04d}_y{y0:04d}_z{z0:04d}"
                built.append(
                    (
                        Placement(
                            name=name,
                            offset=(x0, y0, z0),
                            size=actual_size,
                            structure_namespace=structure_namespace,
                        ),
                        piece,
                    )
                )
    return built


def _write_structures(
    output_dir: Path, built: list[tuple[Placement, Structure]]
) -> list[Placement]:
    placements: list[Placement] = []
    for placement, structure in built:
        namespace_dir = output_dir / "structures" / placement.structure_namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)
        with (namespace_dir / f"{placement.name}.mcstructure").open("wb") as file:
            structure.dump(file)
        placements.append(placement)
    return placements


def _origin_expression(variable: str, target: int, period: int) -> str:
    operation = f"-{target}" if target >= 0 else f"+{abs(target)}"
    return f"math.mod({variable}{operation},{period})==0"


def _write_worldgen(
    output_dir: Path,
    config: ProjectConfig,
    placements: list[Placement],
) -> None:
    features_dir = output_dir / "netease_features"
    rules_dir = output_dir / "netease_feature_rules"
    dimension_dir = output_dir / "netease_dimension"
    features_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)
    dimension_dir.mkdir(parents=True, exist_ok=True)

    for placement in placements:
        feature_identifier = f"{config.namespace}:{placement.name}_structure_feature"
        _json(
            features_dir / f"{placement.name}_structure_feature.json",
            {
                "format_version": "1.14.0",
                "netease:structure_feature": {
                    "description": {"identifier": feature_identifier},
                    "places_structure": placement.identifier,
                    "rotation": 0,
                },
            },
        )
        target_x = config.world_origin[0] + placement.offset[0]
        target_y = config.world_origin[1] + placement.offset[1]
        target_z = config.world_origin[2] + placement.offset[2]
        iterations = (
            _origin_expression("variable.originx", target_x, config.repeat_period)
            + " && "
            + _origin_expression("variable.originz", target_z, config.repeat_period)
            + "?1:0"
        )
        _json(
            rules_dir / f"{placement.name}_feature_rule.json",
            {
                "format_version": "1.14.0",
                "minecraft:feature_rules": {
                    "description": {
                        "identifier": (
                            f"{config.namespace}:{placement.name}_feature_rule"
                        ),
                        "places_feature": feature_identifier,
                    },
                    "conditions": {
                        "placement_pass": "first_pass",
                        "minecraft:biome_filter": [
                            {
                                "all_of": [
                                    {
                                        "any_of": [
                                            {
                                                "test": "has_biome_tag",
                                                "operator": "==",
                                                "value": config.dimension_biome,
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                    },
                    "distribution": {
                        "iterations": iterations,
                        "coordinate_eval_order": "yxz",
                        "scatter_chance": 100.0,
                        "x": 0,
                        "y": target_y,
                        "z": 0,
                    },
                },
            },
        )

    _json(
        dimension_dir / "dimension_config.json",
        {
            "netease:dimension": {
                "modDimensionId": [config.dimension_id],
                "modId": config.dimension_mod_id,
            }
        },
    )
    _json(
        dimension_dir / f"dm{config.dimension_id}.json",
        {
            "format_version": "1.14.0",
            "netease:dimension_info": {
                "components": {
                    "netease:biome_source": [
                        {
                            "pool": [
                                {"biome_type": config.dimension_biome, "weight": 1}
                            ],
                            "type": "random_with_weight",
                        }
                    ],
                    "netease:dimension_type": "minecraft:overworld",
                    "netease:generator_noise": {},
                }
            },
        },
    )


def _relative(variable: str, offset: int) -> str:
    if offset == 0:
        return variable
    return f"{variable} + {offset}" if offset > 0 else f"{variable} - {abs(offset)}"


def _write_modsdk(
    output_dir: Path,
    config: ProjectConfig,
    placements: list[Placement],
) -> None:
    center_x = config.structure_size[0] // 2
    center_z = config.structure_size[2] // 2
    ordered = sorted(
        placements,
        key=lambda item: (item.offset[0] + item.size[0] // 2 - center_x) ** 2
        + (item.offset[2] + item.size[2] // 2 - center_z) ** 2,
    )
    lines = [
        '"""Generated ModSDK placement helper. Copy this into server-side code."""',
        "",
        "",
        "def place_generated_structure(serverApi, levelId, entity_id):",
        "    factory = serverApi.GetEngineCompFactory()",
        "    position = factory.CreatePos(entity_id).GetFootPos()",
        "    x, y, z = (int(value) for value in position)",
        "    game = factory.CreateGame(levelId)",
        "    dimension = factory.CreateDimension(entity_id).GetEntityDimensionId()",
        "    placements = [",
    ]
    for placement in ordered:
        offset_x = placement.offset[0] - center_x
        offset_z = placement.offset[2] - center_z
        lines.append(
            "        (("
            f"{_relative('x', offset_x)}, {_relative('y', placement.offset[1])}, "
            f"{_relative('z', offset_z)}), \"{placement.identifier}\"),"
        )
    lines.extend(
        [
            "    ]",
            f"    batch_size = {config.modsdk_batch_size}",
            f"    batch_delay = {config.modsdk_batch_delay!r}",
            f"    placement_passes = {config.modsdk_passes}",
            f"    pass_delay = {config.modsdk_pass_delay!r}",
            '    state = {"index": 0, "pass": 0}',
            "",
            "    def place_next_batch():",
            '        start = state["index"]',
            "        end = min(start + batch_size, len(placements))",
            "        for index in range(start, end):",
            "            target, structure_name = placements[index]",
            "            game.PlaceStructure(",
            "                None, target, structure_name, dimension, 0",
            "            )",
            '        state["index"] = end',
            "        if end < len(placements):",
            "            game.AddTimer(batch_delay, place_next_batch)",
            '        elif state["pass"] + 1 < placement_passes:',
            '            state["pass"] += 1',
            '            state["index"] = 0',
            "            game.AddTimer(pass_delay, place_next_batch)",
            "",
            "    place_next_batch()",
        ]
    )
    (output_dir / "place_with_modsdk.py").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _clean_owned_outputs(output_dir: Path) -> None:
    for name in (
        "structures",
        "netease_features",
        "netease_feature_rules",
        "netease_dimension",
    ):
        path = output_dir / name
        if path.exists():
            shutil.rmtree(path)
    for name in ("place_with_modsdk.py", "placements.json", "project_manifest.json"):
        path = output_dir / name
        if path.exists():
            path.unlink()


def _teleport(config: ProjectConfig) -> tuple[Vec3, str]:
    # Stand outside the negative-Z facade and face south toward the build.
    x = config.world_origin[0] + config.structure_size[0] // 2
    y = config.world_origin[1] + 10
    z = config.world_origin[2] - 12
    return (x, y, z), f"/tp @s {x} {y} {z} 0 15"


def export_project(
    structure: Structure,
    config: ProjectConfig,
    output_dir: Path,
    *,
    mode: ExportMode = "all",
) -> ExportReport:
    """Export worldgen resources, ModSDK resources, or both."""
    config.validate()
    if structure.size != config.structure_size:
        raise ValueError(
            f"builder returned {structure.size}, expected {config.structure_size}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    _clean_owned_outputs(output_dir)

    worldgen: list[Placement] = []
    modsdk: list[Placement] = []
    if mode in ("all", "worldgen"):
        worldgen = _write_structures(
            output_dir,
            _split(
                structure,
                config.worldgen_piece_size,
                name_prefix=config.structure_name,
                structure_namespace=config.worldgen_structure_namespace,
            ),
        )
        _write_worldgen(output_dir, config, worldgen)
    if mode in ("all", "modsdk"):
        modsdk = _write_structures(
            output_dir,
            _split(
                structure,
                config.modsdk_piece_size,
                name_prefix=config.structure_name,
                structure_namespace=config.modsdk_structure_namespace,
            ),
        )
        _write_modsdk(output_dir, config, modsdk)

    teleport_position, teleport_command = _teleport(config)
    all_placements = {
        "worldgen": [
            asdict(item) | {"identifier": item.identifier} for item in worldgen
        ],
        "modsdk": [asdict(item) | {"identifier": item.identifier} for item in modsdk],
    }
    _json(output_dir / "placements.json", all_placements)
    _json(
        output_dir / "project_manifest.json",
        {
            "project": config.project_name,
            "namespace": config.namespace,
            "structure_size": config.structure_size,
            "world_origin": config.world_origin,
            "dimension_id": config.dimension_id,
            "dimension_biome": config.dimension_biome,
            "repeat_period": config.repeat_period,
            "recommended_teleport": teleport_position,
            "teleport_command": teleport_command,
            "worldgen_pieces": len(worldgen),
            "modsdk_pieces": len(modsdk),
        },
    )
    return ExportReport(output_dir, len(worldgen), len(modsdk), teleport_command)
