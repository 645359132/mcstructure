from io import BytesIO

import mcstructure as mcstructure_module
from mcstructure import Block, Structure, STRUCTURE_MAX_SIZE, has_suitable_size, nbtx
from mcstructure._fast_nbt import read_structure_size
import numpy as np
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


def test_set_blocks_uses_numpy_scalar_broadcast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    air = Block("minecraft:air")
    stone = Block("minecraft:stone")
    struct = Structure((8, 4, 8), fill=air)

    def unexpected_array(*args: object, **kwargs: object) -> None:
        raise AssertionError("set_blocks must not allocate a temporary numpy array")

    monkeypatch.setattr(mcstructure_module.np, "array", unexpected_array)
    struct.set_blocks((1, 1, 2), (6, 3, 7), stone)

    assert struct.get_block((1, 1, 2)) == stone
    assert struct.get_block((6, 3, 7)) == stone
    assert struct.get_block((0, 0, 0)) == air


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


def test_read_structure_size_without_decoding_blocks() -> None:
    struct = Structure((2, 3, 4), fill=Block("minecraft:stone"))
    output = BytesIO()
    struct.dump(output)
    output.seek(0)

    assert read_structure_size(output) == (2, 3, 4)


def test_read_structure_size_rejects_truncated_header() -> None:
    with pytest.raises(ValueError, match="truncated"):
        read_structure_size(BytesIO(b"\x0a\x00"))


def test_dump_falls_back_for_entities() -> None:
    struct = Structure((1, 1, 1), fill=Block("minecraft:air"))
    struct.add_entity(nbtx.TagCompound("", []))
    expected = BytesIO()
    nbtx.dump(struct.as_nbt(), expected, endianness="little")
    actual = BytesIO()

    struct.dump(actual)

    assert actual.getvalue() == expected.getvalue()


def test_load_with_entities_uses_compatible_fallback() -> None:
    struct = Structure((1, 1, 1), fill=Block("minecraft:air"))
    struct.add_entity(nbtx.TagCompound("", []))
    output = BytesIO()
    struct.dump(output)
    output.seek(0)

    loaded = Structure.load(output)

    assert loaded.size == struct.size
    assert len(loaded.entities) == 1


def test_native_load_matches_python_decoder() -> None:
    if mcstructure_module._native_load_simple_structure is None:
        pytest.skip("optional Rust decoder is not installed")
    struct = Structure((4, 3, 2), fill=Block("minecraft:stone"))
    struct.set_block(
        (3, 2, 1),
        Block("minecraft:oak_stairs", upside_down_bit=0, weirdo_direction=2),
    )
    output = BytesIO()
    struct.dump(output)
    data = output.getvalue()

    native = Structure.load(BytesIO(data))
    python = Structure._load_with_nbtx(BytesIO(data))

    assert native.size == python.size
    assert native.palette == python.palette
    np.testing.assert_array_equal(native.structure, python.structure)


def test_load_preserves_waterlogged_palette_entries() -> None:
    stone = Block("minecraft:stone")
    stairs = Block(
        "minecraft:oak_stairs",
        waterlogged=True,
        upside_down_bit=0,
        weirdo_direction=2,
    )
    struct = Structure((2, 1, 1), fill=stone)
    struct.set_block((1, 0, 0), stairs)
    output = BytesIO()
    struct.dump(output)
    output.seek(0)

    loaded = Structure.load(output)

    assert loaded.get_block((1, 0, 0)) == stairs


def test_load_with_block_entity_data_uses_compatible_fallback() -> None:
    chest = Block(
        "minecraft:chest",
        block_entity_data=[nbtx.TagString("id", "Chest")],
    )
    struct = Structure((1, 1, 1), fill=chest)
    output = BytesIO()
    struct.dump(output)
    output.seek(0)

    loaded = Structure.load(output)

    assert loaded.get_block((0, 0, 0)) == chest
