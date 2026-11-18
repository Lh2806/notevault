# Testing notes (for the Assignment 4 report)

## Result

18 tests, 18 passed after the fixes below. `docs/run_before_fixes.txt` is the saved
output of the run with 2 failures. `docs/run_unit.txt`, `docs/run_component.txt` and
`docs/run_full.txt` are the runs after the fixes.

## Bugs found and fixed

The first version of the 18 tests passed. We then tried extra cases by hand, found two
bugs, added a check for each one to an existing test (both failed), and fixed the code.

1. **A note could not be reopened after a formatted line was shortened.**
   - How to reproduce: make "Requirements" bold (0 to 12), change the line text to
     "Req", save the note, open it again.
   - What happened: `ValueError: format range goes past the end of the line` when
     loading the note, so the note would not open.
   - Cause: changing `NoteLine.text` left the old FormatRange (0 to 12) on a 3-character line.
   - Fix: `NoteLine.text` is now a property. When the text gets shorter, formatting is cut
     back to the new length and ranges that are completely past the end are removed.
   - Test: `test_range_at_line_end_and_overlapping_ranges` (unit 2).

2. **Saving a note into a subject that does not exist gave a raw database error.**
   - How to reproduce: delete a subject, then save a note that still has that subject id.
   - What happened: `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
   - Fix: `NoteRepository.save` checks the subject first and raises `SubjectNotFoundError`,
     the same error the search uses.
   - Test: `test_tag_filter_without_matches_and_deleted_subject` (component 2).

## Check that the tests are meaningful

We broke the code on purpose in 14 places (for example: skip renumbering, skip the cycle
check, never delete the pending copy, ignore nested subjects in search) and ran the suite
each time. All 14 broken versions made at least one test fail.

## Remaining failures

None. All 18 tests pass.

## Limitations

- Only the core of the design is implemented: notes, lines, formatting, subjects, tags,
  autosave/sync and search. Pictures, handwriting conversion, AI summaries, export, email
  and the user interface are not implemented yet, so they are not tested.
- The cloud is a fake. The tests show NoteVault does the right thing when an upload works
  or fails, but not that a real cloud service works.
- The fake cloud only has "online" and "offline". Slow connections, an upload that stops
  halfway, and two devices editing the same note are not tested.
- `Note.set_text` replaces all lines, so formatting on the old lines is dropped. Inserting
  or deleting characters in the middle of a line does not shift the formatting ranges.
- Search loads the notes and checks them in Python. This is fine for a small number of
  notes but was not tested for speed with thousands of notes.
- Search does not match a phrase that is split across two lines.
- Deleting a subject makes its notes unfiled. The design does not say yet if the user
  should be asked first.

## Small change from the plan

Unit 4 was planned to reject an "unknown tag". A tag nobody used is not an error (the filter
just returns nothing, tested in component 2), so unit 4 rejects an empty or non-text tag
name instead.
