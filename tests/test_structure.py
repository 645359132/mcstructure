from io import BytesIO

from mcstructure import Block, Structure, STRUCTURE_MAX_SIZE, has_suitable_size, nbtx
import pytest


def test_oversized() -> None:
    assert has_suitable_size(STRUCTURE_MAX_SIZE)
    assert not has_suitable_size((65, 0, 0))


def test_resize_larger() -> None:
    dirt = Block("minecraft:dirt")
    air = Block("minecraft:air")
    struct = Structure((2, 2, 2), fill=dirt)
    struct.resize((4, 4, 4), air)
    assert struct.get_block((3, 3, 3)) == air
    assert struct.get_block((0, 0, 0)) == dirt
    assert struct.get_block((1, 1, 1)) == dirt
    assert struct.get_block((2, 2, 2)) == air


def test_resize_smaller() -> None:
    dirt = Block("minecraft:dirt")
    struct = Structure((4, 4, 4), fill=dirt)
    struct.resize((2, 2, 2))
    with pytest.raises(IndexError):
        assert struct.get_block((3, 3, 3)) is None
    with pytest.raises(IndexError):
        assert struct.get_block((2, 2, 2)) is None
    assert struct.get_block((1, 1, 1)) == dirt
    assert struct.get_block((0, 0, 0)) == dirt


def test_combine() -> None:
    dirt = Block("minecraft:dirt")
    air = Block("minecraft:air")
    void = Block("minecraft:structure_void")
    struct_a = Structure((1, 2, 2), fill=air)
    struct_b = Structure((1, 2, 2), fill=dirt)
    struct_c = struct_a.combine(struct_b, (0, 1, 1))

    # Check the combined structure
    assert struct_c.get_block((0, 0, 0)) == air
    assert struct_c.get_block((0, 0, 1)) == air
    assert struct_c.get_block((0, 0, 2)) == void
    assert struct_c.get_block((0, 1, 0)) == air
    assert struct_c.get_block((0, 1, 1)) == dirt
    assert struct_c.get_block((0, 1, 2)) == dirt
    assert struct_c.get_block((0, 2, 0)) == void
    assert struct_c.get_block((0, 2, 1)) == dirt
    assert struct_c.get_block((0, 2, 2)) == dirt


def test_dump_and_load_with_vendored_nbtx() -> None:
    stone = Block("minecraft:stone")
    struct = Structure((1, 1, 1), fill=stone)
    output = BytesIO()

    struct.dump(output)
    output.seek(0)
    loaded = Structure.load(output)

    assert loaded.size == (1, 1, 1)
    assert loaded.get_block((0, 0, 0)) == stone


def test_fast_dump_matches_reference_encoder() -> None:
    struct = Structure((2, 3, 4), fill=Block("minecraft:stone"))
    struct.set_block(
        (1, 2, 3),
        Block(
            "minecraft:oak_stairs",
            waterlogged=True,
            upside_down_bit=False,
            weirdo_direction=2,
            kind="outer_left",
        ),
    )
    expected = BytesIO()
    nbtx.dump(struct.as_nbt(), expected, endianness="little")
    actual = BytesIO()

    struct.dump(actual)

    assert actual.getvalue() == expected.getvalue()


def test_dump_falls_back_for_entities() -> None:
    struct = Structure((1, 1, 1), fill=Block("minecraft:air"))
    struct.add_entity(nbtx.TagCompound("", []))
    expected = BytesIO()
    nbtx.dump(struct.as_nbt(), expected, endianness="little")
    actual = BytesIO()

    struct.dump(actual)

    assert actual.getvalue() == expected.getvalue()
