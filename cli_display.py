"""CLI-side stage display helpers (AD-7: rendering lives in the adapter, never the engine).

`sams.py` stays a thin entry script (<50 lines, AD-1); the OpenCV window
mechanics live here. Stage windows are shown live DURING processing (FR-11),
each titled with its stage label, and held until a keypress when a real
operator is attached.

Display is gated on actual GUI availability, not on a stdin heuristic: the
first cv2 window failure (headless build, no display server) disables further
attempts for the run. Set SAMS_HEADLESS=1 to suppress windows explicitly
(the test suite does this via tests/conftest.py).
"""

import os
import sys
from typing import TYPE_CHECKING

import cv2

from sams_core import config
from sams_core.models import (
    AttendanceLookup,
    AttendanceRecord,
    LookupOutcome,
    StageArtifact,
    VerificationOutcome,
    VerificationResult,
)

# Verdict copy verbatim from EXPERIENCE.md (Investigate panel / UJ-3): plain
# language, no jargon, identical wording on the CLI and the Web page (FR-14).
_MATCH_VERDICT = "Match — this looks like their usual signature."
_MISMATCH_VERDICT = (
    "Mismatch — this doesn't look like their usual signature. "
    "Worth checking in person."
)

if TYPE_CHECKING:  # matplotlib stays a deferred import: sams.py must not pay
    from matplotlib.figure import Figure  # its import cost for a type name.

_gui_disabled = os.environ.get("SAMS_HEADLESS") == "1"


