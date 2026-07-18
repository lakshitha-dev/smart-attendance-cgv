"""Dashboard logic (SAMS.dc.html design: the Dashboard landing page): the
Streamlit-free core of the class overview, testable without a Streamlit
runtime.

Reuses `history_logic.session_details` for the session grouping and Epic 3's
`verification.verify_signature` (through a patchable seam, like
`process_logic.process_sheet_run`) for the signature alerts — the dashboard
never re-implements engine logic (AD-1/AD-8/AD-9). Date ranges are index
windows over the saved sessions, mirroring the design's presets. No sqlite,
no Streamlit, no rendering lives here.
"""

from dataclasses import dataclass, field

from sams_core.models import AttendanceStatus, VerificationOutcome
from sams_core.repository import AttendanceRepository
from webui.history_logic import NO_SESSIONS, SessionDetail, session_details
from webui.investigate_logic import display_score

# A student under this attendance rate (0-100) needs attention (SAMS.dc.html).
LOW_ATTENDANCE_THRESHOLD = 75


@dataclass
class StudentRate:
    """One student's attendance rate over the selected range."""

    student_index: str
    no: str | None
    name: str
    rate: int  # 0-100 over the sessions in range they appear on


@dataclass
class SignatureAlert:
    """One student whose latest signature did not match their references."""

    student_index: str
    no: str | None
    name: str
    score: int  # displayed 0-100, same rounding as the Investigate page


@dataclass
class DashboardData:
    """Either `sessions` is non-empty (render the dashboard) or `message` is
    set (show the calm no-data copy) — never both, never neither."""

    sessions: list[SessionDetail] = field(default_factory=list)  # oldest first
    roster: list[dict] = field(default_factory=list)  # list_students shape
    message: str | None = None


@dataclass
class RangeView:
    """The dashboard numbers for one selected session window."""

    range_from: int
    range_to: int
    summary: str  # "All 4 sessions", the single date, or "a → b"
    session_count: int
    roster_count: int
    average_rate: int  # mean of per-student rates in range
    low_attendance: list[StudentRate]
    latest: SessionDetail


def load_dashboard(repository: AttendanceRepository) -> DashboardData:
    """The dashboard's whole read: sessions plus the roster (for `no` short
    forms and names). Every no-data shape yields the one calm message."""
    sessions = session_details(repository)
    if not sessions:
        return DashboardData(message=NO_SESSIONS)
    return DashboardData(sessions=sessions, roster=repository.list_students())


def range_view(data: DashboardData, range_from: int, range_to: int) -> RangeView:
    """Aggregate the loaded sessions over one inclusive index window.

    A student's rate counts only the in-range sessions they appear on (a
    student absent from a roster is missing data, not an Absent); students
    with no rows in range are skipped rather than flagged.
    """
    low = min(range_from, range_to)
    high = max(range_from, range_to)
    in_range = data.sessions[low : high + 1]
    if len(in_range) == len(data.sessions):
        summary = f"All {len(in_range)} sessions"
    elif len(in_range) == 1:
        summary = in_range[0].sheet_id
    else:
        summary = f"{len(in_range)} sessions · {in_range[0].sheet_id} → {in_range[-1].sheet_id}"

    status_by_student: dict[str, list[AttendanceStatus]] = {}
    for session in in_range:
        for record in session.records:
            status_by_student.setdefault(record.student_index, []).append(record.status)

    rates = []
    for student in data.roster:
        statuses = status_by_student.get(student["student_index"])
        if not statuses:
            continue
        present = sum(1 for s in statuses if s is AttendanceStatus.PRESENT)
        rates.append(
            StudentRate(
                student_index=student["student_index"],
                no=student["no"],
                name=student["name"] or student["student_index"],
                rate=round(present / len(statuses) * 100),
            )
        )

    average = round(sum(r.rate for r in rates) / len(rates)) if rates else 0
    return RangeView(
        range_from=low,
        range_to=high,
        summary=summary,
        session_count=len(in_range),
        roster_count=len(data.roster),
        average_rate=average,
        low_attendance=[r for r in rates if r.rate < LOW_ATTENDANCE_THRESHOLD],
        latest=in_range[-1],
    )


def verify_signature_run(student_index: str, repository: AttendanceRepository):
    """Thin seam over the engine call (patchable in tests, AD-9)."""
    from sams_core.verification import verify_signature

    return verify_signature(student_index, repository=repository)


def signature_alerts(
    data: DashboardData, repository: AttendanceRepository
) -> list[SignatureAlert]:
    """Students whose latest probe signature scored below the threshold.

    Runs the SAME engine verification the Investigate page uses, per roster
    student. Every no-data outcome (no references, no probe) simply produces
    no alert — missing data is not a mismatch (AD-6).
    """
    alerts = []
    for student in data.roster:
        result = verify_signature_run(student["student_index"], repository)
        if result.outcome is VerificationOutcome.FOUND and not result.matched:
            alerts.append(
                SignatureAlert(
                    student_index=student["student_index"],
                    no=student["no"],
                    name=student["name"] or student["student_index"],
                    score=display_score(result.best.score),
                )
            )
    return alerts
