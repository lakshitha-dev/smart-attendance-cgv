"""Stories 4.2/4.3/4.4: the Process page behaviours via headless AppTest.

Covers the one-shot fence (rerun-storm → zero re-processing), the overwrite
gate, error-catalog surfacing, the results row list + chips, and the Ambiguous
one-tap resolve/undo flow. Uploads can't be simulated by AppTest, so the engine
seam is patched and inputs are injected via session_state; the results renderer
reads the DB, so rendering tests seed a temp DB the page is pointed at.
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

from sams_core.models import StudentRecord  # noqa: E402
from sams_core.repository import AttendanceRepository  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "webui" / "pages" / "Process.py"


def _result(records, warnings=None, sheet_id="2019-05-31"):
    from sams_core.models import SheetResult

    return SheetResult(
        warnings=warnings or [],
        detected_row_count=len(records),
        metadata_row_y_range=None,
        student_table_y_range=None,
        detected_grid_lines={},
        sheet_id=sheet_id,
        records=tuple(records),
        persisted_count=len(records),
        preserved_count=0,
    )


def _rec(index, name, status, sheet_id="2019-05-31"):
    from sams_core.models import AttendanceRecord

    return AttendanceRecord(
        student_index=index,
        student_name=name,
        sheet_id=sheet_id,
        status=status,
        subject_code="CS402.3",
        subject_name="Computer Graphics",
    )


@pytest.fixture
def page_repo(tmp_path, monkeypatch):
    """Point the page's default AttendanceRepository() at a temp DB (config
    .DB_PATH is fixed at import, so the env alone can't redirect it)."""
    import sams_core.config as cfg

    db = tmp_path / "sams.db"
    monkeypatch.setenv("SAMS_DB_PATH", str(db))
    monkeypatch.setattr(cfg, "DB_PATH", db)
    return AttendanceRepository(db_path=db)


def _seed_and_inject(at, repo, records, warnings=None, sheet_id="2019-05-31"):
    """Persist `records` (so the DB-backed row list reflects them) and inject a
    matching stored outcome + a settled input signature."""
    import webui.process_logic as pl
    from sams_core.models import StudentRecord

    repo.upsert_students(
        [
            StudentRecord(no=f"{i + 1:03d}", index=r.student_index, title="Mr", name=r.student_name)
            for i, r in enumerate(records)
        ]
    )
    if records:
        repo.save_attendance(records)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(
        result=_result(records, warnings=warnings, sheet_id=sheet_id), sheet_id=sheet_id
    )


def _body(at):
    return " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)


# --- Empty state + fence ------------------------------------------------------


def test_process_page_empty_state_renders_disabled_button():
    at = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not at.exception
    assert "That's all you need to do." in " ".join(m.value for m in at.markdown)
    buttons = {b.label: b for b in at.button}
    assert set(buttons) == {"Process", "Load sample sheet"}
    assert buttons["Process"].disabled is True


def test_process_page_has_no_engine_side_effect_on_plain_load(page_repo, monkeypatch):
    """A plain page load (no click) must never call the engine."""
    calls = []
    import webui.process_logic as pl

    monkeypatch.setattr(pl, "process_sheet_run", lambda *a, **k: calls.append(1))
    at = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not at.exception
    assert calls == []


def test_process_page_renders_stored_outcome_without_reprocessing(page_repo, monkeypatch):
    """Post-run reruns (scroll/expand) read the outcome from state; the engine
    is NOT called again (the fence)."""
    calls = []
    import webui.process_logic as pl
    from sams_core.models import AttendanceStatus as S

    monkeypatch.setattr(pl, "process_sheet_run", lambda *a, **k: calls.append(1))

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", "Alice", S.PRESENT)])
    at.run()

    assert not at.exception
    assert calls == []  # rerun storm: zero re-processing (the AC that matters here)
    assert _body(at).count("Results saved.") == 1


def test_process_page_overwrite_gate_shows_two_choices(page_repo):
    import webui.process_logic as pl

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(
        needs_overwrite_choice=True, sheet_id="2019-05-31"
    )
    at.session_state["pending_overwrite"] = {"image": b"x", "parsed": None}
    at.run()

    assert not at.exception
    body = " ".join(m.value for m in at.markdown)
    assert pl.OVERWRITE_PROMPT in body
    labels = {b.label for b in at.button}
    assert "Keep resolutions" in labels and "Overwrite everything" in labels


# --- Results list (UX-DR7/DR8) ------------------------------------------------


def test_process_page_results_list_shows_chips_summary_and_saved_once(page_repo):
    from sams_core.models import AttendanceStatus as S

    records = [
        _rec("10000409", "Alice", S.PRESENT),
        _rec("10009301", "Bea", S.ABSENT),
        _rec("10009302", "Cy", S.AMBIGUOUS),
    ]
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, records)
    at.run()

    assert not at.exception
    body = _body(at)
    assert "✓ Present" in body and "✕ Absent" in body  # settled chips
    for token in ("Alice", "Bea", "Cy", "10000409", "10009301", "10009302"):
        assert token in body
    assert "3 students checked. One needs a quick look from you." in body
    assert body.count("Results saved.") == 1


def test_process_page_row_count_mismatch_shows_flag_banner(page_repo):
    from sams_core.models import AttendanceStatus as S

    warning = "The sheet has 5 rows but the info file lists 6 students. Matched by row order."
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", "Alice", S.PRESENT)], warnings=[warning])
    at.run()

    assert not at.exception
    assert any("row order" in w.value for w in at.warning)  # a flag, not a failure


