import unicodedata

import pytest

from koko.lib.dotfont import (
    GLYPHS_5X7,
    IBM_CP850_CHARACTERS,
    JIS_X0201_KATAKANA,
    expand_character,
    glyph,
)
from koko.lib.dottext import layout_pattern, layout_text, pattern, text


def test_character_map_is_readable_binary_5x7_data():
    assert len(GLYPHS_5X7) >= 300
    for character, rows in GLYPHS_5X7.items():
        assert len(character) == 1
        assert len(rows) == 7
        assert all(len(row) == 5 and set(row) <= {"0", "1"} for row in rows)


def test_ibm_850_and_jis_x0201_repertoires_are_covered():
    assert IBM_CP850_CHARACTERS
    assert JIS_X0201_KATAKANA
    assert all(glyph(character) is not None for character in IBM_CP850_CHARACTERS)
    assert all(glyph(character) is not None for character in JIS_X0201_KATAKANA)

    for sample in "ÄÉÑÖÜáçéñøß£¥¼½¾┌─┬┐│╬█":
        assert glyph(sample) is not None


def test_common_european_latin_extended_a_letters_are_covered():
    european_letters = (
        chr(codepoint)
        for codepoint in range(0x00C0, 0x0180)
        if unicodedata.category(chr(codepoint)).startswith("L")
    )
    assert all(glyph(character) is not None for character in european_letters)


def test_unicode_japanese_expands_to_historical_matrix_cells():
    assert expand_character("ア") == "ｱ"
    assert expand_character("ガ") == "ｶﾞ"
    assert expand_character("ぱ") == "はﾟ"
    assert glyph("あ") is not None
    assert glyph("ゃ") is not None


def test_character_spacing_defaults_to_one_blank_matrix_cell():
    default = layout_text("██\n██", dot_diameter=1, dot_spacing=0, align="LT")
    joined = layout_text(
        "██\n██",
        dot_diameter=1,
        dot_spacing=0,
        horizontal_spacing=0,
        vertical_spacing=0,
        align="LT",
    )

    assert (default.columns, default.rows) == (11, 15)
    assert default.bounds == (0, 11, -15, 0)
    assert (joined.columns, joined.rows) == (10, 14)
    assert joined.bounds == (0, 10, -14, 0)

    joined_x = sorted({x for x, _ in joined.points})
    joined_y = sorted({y for _, y in joined.points}, reverse=True)
    assert joined_x == [index + 0.5 for index in range(10)]
    assert joined_y == [-(index + 0.5) for index in range(14)]


def test_dot_diameter_and_clearance_set_physical_pitch():
    layout = layout_text(
        "█", dot_diameter=0.8, dot_spacing=0.2, horizontal_spacing=0, align="LT"
    )

    assert layout.bounds == pytest.approx((0, 4.8, -6.8, 0))
    assert sorted({x for x, _ in layout.points}) == pytest.approx(
        [0.4, 1.4, 2.4, 3.4, 4.4]
    )


def test_multiline_alignment_uses_the_complete_cell_matrix():
    layout = layout_text(
        "A\nAA", dot_diameter=1, dot_spacing=0, horizontal_spacing=0, align="RC"
    )

    assert layout.bounds == (-10, 0, -7.5, 7.5)
    first_line_x = {x for x, y in layout.points if y > 0}
    second_line_x = {x for x, y in layout.points if y < 0}
    assert min(first_line_x) >= -5
    assert min(second_line_x) < -5


def test_arbitrary_binary_pattern_supports_pixel_art():
    matrix = (
        "101",
        "010",
        "101",
    )
    layout = layout_pattern(matrix, dot_diameter=1, dot_spacing=0, align="LT")

    assert layout.columns == 3
    assert layout.rows == 3
    assert layout.bounds == (0, 3, -3, 0)
    assert layout.points == (
        (0.5, -0.5),
        (2.5, -0.5),
        (1.5, -1.5),
        (0.5, -2.5),
        (2.5, -2.5),
    )


def test_text_and_pattern_create_bounded_mathtree_geometry():
    label = text("A", dot_diameter=0.2, dot_spacing=0.1, align="LT")
    art = pattern(("10", "01"), dot_diameter=0.2, dot_spacing=0.1, align="LT")

    assert label.bounds == pytest.approx([0, 1.4, -2, 0, None, None])
    assert art.bounds == pytest.approx([0, 0.5, -0.5, 0, None, None])
    assert text("") is None


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"dot_diameter": 0}, ValueError),
        ({"dot_spacing": -0.1}, ValueError),
        ({"horizontal_spacing": 0.5}, TypeError),
        ({"vertical_spacing": -1}, ValueError),
        ({"align": "XX"}, ValueError),
    ],
)
def test_invalid_label_settings_are_rejected(kwargs, error):
    with pytest.raises(error):
        layout_text("A", **kwargs)


def test_invalid_pixel_matrix_is_rejected():
    with pytest.raises(ValueError):
        layout_pattern(("10", "1"))
    with pytest.raises(ValueError):
        layout_pattern(("10", "x1"))
