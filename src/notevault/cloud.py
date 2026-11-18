"""The interface NoteVault uses to talk to the Cloud Storage Service.

The real client is an external service. The tests use a fake one
(tests/fakes.py), so no live API is ever called.
"""


class CloudStorageClient:
    def upload(self, note_id, content):
        """Upload one note. Raises CloudUnavailableError if it cannot be reached."""
        raise NotImplementedError
