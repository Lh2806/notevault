# NoteVault

NoteVault is a stand-alone desktop note-taking app (Software Engineering class project,
Youngstown State University). Team: LeBraun Hall and Andrew Gibson.

This repository has the core classes from our Assignment 3 design and the automated
tests for Assignment 4 (Unit and Component Testing).

## What is in here

```
src/notevault/
    models.py                  Note, NoteLine, FormatRange, Subject, Tag, PendingSave
    repositories.py            Database, NoteRepository, SubjectRepository (SQLite)
    note_manager.py            NoteManager (create, autosave, open)
    sync_service.py            SyncService (upload to cloud, retry pending copies)
    search_filter_service.py   SearchFilterService (keyword search, tag filter)
    cloud.py                   interface for the Cloud Storage Service
    errors.py                  NoteVault errors
tests/
    unit/                      12 unit tests (4 units, 3 tests each)
    component/                 6 component tests (2 components, 3 tests each)
    fakes.py                   fake Cloud Storage Service (no live API)
    conftest.py                test setup, temporary SQLite database for every test
docs/                          saved test output and testing notes
```

## Install

You need Python 3.10 or newer.

```
git clone <repository link>
cd notevault
python -m pip install -r requirements.txt
```

The only thing to install is pytest. SQLite comes with Python.

## Run the tests

Run these from the top folder of the repository.

Full suite (all 18 tests):

```
python -m pytest -v
```

Unit tests only:

```
python -m pytest tests/unit -v
```

Component tests only:

```
python -m pytest tests/component -v
```

On some computers the command is `python3` instead of `python`.

## Notes about the tests

- The tests never use the internet. The cloud service is replaced by `FakeCloudStorage`
  in `tests/fakes.py`.
- Every test makes a new temporary SQLite database and it is thrown away after the test.
  No real notes or user data are used.
