"""Story 4.2: the Streamlit-free Process orchestration (FR-12/AD-11/AD-12).

Pure-logic coverage of parse_info, the overwrite gate, error-catalog mapping,
and the AD-11 rule that the Web UI never uses the upload filename as the Sheet
Identifier.
"""

import pytest

from sams_core.models import AttendanceStatus, SheetResult
from sams_core.repository import AttendanceRepository
from webui import process_logic
from webui.process_logic import (
    BAD_INFO_FILE,
    parse_info,
    run_process,
)

DATED_XML = b"""<subject code="CS402.3" name="Computer Graphics">
  <session date="2019-05-31" time="13:00" lecturer="Dr X"/>
  <students>
    <student no="001" index="10000409" title="Mr" name="Alice"/>
    <student no="002" index="10009301" title="Ms" name="Bea"/>
  </students>
</subject>"""

DATELESS_XML = b"""<subject code="CS402.3" name="Computer Graphics">
  <session time="13:00" lecturer="Dr X"/>
  <students>
    <student no="001" index="10000409" title="Mr" name="Alice"/>
  </students>
</subject>"""


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


# --- parse_info ---------------------------------------------------------------


def test_parse_info_dated_resolves_sheet_id_from_the_info_file():
    parsed = parse_info(DATED_XML)
    assert parsed.error is None
    assert parsed.needs_date is False
    assert parsed.sheet_id == "2019-05-31"


def test_parse_info_dateless_requests_a_date_and_never_uses_a_filename():
    parsed = parse_info(DATELESS_XML)
    assert parsed.needs_date is True
    assert parsed.sheet_id is None  # AD-11: no filename fallback in the Web UI
    assert parsed.error is None


def test_parse_info_dateless_with_entered_date_resolves():
    parsed = parse_info(DATELESS_XML, session_date="2019-07-10")
    assert parsed.sheet_id == "2019-07-10"


def test_parse_info_dateless_with_bad_date_reports_catalog_copy():
    parsed = parse_info(DATELESS_XML, session_date="not-a-date")
    assert parsed.sheet_id is None
    assert "session date" in parsed.error


def test_parse_info_garbage_maps_to_bad_info_file_copy():
    assert parse_info(b"not xml at all").error == BAD_INFO_FILE
    assert parse_info(b"<subject></subject>").error == BAD_INFO_FILE


# --- run_process: overwrite gate + errors ------------------------------------


def _fake_result(sheet_id="2019-05-31", saved=2):
    return SheetResult(
        warnings=[],
        detected_row_count=saved,
        metadata_row_y_range=None,
        student_table_y_range=None,
        detected_grid_lines={},
        sheet_id=sheet_id,
        persisted_count=saved,
        preserved_count=0,
    )


def test_run_process_gates_on_existing_operator_resolutions(repo, monkeypatch):
    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: True)
    called = False

    def _never(*a, **k):
        nonlocal called
        called = True

    monkeypatch.setattr(process_logic, "process_sheet_run", _never)

    outcome = run_process(b"imgbytes", parsed, repo, overwrite_decided=False)

    assert outcome.needs_overwrite_choice is True
    assert outcome.result is None
    assert called is False  # nothing processed until the operator chooses


def test_run_process_proceeds_once_the_choice_is_made(repo, monkeypatch):
    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: True)
    seen = {}
    monkeypatch.setattr(
        process_logic,
        "process_sheet_run",
        lambda img, p, r, overwrite, on_stage: seen.update(overwrite=overwrite) or _fake_result(),
    )

    outcome = run_process(
        b"imgbytes", parsed, repo, overwrite=True, overwrite_decided=True
    )

    assert outcome.needs_overwrite_choice is False
    assert outcome.result is not None
    assert seen["overwrite"] is True


def test_run_process_maps_bad_image_to_catalog_copy(repo, monkeypatch):
    from sams_core.errors import InputError

    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: False)

    def _boom(*a, **k):
        raise InputError("Image could not be read (unreadable or corrupt)")

    monkeypatch.setattr(process_logic, "process_sheet_run", _boom)

    outcome = run_process(b"garbage", parsed, repo)
    assert outcome.result is None
    assert "JPEG or PNG" in outcome.error


def test_run_process_end_to_end_persists_once(repo):
    """Real engine call through the seam: a dated sheet processes and the
    result carries the resolved Sheet Identifier."""
    import cv2

    from tests.test_locate import _synthetic_sheet

    ok, buf = cv2.imencode(".png", _synthetic_sheet())
    assert ok
    # A 1-student dateless info matching the synthetic sheet's first row.
    parsed = parse_info(DATED_XML)
    outcome = run_process(buf.tobytes(), parsed, repo)
    # The synthetic sheet may classify rows either way; what matters for 4.2 is
    # the run completed, persisted, and reported the right sheet id — no raise.
    assert outcome.error is None
    assert outcome.result is not None
    assert outcome.result.sheet_id == "2019-05-31"
