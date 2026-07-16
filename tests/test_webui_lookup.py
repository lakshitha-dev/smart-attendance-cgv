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
    assert "don't have any attendance saved" in result.message


# --- CLI/Web figure parity (DoD: "compare saved PNGs") -----------------------


def _png_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return buf.getvalue()


def test_lookup_figure_matches_cli_figure_for_both_index_forms(repo):
    _seed_multi_session(repo)
    cli_records = repo.query_attendance("10000409")
    cli_png = _png_bytes(render_attendance_timeline(cli_records))

    web_short = lookup("001", repo)
    web_long = lookup("10000409", repo)

    assert _png_bytes(render_attendance_timeline(web_short.records)) == cli_png
    assert _png_bytes(render_attendance_timeline(web_long.records)) == cli_png
