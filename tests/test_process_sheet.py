"""AD-12 guarantees of `process_sheet` — the one engine entry point (Story 1.5).

Runs the REAL pipeline end-to-end on a synthetic Signing Sheet (drawn grid +
ink, same builder as test_locate), with the repository and output dir fully
isolated. Covers the contracts nothing else exercises: persistence happens on
success, an aborted run never persists, and overwrite semantics round-trip.
"""

import cv2
import numpy as np
import pytest

import sams_core.artifacts as artifacts
import sams_core.config as config
from sams_core.models import AttendanceStatus, InfoFile, Session, StudentRecord
from sams_core.pipeline import process_sheet
from sams_core.repository import AttendanceRepository
from tests.test_locate import SIGNATURE_COLUMN, STUD_H, _synthetic_sheet

SHEET_DATE = "2019-05-31"


def _info_file() -> InfoFile:
    session = Session(
        subject_code="CS402.3",
        subject_name="Computer Graphics and Visualization",
        date=SHEET_DATE,
        time="13:00",
        lecturer="Dr. Rasika Ranaweera",
    )
    students = tuple(
        StudentRecord(no=f"{i + 1:03d}", index=f"1000940{i}", title="Mr", name=f"Student {i + 1}")
        for i in range(3)
    )
    return InfoFile(session=session, students=students)


def _sheet_png_bytes() -> bytes:
    """Synthetic sheet with signatures in rows 1-2 and row 3 left empty."""
    image = _synthetic_sheet()
    x0, x1 = SIGNATURE_COLUMN
    for row in (0, 1):  # fat ink blobs well above the Present threshold
        top, bottom = STUD_H[1 + row] + 15, STUD_H[2 + row] - 15
        image[top:bottom, x0 + 20 : x1 - 20] = 0
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    out = tmp_path / "output"
    monkeypatch.setattr(config, "OUTPUT_DIR", out)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", out)
    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    return repo, out


def test_success_persists_records_counts_and_registrations(isolated):
    repo, out = isolated

    result = process_sheet(_sheet_png_bytes(), _info_file(), repository=repo)

    assert result.sheet_id == SHEET_DATE
    assert result.persisted_count == 3 and result.preserved_count == 0
    persisted = repo.get_attendance(sheet_id=SHEET_DATE)
    statuses = {r.student_index: r.status for r in persisted}
    assert statuses["10009400"] == AttendanceStatus.PRESENT
    assert statuses["10009401"] == AttendanceStatus.PRESENT
    assert statuses["10009402"] == AttendanceStatus.ABSENT
    # Crops registered (atomically, with the attendance) and files exist.
    for index in statuses:
        path = repo.get_signature_image(index, SHEET_DATE, "probe")
        assert path is not None and (out / SHEET_DATE / "crops").exists()


def test_aborted_run_never_persists(isolated):
    repo, _ = isolated

    def _explode(stage):
        raise RuntimeError("display side channel failed")

    with pytest.raises(RuntimeError):
        process_sheet(_sheet_png_bytes(), _info_file(), on_stage=_explode, repository=repo)

    assert repo.get_attendance(sheet_id=SHEET_DATE) == []
    assert repo.list_students() == []


def test_operator_resolution_survives_rerun_unless_overwrite(isolated):
    repo, _ = isolated
    process_sheet(_sheet_png_bytes(), _info_file(), repository=repo)
    assert repo.resolve(SHEET_DATE, "10009402", AttendanceStatus.PRESENT) is True

    rerun = process_sheet(_sheet_png_bytes(), _info_file(), repository=repo)

    kept = {r.student_index: r for r in repo.get_attendance(sheet_id=SHEET_DATE)}
    assert kept["10009402"].status == AttendanceStatus.PRESENT  # human wins
    assert kept["10009402"].resolved_by_operator is True
    assert rerun.preserved_count == 1 and rerun.persisted_count == 2
    assert any("operator resolutions" in w for w in rerun.warnings)

    overwritten = process_sheet(_sheet_png_bytes(), _info_file(), overwrite=True, repository=repo)

    replaced = {r.student_index: r for r in repo.get_attendance(sheet_id=SHEET_DATE)}
    assert replaced["10009402"].status == AttendanceStatus.ABSENT  # machine verdict restored
    assert replaced["10009402"].resolved_by_operator is False
    assert overwritten.preserved_count == 0


def test_resolve_and_undo_report_whether_a_row_matched(isolated):
    repo, _ = isolated
    process_sheet(_sheet_png_bytes(), _info_file(), repository=repo)

    assert repo.resolve(SHEET_DATE, "99999999", AttendanceStatus.PRESENT) is False  # typo'd index
    assert repo.undo_resolution(SHEET_DATE, "10009402") is False  # never operator-resolved
    machine = {r.student_index: r.status for r in repo.get_attendance(sheet_id=SHEET_DATE)}
    assert machine["10009402"] == AttendanceStatus.ABSENT  # verdict NOT destroyed by the no-op undo
