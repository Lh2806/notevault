"""NoteManager: creating, autosaving and opening notes."""

from notevault.errors import NoteNotFoundError
from notevault.models import Note


class NoteManager:
    def __init__(self, note_repository, sync_service):
        self.notes = note_repository
        self.sync = sync_service

    def create_note(self, title, subject_id=None):
        note = Note(title, subject_id=subject_id)
        self.notes.save(note)
        return note

    def autosave(self, note):
        """Autosave sequence from the Assignment 3 design.

        1. save the current version locally (so the note opens offline)
        2. save a temporary PendingSave copy
        3. ask SyncService to upload it; the copy is deleted only after
           the cloud confirms
        Returns True if the note reached the cloud, False if it is still pending.
        """
        self.notes.save(note)
        self.notes.save_pending(note)
        return self.sync.sync_note(note.note_id)

    def open_note(self, note_id):
        note = self.notes.get(note_id)
        if note is None:
            raise NoteNotFoundError(f"no note with id {note_id}")
        return note
