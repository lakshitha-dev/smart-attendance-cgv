"""Process page logic (Stories 4.2/4.3, FR-12/FR-13/AD-12): the Streamlit-free
core of the one-tap processing flow, kept testable without a Streamlit runtime.

The engine owns everything real — `parse_info_file_bytes` validates the Info
File, `resolve_sheet_identifier` fixes the Sheet Identifier (AD-11: the Web UI
NEVER falls back to the upload filename), `has_operator_resolutions` is the
pre-Process safety check (AD-4), and `process_sheet` does all detection and
persistence in one call (AD-12). This module only sequences those calls and
maps engine `InputError`s to the verbatim UX-DR12 error-catalog copy. No cv2,
no sqlite, no Streamlit.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sams_core.errors import InputError, SamsError
from sams_core.image_io import load_image_bytes
from sams_core.info_file import parse_info_file_bytes, resolve_sheet_identifier
from sams_core.models import AttendanceRecord, AttendanceStatus, InfoFile, SheetResult
from sams_core.pipeline import STAGE_COUNT
from sams_core.repository import AttendanceRepository

__all__ = [
    "STAGE_COUNT",
    "STATUS_CHIP",
    "MUTED_INK",
    "BAD_IMAGE",
    "BAD_INFO_FILE",
    "BAD_DATE",
    "GENERIC_FAILURE",
    "OVERWRITE_PROMPT",
    "ParsedInfo",
    "ProcessOutcome",
    "parse_info",
    "check_image",
    "run_process",
    "needs_overwrite",
    "results_summary",
    "result_banners",
    "saved_rows",
    "resolve_row",
    "undo_row",
    "HAIRLINE",
    "AMBIGUOUS_FILL",
    "AMBIGUOUS_BORDER",
    "AMBIGUOUS_QUESTION",
    "ALL_RESOLVED",
]

# UX-DR8 status chips: icon + label + colour, ALWAYS all three (greyscale-
# survivable). Coloured text/glyph only — no filled backgrounds. The exact hex
# is carried here so the chip can render its colour INLINE (independent of the
# app.py CSS classes), which also lets a page render coloured chips standalone.
STATUS_CHIP = {
    AttendanceStatus.PRESENT: ("✓", "Present", "#256E4C"),
    AttendanceStatus.ABSENT: ("✕", "Absent", "#A63D2A"),
    AttendanceStatus.AMBIGUOUS: ("?", "Ambiguous", "#7A6212"),
}
MUTED_INK = "#7B818A"  # DESIGN.md ink-muted: overline + current-stage caption
HAIRLINE = "#E9E8E3"  # neutral outline for resolve buttons (NO status colour)

# UX-DR9 Ambiguous-row treatment + verbatim copy.
AMBIGUOUS_FILL = "#FDFBF2"  # pale straw
AMBIGUOUS_BORDER = "#E3D9B4"  # ochre
AMBIGUOUS_QUESTION = "We couldn't read this signature clearly. Which is right?"
ALL_RESOLVED = "All done. Every student on this sheet is marked."

# UX-DR12 error catalog, verbatim.
BAD_IMAGE = (
    "We couldn't read that file as a photo. "
    "Please add a JPEG or PNG of the Signing Sheet."
)
BAD_INFO_FILE = (
    "This info file doesn't look right — we couldn't find the student list in it. "
    "Check it's the info.xml for this class."
)
BAD_DATE = (
    "This sheet's info file has no session date, so please enter the session "
    "date (YYYY-MM-DD) before processing."
)
GENERIC_FAILURE = "Something went wrong while processing that sheet. Your files are still here."

# UX-DR5 overwrite copy, verbatim.
OVERWRITE_PROMPT = "You've already fixed some answers for this sheet by hand."


@dataclass
class ParsedInfo:
    """Outcome of validating the uploaded Info File before Process is armed."""

    info_file: InfoFile | None = None
    sheet_id: str | None = None
    needs_date: bool = False  # Info File carries no session date (AD-11)
    error: str | None = None


@dataclass
class ProcessOutcome:
    """Outcome of a Process run (or the pre-run overwrite gate)."""

    result: SheetResult | None = None
    error: str | None = None
    needs_overwrite_choice: bool = False
    sheet_id: str | None = None


def parse_info(info_bytes: bytes, session_date: str | None = None) -> ParsedInfo:
    """Validate the uploaded Info File and resolve its Sheet Identifier.

    `session_date` is the operator-entered date, used ONLY when the Info File
    itself carries no session date (AD-11). Returns UX-catalog copy on failure.
    """
    try:
        info_file = parse_info_file_bytes(info_bytes)
    except InputError as exc:
        # A dated Info File with an impossible date raises here too — route it
        # to the date-catalog copy, not "we couldn't find the student list".
        message = BAD_DATE if "date" in str(exc).lower() else BAD_INFO_FILE
        return ParsedInfo(error=message)
    except Exception:
        # Never let a hostile/malformed document escape as a raw traceback.
        return ParsedInfo(error=BAD_INFO_FILE)

    if info_file.session.date:
        return ParsedInfo(info_file=info_file, sheet_id=info_file.session.date)

    if not session_date:
        return ParsedInfo(info_file=info_file, needs_date=True, error=None)

    try:
        # date_flag path — NEVER image_path (the Web UI must not use the filename).
        sheet_id = resolve_sheet_identifier(info_file, date_flag=session_date)
    except InputError:
        return ParsedInfo(info_file=info_file, needs_date=True, error=BAD_DATE)
    return ParsedInfo(info_file=info_file, sheet_id=sheet_id, needs_date=True)


def check_image(image_bytes: bytes) -> str | None:
    """Validate the uploaded photo at decode level so the page can show a
    SLOT-level error before Process (UX-DR12 item #1), reusing the engine's
    own decoder. Returns catalog copy on failure, else None. Decode-level only:
    a dim or skewed photo decodes fine and proceeds."""
    try:
        load_image_bytes(image_bytes)
        return None
    except InputError:
        return BAD_IMAGE


def run_process(
    image_bytes: bytes,
    parsed: ParsedInfo,
    repository: AttendanceRepository,
    overwrite: bool = False,
    overwrite_decided: bool = False,
    on_stage=None,
) -> ProcessOutcome:
    """Process one uploaded sheet exactly once (the caller owns the rerun fence).

    Guards the destructive re-process (UX-DR5/AD-4): if the Sheet Identifier
    already carries operator resolutions and the operator has not yet chosen,
    returns `needs_overwrite_choice` and does NOT process. Maps engine errors
    to UX-catalog copy; the pipeline itself persists atomically (AD-12).
    """
    if parsed.info_file is None or parsed.sheet_id is None:
        # sheet_id is None only in the needs-a-date state (info parsed OK).
        fallback = BAD_DATE if parsed.needs_date else BAD_INFO_FILE
        return ProcessOutcome(error=parsed.error or fallback)

    # Validate the photo up front so an image failure is unambiguous (no more
    # guessing from an exception message); also catches an empty upload.
    image_error = check_image(image_bytes)
    if image_error:
        return ProcessOutcome(error=image_error, sheet_id=parsed.sheet_id)

    try:
        if not overwrite_decided and repository.has_operator_resolutions(parsed.sheet_id):
            return ProcessOutcome(needs_overwrite_choice=True, sheet_id=parsed.sheet_id)

        result = process_sheet_run(
            image_bytes, parsed, repository, overwrite=overwrite, on_stage=on_stage
        )
        return ProcessOutcome(result=result, sheet_id=parsed.sheet_id)
    except SamsError:
        # Image + Info File are already validated, so a failure here is a
        # processing/persistence fault — one calm page-level message (AD-6).
        return ProcessOutcome(error=GENERIC_FAILURE, sheet_id=parsed.sheet_id)
    except Exception:
        # Defensive: nothing raw ever reaches the browser (UX-DR12).
        return ProcessOutcome(error=GENERIC_FAILURE, sheet_id=parsed.sheet_id)


def process_sheet_run(image_bytes, parsed, repository, overwrite, on_stage):
    """Thin seam over the engine call (patchable in tests)."""
    from sams_core.pipeline import process_sheet

    return process_sheet(
        image_bytes,
        parsed.info_file,
        sheet_id_override=parsed.sheet_id,
        overwrite=overwrite,
        on_stage=on_stage,
        repository=repository,
    )


def results_summary(records: Sequence[AttendanceRecord]) -> str:
    """UX-DR7 summary line: "42 students checked. One needs a quick look from
    you." Ambiguous rows are the ones that need a look; Present/Absent are
    settled."""
    total = len(records)
    ambiguous = sum(1 for r in records if r.status is AttendanceStatus.AMBIGUOUS)
    noun = "student" if total == 1 else "students"
    line = f"{total} {noun} checked."
    if ambiguous == 1:
        line += " One needs a quick look from you."
    elif ambiguous > 1:
        line += f" {ambiguous} need a quick look from you."
    return line


def result_banners(result: SheetResult) -> list[str]:
    """Non-fatal notices to surface as flag banners ABOVE the results list
    (UX-DR12: prominent flags, not failures) — the row-count-mismatch line and
    the preserved-resolutions note the engine records in `warnings`, already in
    catalog wording."""
    return list(result.warnings)


def needs_overwrite(parsed: "ParsedInfo", repository: AttendanceRepository) -> bool:
    """Pre-flight check (AD-4): does this Sheet Identifier already carry operator
    resolutions? Lets the page raise the UX-DR5 gate BEFORE it starts streaming,
    so a sheet awaiting a Keep/Overwrite choice never flashes a processing strip."""
    if parsed.sheet_id is None:
        return False
    return repository.has_operator_resolutions(parsed.sheet_id)


def saved_rows(sheet_id: str, repository: AttendanceRepository) -> list[AttendanceRecord]:
    """The sheet's Attendance Records as CURRENTLY persisted (UX-DR7: the row
    list reflects saved DB state, so an operator resolution flips its row)."""
    return repository.get_attendance(sheet_id=sheet_id)


def resolve_row(
    sheet_id: str, student_index: str, present: bool, repository: AttendanceRepository
) -> bool:
    """Operator resolution of one Ambiguous row (AD-4, Story 4.4). Marks
    `resolved_by_operator` so 1.5's survival rule protects it from re-processing.
    Returns whether a row actually matched."""
    status = AttendanceStatus.PRESENT if present else AttendanceStatus.ABSENT
    return repository.resolve(sheet_id, student_index, status, by_operator=True)


def undo_row(sheet_id: str, student_index: str, repository: AttendanceRepository) -> bool:
    """Undo an operator resolution: restore Ambiguous and clear the flag (AD-4)."""
    return repository.undo_resolution(sheet_id, student_index)
