import io

import pytest

from sams_core.models import AttendanceRecord, AttendanceStatus, StudentRecord
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_attendance_timeline
from webui.lookup_logic import lookup


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


def _seed_one_session(repo):
    repo.upsert_students([StudentRecord(no="001", index="10000409", title="Mr", name="Alice")])
    repo.save_attendance(
        [
            AttendanceRecord(
                student_index="10000409",
                student_name="Alice",
                sheet_id="2019-05-31",
                status=AttendanceStatus.PRESENT,
                subject_code="CS402.3",
                subject_name="Computer Graphics",
            )
        ]
    )


def _seed_multi_session(repo):
    repo.upsert_students([StudentRecord(no="001", index="10000409", title="Mr", name="Alice")])
    repo.save_attendance(
        [
            AttendanceRecord(
                student_index="10000409",
                student_name="Alice",
                sheet_id=sheet_id,
                status=status,
                subject_code="CS402.3",
                subject_name="Computer Graphics",
            )
            for sheet_id, status in [
                ("2019-05-31", AttendanceStatus.PRESENT),
                ("2019-06-07", AttendanceStatus.ABSENT),
                ("2019-06-14", AttendanceStatus.AMBIGUOUS),
            ]
        ]
    )


# --- lookup() pure logic ------------------------------------------------------


def test_lookup_short_form_and_eight_digit_form_return_identical_records(repo):
    _seed_one_session(repo)

    by_short_form = lookup("001", repo)
    by_eight_digit = lookup("10000409", repo)

    assert by_short_form.records == by_eight_digit.records
    assert by_short_form.message is None
    assert by_eight_digit.message is None


def test_lookup_unknown_index_lists_valid_indices_never_error_tone(repo):
    _seed_one_session(repo)

    result = lookup("999", repo)

    assert result.records == []
    assert result.message is not None
    assert "don't have any attendance saved" in result.message
    assert "001 (10000409)" in result.message


def test_lookup_empty_db_reports_no_students_calmly(repo):
    result = lookup("001", repo)

    assert result.records == []
    assert result.message is not None
    assert "No students in the local database yet" in result.message  # actual empty-DB copy


def test_lookup_ambiguous_ordinal_says_so_and_never_claims_no_data(repo):
    _seed_one_session(repo)
    repo.upsert_students([StudentRecord(no="001", index="20000001", title="Ms", name="Bea")])

    result = lookup("001", repo)

    assert result.records == []
    assert "more than one student" in result.message
    assert "10000409" in result.message and "20000001" in result.message
    assert "don't have any attendance saved" not in result.message


def test_lookup_known_student_without_rows_is_distinct_from_unknown(repo):
    repo.upsert_students([StudentRecord(no="001", index="10000409", title="Mr", name="Alice")])

    result = lookup("001", repo)

    assert "no attendance saved yet" in result.message
    assert "don't have any attendance saved for that number" not in result.message


def test_lookup_unknown_listing_ellipsis_only_when_truncated(repo):
    _seed_one_session(repo)

    result = lookup("999", repo)

    assert "001 (10000409)" in result.message
    assert "…" not in result.message  # one student, nothing truncated

    repo.upsert_students(
        [
            StudentRecord(no=f"{i:03d}", index=f"3000{i:04d}", title="Ms", name=f"S{i}")
            for i in range(2, 22)
        ]
    )
    result = lookup("999", repo)
    assert "… and" in result.message  # 21 students, listing capped honestly


# --- CLI/Web figure parity (DoD: "compare saved PNGs") -----------------------


def _png_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return buf.getvalue()


def test_lookup_figure_matches_cli_figure_for_both_index_forms(repo):
    _seed_multi_session(repo)
    cli_records = list(repo.query_attendance("10000409").records)
    cli_png = _png_bytes(render_attendance_timeline(cli_records))

    web_short = lookup("001", repo)
    web_long = lookup("10000409", repo)

    assert _png_bytes(render_attendance_timeline(web_short.records)) == cli_png
    assert _png_bytes(render_attendance_timeline(web_long.records)) == cli_png


# --- The Streamlit page itself (streamlit.testing AppTest, headless) ----------


def _app_test(tmp_path, monkeypatch):
    """Run the real Lookup page headlessly with DB/output redirected."""
    pytest.importorskip("streamlit.testing.v1")
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    import sams_core.config as config

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "sams.db")
    page = Path(__file__).resolve().parent.parent / "webui" / "pages" / "Lookup.py"
    return AppTest.from_file(str(page), default_timeout=30)


def test_page_empty_state_prompts_calmly(tmp_path, monkeypatch):
    at = _app_test(tmp_path, monkeypatch).run()
    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    assert "Type a student's number" in body


def test_page_whitespace_input_stays_in_empty_state(tmp_path, monkeypatch):
    at = _app_test(tmp_path, monkeypatch).run()
    at.text_input[0].set_value("   ").run()
    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    assert "Type a student's number" in body


def test_page_unknown_index_shows_no_data_copy_never_an_error(tmp_path, monkeypatch):
    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    _seed_one_session(repo)

    at = _app_test(tmp_path, monkeypatch).run()
    at.text_input[0].set_value("999").run()

    assert not at.exception
    assert not at.error
    body = " ".join(el.value for el in at.markdown)
    assert "don't have any attendance saved" in body
    assert "001 (10000409)" in body


def test_page_known_index_renders_without_error(tmp_path, monkeypatch):
    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    _seed_multi_session(repo)

    at = _app_test(tmp_path, monkeypatch).run()
    at.text_input[0].set_value("001").run()

    assert not at.exception
    assert not at.error
