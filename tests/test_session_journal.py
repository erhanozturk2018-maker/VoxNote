from app.session_journal import SessionJournal, delete_journal, find_journals, load_journal
from app.transcript_models import Session, TranscriptSegment


def test_journal_round_trip(session, tmp_path):
    fresh = Session(
        session_id=session.session_id,
        started_at=session.started_at,
        model="small",
        device="cuda",
        compute_type="float16",
    )
    journal = SessionJournal(tmp_path, fresh)
    languages = []
    for segment in session.segments:
        if segment.language not in languages:
            languages.append(segment.language)
        journal.append(segment, list(languages))
    journal.close()

    assert find_journals(tmp_path) == [journal.path]
    restored = load_journal(journal.path)
    assert restored.session_id == session.session_id
    assert restored.started_at == session.started_at
    assert restored.segments == session.segments
    assert restored.languages == ["en", "tr"]
    assert restored.duration_seconds == 5.5
    assert (restored.model, restored.device, restored.compute_type) == ("small", "cuda", "float16")


def test_segments_are_on_disk_before_close(session, tmp_path):
    journal = SessionJournal(tmp_path, session)
    journal.append(session.segments[0], ["en"])
    # Simulates a crash: the file is read without the journal being closed.
    restored = load_journal(journal.path)
    assert [s.text for s in restored.segments] == [session.segments[0].text]
    journal.close()


def test_truncated_last_line_is_skipped(session, tmp_path):
    journal = SessionJournal(tmp_path, session)
    journal.append(session.segments[0], ["en"])
    journal.close()
    with open(journal.path, "a", encoding="utf-8") as handle:
        handle.write('{"type": "segment", "start": 3.0, "te')
    restored = load_journal(journal.path)
    assert len(restored.segments) == 1


def test_delete(session, tmp_path):
    journal = SessionJournal(tmp_path, session)
    journal.delete()
    assert find_journals(tmp_path) == []
    delete_journal(journal.path)  # deleting twice is harmless


def test_unreadable_or_foreign_files(tmp_path):
    assert load_journal(tmp_path / "missing.jsonl") is None
    garbage = tmp_path / "garbage.jsonl"
    garbage.write_text("not json at all\n", encoding="utf-8")
    assert load_journal(garbage) is None
    assert find_journals(tmp_path / "no-such-folder") == []


def test_journal_failure_does_not_raise(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    journal = SessionJournal(blocker / "sub", Session())  # cannot be created
    journal.append(TranscriptSegment(0, 1, "en", "hello"), ["en"])
    journal.delete()
