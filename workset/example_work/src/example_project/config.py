"""All project-specific names, dimensions, and placement coordinates."""

from __future__ import annotations

from dataclasses import dataclass
from re import fullmatch


Vec3 = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    project_name: str
    namespace: str
    structure_name: str
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

    @property
    def worldgen_structure_namespace(self) -> str:
        return f"{self.namespace}_worldgen"

    @property
    def modsdk_structure_namespace(self) -> str:
        return f"{self.namespace}_modsdk"

    def validate(self) -> None:
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
        if self.dimension_id <= 0:
            raise ValueError("dimension_id must be positive")
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


def _volume(size: Vec3) -> int:
    return size[0] * size[1] * size[2]


# Change this object first when starting a real project.
# dimension_id must be unique inside the add-on; dimension_biome must match a
# biome identifier available in that custom dimension.
CONFIG = ProjectConfig(
    project_name="Example Landmark",
    namespace="example_work",
    structure_name="landmark",
    structure_size=(96, 48, 96),
    world_origin=(1024, 56, 1024),
    dimension_id=645_359_134,
    dimension_mod_id="example_work",
    dimension_biome="dm645359134_plains",
)
