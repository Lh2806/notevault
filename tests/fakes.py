"""Fake external services for the tests. Nothing here touches the internet."""

from notevault.cloud import CloudStorageClient
from notevault.errors import CloudUnavailableError


class FakeCloudStorage(CloudStorageClient):
    """Stands in for the Cloud Storage Service.

    Set online = False to act like the computer has no connection.
    Everything that was "uploaded" is kept in the uploads dictionary.
    """

    def __init__(self):
        self.online = True
        self.uploads = {}
        self.upload_calls = 0

    def upload(self, note_id, content):
        self.upload_calls += 1
        if not self.online:
            raise CloudUnavailableError("fake cloud is offline")
        self.uploads[note_id] = content
