"""Tool-aware 5x7 dot-matrix text and pixel-art geometry.

``horizontal_spacing`` and ``vertical_spacing`` count empty matrix columns
and rows between character cells.  Their normal defaults are one; zero joins
cells directly into a continuous matrix.  ``dot_spacing`` is separate: it is
the edge-to-edge clearance between neighboring dots inside that matrix.

All physical values use the current model's units.  A label made with a
0.8 mm cutter should therefore use ``dot_diameter=0.8`` in a millimetre model.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
import operator
import warnings

from koko.lib.dotfont import (
    GLYPH_HEIGHT,
    GLYPH_WIDTH,
    GLYPHS_5X7,
    IBM_CP850_CHARACTERS,
    JIS_X0201_KATAKANA,
    expand_character,
    glyph,
)
from koko.lib.shapes2d import circle


@dataclass(frozen=True)
class DotLayout:
    """Physical dot centers and the complete matrix-cell bounds."""

    points: tuple[tuple[float, float], ...]
    bounds: tuple[float, float, float, float] | None
    columns: int
    rows: int


def _positive_number(name: str, value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a number") from error
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def _nonnegative_number(name: str, value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a number") from error
    if number < 0:
        raise ValueError(f"{name} must be zero or greater")
    return number


def _matrix_spacing(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer number of matrix cells")
    if value < 0:
        raise ValueError(f"{name} must be zero or greater")
    return value


def _alignment(align: str) -> str:
    normalized = align.upper()
    if len(normalized) != 2 or normalized[0] not in "LCR" or normalized[1] not in "TCB":
        raise ValueError("align must combine L, C, or R with T, C, or B")
    return normalized


def _anchored_bounds(
    columns: int,
    rows: int,
    pitch: float,
    radius: float,
    x: float,
    y: float,
    align: str,
) -> tuple[tuple[float, float, float, float] | None, float, float]:
    if columns <= 0 or rows <= 0:
        return None, 0.0, 0.0

    width = (columns - 1) * pitch + radius * 2
    height = (rows - 1) * pitch + radius * 2
    if align[0] == "L":
        offset_x = x + radius
    elif align[0] == "C":
        offset_x = x - width / 2 + radius
    else:
        offset_x = x - width + radius

    if align[1] == "T":
        offset_y = y - radius
    elif align[1] == "C":
        offset_y = y + height / 2 - radius
    else:
        offset_y = y + height - radius

    bounds = (
        offset_x - radius,
        offset_x + (columns - 1) * pitch + radius,
        offset_y - (rows - 1) * pitch - radius,
        offset_y + radius,
    )
    return bounds, offset_x, offset_y


def _expanded_line(value: str, missing: str) -> list[str]:
    cells: list[str] = []
    for character in value:
        expanded = expand_character(character)
        if all(glyph(cell) is not None for cell in expanded):
            cells.extend(expanded)
            continue
        warnings.warn(
            f"Unknown 5x7 character U+{ord(character):04X}; using {missing!r}",
            stacklevel=3,
        )
        cells.append(missing)
    return cells


def layout_text(
    value: str,
    x: float = 0,
    y: float = 0,
    *,
    dot_diameter: float = 0.1,
    dot_spacing: float = 0.05,
    horizontal_spacing: int = 1,
    vertical_spacing: int = 1,
    align: str = "CC",
    missing: str = "?",
) -> DotLayout:
    """Lay out Unicode text as physical dot centers without making geometry."""

    if not isinstance(value, str):
        raise TypeError("value must be a string")
    if len(missing) != 1 or glyph(missing) is None:
        raise ValueError("missing must be one character available in the 5x7 map")
    diameter = _positive_number("dot_diameter", dot_diameter)
    clearance = _nonnegative_number("dot_spacing", dot_spacing)
    horizontal = _matrix_spacing("horizontal_spacing", horizontal_spacing)
    vertical = _matrix_spacing("vertical_spacing", vertical_spacing)
    normalized_align = _alignment(align)
    pitch = diameter + clearance
    radius = diameter / 2

    source_lines = value.split("\n")
    lines = [_expanded_line(line, missing) for line in source_lines]
    line_columns = [
        len(line) * GLYPH_WIDTH + max(0, len(line) - 1) * horizontal for line in lines
    ]
    columns = max(line_columns, default=0)
    rows = len(lines) * GLYPH_HEIGHT + max(0, len(lines) - 1) * vertical if value else 0
    bounds, origin_x, origin_y = _anchored_bounds(
        columns, rows, pitch, radius, float(x), float(y), normalized_align
    )

    points: list[tuple[float, float]] = []
    for line_index, (line, occupied_columns) in enumerate(zip(lines, line_columns)):
        if normalized_align[0] == "L":
            line_offset = 0.0
        elif normalized_align[0] == "C":
            line_offset = (columns - occupied_columns) * pitch / 2
        else:
            line_offset = (columns - occupied_columns) * pitch
        line_row = line_index * (GLYPH_HEIGHT + vertical)
        for cell_index, character in enumerate(line):
            matrix = glyph(character)
            assert matrix is not None
            cell_column = cell_index * (GLYPH_WIDTH + horizontal)
            for row_index, row in enumerate(matrix):
                for column_index, pixel in enumerate(row):
                    if pixel == "1":
                        points.append(
                            (
                                origin_x + line_offset + (cell_column + column_index) * pitch,
                                origin_y - (line_row + row_index) * pitch,
                            )
                        )

    return DotLayout(tuple(points), bounds, columns, rows)


def text_points(*args, **kwargs) -> tuple[tuple[float, float], ...]:
    """Return the physical center of every dot in a label."""

    return layout_text(*args, **kwargs).points


def _matrix_rows(matrix) -> tuple[str, ...]:
    try:
        rows = tuple(str(row) for row in matrix)
    except TypeError as error:
        raise TypeError("matrix must be an iterable of binary strings") from error
    if not rows:
        return ()
    width = len(rows[0])
    if width == 0 or any(len(row) != width or set(row) - {"0", "1"} for row in rows):
        raise ValueError("matrix rows must be equally sized strings containing only 0 and 1")
    return rows


def layout_pattern(
    matrix,
    x: float = 0,
    y: float = 0,
    *,
    dot_diameter: float = 0.1,
    dot_spacing: float = 0.05,
    align: str = "CC",
) -> DotLayout:
    """Lay out an arbitrary binary matrix for pixel art or fabrication."""

    matrix = _matrix_rows(matrix)
    diameter = _positive_number("dot_diameter", dot_diameter)
    clearance = _nonnegative_number("dot_spacing", dot_spacing)
    normalized_align = _alignment(align)
    pitch = diameter + clearance
    radius = diameter / 2
    rows = len(matrix)
    columns = len(matrix[0]) if matrix else 0
    bounds, origin_x, origin_y = _anchored_bounds(
        columns, rows, pitch, radius, float(x), float(y), normalized_align
    )
    points = tuple(
        (origin_x + column * pitch, origin_y - row * pitch)
        for row, encoded in enumerate(matrix)
        for column, pixel in enumerate(encoded)
        if pixel == "1"
    )
    return DotLayout(points, bounds, columns, rows)


def pattern_points(*args, **kwargs) -> tuple[tuple[float, float], ...]:
    """Return the physical center of every dot in an arbitrary matrix."""

    return layout_pattern(*args, **kwargs).points


def _geometry(layout: DotLayout, dot_diameter: float):
    if not layout.points:
        return None
    radius = float(dot_diameter) / 2
    shape = reduce(operator.add, (circle(x, y, radius) for x, y in layout.points))
    if layout.bounds is not None:
        shape.xmin, shape.xmax, shape.ymin, shape.ymax = layout.bounds
    return shape


def text(
    value: str,
    x: float = 0,
    y: float = 0,
    *,
    dot_diameter: float = 0.1,
    dot_spacing: float = 0.05,
    horizontal_spacing: int = 1,
    vertical_spacing: int = 1,
    align: str = "CC",
    missing: str = "?",
):
    """Create circular MathTree geometry for a Unicode dot-matrix label."""

    layout = layout_text(
        value,
        x,
        y,
        dot_diameter=dot_diameter,
        dot_spacing=dot_spacing,
        horizontal_spacing=horizontal_spacing,
        vertical_spacing=vertical_spacing,
        align=align,
        missing=missing,
    )
    return _geometry(layout, dot_diameter)


def pattern(
    matrix,
    x: float = 0,
    y: float = 0,
    *,
    dot_diameter: float = 0.1,
    dot_spacing: float = 0.05,
    align: str = "CC",
):
    """Create circular MathTree geometry from an arbitrary binary matrix."""

    layout = layout_pattern(
        matrix,
        x,
        y,
        dot_diameter=dot_diameter,
        dot_spacing=dot_spacing,
        align=align,
    )
    return _geometry(layout, dot_diameter)


label = text
dot_text = text
dot_pattern = pattern
pixels = pattern


__all__ = [
    "DotLayout",
    "GLYPHS_5X7",
    "IBM_CP850_CHARACTERS",
    "JIS_X0201_KATAKANA",
    "dot_pattern",
    "dot_text",
    "label",
    "layout_pattern",
    "layout_text",
    "pattern",
    "pattern_points",
    "pixels",
    "text",
    "text_points",
]
