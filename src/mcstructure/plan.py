"""Low-memory recorded structure generation for very large logical canvases."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, Self

import numpy as np

from . import Block, Coordinate, Structure


Vec3 = tuple[int, int, int]
Box = tuple[int, int, int, int, int, int]
_DEFAULT_BUCKET_SIZE: Vec3 = (16, 64, 16)


class BlockCanvas(Protocol):
    """The small construction interface shared by dense and recorded adapters."""

    @property
    def size(self) -> Vec3: ...

    def set_block(self, coordinate: Coordinate, block: Block | None) -> Self: ...

    def set_blocks(
        self,
        from_coordinate: Coordinate,
        to_coordinate: Coordinate,
        block: Block | None,
    ) -> Self: ...


@dataclass(frozen=True, slots=True)
class FillOperation:
    """One inclusive, ordered palette-index fill in global canvas coordinates."""

    box: Box
    palette_index: int


class StructurePlan:
    """Record global block writes and materialize only one output piece at a time.

    Building code uses the same ``set_block`` and ``set_blocks`` calls as a dense
    :class:`Structure`. Operations keep their insertion order, so later writes
    overwrite earlier writes exactly as they do on a NumPy-backed canvas.
    """

    __slots__ = (
        "_bucket_operations",
        "_bucket_size",
        "_default_palette_index",
        "_operations",
        "_palette",
        "_size",
    )

    def __init__(
        self,
        size: Vec3,
        fill: Block | None = Block("minecraft:air"),
        *,
        bucket_size: Vec3 = _DEFAULT_BUCKET_SIZE,
    ) -> None:
        if any(dimension <= 0 for dimension in size):
            raise ValueError("structure plan dimensions must be positive")
        if any(dimension <= 0 for dimension in bucket_size):
            raise ValueError("structure plan bucket dimensions must be positive")
        self._size = size
        self._bucket_size = bucket_size
        self._palette: list[Block] = []
        self._default_palette_index = self._add_block_to_palette(fill)
        self._operations: list[FillOperation] = []
        self._bucket_operations: dict[Vec3, list[int]] = {}

    @property
    def size(self) -> Vec3:
        return self._size

    @property
    def palette(self) -> list[Block]:
        return self._palette.copy()

    @property
    def operation_count(self) -> int:
        return len(self._operations)

    def _add_block_to_palette(self, block: Block | None) -> int:
        if block is None:
            return -1
        for index, palette_block in enumerate(self._palette):
            if block == palette_block:
                return index
        self._palette.append(block)
        return len(self._palette) - 1

    def _validate_coordinate(self, coordinate: Coordinate) -> None:
        if any(
            value < 0 or value >= limit
            for value, limit in zip(coordinate, self._size)
        ):
            raise IndexError(f"coordinate outside structure plan: {coordinate}")

    def _bucket_keys(self, box: Box) -> Iterator[Vec3]:
        x1, y1, z1, x2, y2, z2 = box
        step_x, step_y, step_z = self._bucket_size
        for by in range(y1 // step_y, y2 // step_y + 1):
            for bz in range(z1 // step_z, z2 // step_z + 1):
                for bx in range(x1 // step_x, x2 // step_x + 1):
                    yield bx, by, bz

    def set_block(self, coordinate: Coordinate, block: Block | None) -> Self:
        self._validate_coordinate(coordinate)
        x, y, z = coordinate
        return self.set_blocks((x, y, z), (x, y, z), block)

    def set_blocks(
        self,
        from_coordinate: Coordinate,
        to_coordinate: Coordinate,
        block: Block | None,
    ) -> Self:
        self._validate_coordinate(from_coordinate)
        self._validate_coordinate(to_coordinate)
        if any(start > end for start, end in zip(from_coordinate, to_coordinate)):
            raise ValueError("structure plan fill coordinates must be ordered")
        x1, y1, z1 = from_coordinate
        x2, y2, z2 = to_coordinate
        operation = FillOperation(
            (x1, y1, z1, x2, y2, z2), self._add_block_to_palette(block)
        )
        operation_index = len(self._operations)
        self._operations.append(operation)
        for key in self._bucket_keys(operation.box):
            self._bucket_operations.setdefault(key, []).append(operation_index)
        return self

    def _operation_ids_for_box(self, box: Box) -> list[int]:
        operation_ids: set[int] = set()
        for key in self._bucket_keys(box):
            operation_ids.update(self._bucket_operations.get(key, ()))
        return sorted(operation_ids)

    def _render_region(
        self,
        offset: Coordinate,
        size: Vec3,
        operation_ids: list[int],
    ) -> Structure:
        ox, oy, oz = offset
        sx, sy, sz = size
        rx2, ry2, rz2 = ox + sx - 1, oy + sy - 1, oz + sz - 1
        piece = Structure(size, None)
        piece._palette = self._palette.copy()
        piece.structure.fill(self._default_palette_index)
        for operation_id in operation_ids:
            operation = self._operations[operation_id]
            x1, y1, z1, x2, y2, z2 = operation.box
            ix1, iy1, iz1 = max(x1, ox), max(y1, oy), max(z1, oz)
            ix2, iy2, iz2 = min(x2, rx2), min(y2, ry2), min(z2, rz2)
            if ix1 > ix2 or iy1 > iy2 or iz1 > iz2:
                continue
            piece.structure[
                ix1 - ox : ix2 - ox + 1,
                iy1 - oy : iy2 - oy + 1,
                iz1 - oz : iz2 - oz + 1,
            ] = operation.palette_index
        return piece

    def render_region(self, offset: Coordinate, size: Vec3) -> Structure:
        """Materialize one bounded region for preview, audit, or export."""
        self._validate_coordinate(offset)
        if any(dimension <= 0 for dimension in size):
            raise ValueError("rendered region dimensions must be positive")
        end = tuple(start + length - 1 for start, length in zip(offset, size))
        self._validate_coordinate(end)
        box = (offset[0], offset[1], offset[2], end[0], end[1], end[2])
        return self._render_region(offset, size, self._operation_ids_for_box(box))

    def get_block(self, coordinate: Coordinate) -> Block:
        """Resolve one point without materializing the complete logical canvas."""
        self._validate_coordinate(coordinate)
        x, y, z = coordinate
        palette_index = self._default_palette_index
        for operation_id in self._operation_ids_for_box((x, y, z, x, y, z)):
            operation = self._operations[operation_id]
            x1, y1, z1, x2, y2, z2 = operation.box
            if x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2:
                palette_index = operation.palette_index
        if palette_index < 0:
            return Block("minecraft:structure_void")
        return self._palette[palette_index]

    def iter_pieces(self, piece_size: Vec3) -> Iterator[tuple[Coordinate, Structure]]:
        """Render non-air pieces in deterministic Y/Z/X order."""
        if any(dimension <= 0 for dimension in piece_size):
            raise ValueError("piece dimensions must be positive")
        empty_index = next(
            (
                index
                for index, block in enumerate(self._palette)
                if block == Block("minecraft:air")
            ),
            None,
        )
        size_x, size_y, size_z = self._size
        step_x, step_y, step_z = piece_size
        for y0 in range(0, size_y, step_y):
            for z0 in range(0, size_z, step_z):
                for x0 in range(0, size_x, step_x):
                    actual_size = (
                        min(step_x, size_x - x0),
                        min(step_y, size_y - y0),
                        min(step_z, size_z - z0),
                    )
                    end = (
                        x0 + actual_size[0] - 1,
                        y0 + actual_size[1] - 1,
                        z0 + actual_size[2] - 1,
                    )
                    box = (x0, y0, z0, end[0], end[1], end[2])
                    operation_ids = self._operation_ids_for_box(box)
                    if (
                        empty_index is not None
                        and self._default_palette_index == empty_index
                        and not operation_ids
                    ):
                        continue
                    piece = self._render_region(
                        (x0, y0, z0), actual_size, operation_ids
                    )
                    if empty_index is not None and not np.any(
                        piece.structure != empty_index
                    ):
                        continue
                    yield (x0, y0, z0), piece


__all__ = ["BlockCanvas", "FillOperation", "StructurePlan"]
