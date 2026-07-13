"""Example architecture. Replace this module with your own generator."""

from __future__ import annotations

from mcstructure import Block, Structure

from .config import CONFIG, Vec3


AIR = Block("minecraft:air")
STONE = Block("minecraft:stonebrick")
STONE_DETAIL = Block("minecraft:chiseled_stone_bricks")
DARK = Block("minecraft:polished_blackstone_bricks")
FLOOR = Block("minecraft:smooth_stone")
GLASS = Block("minecraft:glass")
LIGHT = Block("minecraft:sea_lantern")


def fill(structure: Structure, minimum: Vec3, maximum: Vec3, block: Block) -> None:
    """Fill an inclusive box."""
    structure.set_blocks(minimum, maximum, block)


def hollow_box(
    structure: Structure, minimum: Vec3, maximum: Vec3, block: Block
) -> None:
    """Build the six faces of an inclusive axis-aligned box."""
    x1, y1, z1 = minimum
    x2, y2, z2 = maximum
    fill(structure, (x1, y1, z1), (x2, y1, z2), block)
    fill(structure, (x1, y2, z1), (x2, y2, z2), block)
    fill(structure, (x1, y1, z1), (x1, y2, z2), block)
    fill(structure, (x2, y1, z1), (x2, y2, z2), block)
    fill(structure, (x1, y1, z1), (x2, y2, z1), block)
    fill(structure, (x1, y1, z2), (x2, y2, z2), block)


def _build_tower(structure: Structure, center_x: int, center_z: int) -> None:
    radius = 7
    hollow_box(
        structure,
        (center_x - radius, 4, center_z - radius),
        (center_x + radius, 31, center_z + radius),
        STONE,
    )
    fill(
        structure,
        (center_x - radius - 1, 31, center_z - radius - 1),
        (center_x + radius + 1, 33, center_z + radius + 1),
        DARK,
    )
    fill(
        structure,
        (center_x - 1, 32, center_z - 1),
        (center_x + 1, 39, center_z + 1),
        LIGHT,
    )
    for y in (11, 19, 27):
        for x in (center_x - radius, center_x + radius):
            fill(
                structure,
                (x, y, center_z - 1),
                (x, y + 2, center_z + 1),
                GLASS,
            )


def build_structure() -> Structure:
    """Return one logical structure; the exporter handles all chunk splitting."""
    CONFIG.validate()
    size_x, _, size_z = CONFIG.structure_size
    structure = Structure(CONFIG.structure_size, AIR)

    # Foundation and approach plaza.
    fill(structure, (0, 0, 0), (size_x - 1, 2, size_z - 1), STONE)
    fill(structure, (4, 3, 4), (size_x - 5, 3, size_z - 5), FLOOR)
    fill(structure, (size_x // 2 - 4, 3, 0), (size_x // 2 + 4, 3, 23), DARK)

    # Central hall with a deliberately open entrance facing negative Z.
    hollow_box(structure, (24, 4, 24), (71, 25, 71), STONE)
    fill(structure, (28, 4, 28), (67, 4, 67), FLOOR)
    fill(structure, (44, 4, 24), (51, 13, 24), AIR)
    fill(structure, (33, 25, 33), (62, 29, 62), DARK)
    fill(structure, (45, 29, 45), (50, 42, 50), STONE_DETAIL)
    fill(structure, (46, 42, 46), (49, 45, 49), LIGHT)

    # Four towers make the generated pieces and their alignment easy to inspect.
    for center_x, center_z in ((16, 16), (79, 16), (16, 79), (79, 79)):
        _build_tower(structure, center_x, center_z)

    # Lit cross through the courtyard.
    fill(structure, (47, 5, 28), (48, 5, 67), LIGHT)
    fill(structure, (28, 5, 47), (67, 5, 48), LIGHT)
    return structure
