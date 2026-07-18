"""Story 4.2: the Process page behaviours via headless AppTest (FR-12/UX-DR4/DR5).

Covers the one-shot fence (rerun-storm triggers zero re-processing), the
overwrite gate, the AD-11 date field, and error-catalog surfacing. Uploads
can't be simulated by AppTest, so the engine seam is patched and inputs are
injected via session_state / a fake uploader where the page reads them.
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "webui" / "pages" / "Process.py"


def test_process_page_empty_state_renders_disabled_button():
    at = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not at.exception
    assert "That's all you need to do." in " ".join(m.value for m in at.markdown)
    assert len(at.button) == 1 and at.button[0].disabled is True


def test_process_page_has_no_engine_side_effect_on_plain_load(tmp_path, monkeypatch):
    """A plain page load (no click) must never call the engine — the fence
    guards the button-press rerun only."""
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    calls = []
    import webui.process_logic as pl

    monkeypatch.setattr(pl, "process_sheet_run", lambda *a, **k: calls.append(1))
    at = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not at.exception
    assert calls == []


def test_process_page_renders_stored_outcome_without_reprocessing(tmp_path, monkeypatch):
    """Simulate the post-run reruns (scroll/expand): the outcome is read from
    session_state and the engine is NOT called again."""
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    calls = []
    import webui.process_logic as pl
    from sams_core.models import SheetResult

    monkeypatch.setattr(pl, "process_sheet_run", lambda *a, **k: calls.append(1))

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(
        result=SheetResult(
            warnings=[],
            detected_row_count=6,
            metadata_row_y_range=None,
            student_table_y_range=None,
            detected_grid_lines={},
            sheet_id="2019-05-31",
            persisted_count=6,
            preserved_count=0,
        ),
        sheet_id="2019-05-31",
    )
    at.run()

    assert not at.exception
    assert calls == []  # rerun storm: zero re-processing (the AC that matters here)
    body = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert body.count("Results saved.") == 1  # settled results re-rendered from state


def test_process_page_overwrite_gate_shows_two_choices(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    import webui.process_logic as pl

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(
        needs_overwrite_choice=True, sheet_id="2019-05-31"
    )
    at.session_state["pending_overwrite"] = {"image": b"x", "parsed": None}
    at.run()

    assert not at.exception
    # UX-DR5 modal-style gate (st.dialog): prompt + the two choices render.
    body = " ".join(m.value for m in at.markdown)
    assert pl.OVERWRITE_PROMPT in body
    labels = {b.label for b in at.button}
    assert "Keep resolutions" in labels
    assert "Overwrite everything" in labels


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


def _rec(index, name, status):
    from sams_core.models import AttendanceRecord

    return AttendanceRecord(
        student_index=index,
        student_name=name,
        sheet_id="2019-05-31",
        status=status,
        subject_code="CS402.3",
        subject_name="Computer Graphics",
    )


def test_process_page_results_list_shows_chips_summary_and_saved_once(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    import webui.process_logic as pl
    from sams_core.models import AttendanceStatus as S

    records = [
        _rec("10000409", "Alice", S.PRESENT),
        _rec("10009301", "Bea", S.ABSENT),
        _rec("10009302", "Cy", S.AMBIGUOUS),
    ]
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(
        result=_result(records), sheet_id="2019-05-31"
    )
    at.run()

    assert not at.exception
    body = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    # Chips: icon + label together for each status (UX-DR8, greyscale-survivable).
    assert "✓ Present" in body and "✕ Absent" in body and "? Ambiguous" in body
    # Every student's name and index rendered.
    for token in ("Alice", "Bea", "Cy", "10000409", "10009301", "10009302"):
        assert token in body
    # Summary line + Ambiguous call-to-action.
    assert "3 students checked. One needs a quick look from you." in body
    # "Results saved." stated exactly once.
    assert body.count("Results saved.") == 1


def test_process_page_row_count_mismatch_shows_flag_banner(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    import webui.process_logic as pl
    from sams_core.models import AttendanceStatus as S

    warning = "The sheet has 5 rows but the info file lists 6 students. Matched by row order."
    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(
        result=_result([_rec("10000409", "Alice", S.PRESENT)], warnings=[warning]),
        sheet_id="2019-05-31",
    )
    at.run()

    assert not at.exception
    assert any("row order" in w.value for w in at.warning)  # a flag, not a failure


def test_process_page_error_outcome_surfaces_catalog_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    import webui.process_logic as pl

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(error=pl.BAD_IMAGE)
    at.run()

    assert not at.exception
    assert any("JPEG or PNG" in e.value for e in at.error)
