"""SearchFilterService: keyword search and tag filters."""

from notevault.errors import SubjectNotFoundError
from notevault.models import Tag


def matches_keyword(note, keyword):
    """True if the keyword is in the note title or any line (upper/lower case ignored)."""
    if not isinstance(keyword, str):
        raise TypeError("keyword must be a string")
    needle = keyword.strip().casefold()
    if not needle:
        raise ValueError("keyword cannot be empty")
    if needle in note.title.casefold():
        return True
    return any(needle in line.text.casefold() for line in note.lines)


class SearchFilterService:
    def __init__(self, note_repository, subject_repository):
        self.notes = note_repository
        self.subjects = subject_repository

    def search(self, keyword, subject_id=None):
        """Search all notes, or only one subject and the subjects nested in it."""
        return [n for n in self._notes_in_scope(subject_id) if matches_keyword(n, keyword)]

    def filter_by_tag(self, tag_name, subject_id=None):
        tag = Tag(tag_name)  # raises if the tag name is not valid
        return [n for n in self._notes_in_scope(subject_id) if tag in n.tags]

    def _notes_in_scope(self, subject_id):
        if subject_id is None:
            return self.notes.all()
        if not self.subjects.exists(subject_id):
            raise SubjectNotFoundError(f"no subject with id {subject_id}")
        ids = [subject_id] + self.subjects.descendant_ids(subject_id)
        return self.notes.find_by_subjects(ids)
