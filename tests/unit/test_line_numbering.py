"""Unit 1: line numbering (Note and NoteLine)."""

import pytest

from notevault.models import Note


def test_lines_are_numbered_and_renumbered_after_insert():
    # expected behavior
    note = Note("Lecture 1")
    note.set_text("first\nsecond\nthird")
    assert [(line.number, line.text) for line in note.lines] == [
        (1, "first"), (2, "second"), (3, "third"),
    ]

    note.insert_line(2, "new line")
    assert [(line.number, line.text) for line in note.lines] == [
        (1, "first"), (2, "new line"), (3, "second"), (4, "third"),
    ]


def test_empty_note_and_very_long_line():
    # edge cases
    note = Note("Empty")
    assert len(note.lines) == 1          # a note always has at least one line
    assert note.lines[0].number == 1
    assert note.lines[0].text == ""

    long_text = "x" * 10000
    note.set_text(long_text)
    assert len(note.lines) == 1          # a long line is not split
    assert note.lines[0].text == long_text

    note.delete_line(1)                  # deleting the only line leaves an empty line 1
    assert [(line.number, line.text) for line in note.lines] == [(1, "")]


def test_non_text_input_and_bad_line_number_are_rejected():
    # invalid input
    note = Note("Lecture 1")
    note.set_text("first\nsecond")

    with pytest.raises(TypeError):
        note.set_text(12345)
    with pytest.raises(TypeError):
        note.insert_line(1, None)
    with pytest.raises(IndexError):
        note.insert_line(0, "before line 1")
    with pytest.raises(IndexError):
        note.insert_line(4, "skips a line number")

    # the failed calls did not change the note
    assert note.text == "first\nsecond"
