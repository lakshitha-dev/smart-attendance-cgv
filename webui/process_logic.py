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
from sams_core.repository import AttendanceRepository

# UX-DR8 status chips: icon + label + colour, ALWAYS all three (greyscale-
# survivable). Coloured text/glyph only — no filled backgrounds. Colours are
# the CSS classes injected by app.py; the icon+label carry meaning without them.
STATUS_CHIP = {
    AttendanceStatus.PRESENT: ("✓", "Present", "sams-chip-present"),
    AttendanceStatus.ABSENT: ("✕", "Absent", "sams-chip-absent"),
    AttendanceStatus.AMBIGUOUS: ("?", "Ambiguous", "sams-chip-ambiguous"),
}

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


def mismatch_warnings(result: SheetResult) -> list[str]:
    """The row-count-mismatch flag(s) to surface as a banner ABOVE results
    (UX-DR12: a prominent flag, not a failure). The engine already phrased
    these in error-catalog wording."""
    return list(result.warnings)
