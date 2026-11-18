"""Unit 3: nested subjects (Subject)."""

import pytest

from notevault.models import Subject


def test_add_child_subject():
    # expected behavior
    school = Subject("School")
    software = Subject("Software Engineering")
    school.add_child(software)

    assert software.parent is school
    assert school.children == [software]
    assert software.path() == "School / Software Engineering"


def test_three_level_nest_and_moving_a_subject():
    # edge cases
    school = Subject("School")
    software = Subject("Software Engineering", parent=school)
    week5 = Subject("Week 5", parent=software)

    assert week5.depth() == 2
    assert week5.path() == "School / Software Engineering / Week 5"
    assert school.descendants() == [software, week5]

    # moving a subject takes it out of the old parent
    archive = Subject("Archive")
    week5.move_to(archive)
    assert software.children == []
    assert archive.children == [week5]
    assert week5.path() == "Archive / Week 5"

    # moving to None makes it a top-level subject
    week5.move_to(None)
    assert week5.parent is None
    assert archive.children == []


def test_own_parent_cycle_and_empty_name_are_rejected():
    # invalid input
    school = Subject("School")
    software = Subject("Software Engineering", parent=school)
    week5 = Subject("Week 5", parent=software)

    with pytest.raises(ValueError):
        school.move_to(school)       # its own parent
    with pytest.raises(ValueError):
        school.move_to(week5)        # School under its own grandchild = cycle
    with pytest.raises(ValueError):
        Subject("   ")               # empty name

    # the tree is the same as before the failed moves
    assert school.parent is None
    assert week5.path() == "School / Software Engineering / Week 5"
