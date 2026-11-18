"""Errors that NoteVault raises on purpose."""


class NoteNotFoundError(LookupError):
    """The note id is not in local storage."""


class SubjectNotFoundError(LookupError):
    """The subject id is not in local storage (for example it was deleted)."""


class CloudUnavailableError(Exception):
    """The cloud storage service could not be reached (offline or upload failed)."""
