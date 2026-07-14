"""Replace this starter with the architecture described in BRIEF.md."""

from mcstructure import Block, Structure


SIZE = (64, 32, 64)
AIR = Block("minecraft:air")
FOUNDATION = Block("minecraft:stonebrick")


def build_structure() -> Structure:
    """Return one logical canvas; shared tooling handles every export format."""
    structure = Structure(SIZE, AIR)
    structure.set_blocks((0, 0, 0), (SIZE[0] - 1, 2, SIZE[2] - 1), FOUNDATION)
    return structure
