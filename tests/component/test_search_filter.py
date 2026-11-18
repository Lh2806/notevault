"""Component 2: search and filter.

Parts working together: SearchFilterService + NoteRepository +
SubjectRepository on a temporary SQLite database.
"""

import pytest

from notevault.errors import SubjectNotFoundError
from notevault.models import Note, Subject


@pytest.fixture
def library(note_repo, subject_repo):
    """A small set of made-up subjects and notes saved in the temporary database.

    School
      Software Engineering      -> "UML Basics" (tag Week 5)
        Lectures                -> "Sequence Diagrams"
      History                   -> "French Revolution" (tag Week 4)
    (no subject)                -> "Poster Ideas"
    """
    school = Subject("School")
    software = Subject("Software Engineering", parent=school)
    lectures = Subject("Lectures", parent=software)
    history = Subject("History", parent=school)
    for subject in (school, software, lectures, history):
        subject_repo.save(subject)

    uml = Note("UML Basics", subject_id=software.subject_id)
    uml.set_text("Class diagrams show structure")
    uml.add_tag("Week 5")

    sequence = Note("Sequence Diagrams", subject_id=lectures.subject_id)
    sequence.set_text("Messages between objects\nRead from top to bottom")

    french = Note("French Revolution", subject_id=history.subject_id)
    french.set_text("Started in 1789")
    french.add_tag("Week 4")

    poster = Note("Poster Ideas")
    poster.set_text("Print the class DIAGRAM for the wall")

    for note in (uml, sequence, french, poster):
        note_repo.save(note)

    return {"school": school, "software": software, "lectures": lectures, "history": history}


def titles(notes):
    return [note.title for note in notes]


def test_keyword_search_across_all_notes(search_service, library):
    # success scenario
    found = search_service.search("diagram")
    assert titles(found) == ["Poster Ideas", "Sequence Diagrams", "UML Basics"]

    assert titles(search_service.search("1789")) == ["French Revolution"]
    assert search_service.search("chemistry") == []


def test_search_within_subject_includes_nested_subjects(search_service, library):
    # success scenario with scope: Software Engineering and the Lectures subject inside it
    found = search_service.search("diagram", subject_id=library["software"].subject_id)
    assert titles(found) == ["Sequence Diagrams", "UML Basics"]   # not the unfiled poster note

    # only the nested subject
    found = search_service.search("diagram", subject_id=library["lectures"].subject_id)
    assert titles(found) == ["Sequence Diagrams"]

    # a subject that has notes, but none with the keyword
    assert search_service.search("diagram", subject_id=library["history"].subject_id) == []


def test_tag_filter_without_matches_and_deleted_subject(search_service, subject_repo, note_repo, library):
    # failure / unusual scenarios
    assert titles(search_service.filter_by_tag("week 5")) == ["UML Basics"]
    assert search_service.filter_by_tag("Week 9") == []           # tag nobody used
    assert search_service.filter_by_tag(
        "Week 5", subject_id=library["history"].subject_id) == [] # tag exists, wrong subject

    with pytest.raises(ValueError):
        search_service.search("   ")                              # empty keyword

    # delete Software Engineering (and Lectures inside it)
    software_id = library["software"].subject_id
    subject_repo.delete(software_id)

    with pytest.raises(SubjectNotFoundError):
        search_service.search("diagram", subject_id=software_id)
    with pytest.raises(SubjectNotFoundError):
        search_service.search("diagram", subject_id=library["lectures"].subject_id)

    # a new note cannot be saved into the deleted subject
    with pytest.raises(SubjectNotFoundError):
        note_repo.save(Note("Late note", subject_id=software_id))

    # the notes were not lost, they are just unfiled now
    assert titles(search_service.search("diagram")) == [
        "Poster Ideas", "Sequence Diagrams", "UML Basics",
    ]
