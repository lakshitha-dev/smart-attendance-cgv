"""Session history logic (SAMS.dc.html design: the Session history page):
the Streamlit-free core of the history view, testable without a Streamlit
runtime.

Everything real comes from `AttendanceRepository.get_attendance` — this module
only groups the saved Attendance Records by Sheet Identifier and derives the
per-session aggregates the page renders (counts, rate, weekday). No sqlite, no
Streamlit, no chart rendering lives here (AD-1/AD-8). The empty-DB path checks
`db_exists` first so a read-only visit never creates a DB file on disk (AD-4).
"""

from dataclasses import dataclass, field
from datetime import date

from sams_core.models import AttendanceRecord, AttendanceStatus
from sams_core.repository import AttendanceRepository

# Calm no-data copy, same register as the Lookup/Investigate catalog (AD-6).
NO_SESSIONS = "No sessions recorded yet — process a signing sheet first."


@dataclass
class SessionDetail:
    """One processed sheet: identity, aggregate counts, and its saved rows."""

    sheet_id: str
    weekday: str  # "" when the Sheet Identifier is not an ISO date
    present: int
    absent: int
    ambiguous: int
    total: int
    rate: int  # 0-100, present / total
    records: tuple[AttendanceRecord, ...]


@dataclass
class HistoryData:
    """Either `sessions` is non-empty (render the history) or `message` is set
    (show the calm no-data copy) — never both, never neither."""

    sessions: list[SessionDetail] = field(default_factory=list)  # newest first
    total_sessions: int = 0
    average_rate: int = 0  # mean of per-session rates
    message: str | None = None


def weekday_of(sheet_id: str) -> str:
    """Long weekday name for an ISO-date Sheet Identifier, "" otherwise —
    a non-date identifier is a display gap, never an error (AD-6)."""
    try:
        return date.fromisoformat(sheet_id).strftime("%A")
    except ValueError:
        return ""


def rate_colour(rate: int) -> str:
    """Rate reading colour (SAMS.dc.html): green ≥80, ochre ≥50, red below —
    the same status hues the chips use, applied to the session-level number."""
    if rate >= 80:
        return "#256E4C"
    if rate >= 50:
        return "#7A6212"
    return "#A63D2A"


def session_details(repository: AttendanceRepository) -> list[SessionDetail]:
    """All saved sessions, oldest first, each with counts + rate + rows.

    Rows within a session keep the repository's stable student-index order.
    Returns [] when nothing is saved yet (including no DB file — checked
    before connecting, so a read-only page never creates one).
    """
    if not repository.db_exists:
        return []
    records = repository.get_attendance()
    by_sheet: dict[str, list[AttendanceRecord]] = {}
    for record in records:
        by_sheet.setdefault(record.sheet_id, []).append(record)

    sessions = []
    for sheet_id in sorted(by_sheet):
        rows = by_sheet[sheet_id]
        present = sum(1 for r in rows if r.status is AttendanceStatus.PRESENT)
        absent = sum(1 for r in rows if r.status is AttendanceStatus.ABSENT)
        ambiguous = sum(1 for r in rows if r.status is AttendanceStatus.AMBIGUOUS)
        total = len(rows)
        sessions.append(
            SessionDetail(
                sheet_id=sheet_id,
                weekday=weekday_of(sheet_id),
                present=present,
                absent=absent,
                ambiguous=ambiguous,
                total=total,
                rate=round(present / total * 100) if total else 0,
                records=tuple(rows),
            )
        )
    return sessions


def history(repository: AttendanceRepository) -> HistoryData:
    """The Session history page's whole read: sessions newest first plus the
    two headline numbers. Every no-data shape yields the one calm message —
    never an exception, never an error tone (AD-6)."""
    sessions = session_details(repository)
    if not sessions:
        return HistoryData(message=NO_SESSIONS)
    newest_first = list(reversed(sessions))
    average = round(sum(s.rate for s in sessions) / len(sessions))
    return HistoryData(
        sessions=newest_first,
        total_sessions=len(sessions),
        average_rate=average,
    )
