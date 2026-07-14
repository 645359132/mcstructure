from io import BytesIO

import numpy as np

from mcstructure import Block, Structure, StructurePlan
from scripts.structure_workflow.exporter import _split


def _apply_example(canvas: Structure | StructurePlan) -> None:
    stone = Block("minecraft:stone")
    air = Block("minecraft:air")
    stairs = Block(
        "minecraft:oak_stairs",
        waterlogged=True,
        upside_down_bit=0,
        weirdo_direction=2,
    )
    canvas.set_blocks((2, 1, 3), (17, 7, 16), stone)
    canvas.set_blocks((5, 2, 6), (11, 5, 12), air)
    canvas.set_block((15, 6, 15), stairs)


def test_structure_plan_renders_the_same_blocks_as_dense_structure() -> None:
    size = (20, 10, 20)
    air = Block("minecraft:air")
    dense = Structure(size, air)
    plan = StructurePlan(size, air)

    _apply_example(dense)
    _apply_example(plan)
    rendered = plan.render_region((0, 0, 0), size)

    assert rendered.palette == dense.palette
    np.testing.assert_array_equal(rendered.structure, dense.structure)
    assert plan.get_block((15, 6, 15)) == dense.get_block((15, 6, 15))
    assert plan.get_block((7, 3, 8)) == air


def test_structure_plan_dump_matches_dense_structure() -> None:
    size = (20, 10, 20)
    air = Block("minecraft:air")
    dense = Structure(size, air)
    plan = StructurePlan(size, air)
    _apply_example(dense)
    _apply_example(plan)
    dense_output = BytesIO()
    planned_output = BytesIO()

    dense.dump(dense_output)
    plan.render_region((0, 0, 0), size).dump(planned_output)

    assert planned_output.getvalue() == dense_output.getvalue()


def test_structure_plan_streams_piece_arrays_equivalent_to_dense_splits() -> None:
    size = (20, 10, 20)
    piece_size = (8, 6, 8)
    air = Block("minecraft:air")
    dense = Structure(size, air)
    plan = StructurePlan(size, air)
    _apply_example(dense)
    _apply_example(plan)

    dense_pieces = {
        placement.offset: piece.structure.copy()
        for placement, piece in _split(
            dense,
            piece_size,
            name_prefix="piece",
            structure_namespace="test",
        )
    }
    planned_pieces = {
        offset: piece.structure.copy()
        for offset, piece in plan.iter_pieces(piece_size)
    }

    assert planned_pieces.keys() == dense_pieces.keys()
    for offset in dense_pieces:
        np.testing.assert_array_equal(planned_pieces[offset], dense_pieces[offset])


def test_structure_plan_keeps_large_canvas_as_compact_operations() -> None:
    air = Block("minecraft:air")
    stone = Block("minecraft:stone")
    plan = StructurePlan((2048, 128, 2048), air)

    plan.set_blocks((0, 0, 0), (2047, 3, 2047), stone)
    piece = plan.render_region((1024, 0, 1024), (16, 128, 16))

    assert not hasattr(plan, "structure")
    assert plan.operation_count == 1
    assert piece.structure.nbytes == 16 * 128 * 16 * 4
    assert piece.get_block((0, 3, 0)) == stone
    assert piece.get_block((0, 4, 0)) == air