def test_process_page_escapes_markdown_and_html_in_student_name(page_repo):
    from sams_core.models import AttendanceStatus as S

    hostile = "Ann [tap](http://evil) <script>x</script> **bold**"
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", hostile, S.PRESENT)])
    at.run()

    assert not at.exception
    body = " ".join(m.value for m in at.markdown)
    assert "<script>" not in body  # escaped, never a live tag
    assert "&lt;script&gt;" in body
    assert "](http://evil)" in body  # link syntax renders as literal text


def test_process_page_empty_records_shows_no_students_message_not_saved(page_repo):
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [])
    at.run()

    assert not at.exception
    assert "Results saved." not in _body(at)  # no false success on zero detections
    assert any("couldn't find any students" in i.value for i in at.info)


# --- Ambiguous resolve / undo (UX-DR9, Story 4.4) -----------------------------


def test_process_page_ambiguous_row_shows_question_and_resolve_buttons(page_repo):
    import webui.process_logic as pl
    from sams_core.models import AttendanceStatus as S

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", "Alice", S.AMBIGUOUS)])
    at.run()

    assert not at.exception
    assert pl.AMBIGUOUS_QUESTION in " ".join(m.value for m in at.markdown)
    labels = {b.label for b in at.button}
    assert "✓ Present" in labels and "✕ Absent" in labels


def test_process_page_resolve_then_undo_round_trip(page_repo):
    """DoD: tap → instant flip + Undo works both directions; DB verified."""
    from sams_core.models import AttendanceStatus as S

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", "Alice", S.AMBIGUOUS)])
    at.run()

    next(b for b in at.button if b.label == "✓ Present").click().run()
    assert not at.exception
    assert page_repo.get_attendance(sheet_id="2019-05-31")[0].status is S.PRESENT
    assert "Saved as Present." in " ".join(m.value for m in at.markdown)  # on-page text
    assert any("Every student on this sheet is marked" in s.value for s in at.success)

    next(b for b in at.button if b.label == "Undo").click().run()
    assert not at.exception
    assert page_repo.get_attendance(sheet_id="2019-05-31")[0].status is S.AMBIGUOUS


def test_process_page_clean_sheet_does_not_claim_all_resolved(page_repo):
    """A sheet that never had an Ambiguous row must NOT show "All done. Every
    student is marked" — that message is scoped to resolving ambiguity (UX-DR9),
    not to a clean run the operator never touched."""
    from sams_core.models import AttendanceStatus as S

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", "Alice", S.PRESENT)])
    at.run()

    assert not at.exception
    assert not any("Every student on this sheet is marked" in s.value for s in at.success)


def test_process_page_scopes_rows_to_this_run_not_the_whole_date(page_repo):
    """sheet_id is the session date — a second sheet on the same date must NOT
    pull the first sheet's rows into this result list."""
    from sams_core.models import AttendanceStatus as S

    # A prior sheet on the SAME date left rows in the DB for other students.
    page_repo.upsert_students(
        [StudentRecord(no="099", index="88888888", title="Mr", name="Stale Student")]
    )
    page_repo.save_attendance([_rec("88888888", "Stale Student", S.PRESENT)])

    # This run's roster is just Alice.
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(at, page_repo, [_rec("10000409", "Alice", S.PRESENT)])
    at.run()

    assert not at.exception
    body = _body(at)
    assert "Alice" in body
    assert "Stale Student" not in body and "88888888" not in body  # not this run's roster
    assert "1 student checked." in body  # count reflects THIS run only


def test_process_page_every_resolved_row_keeps_an_undo(page_repo):
    """Resolving a second Ambiguous row must not strip the first's Undo — every
    operator-resolved row stays undoable while results are on screen."""
    from sams_core.models import AttendanceStatus as S

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    _seed_and_inject(
        at,
        page_repo,
        [_rec("10000409", "Alice", S.AMBIGUOUS), _rec("10009301", "Bea", S.AMBIGUOUS)],
    )
    at.run()

    next(b for b in at.button if b.key == "present_10000409").click().run()  # resolve Alice
    next(b for b in at.button if b.key == "absent_10009301").click().run()  # resolve Bea

    assert not at.exception
    # Both resolved rows expose an Undo (single-slot notice would have dropped Alice's).
    undo_keys = {b.key for b in at.button if b.key and b.key.startswith("undo_")}
    assert undo_keys == {"undo_10000409", "undo_10009301"}


def test_process_page_resolve_then_reprocess_triggers_overwrite_gate(page_repo):
    """DoD: a resolution makes a later re-process hit the 4.2 overwrite gate."""
    from sams_core.models import AttendanceStatus as S
    from webui.process_logic import needs_overwrite, parse_info, resolve_row

    page_repo.upsert_students(
        [StudentRecord(no="001", index="10000409", title="Mr", name="Alice")]
    )
    page_repo.save_attendance([_rec("10000409", "Alice", S.AMBIGUOUS)])
    resolve_row("2019-05-31", "10000409", present=True, repository=page_repo)

    parsed = parse_info(
        b'<subject code="C" name="N"><session date="2019-05-31"/>'
        b'<students><student no="001" index="10000409" title="Mr" name="Alice"/>'
        b"</students></subject>"
    )
    assert needs_overwrite(parsed, page_repo) is True


def test_process_page_error_outcome_surfaces_catalog_copy(page_repo):
    import webui.process_logic as pl

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(error=pl.BAD_IMAGE)
    at.run()

    assert not at.exception
    assert any("JPEG or PNG" in e.value for e in at.error)
