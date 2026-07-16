import pytest

from sams_core.models import AttendanceRecord, AttendanceStatus, StudentRecord
from sams_core.repository import AttendanceRepository


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


def _students(n=3):
    return [
        StudentRecord(no=f"{i + 1:03d}", index=f"1000930{i}", title="Mr", name=f"Student {i}")
        for i in range(n)
    ]


def _record(index, sheet_id="2019-05-31", status=AttendanceStatus.PRESENT):
    return AttendanceRecord(
        student_index=index,
        student_name="Some Student",
        sheet_id=sheet_id,
        status=status,
        subject_code="CS402.3",
        subject_name="Computer Graphics",
        session_time="13:00",
        lecturer="Dr. X",
    )


# --- Schema bootstrap -------------------------------------------------------


def test_ensure_schema_creates_db_file(repo, tmp_path):
    repo.ensure_schema()
    assert (tmp_path / "sams.db").is_file()


# --- Students / index resolution --------------------------------------------


def test_upsert_students_is_idempotent(repo):
    students = _students(3)
    repo.upsert_students(students)
    repo.upsert_students(students)  # re-run should not duplicate

    assert len(repo.list_students()) == 3


def test_resolve_student_index_passes_through_8_digit_form(repo):
    repo.upsert_students(_students(1))
    assert repo.resolve_student_index("10009300") == "10009300"


def test_resolve_student_index_resolves_short_ordinal(repo):
    repo.upsert_students(_students(3))  # no="001".."003"
    assert repo.resolve_student_index("002") == "10009301"
    assert repo.resolve_student_index("2") == "10009301"  # unpadded form


def test_resolve_student_index_unknown_ordinal_returns_none_not_raises(repo):
    """An unresolvable short ordinal returns None (AD-6: unknown index is a
    no-data result at the read layer, never an exception)."""
    repo.upsert_students(_students(1))
    assert repo.resolve_student_index("999") is None
    assert repo.resolve_student_index("not-a-number") is None


def test_resolve_student_index_unknown_8_digit_passes_through_unchanged(repo):
    """An 8-digit form is already canonical — the resolver's job is normalizing
    alias forms, not validating roster membership; a genuinely unknown index is
    surfaced as a no-data result by the read APIs (AD-6), not rejected here."""
    repo.upsert_students(_students(1))
    assert repo.resolve_student_index("99999999") == "99999999"


# --- Attendance upsert / re-processing --------------------------------------


def test_save_attendance_upserts_without_duplicating_on_reprocess(repo):
    students = _students(2)
    repo.upsert_students(students)
    records = [_record(s.index) for s in students]

    repo.save_attendance(records)
    repo.save_attendance(records)  # simulate re-processing the same sheet

    stored = repo.get_attendance(sheet_id="2019-05-31")
    assert len(stored) == 2


def test_save_attendance_updates_status_on_reprocess(repo):
    students = _students(1)
    repo.upsert_students(students)
    repo.save_attendance([_record(students[0].index, status=AttendanceStatus.ABSENT)])
    repo.save_attendance([_record(students[0].index, status=AttendanceStatus.PRESENT)])

    stored = repo.get_attendance(student_index=students[0].index, sheet_id="2019-05-31")
    assert stored[0].status == AttendanceStatus.PRESENT


# --- Operator resolution survival / overwrite semantics ---------------------


def test_operator_resolution_survives_reprocess_without_overwrite(repo):
    students = _students(1)
    index = students[0].index
    repo.upsert_students(students)
    repo.save_attendance([_record(index, status=AttendanceStatus.AMBIGUOUS)])

    repo.resolve("2019-05-31", index, AttendanceStatus.PRESENT, by_operator=True)

    # Re-process without --overwrite: the human's resolution must survive.
    repo.save_attendance([_record(index, status=AttendanceStatus.ABSENT)], overwrite=False)

    stored = repo.get_attendance(student_index=index, sheet_id="2019-05-31")[0]
    assert stored.status == AttendanceStatus.PRESENT
    assert stored.resolved_by_operator is True


def test_operator_resolution_replaced_with_overwrite_true(repo):
    students = _students(1)
    index = students[0].index
    repo.upsert_students(students)
    repo.save_attendance([_record(index, status=AttendanceStatus.AMBIGUOUS)])
    repo.resolve("2019-05-31", index, AttendanceStatus.PRESENT, by_operator=True)

    repo.save_attendance([_record(index, status=AttendanceStatus.ABSENT)], overwrite=True)

    stored = repo.get_attendance(student_index=index, sheet_id="2019-05-31")[0]
    assert stored.status == AttendanceStatus.ABSENT
    assert stored.resolved_by_operator is False


def test_has_operator_resolutions_reflects_resolved_state(repo):
    students = _students(1)
    index = students[0].index
    repo.upsert_students(students)
    repo.save_attendance([_record(index, status=AttendanceStatus.AMBIGUOUS)])

    assert repo.has_operator_resolutions("2019-05-31") is False

    repo.resolve("2019-05-31", index, AttendanceStatus.PRESENT, by_operator=True)

    assert repo.has_operator_resolutions("2019-05-31") is True


def test_undo_resolution_restores_ambiguous_and_clears_flag(repo):
    students = _students(1)
    index = students[0].index
    repo.upsert_students(students)
    repo.save_attendance([_record(index, status=AttendanceStatus.AMBIGUOUS)])
    repo.resolve("2019-05-31", index, AttendanceStatus.PRESENT, by_operator=True)

    repo.undo_resolution("2019-05-31", index)

    stored = repo.get_attendance(student_index=index, sheet_id="2019-05-31")[0]
    assert stored.status == AttendanceStatus.AMBIGUOUS
    assert stored.resolved_by_operator is False


# --- Signature image path registration (no blobs) ---------------------------


def test_register_and_get_signature_image_path(repo):
    repo.register_signature_image("10009300", "2019-05-31", "probe", "/output/2019-05-31/crops/10009300.png")

    path = repo.get_signature_image("10009300", "2019-05-31", "probe")

    assert path == "/output/2019-05-31/crops/10009300.png"


def test_get_signature_image_unregistered_returns_none(repo):
    assert repo.get_signature_image("10009300", "2019-05-31", "probe") is None


# --- Connection hygiene ------------------------------------------------------


def test_each_operation_uses_its_own_connection_no_shared_state(repo):
    """AD-4: no cached/global connection — sequential calls must not error out
    from a stale or half-closed handle."""
    repo.ensure_schema()
    repo.upsert_students(_students(1))
    repo.list_students()
    repo.has_operator_resolutions("2019-05-31")
    repo.get_attendance()
    # No assertion beyond "did not raise" — this exercises the connection lifecycle.
