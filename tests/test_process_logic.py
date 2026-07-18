"""Story 4.2: the Streamlit-free Process orchestration (FR-12/AD-11/AD-12).

Pure-logic coverage of parse_info, the overwrite gate, error-catalog mapping,
and the AD-11 rule that the Web UI never uses the upload filename as the Sheet
Identifier.
"""

import pytest

from sams_core.models import AttendanceRecord, AttendanceStatus, SheetResult
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


@pytest.fixture
def image_bytes():
    """Real decodable PNG so run_process's up-front image check passes and the
    gate/engine logic under test is actually reached."""
    import cv2

    from tests.test_locate import _synthetic_sheet

    ok, buf = cv2.imencode(".png", _synthetic_sheet())
    assert ok
    return buf.tobytes()


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


def test_parse_info_dated_file_with_bad_date_maps_to_date_copy():
    bad = DATED_XML.replace(b'date="2019-05-31"', b'date="2019-13-45"')
    parsed = parse_info(bad)
    assert parsed.sheet_id is None
    assert "session date" in parsed.error  # BAD_DATE, not "student list"


def test_parse_info_rejects_dtd_billion_laughs_without_hanging():
    """A hostile Info File declaring entities must be refused at the door
    (engine DTD guard) — never expanded by ElementTree."""
    bomb = (
        b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
        b'<!ENTITY lol2 "&lol;&lol;&lol;">]><subject code="C" name="N">'
        b'<session date="2019-05-31"/><students>'
        b'<student no="1" index="10000001" title="Mr" name="&lol2;"/>'
        b"</students></subject>"
    )
    assert parse_info(bomb).error == BAD_INFO_FILE


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


def test_run_process_gates_on_existing_operator_resolutions(repo, image_bytes, monkeypatch):
    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: True)
    called = False

    def _never(*a, **k):
        nonlocal called
        called = True

    monkeypatch.setattr(process_logic, "process_sheet_run", _never)

    outcome = run_process(image_bytes, parsed, repo, overwrite_decided=False)

    assert outcome.needs_overwrite_choice is True
    assert outcome.result is None
    assert called is False  # nothing processed until the operator chooses


def test_run_process_proceeds_once_the_choice_is_made(repo, image_bytes, monkeypatch):
    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: True)
    seen = {}
    monkeypatch.setattr(
        process_logic,
        "process_sheet_run",
        lambda img, p, r, overwrite, on_stage: seen.update(overwrite=overwrite) or _fake_result(),
    )

    outcome = run_process(
        image_bytes, parsed, repo, overwrite=True, overwrite_decided=True
    )

    assert outcome.needs_overwrite_choice is False
    assert outcome.result is not None
    assert seen["overwrite"] is True


def test_run_process_rejects_undecodable_image_before_touching_the_engine(repo, monkeypatch):
    """Image is validated up front (no more guessing from an exception
    message): garbage bytes never reach process_sheet."""
    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: False)
    called = False

    def _never(*a, **k):
        nonlocal called
        called = True

    monkeypatch.setattr(process_logic, "process_sheet_run", _never)

    outcome = run_process(b"not-an-image", parsed, repo)
    assert "JPEG or PNG" in outcome.error
    assert called is False


def test_run_process_empty_image_is_bad_image_not_a_crash(repo, monkeypatch):
    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: False)
    outcome = run_process(b"", parsed, repo)
    assert "JPEG or PNG" in outcome.error


def test_run_process_unexpected_engine_error_is_calm_not_a_traceback(repo, monkeypatch):
    import cv2

    from tests.test_locate import _synthetic_sheet

    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: False)
    ok, buf = cv2.imencode(".png", _synthetic_sheet())
    assert ok

    def _boom(*a, **k):
        raise RuntimeError("unexpected non-Sams failure")

    monkeypatch.setattr(process_logic, "process_sheet_run", _boom)

    outcome = run_process(buf.tobytes(), parsed, repo)
    assert outcome.result is None
    assert outcome.error == process_logic.GENERIC_FAILURE


def test_results_summary_singular_plural_and_ambiguous_call_to_action():
    from webui.process_logic import results_summary

    def rec(status):
        return AttendanceRecord(
            student_index="10000001",
            student_name="X",
            sheet_id="s",
            status=status,
            subject_code="C",
            subject_name="N",
        )

    P, A, Q = AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.AMBIGUOUS
    assert results_summary([rec(P)]) == "1 student checked."
    assert results_summary([rec(P), rec(A)]) == "2 students checked."
    assert (
        results_summary([rec(P), rec(Q)])
        == "2 students checked. One needs a quick look from you."
    )
    assert (
        results_summary([rec(Q), rec(Q), rec(P)])
        == "3 students checked. 2 need a quick look from you."
    )


def test_status_chip_map_has_icon_label_and_exact_hex_for_every_status():
    from webui.process_logic import STATUS_CHIP

    expected_hex = {
        AttendanceStatus.PRESENT: "#256E4C",
        AttendanceStatus.ABSENT: "#A63D2A",
        AttendanceStatus.AMBIGUOUS: "#7A6212",
    }
    assert set(STATUS_CHIP) == set(AttendanceStatus)
    for status, (icon, label, colour) in STATUS_CHIP.items():
        assert icon and label == status.value  # icon + label (greyscale-survivable)
        assert colour == expected_hex[status]  # exact UX-DR8 hex, rendered inline


def test_needs_overwrite_reflects_existing_operator_resolutions(repo, monkeypatch):
    from webui.process_logic import needs_overwrite

    parsed = parse_info(DATED_XML)
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: True)
    assert needs_overwrite(parsed, repo) is True
    monkeypatch.setattr(repo, "has_operator_resolutions", lambda sid: False)
    assert needs_overwrite(parsed, repo) is False


def test_run_process_end_to_end_persists_to_the_db(repo):
    """Real engine call through the seam: a dated 2-student sheet processes,
    reports the resolved Sheet Identifier, AND actually writes rows to the DB
    (proves persistence happened, not just that no exception was raised)."""
    import cv2

    from tests.test_locate import _synthetic_sheet

    ok, buf = cv2.imencode(".png", _synthetic_sheet())
    assert ok
    parsed = parse_info(DATED_XML)  # 2 students, dated 2019-05-31

    outcome = run_process(buf.tobytes(), parsed, repo)

    assert outcome.error is None
    assert outcome.result is not None
    assert outcome.result.sheet_id == "2019-05-31"
    saved = repo.get_attendance(sheet_id="2019-05-31")
    assert {r.student_index for r in saved} == {"10000409", "10009301"}
