"""Shared test setup. Every test gets its own temporary SQLite database."""

import pytest

from fakes import FakeCloudStorage
from notevault.note_manager import NoteManager
from notevault.repositories import Database, NoteRepository, SubjectRepository
from notevault.search_filter_service import SearchFilterService
from notevault.sync_service import SyncService


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "notevault_test.db")
    yield db
    db.close()


@pytest.fixture
def note_repo(database):
    return NoteRepository(database)


@pytest.fixture
def subject_repo(database):
    return SubjectRepository(database)


@pytest.fixture
def cloud():
    return FakeCloudStorage()


@pytest.fixture
def sync_service(note_repo, cloud):
    return SyncService(note_repo, cloud)


@pytest.fixture
def note_manager(note_repo, sync_service):
    return NoteManager(note_repo, sync_service)


@pytest.fixture
def search_service(note_repo, subject_repo):
    return SearchFilterService(note_repo, subject_repo)
