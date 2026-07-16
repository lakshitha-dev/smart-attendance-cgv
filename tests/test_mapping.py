from dataclasses import dataclass

from sams_core import mapping
from sams_core.models import AttendanceStatus, InfoFile, Session, StudentRecord


@dataclass(frozen=True)
class _FakeCellResult:
    """Minimal stand-in for detect.CellResult — only row_index/status matter here."""

    row_index: int
    status: AttendanceStatus


def _info_file(n=3):
    session = Session(subject_code="CS402.3", subject_name="Computer Graphics", date="2019-05-31", time="13:00", lecturer="Dr. X")
    students = tuple(
        StudentRecord(no=f"{i + 1:03d}", index=f"1000930{i}", title="Mr", name=f"Student {i}")
        for i in range(n)
    )
    return InfoFile(session=session, students=students)


def test_one_record_per_student_when_rows_match():
    info = _info_file(3)
    cells = [
        _FakeCellResult(0, AttendanceStatus.PRESENT),
        _FakeCellResult(1, AttendanceStatus.ABSENT),
        _FakeCellResult(2, AttendanceStatus.PRESENT),
    ]

    records, warnings = mapping.map_detections_to_students(cells, info, "2019-05-31")

    assert len(records) == 3
    assert [r.status for r in records] == [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.PRESENT]
    assert warnings == []


def test_student_with_no_detected_row_is_ambiguous_never_absent():
    """No evidence is not evidence of absence (FR-5)."""
    info = _info_file(3)
    cells = [_FakeCellResult(0, AttendanceStatus.PRESENT)]  # rows 1, 2 never detected

    records, warnings = mapping.map_detections_to_students(cells, info, "2019-05-31")

    assert len(records) == 3
    assert records[1].status == AttendanceStatus.AMBIGUOUS
    assert records[2].status == AttendanceStatus.AMBIGUOUS


def test_row_count_mismatch_produces_warning_with_ux_wording():
    info = _info_file(3)
    cells = [_FakeCellResult(0, AttendanceStatus.PRESENT), _FakeCellResult(1, AttendanceStatus.PRESENT)]

    records, warnings = mapping.map_detections_to_students(cells, info, "2019-05-31")

    assert len(records) == 3  # still one record per Student Record, mismatch or not
    assert len(warnings) == 1
    assert "2 signature rows" in warnings[0]
    assert "3 students" in warnings[0]
    assert "matched by row order" in warnings[0]


def test_matching_row_count_produces_no_warning():
    info = _info_file(2)
    cells = [_FakeCellResult(0, AttendanceStatus.PRESENT), _FakeCellResult(1, AttendanceStatus.ABSENT)]

    _, warnings = mapping.map_detections_to_students(cells, info, "2019-05-31")

    assert warnings == []


def test_records_carry_canonical_index_and_session_metadata():
    info = _info_file(1)
    cells = [_FakeCellResult(0, AttendanceStatus.PRESENT)]

    records, _ = mapping.map_detections_to_students(cells, info, "2019-05-31")

    record = records[0]
    assert record.student_index == "10009300"
    assert record.student_name == "Student 0"
    assert record.sheet_id == "2019-05-31"
    assert record.subject_code == "CS402.3"
    assert record.subject_name == "Computer Graphics"
    assert record.session_time == "13:00"
    assert record.lecturer == "Dr. X"
    assert record.resolved_by_operator is False


def test_student_indices_in_row_order_matches_by_position():
    info = _info_file(3)
    cells = [
        _FakeCellResult(0, AttendanceStatus.PRESENT),
        _FakeCellResult(1, AttendanceStatus.ABSENT),
        _FakeCellResult(2, AttendanceStatus.PRESENT),
    ]

    indices = mapping.student_indices_in_row_order(cells, info.students)

    assert indices == ["10009300", "10009301", "10009302"]


def test_student_indices_in_row_order_none_on_mismatch():
    """A mislabelled probe would silently corrupt Epic 3's verification set — fall
    back to row ordinals instead of guessing the alignment on mismatch."""
    info = _info_file(3)
    cells = [_FakeCellResult(0, AttendanceStatus.PRESENT)]

    assert mapping.student_indices_in_row_order(cells, info.students) is None
