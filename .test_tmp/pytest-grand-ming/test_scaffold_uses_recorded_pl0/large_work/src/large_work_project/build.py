"""Replace this starter with the architecture described in BRIEF.md."""

from mcstructure import Block, StructurePlan


SIZE = (1024, 128, 1024)
AIR = Block("minecraft:air")
FOUNDATION = Block("minecraft:stonebrick")


def build_structure() -> StructurePlan:
    """Return one logical canvas; shared tooling handles every export format."""
    structure = StructurePlan(SIZE, AIR)
    structure.set_blocks((0, 0, 0), (SIZE[0] - 1, 2, SIZE[2] - 1), FOUNDATION)
    return structure
