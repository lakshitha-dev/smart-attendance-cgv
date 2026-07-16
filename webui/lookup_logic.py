"""Lookup page logic (Story 4.5, FR-14/AD-8): the ONLY piece of the Lookup
page that isn't a bare widget call, kept Streamlit-free so it is testable
without a Streamlit runtime.

`lookup()` reuses Story 2.1's `AttendanceRepository.query_attendance` — the
same single index resolver the CLI uses — so both index forms and both
entry points return identical Attendance Records (data-layer parity, FR-14).
No chart logic lives here: rendering the returned records into a Figure is
`sams_core.visualization.render_attendance_timeline`'s job alone.
"""

from dataclasses import dataclass

from sams_core.models import AttendanceRecord
from sams_core.repository import AttendanceRepository

# Verbatim UX-DR12 catalog copy (EXPERIENCE.md "Unknown Student Index" row).
_NO_DATA_PREFIX = "We don't have any attendance saved for that number."


@dataclass
class LookupResult:
    """Either `records` is non-empty (render the figure) or `message` is set
    (show the calm no-data copy) — never both, never neither."""

    records: list[AttendanceRecord]
    message: str | None


def lookup(alias: str, repository: AttendanceRepository) -> LookupResult:
    """Resolve `alias` (either index form) and fetch its Attendance Records.

    An unresolvable alias or a student with no saved records yields a
    no-data `LookupResult` (AD-6) — never an exception, never an error tone.
    """
    records = repository.query_attendance(alias)
    if records:
        return LookupResult(records=records, message=None)

    students = repository.list_students()
    if not students:
        return LookupResult(records=[], message=_NO_DATA_PREFIX)

    listing = ", ".join(f"{s['no']} ({s['student_index']})" for s in students)
    return LookupResult(records=[], message=f"{_NO_DATA_PREFIX} Students we do know: {listing}…")
