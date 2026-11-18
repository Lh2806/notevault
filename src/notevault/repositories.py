"""Data access layer: repositories on top of a local SQLite database."""

import json
import sqlite3
from datetime import datetime, timezone

from notevault.errors import SubjectNotFoundError
from notevault.models import Note, PendingSave, Subject, new_id

SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    parent_id  TEXT REFERENCES subjects(subject_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS notes (
    note_id    TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    subject_id TEXT REFERENCES subjects(subject_id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS note_lines (
    note_id     TEXT NOT NULL REFERENCES notes(note_id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    text        TEXT NOT NULL,
    PRIMARY KEY (note_id, line_number)
);
CREATE TABLE IF NOT EXISTS format_ranges (
    note_id     TEXT NOT NULL REFERENCES notes(note_id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    start_pos   INTEGER NOT NULL,
    end_pos     INTEGER NOT NULL,
    style       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS note_tags (
    note_id TEXT NOT NULL REFERENCES notes(note_id) ON DELETE CASCADE,
    name    TEXT NOT NULL,
    PRIMARY KEY (note_id, name)
);
CREATE TABLE IF NOT EXISTS pending_saves (
    pending_id TEXT PRIMARY KEY,
    note_id    TEXT NOT NULL UNIQUE REFERENCES notes(note_id) ON DELETE CASCADE,
    saved_at   TEXT NOT NULL,
    content    TEXT NOT NULL
);
"""


class Database:
    """Opens the SQLite file and creates the tables if they are missing."""

    def __init__(self, path):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()


class NoteRepository:
    def __init__(self, database):
        self.conn = database.conn

    def save(self, note):
        """Save the current version of a note (insert or update)."""
        if note.subject_id is not None:
            found = self.conn.execute(
                "SELECT 1 FROM subjects WHERE subject_id = ?", (note.subject_id,)
            ).fetchone()
            if found is None:
                raise SubjectNotFoundError(f"no subject with id {note.subject_id}")
        with self.conn:
            self.conn.execute(
                "INSERT INTO notes (note_id, title, subject_id) VALUES (?, ?, ?) "
                "ON CONFLICT(note_id) DO UPDATE SET title = excluded.title, "
                "subject_id = excluded.subject_id",
                (note.note_id, note.title, note.subject_id),
            )
            for table in ("note_lines", "format_ranges", "note_tags"):
                self.conn.execute(f"DELETE FROM {table} WHERE note_id = ?", (note.note_id,))
            for line in note.lines:
                self.conn.execute(
                    "INSERT INTO note_lines VALUES (?, ?, ?)",
                    (note.note_id, line.number, line.text),
                )
                for r in line.formats:
                    self.conn.execute(
                        "INSERT INTO format_ranges VALUES (?, ?, ?, ?, ?)",
                        (note.note_id, line.number, r.start, r.end, r.style),
                    )
            for tag in note.tags:
                self.conn.execute(
                    "INSERT INTO note_tags VALUES (?, ?)", (note.note_id, tag.name)
                )

    def get(self, note_id):
        row = self.conn.execute(
            "SELECT * FROM notes WHERE note_id = ?", (note_id,)
        ).fetchone()
        return self._build(row) if row else None

    def all(self):
        rows = self.conn.execute("SELECT * FROM notes ORDER BY title").fetchall()
        return [self._build(row) for row in rows]

    def find_by_subjects(self, subject_ids):
        subject_ids = list(subject_ids)
        if not subject_ids:
            return []
        marks = ",".join("?" for _ in subject_ids)
        rows = self.conn.execute(
            f"SELECT * FROM notes WHERE subject_id IN ({marks}) ORDER BY title",
            subject_ids,
        ).fetchall()
        return [self._build(row) for row in rows]

    def _build(self, row):
        note = Note(row["title"], note_id=row["note_id"], subject_id=row["subject_id"])
        lines = self.conn.execute(
            "SELECT text FROM note_lines WHERE note_id = ? ORDER BY line_number",
            (note.note_id,),
        ).fetchall()
        note.set_text("\n".join(r["text"] for r in lines))
        formats = self.conn.execute(
            "SELECT * FROM format_ranges WHERE note_id = ?", (note.note_id,)
        ).fetchall()
        for f in formats:
            note.lines[f["line_number"] - 1].apply_format(
                f["start_pos"], f["end_pos"], f["style"]
            )
        tags = self.conn.execute(
            "SELECT name FROM note_tags WHERE note_id = ? ORDER BY name", (note.note_id,)
        ).fetchall()
        for t in tags:
            note.add_tag(t["name"])
        return note

    # ---- temporary autosave copies (PendingSave) ----

    def save_pending(self, note):
        """Keep a temporary copy until the cloud upload is confirmed.

        Only the newest copy of each note is kept, since that is the one
        that has to reach the cloud.
        """
        content = json.dumps(
            {"title": note.title, "lines": [line.text for line in note.lines]}
        )
        pending = PendingSave(
            new_id(), note.note_id, datetime.now(timezone.utc).isoformat(), content
        )
        with self.conn:
            self.conn.execute(
                "DELETE FROM pending_saves WHERE note_id = ?", (note.note_id,)
            )
            self.conn.execute(
                "INSERT INTO pending_saves VALUES (?, ?, ?, ?)",
                (pending.pending_id, pending.note_id, pending.saved_at, pending.content),
            )
        return pending

    def list_pending(self):
        rows = self.conn.execute(
            "SELECT * FROM pending_saves ORDER BY saved_at"
        ).fetchall()
        return [
            PendingSave(r["pending_id"], r["note_id"], r["saved_at"], r["content"])
            for r in rows
        ]

    def get_pending_for(self, note_id):
        for pending in self.list_pending():
            if pending.note_id == note_id:
                return pending
        return None

    def delete_pending(self, pending_id):
        with self.conn:
            self.conn.execute(
                "DELETE FROM pending_saves WHERE pending_id = ?", (pending_id,)
            )


class SubjectRepository:
    def __init__(self, database):
        self.conn = database.conn

    def save(self, subject):
        """Save a subject. A parent has to be saved before its children."""
        parent_id = subject.parent.subject_id if subject.parent else None
        with self.conn:
            self.conn.execute(
                "INSERT INTO subjects (subject_id, name, parent_id) VALUES (?, ?, ?) "
                "ON CONFLICT(subject_id) DO UPDATE SET name = excluded.name, "
                "parent_id = excluded.parent_id",
                (subject.subject_id, subject.name, parent_id),
            )

    def exists(self, subject_id):
        row = self.conn.execute(
            "SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)
        ).fetchone()
        return row is not None

    def get(self, subject_id):
        """Load a subject together with its chain of parents."""
        row = self.conn.execute(
            "SELECT * FROM subjects WHERE subject_id = ?", (subject_id,)
        ).fetchone()
        if row is None:
            return None
        parent = self.get(row["parent_id"]) if row["parent_id"] else None
        return Subject(row["name"], subject_id=row["subject_id"], parent=parent)

    def descendant_ids(self, subject_id):
        """Ids of every subject nested under this one (children, grandchildren, ...)."""
        rows = self.conn.execute(
            "WITH RECURSIVE tree(id) AS ("
            "  SELECT subject_id FROM subjects WHERE parent_id = ?"
            "  UNION ALL"
            "  SELECT s.subject_id FROM subjects s JOIN tree ON s.parent_id = tree.id"
            ") SELECT id FROM tree",
            (subject_id,),
        ).fetchall()
        return [r["id"] for r in rows]

    def delete(self, subject_id):
        """Delete a subject and the subjects nested in it.

        Notes that were inside are kept and become unfiled (no subject).
        """
        with self.conn:
            self.conn.execute(
                "DELETE FROM subjects WHERE subject_id = ?", (subject_id,)
            )
