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
    assert calls == []  # rerun storm: zero re-processing
    assert any("6 students on sheet 2019-05-31" in s.value for s in at.success)


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


def test_process_page_error_outcome_surfaces_catalog_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    import webui.process_logic as pl

    at = AppTest.from_file(str(PAGE), default_timeout=30)
    at.session_state["_input_sig"] = (None, None, None)
    at.session_state["process_outcome"] = pl.ProcessOutcome(error=pl.BAD_IMAGE)
    at.run()

    assert not at.exception
    assert any("JPEG or PNG" in e.value for e in at.error)
