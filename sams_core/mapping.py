"""Map signature detections to Student Records by row order (Story 1.5, FR-5).

The Info File's `no` ordinal *is* the row order: roster student i (0-based)
corresponds to the detected row whose `CellResult.row_index` is i. This module
produces exactly one `AttendanceRecord` per Student Record — a student with no
detected row is Ambiguous (no evidence is not evidence of absence, and must
never be coerced to Absent). Row-count mismatches are flagged as warnings, never
dropped silently (AD-6): the frontends render every student.

Only cross-boundary contracts from `models.py` leave this module (AD-2); no bare
dicts/tuples. This module never imports a UI framework or `sqlite3`.
"""

from collections.abc import Sequence

from sams_core.models import (
    AttendanceRecord,
    AttendanceStatus,
    InfoFile,
    StudentRecord,
)

# UX error-catalog wording (EXPERIENCE.md, Row-count mismatch). Kept as a module
# constant so the CLI and Web UI surface identical copy from one source.
ROW_COUNT_MISMATCH_TEMPLATE = (
    "The sheet has {detected} signature rows but the info file lists {expected} "
    "students. Results are matched by row order — please double-check them."
)


def _status_by_row_index(cell_results: Sequence) -> dict[int, AttendanceStatus]:
    """Index detection outcomes by their 0-based row position."""
    return {cell.row_index: cell.status for cell in cell_results}


def _row_indices_are_aligned(cell_results: Sequence, student_count: int) -> bool:
    """True when detected rows are exactly 0..N-1 for the N-student roster.

    Length equality alone is a weak proxy: duplicate or out-of-range
    `row_index` values (e.g. [0, 0, 2] or [0, 1, 5]) match on length but are
    NOT a trustworthy row-order alignment — indexing the roster with them
    would mis-assign or crash.
    """
    indices = [cell.row_index for cell in cell_results]
    return sorted(indices) == list(range(student_count))


def map_detections_to_students(
    cell_results: Sequence,
    info_file: InfoFile,
    sheet_id: str,
) -> tuple[list[AttendanceRecord], list[str]]:
    """Map detected Signature Cells to Student Records by row order (FR-5).

    Args:
        cell_results: `detect.CellResult` list, one per detected row, in row order.
        info_file: the parsed Info File (Session metadata + Student Records).
        sheet_id: the resolved Sheet Identifier (AD-11).

    Returns:
        (records, warnings)
        - records: one `AttendanceRecord` per Student Record, always
          `len(info_file.students)` long, in roster order. A student with no
          detected row → Ambiguous (never coerced to Absent).
        - warnings: the row-count-mismatch flag (UX wording) when the detected
          row count differs from the Student Record count, else empty. Non-fatal
          (AD-6): processing completes.
    """
    status_by_row = _status_by_row_index(cell_results)
    session = info_file.session

    records: list[AttendanceRecord] = []
    for row_index, student in enumerate(info_file.students):
        status = status_by_row.get(row_index, AttendanceStatus.AMBIGUOUS)
        records.append(
            AttendanceRecord(
                student_index=student.index,
                student_name=student.name,
                sheet_id=sheet_id,
                status=status,
                subject_code=session.subject_code,
                subject_name=session.subject_name,
                session_time=session.time,
                lecturer=session.lecturer,
            )
        )

    warnings: list[str] = []
    detected = len(cell_results)
    expected = len(info_file.students)
    if detected != expected:
        warnings.append(
            ROW_COUNT_MISMATCH_TEMPLATE.format(detected=detected, expected=expected)
        )

    return records, warnings


def student_indices_in_row_order(
    cell_results: Sequence,
    students: Sequence[StudentRecord],
) -> list[str] | None:
    """Canonical Student Indices aligned to detected rows, or None on mismatch.

    Used to name signature-cell crops by Student Index (AD-10). Returns `None`
    when the detected row count does not equal the Student Record count: a
    mislabelled probe would silently write one student's signature under
    another's index and corrupt Epic 3's verification set, so on any mismatch
    callers fall back to row ordinals instead of guessing the alignment.
    """
    if not _row_indices_are_aligned(cell_results, len(students)):
        return None
    # Rows are in row order and the roster is in `no` order — the same order.
    return [students[cell.row_index].index for cell in cell_results]
