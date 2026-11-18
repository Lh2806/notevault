"""Unit 4: tags and keyword matching (Tag and matches_keyword)."""

import pytest

from notevault.models import Note, Tag
from notevault.search_filter_service import matches_keyword


def make_note():
    note = Note("UML Basics")
    note.set_text("Class diagrams show structure\nSequence diagrams show order")
    return note


def test_keyword_and_tag_match_ignoring_case():
    # expected behavior
    note = make_note()
    assert matches_keyword(note, "sequence")      # in line 2
    assert matches_keyword(note, "CLASS DIAGRAMS")
    assert matches_keyword(note, "uml")           # in the title

    note.add_tag("Week 5")
    assert note.has_tag("week 5")
    assert Tag("Week 5") == Tag("WEEK 5")


def test_no_match_spaces_and_duplicate_tags():
    # edge cases
    note = make_note()
    assert not matches_keyword(note, "database")          # word is not in the note
    assert matches_keyword(note, "  structure  ")         # spaces around the keyword
    assert not matches_keyword(note, "structure Sequence")  # does not match across lines

    note.add_tag("Week 5")
    note.add_tag("  week   5 ")                           # same tag typed differently
    assert [tag.name for tag in note.tags] == ["Week 5"]
    assert not note.has_tag("Week 6")


def test_empty_keyword_and_invalid_tag_are_rejected():
    # invalid input
    note = make_note()

    with pytest.raises(ValueError):
        matches_keyword(note, "")
    with pytest.raises(ValueError):
        matches_keyword(note, "    ")
    with pytest.raises(TypeError):
        matches_keyword(note, None)
    with pytest.raises(ValueError):
        note.add_tag("   ")
    with pytest.raises(TypeError):
        Tag(5)

    assert note.tags == []
