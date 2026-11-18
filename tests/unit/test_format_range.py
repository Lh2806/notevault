"""Unit 2: bold, italic and underline (FormatRange on a NoteLine)."""

import pytest

from notevault.models import FormatRange, NoteLine


def test_bold_is_applied_only_to_the_chosen_range():
    # expected behavior
    line = NoteLine(1, "Hello world")
    line.apply_format(0, 5, "bold")          # "Hello"

    assert line.formats == [FormatRange(0, 5, "bold")]
    assert line.styles_at(0) == {"bold"}
    assert line.styles_at(4) == {"bold"}
    assert line.styles_at(5) == set()        # the space after Hello
    assert line.styles_at(8) == set()


def test_range_at_line_end_and_overlapping_ranges():
    # edge cases
    line = NoteLine(1, "Hello world")

    line.apply_format(6, 11, "italic")       # ends exactly at the end of the line
    assert line.styles_at(10) == {"italic"}

    line.apply_format(0, 4, "bold")
    line.apply_format(2, 8, "bold")          # overlaps the first bold range
    bold = [r for r in line.formats if r.style == "bold"]
    assert bold == [FormatRange(0, 8, "bold")]   # merged into one range

    # different styles can overlap and both stay
    assert line.styles_at(7) == {"bold", "italic"}

    # shortening the line cuts the formatting back so it never points past the text
    line.text = "Hello"
    assert line.formats == [FormatRange(0, 5, "bold")]   # bold cut to 5, italic gone


def test_invalid_ranges_are_rejected():
    # invalid input
    line = NoteLine(1, "Hello")

    with pytest.raises(ValueError):
        line.apply_format(-1, 3, "bold")         # negative start
    with pytest.raises(ValueError):
        line.apply_format(4, 2, "bold")          # end before start
    with pytest.raises(ValueError):
        line.apply_format(0, 6, "bold")          # past the end of "Hello"
    with pytest.raises(ValueError):
        line.apply_format(0, 3, "strikethrough") # style NoteVault does not have
    with pytest.raises(TypeError):
        line.apply_format("0", 3, "bold")        # start is not a number

    assert line.formats == []                    # nothing was added
