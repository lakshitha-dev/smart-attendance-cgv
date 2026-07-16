"""Lookup page logic (Story 4.5, FR-14/AD-8): the ONLY piece of the Lookup
page that isn't a bare widget call, kept Streamlit-free so it is testable
without a Streamlit runtime.

`lookup()` reuses Story 2.1's `AttendanceRepository.query_attendance` — the
same single index resolver the CLI uses — so both index forms and both
entry points return identical Attendance Records (data-layer parity, FR-14).
Each engine outcome gets its own calm copy: unknown, ambiguous, known-but-
empty, and empty-DB are different operator situations (AD-6). No chart logic
lives here: rendering the returned records into a Figure is
`sams_core.visualization.render_attendance_timeline`'s job alone.
"""

from dataclasses import dataclass, field

from sams_core.models import AttendanceRecord, LookupOutcome
from sams_core.repository import AttendanceRepository

# Verbatim UX-DR12 catalog copy (EXPERIENCE.md "Unknown Student Index" row).
_NO_DATA_PREFIX = "We don't have any attendance saved for that number."
_LISTING_LIMIT = 12


@dataclass
class LookupResult:
    """Either `records` is non-empty (render the figure) or `message` is set
    (show the calm no-data copy) — never both, never neither."""

    records: list[AttendanceRecord] = field(default_factory=list)
    message: str | None = None


def _listing(students, limit: int = _LISTING_LIMIT) -> str:
    """Short-form + 8-digit listing, ellipsis ONLY when actually truncated."""
    shown = ", ".join(
        f"{(s['no'] or s['student_index'])} ({s['student_index']})" for s in students[:limit]
    )
    extra = len(students) - limit
    return shown + (f" … and {extra} more" if extra > 0 else "")


def lookup(alias: str, repository: AttendanceRepository) -> LookupResult:
    """Resolve `alias` (either index form) and fetch its Attendance Records.

    Every no-data shape yields a `LookupResult` with outcome-specific copy
    (AD-6) — never an exception, never an error tone.
    """
    result = repository.query_attendance(alias)

    if result.outcome is LookupOutcome.FOUND:
        return LookupResult(records=list(result.records))

    if result.outcome is LookupOutcome.EMPTY_DB:
        return LookupResult(
            message="No students in the local database yet — process a signing sheet first."
        )

    if result.outcome is LookupOutcome.AMBIGUOUS:
        return LookupResult(
            message=(
                "That short number matches more than one student — "
                f"use the 8-digit index: {', '.join(result.candidates)}."
            )
        )

    if result.outcome is LookupOutcome.NO_ATTENDANCE:
        return LookupResult(
            message=(
                "That student is on the roster but has no attendance saved yet — "
                "process their signing sheet first."
            )
        )

    # UNKNOWN
    students = list(result.valid_students)
    if not students:
        return LookupResult(message=_NO_DATA_PREFIX)
    return LookupResult(
        message=f"{_NO_DATA_PREFIX} Students we do know: {_listing(students)}"
    )
