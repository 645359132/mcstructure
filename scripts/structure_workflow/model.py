"""Project contract shared by structure generators and deterministic exporters."""

from __future__ import annotations

from dataclasses import dataclass, fields
import json
from pathlib import Path
from re import fullmatch
from typing import Any


Vec3 = tuple[int, int, int]


def _vec3(value: Any, field_name: str) -> Vec3:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(not isinstance(item, int) or isinstance(item, bool) for item in value)
    ):
        raise ValueError(f"{field_name} must be an array of three integers")
    return value[0], value[1], value[2]


@dataclass(frozen=True, slots=True)
class ProjectSpec:
    """Validated, serializable contract for one work directory."""

    schema_version: int
    project_name: str
    namespace: str
    structure_name: str
    builder: str
    structure_size: Vec3
    world_origin: Vec3
    dimension_id: int
    dimension_mod_id: str
    dimension_biome: str
    repeat_period: int = 4096
    worldgen_piece_size: Vec3 = (16, 256, 16)
    modsdk_piece_size: Vec3 = (32, 64, 32)
    modsdk_batch_size: int = 4
    modsdk_batch_delay: float = 0.25
    modsdk_passes: int = 3
    modsdk_pass_delay: float = 2.0

    @classmethod
    def load(cls, work_dir: Path) -> "ProjectSpec":
        path = work_dir / "project.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ValueError(f"missing work contract: {path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON in {path}: {error}") from error
        if not isinstance(raw, dict):
            raise ValueError("project.json root must be an object")

        known = {field.name for field in fields(cls)}
        unknown = sorted(set(raw) - known)
        if unknown:
            raise ValueError(f"unknown project.json fields: {', '.join(unknown)}")
        required = {
            "schema_version",
            "project_name",
            "namespace",
            "structure_name",
            "builder",
            "structure_size",
            "world_origin",
            "dimension_id",
            "dimension_mod_id",
            "dimension_biome",
        }
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"missing project.json fields: {', '.join(missing)}")

        for name in (
            "structure_size",
            "world_origin",
            "worldgen_piece_size",
            "modsdk_piece_size",
        ):
            if name in raw:
                raw[name] = _vec3(raw[name], name)
        spec = cls(**raw)
        spec.validate()
        return spec

    @property
    def worldgen_structure_namespace(self) -> str:
        return f"{self.namespace}_worldgen"

    @property
    def modsdk_structure_namespace(self) -> str:
        return f"{self.namespace}_modsdk"

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported project schema_version; expected 1")
        for field_name, value in (
            ("namespace", self.namespace),
            ("structure_name", self.structure_name),
            ("dimension_mod_id", self.dimension_mod_id),
        ):
            if fullmatch(r"[a-z0-9_]+", value) is None:
                raise ValueError(
                    f"{field_name} must contain only lowercase letters, digits, "
                    "and underscores"
                )
        if (
            fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*", self.builder)
            is None
        ):
            raise ValueError("builder must use module.path:function syntax")
        if self.dimension_id <= 0:
            raise ValueError("dimension_id must be positive")
        if not self.dimension_biome:
            raise ValueError("dimension_biome must not be empty")
        if any(dimension <= 0 for dimension in self.structure_size):
            raise ValueError("structure_size dimensions must be positive")
        if any(dimension <= 0 for dimension in self.worldgen_piece_size):
            raise ValueError("worldgen_piece_size dimensions must be positive")
        if any(dimension <= 0 for dimension in self.modsdk_piece_size):
            raise ValueError("modsdk_piece_size dimensions must be positive")
        if self.worldgen_piece_size[0] > 16 or self.worldgen_piece_size[2] > 16:
            raise ValueError("worldgen X/Z pieces must not exceed 16 blocks")
        if self.worldgen_piece_size[1] > 256:
            raise ValueError("worldgen Y pieces must not exceed 256 blocks")
        if _volume(self.worldgen_piece_size) > 65_536:
            raise ValueError("worldgen piece volume exceeds 65,536 blocks")
        if _volume(self.modsdk_piece_size) > 65_536:
            raise ValueError("ModSDK piece volume exceeds 65,536 blocks")
        if any(
            actual > maximum
            for actual, maximum in zip(self.modsdk_piece_size, (64, 384, 64))
        ):
            raise ValueError("ModSDK piece dimensions exceed 64×384×64")
        if self.repeat_period <= 0 or self.repeat_period % 16 != 0:
            raise ValueError("repeat_period must be a positive multiple of 16")
        if self.world_origin[0] % 16 or self.world_origin[2] % 16:
            raise ValueError("world_origin X/Z must align to 16-block chunk origins")
        if self.modsdk_batch_size <= 0 or self.modsdk_passes <= 0:
            raise ValueError("ModSDK batch size and placement passes must be positive")
        if self.modsdk_batch_delay < 0 or self.modsdk_pass_delay < 0:
            raise ValueError("ModSDK placement delays must not be negative")


def _volume(size: Vec3) -> int:
    return size[0] * size[1] * size[2]
