"""Domain classes from the Assignment 3 class diagram.

Note is made of NoteLines (a note always has at least one line).
A NoteLine owns its FormatRanges (bold / italic / underline).
A Subject can have one parent and many children (nested subjects).
A Tag is a label such as "Week 5" that can be put on many notes.
"""

import uuid


def new_id():
    return uuid.uuid4().hex


class FormatRange:
    """Formatting on part of one line. start is included, end is not."""

    STYLES = ("bold", "italic", "underline")

    def __init__(self, start, end, style):
        for value in (start, end):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("start and end must be whole numbers")
        if style not in self.STYLES:
            raise ValueError("style must be bold, italic or underline")
        if start < 0:
            raise ValueError("start cannot be negative")
        if end <= start:
            raise ValueError("end must be after start")
        self.start = start
        self.end = end
        self.style = style

    def covers(self, index):
        return self.start <= index < self.end

    def overlaps_or_touches(self, other):
        return self.start <= other.end and other.start <= self.end

    def __eq__(self, other):
        return (
            isinstance(other, FormatRange)
            and (self.start, self.end, self.style) == (other.start, other.end, other.style)
        )

    def __repr__(self):
        return f"FormatRange({self.start}, {self.end}, '{self.style}')"


class NoteLine:
    """One numbered line of a note."""

    def __init__(self, number, text=""):
        if not isinstance(text, str):
            raise TypeError("line text must be a string")
        self.number = number
        self._text = text
        self.formats = []

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        """Change the line text. Formatting past the new end of the line is cut off."""
        if not isinstance(new_text, str):
            raise TypeError("line text must be a string")
        self._text = new_text
        length = len(new_text)
        kept = []
        for r in self.formats:
            if r.start < length:
                kept.append(FormatRange(r.start, min(r.end, length), r.style))
        self.formats = kept

    def apply_format(self, start, end, style):
        """Add bold, italic or underline to characters start..end of this line."""
        new_range = FormatRange(start, end, style)
        if end > len(self.text):
            raise ValueError("format range goes past the end of the line")

        # Two ranges of the same style that overlap or touch become one range.
        kept = []
        for existing in self.formats:
            if existing.style == style and existing.overlaps_or_touches(new_range):
                new_range = FormatRange(
                    min(existing.start, new_range.start),
                    max(existing.end, new_range.end),
                    style,
                )
            else:
                kept.append(existing)
        kept.append(new_range)
        self.formats = sorted(kept, key=lambda r: (r.start, r.style))
        return new_range

    def styles_at(self, index):
        """Return the set of styles on the character at this position."""
        return {r.style for r in self.formats if r.covers(index)}


class Tag:
    """A label for filtering notes. "Week 5" and "week 5" are the same tag."""

    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("tag name must be a string")
        cleaned = " ".join(name.split())
        if not cleaned:
            raise ValueError("tag name cannot be empty")
        self.name = cleaned

    @property
    def key(self):
        return self.name.casefold()

    def __eq__(self, other):
        return isinstance(other, Tag) and self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return f"Tag('{self.name}')"


class Note:
    """A note with a title and numbered lines."""

    def __init__(self, title, note_id=None, subject_id=None):
        if not isinstance(title, str) or not title.strip():
            raise ValueError("a note needs a title")
        self.note_id = note_id or new_id()
        self.title = title.strip()
        self.subject_id = subject_id
        self.lines = [NoteLine(1, "")]
        self.tags = []

    @property
    def text(self):
        return "\n".join(line.text for line in self.lines)

    def set_text(self, text):
        """Replace the whole note body. Each line break starts a new numbered line."""
        if not isinstance(text, str):
            raise TypeError("note text must be a string")
        parts = text.replace("\r\n", "\n").split("\n")
        self.lines = [NoteLine(i + 1, part) for i, part in enumerate(parts)]

    def insert_line(self, number, text):
        """Insert a new line so that it gets this line number."""
        if not isinstance(text, str):
            raise TypeError("line text must be a string")
        if isinstance(number, bool) or not isinstance(number, int):
            raise TypeError("line number must be a whole number")
        if number < 1 or number > len(self.lines) + 1:
            raise IndexError("line number is out of range")
        self.lines.insert(number - 1, NoteLine(number, text))
        self._renumber()

    def delete_line(self, number):
        if isinstance(number, bool) or not isinstance(number, int):
            raise TypeError("line number must be a whole number")
        if number < 1 or number > len(self.lines):
            raise IndexError("line number is out of range")
        if len(self.lines) == 1:
            # a note always keeps at least one line
            self.lines = [NoteLine(1, "")]
        else:
            del self.lines[number - 1]
            self._renumber()

    def _renumber(self):
        for i, line in enumerate(self.lines):
            line.number = i + 1

    def add_tag(self, name):
        tag = Tag(name)
        if tag not in self.tags:
            self.tags.append(tag)
        return tag

    def has_tag(self, name):
        return Tag(name) in self.tags


class Subject:
    """A subject (folder) that can hold notes and other subjects."""

    def __init__(self, name, subject_id=None, parent=None):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("a subject needs a name")
        self.subject_id = subject_id or new_id()
        self.name = name.strip()
        self.parent = None
        self.children = []
        if parent is not None:
            self.move_to(parent)

    def add_child(self, child):
        child.move_to(self)

    def move_to(self, new_parent):
        """Put this subject under new_parent (None makes it a top-level subject)."""
        if new_parent is self:
            raise ValueError("a subject cannot be its own parent")
        if new_parent is not None and new_parent.is_descendant_of(self):
            raise ValueError("this move would make a cycle of subjects")
        if self.parent is not None:
            self.parent.children.remove(self)
        self.parent = new_parent
        if new_parent is not None:
            new_parent.children.append(self)

    def is_descendant_of(self, other):
        current = self.parent
        while current is not None:
            if current is other:
                return True
            current = current.parent
        return False

    def descendants(self):
        found = []
        for child in self.children:
            found.append(child)
            found.extend(child.descendants())
        return found

    def depth(self):
        return 0 if self.parent is None else self.parent.depth() + 1

    def path(self):
        if self.parent is None:
            return self.name
        return self.parent.path() + " / " + self.name


class PendingSave:
    """Temporary autosave copy that waits here until the cloud confirms the upload."""

    def __init__(self, pending_id, note_id, saved_at, content):
        self.pending_id = pending_id
        self.note_id = note_id
        self.saved_at = saved_at
        self.content = content