def show_stage_live(stage: StageArtifact) -> None:
    """Show one pipeline stage in a titled OpenCV window, without blocking."""
    global _gui_disabled
    if _gui_disabled or stage.image.size == 0:
        return
    display = stage.image if stage.image.ndim == 2 else cv2.cvtColor(stage.image, cv2.COLOR_RGB2BGR)
    scale = min(1.0, config.CLI_MAX_DISPLAY_DIM / max(display.shape[:2]))
    if scale < 1.0:
        display = cv2.resize(display, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    try:
        cv2.namedWindow(stage.label, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(stage.label, display.shape[1], display.shape[0])
        cv2.imshow(stage.label, display)
        cv2.waitKey(1)  # pump the window event loop so the stage appears live
    except cv2.error:
        _gui_disabled = True  # no GUI backend available: keep processing, skip display


def close_windows() -> None:
    """Tear down any open stage windows (also safe when none are open)."""
    if not _gui_disabled:
        cv2.destroyAllWindows()


def hold_windows_until_dismissed() -> None:
    """Keep the stage windows open until a keypress, then close them.

    The blocking wait only makes sense with an operator attached (a TTY);
    otherwise windows are closed immediately.
    """
    if _gui_disabled:
        return
    if sys.stdin.isatty():
        cv2.waitKey(0)
    cv2.destroyAllWindows()


def print_run_summary(result) -> None:
    """Per-student stdout summary after a successful run (UX-DR16).

    `result` is the engine's SheetResult: Attendance Records carry the
    canonical Student Index, name, and first-class status (Ambiguous included).
    The saved-count line reports what was actually written — rows preserved by
    an earlier operator resolution are called out via the engine's warning.
    """
    print(f"Parsed {len(result.records)} Student Records. Sheet Identifier: {result.sheet_id}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for record in result.records:
        print(f"{record.student_index}  {record.student_name}: {record.status.value}")
    saved = result.persisted_count if result.persisted_count is not None else len(result.records)
    print(f"Saved {saved} Attendance Records to the Local DB.")
    print(f"Signature crops: {config.OUTPUT_DIR / str(result.sheet_id) / 'crops'}")


def print_attendance_records(records: list[AttendanceRecord]) -> None:
    """Render one student's Attendance Records for `infovis.py` (Story 2.1, AD-7).

    `records` is the engine's `query_attendance` result: one row per Signing
    Sheet the student appears on, already resolved to the canonical index.
    Operator-resolved rows are marked — an audited hand decision must be
    distinguishable from a machine verdict. Nullable metadata never prints
    as a literal "None".
    """
    if not records:
        return
    name = records[0].student_name or records[0].student_index
    print(f"Attendance for {name} ({records[0].student_index}):")
    for record in records:
        subject = f"  {record.subject_code}" if record.subject_code else ""
        marker = "  [operator-resolved]" if record.resolved_by_operator else ""
        print(f"{record.sheet_id}{subject}: {record.status.value}{marker}")


def show_figure(fig: "Figure") -> None:
    """Display a Matplotlib Figure via `plt.show` (Story 2.2, AD-7: rendering
    stays in the adapter; the engine's `visualization.py` never shows it).

    Shares the OpenCV helpers' gating (SAMS_HEADLESS + the runtime
    `_gui_disabled` flag), degrades gracefully when no GUI backend exists,
    and ALWAYS closes the figure afterwards — pyplot's global registry must
    not accumulate figures across calls.
    """
    global _gui_disabled
    import matplotlib.pyplot as plt

    try:
        if _gui_disabled or os.environ.get("SAMS_HEADLESS") == "1":
            return
        try:
            plt.figure(fig.number)  # make the PASSED figure the active one
            plt.show()
        except Exception:
            _gui_disabled = True  # no GUI backend: keep going, skip display
    finally:
        plt.close(fig)


def _student_listing(students: list[dict], limit: int = 12) -> str:
    """Short-form + 8-digit listing (`001 (10000409)`), honestly truncated."""
    shown = ", ".join(
        f"{(s['no'] or s['student_index'])} ({s['student_index']})" for s in students[:limit]
    )
    extra = len(students) - limit
    return shown + (f", … and {extra} more" if extra > 0 else "")


def display_score(score: float) -> int:
    """Normalize an engine similarity score (0-1) to the displayed 0-100 scale.

    Display-side only (UX assumption): the stored score and threshold stay 0-1.
    Both the CLI and the Web page round the same way so the shown numbers match.
    """
    return round(score * 100)


def print_verification_result(result: VerificationResult) -> None:
    """Present an `investigate.py` verdict (Story 3.2, AD-7/AD-9).

    On FOUND: the numeric similarity score (0-100), the threshold, and the plain
    Match/Mismatch sentence — same score and outcome the Web page shows (FR-14).
    Every no-data outcome gets its own calm copy (AD-6) and exits 0 upstream.
    """
    if result.outcome is VerificationOutcome.FOUND:
        who = result.student_name or result.student_index
        print(f"Signature check for {who} ({result.student_index}):")
        print(
            f"Similarity score: {display_score(result.best.score)} / 100 "
            f"(threshold {display_score(result.threshold)})"
        )
        print(_MATCH_VERDICT if result.matched else _MISMATCH_VERDICT)
        print(
            f"Compared against the best of {len(result.all_scores)} "
            f"Reference Signature(s); probe from sheet {result.probe_sheet_id}."
        )
        return

    if result.outcome is VerificationOutcome.EMPTY_DB:
        print("No students in the Local DB yet. Process a signing sheet first (sams.py).")
    elif result.outcome is VerificationOutcome.AMBIGUOUS:
        print(
            f"'{result.alias}' matches more than one student: "
            f"{', '.join(result.candidates)}."
        )
        print("Use the 8-digit Student Index to pick one.")
    elif result.outcome is VerificationOutcome.NO_REFERENCES:
        who = result.student_name or result.student_index
        print(
            f"No Reference Signatures on file for {who} ({result.student_index}) — "
            f"add images to references/{result.student_index}/ first."
        )
    elif result.outcome is VerificationOutcome.NO_PROBE:
        who = result.student_name or result.student_index
        print(
            f"No signature to check for {who} ({result.student_index}) yet — "
            "process a signing sheet they appear on first."
        )
    else:  # UNKNOWN
        print(f"No data found for index '{result.alias}'.")
        if result.valid_students:
            print(f"Valid indices: {_student_listing(list(result.valid_students))}")


def print_lookup_outcome(lookup: AttendanceLookup) -> None:
    """Present a no-data lookup outcome (AD-6): each shape gets ITS OWN copy —
    unknown, ambiguous, known-but-empty, and empty-DB are different operator
    situations, and a friendly tone must never misdiagnose one as another.
    """
    if lookup.outcome is LookupOutcome.EMPTY_DB:
        print("No students in the Local DB yet. Process a signing sheet first (sams.py).")
    elif lookup.outcome is LookupOutcome.AMBIGUOUS:
        print(
            f"'{lookup.alias}' matches more than one student: "
            f"{', '.join(lookup.candidates)}."
        )
        print("Use the 8-digit Student Index to pick one.")
    elif lookup.outcome is LookupOutcome.NO_ATTENDANCE:
        print(
            f"'{lookup.alias}' is on the roster but has no attendance saved yet — "
            "process their signing sheet first."
        )
    else:  # UNKNOWN
        print(f"No data found for index '{lookup.alias}'.")
        if lookup.valid_students:
            print(f"Valid indices: {_student_listing(list(lookup.valid_students))}")
