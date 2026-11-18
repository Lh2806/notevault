"""SyncService: sends autosaved notes to the Cloud Storage Service."""

from notevault.errors import CloudUnavailableError


class SyncService:
    def __init__(self, note_repository, cloud_client):
        self.notes = note_repository
        self.cloud = cloud_client

    def sync_note(self, note_id):
        """Upload the pending copy of one note.

        Returns True when the cloud confirmed the upload (the temporary copy
        is then deleted). Returns False when the cloud could not be reached
        (the temporary copy is kept for retry_pending).
        """
        pending = self.notes.get_pending_for(note_id)
        if pending is None:
            return True  # nothing is waiting for this note
        try:
            self.cloud.upload(pending.note_id, pending.content)
        except CloudUnavailableError:
            return False
        self.notes.delete_pending(pending.pending_id)
        return True

    def retry_pending(self):
        """Try again for every pending copy. Returns how many were uploaded."""
        uploaded = 0
        for pending in self.notes.list_pending():
            try:
                self.cloud.upload(pending.note_id, pending.content)
            except CloudUnavailableError:
                break  # still offline, keep the rest for next time
            self.notes.delete_pending(pending.pending_id)
            uploaded += 1
        return uploaded
