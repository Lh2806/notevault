"""Component 1: autosave and sync.

Parts working together: NoteManager + NoteRepository (temporary SQLite
database) + SyncService + PendingSave + a fake Cloud Storage Service.
"""

import json

import pytest

from notevault.errors import NoteNotFoundError


def test_autosave_uploads_and_deletes_only_the_pending_copy(note_manager, note_repo, cloud):
    # success scenario
    note = note_manager.create_note("Lecture 1")
    note.set_text("Requirements\nDesign")
    note.lines[0].apply_format(0, 12, "bold")
    note.add_tag("Week 5")

    reached_cloud = note_manager.autosave(note)

    assert reached_cloud is True
    assert json.loads(cloud.uploads[note.note_id])["lines"] == ["Requirements", "Design"]
    assert note_repo.list_pending() == []        # temporary copy was deleted

    # the current version is still on the computer, with formatting and tags
    reopened = note_manager.open_note(note.note_id)
    assert reopened.text == "Requirements\nDesign"
    assert reopened.lines[0].styles_at(0) == {"bold"}
    assert reopened.has_tag("week 5")


def test_autosave_offline_keeps_pending_copy_and_note_still_opens(note_manager, note_repo, cloud):
    # failure scenario: no connection
    cloud.online = False
    note = note_manager.create_note("Lecture 2")
    note.set_text("written with no internet")

    reached_cloud = note_manager.autosave(note)

    assert reached_cloud is False
    assert cloud.uploads == {}
    pending = note_repo.list_pending()
    assert len(pending) == 1
    assert pending[0].note_id == note.note_id

    # offline opening still works
    assert note_manager.open_note(note.note_id).text == "written with no internet"

    # a note id that does not exist is reported, not returned as empty
    with pytest.raises(NoteNotFoundError):
        note_manager.open_note("no-such-note")


def test_retry_pending_uploads_newest_copy_when_cloud_is_back(note_manager, note_repo, sync_service, cloud):
    # unusual scenario: several offline saves, then the connection returns
    cloud.online = False
    first = note_manager.create_note("Lecture 3")
    second = note_manager.create_note("Lecture 4")

    first.set_text("draft")
    note_manager.autosave(first)
    first.set_text("draft\nfinished version")
    note_manager.autosave(first)                 # same note saved again offline
    second.set_text("other note")
    note_manager.autosave(second)

    assert len(note_repo.list_pending()) == 2    # one copy per note, not three

    cloud.online = True
    uploaded = sync_service.retry_pending()

    assert uploaded == 2
    assert note_repo.list_pending() == []
    assert json.loads(cloud.uploads[first.note_id])["lines"] == ["draft", "finished version"]
    assert json.loads(cloud.uploads[second.note_id])["lines"] == ["other note"]
    assert sync_service.retry_pending() == 0     # nothing left to send
