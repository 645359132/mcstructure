"""Fast encoder for the common, metadata-only ``.mcstructure`` case."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import lru_cache
from struct import pack, unpack
from typing import BinaryIO, Protocol

import numpy as np
from numpy.typing import NDArray


TAG_BYTE = 1
TAG_INT = 3
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10


class BlockLike(Protocol):
    @property
    def identifier(self) -> str: ...

    @property
    def states(self) -> Mapping[str, str | bool | int]: ...

    @property
    def waterlogged(self) -> bool: ...


class Writer:
    def __init__(self) -> None:
        self.data = bytearray()

    def byte(self, value: int) -> None:
        self.data.extend(pack("<b", value))

    def int(self, value: int) -> None:
        self.data.extend(pack("<i", value))

    def string(self, value: str) -> None:
        encoded = value.encode("utf-8")
        self.data.extend(pack("<h", len(encoded)))
        self.data.extend(encoded)

    def header(self, tag: int, name: str) -> None:
        self.byte(tag)
        self.string(name)

    def named_int(self, name: str, value: int) -> None:
        self.header(TAG_INT, name)
        self.int(value)

    def named_string(self, name: str, value: str) -> None:
        self.header(TAG_STRING, name)
        self.string(value)

    def int_list(self, name: str, values: Sequence[int]) -> None:
        self.header(TAG_LIST, name)
        self.byte(TAG_INT)
        self.int(len(values))
        for value in values:
            self.int(value)


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("truncated mcstructure NBT header")
    return data


def _read_string(stream: BinaryIO) -> str:
    (length,) = unpack("<h", _read_exact(stream, 2))
    if length < 0:
        raise ValueError("negative string length in mcstructure NBT header")
    try:
        return _read_exact(stream, length).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("invalid UTF-8 in mcstructure NBT header") from error


def _read_named_tag(stream: BinaryIO) -> tuple[int, str]:
    tag_id = _read_exact(stream, 1)[0]
    return tag_id, _read_string(stream)


def read_structure_size(stream: BinaryIO) -> tuple[int, int, int]:
    """Read the fixed mcstructure header without decoding its block arrays.

    Structures emitted by :class:`Structure` begin with a root compound,
    ``format_version``, then the three-element ``size`` list. Validating that
    header is sufficient when auditing files that the exporter just wrote.
    """
    root_tag = _read_exact(stream, 1)[0]
    if root_tag != TAG_COMPOUND:
        raise ValueError("mcstructure root must be an NBT compound")
    _read_string(stream)

    version_tag, version_name = _read_named_tag(stream)
    if version_tag != TAG_INT or version_name != "format_version":
        raise ValueError("mcstructure header is missing format_version")
    (format_version,) = unpack("<i", _read_exact(stream, 4))
    if format_version != 1:
        raise ValueError(f"unsupported mcstructure format_version: {format_version}")

    size_tag, size_name = _read_named_tag(stream)
    if size_tag != TAG_LIST or size_name != "size":
        raise ValueError("mcstructure header is missing size")
    child_tag = _read_exact(stream, 1)[0]
    (length,) = unpack("<i", _read_exact(stream, 4))
    if child_tag != TAG_INT or length != 3:
        raise ValueError("mcstructure size must contain three integers")
    size = unpack("<iii", _read_exact(stream, 12))
    if any(dimension <= 0 for dimension in size):
        raise ValueError(f"invalid mcstructure size: {size}")
    return size


@lru_cache(maxsize=4)
def empty_water_layer(block_count: int) -> bytes:
    """Return a reusable secondary layer containing only ``-1`` indices."""
    return b"\xff" * (block_count * 4)


def write_simple_structure(
    stream: BinaryIO,
    shape: tuple[int, int, int],
    indices: NDArray[np.intc],
    palette: Sequence[BlockLike],
    *,
    compatibility_version: int,
    water_index: int,
) -> None:
    """Write a structure without entities or per-position block metadata."""
    flat_indices = indices.astype("<i4", copy=False).ravel(order="C")
    block_count = flat_indices.size

    output = Writer()
    output.header(TAG_COMPOUND, "")
    output.named_int("format_version", 1)
    output.int_list("size", shape)

    output.header(TAG_COMPOUND, "structure")
    output.header(TAG_LIST, "block_indices")
    output.byte(TAG_LIST)
    output.int(2)
    output.byte(TAG_INT)
    output.int(block_count)
    stream.write(output.data)
    stream.write(memoryview(flat_indices).cast("B"))

    output.data.clear()
    output.byte(TAG_INT)
    output.int(block_count)
    stream.write(output.data)
    if water_index == -1:
        stream.write(empty_water_layer(block_count))
    else:
        water_mapping = np.fromiter(
            (water_index if block.waterlogged else -1 for block in palette),
            dtype="<i4",
            count=len(palette),
        )
        secondary = water_mapping[flat_indices].astype("<i4", copy=False)
        stream.write(memoryview(secondary).cast("B"))

    output.data.clear()
    output.header(TAG_LIST, "entities")
    output.byte(TAG_COMPOUND)
    output.int(0)

    output.header(TAG_COMPOUND, "palette")
    output.header(TAG_COMPOUND, "default")
    output.header(TAG_LIST, "block_palette")
    output.byte(TAG_COMPOUND)
    output.int(len(palette))
    for block in palette:
        output.named_string("name", block.identifier)
        output.header(TAG_COMPOUND, "states")
        for state_name, state_value in block.states.items():
            # Preserve the existing encoder's behaviour: bool is an int because
            # bool subclasses int and the int branch is checked first.
            if isinstance(state_value, int):
                output.named_int(state_name, state_value)
            elif isinstance(state_value, str):
                output.named_string(state_name, state_value)
            else:
                output.header(TAG_BYTE, state_name)
                output.byte(state_value)
        output.byte(0)
        output.named_int("version", compatibility_version)
        output.byte(0)

    output.header(TAG_COMPOUND, "block_position_data")
    output.byte(0)
    output.byte(0)
    output.byte(0)
    output.byte(0)

    output.int_list("structure_world_origin", (0, 0, 0))
    output.byte(0)
    stream.write(output.data)
