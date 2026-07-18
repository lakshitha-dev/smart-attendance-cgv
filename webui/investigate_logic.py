"""Investigate page logic (Story 4.6, FR-14/AD-9): the only piece of the
Investigate page that isn't a bare widget call, kept Streamlit-free so it is
testable without a Streamlit runtime.

`investigate()` reuses Epic 3's `verification.verify_signature` — the same
single engine call `investigate.py` makes — so the CLI and the browser return
the identical score, threshold, and best-match selection (data-layer parity,
FR-14). Best-match selection already happened in the engine (AD-9); this module
never re-implements it. Each no-data outcome gets its own calm copy: unknown,
ambiguous, no references, no probe, and empty-DB are different operator
situations (AD-6). No image loading or chart logic lives here.
"""

from dataclasses import dataclass

from sams_core.models import VerificationOutcome, VerificationResult
from sams_core.repository import AttendanceRepository
from sams_core.verification import verify_signature

# Verdict copy verbatim from EXPERIENCE.md (Investigate panel / UJ-3) — the same
# sentences investigate.py prints, so CLI and browser read identically (FR-14).
_MATCH_VERDICT = "Match — this looks like their usual signature."
_MISMATCH_VERDICT = (
    "Mismatch — this doesn't look like their usual signature. "
    "Worth checking in person."
)
_NO_DATA_PREFIX = "We don't have a signature to check for that number."
_LISTING_LIMIT = 12


@dataclass
class InvestigateResult:
    """Either `result` is a FOUND `VerificationResult` (render the panel) or
    `message` is set (show the calm no-data copy) — never both, never neither."""

    result: VerificationResult | None = None
    message: str | None = None


def display_score(score: float) -> int:
    """Engine similarity score (0-1) -> displayed 0-100 (UX assumption, display
    side only; the stored score and threshold stay 0-1). Rounds the same way as
    the CLI so both surfaces show the same number (FR-14)."""
    return round(score * 100)


def verdict_sentence(matched: bool) -> str:
    """The plain Match/Mismatch sentence for a scored result (verbatim copy)."""
    return _MATCH_VERDICT if matched else _MISMATCH_VERDICT


def _listing(students, limit: int = _LISTING_LIMIT) -> str:
    """Short-form + 8-digit listing, ellipsis ONLY when actually truncated."""
    shown = ", ".join(
        f"{(s['no'] or s['student_index'])} ({s['student_index']})" for s in students[:limit]
    )
    extra = len(students) - limit
    return shown + (f" … and {extra} more" if extra > 0 else "")


def investigate(alias: str, repository: AttendanceRepository) -> InvestigateResult:
    """Verify `alias` (either index form) and package it for the page.

    FOUND yields the `VerificationResult` for side-by-side rendering; every
    no-data shape yields outcome-specific copy (AD-6), never an exception.
    """
    result = verify_signature(alias, repository=repository)

    if result.outcome is VerificationOutcome.FOUND:
        return InvestigateResult(result=result)

    if result.outcome is VerificationOutcome.EMPTY_DB:
        return InvestigateResult(
            message="No students in the local database yet — process a signing sheet first."
        )

    if result.outcome is VerificationOutcome.AMBIGUOUS:
        return InvestigateResult(
            message=(
                "That short number matches more than one student — "
                f"use the 8-digit index: {', '.join(result.candidates)}."
            )
        )

    if result.outcome is VerificationOutcome.NO_REFERENCES:
        return InvestigateResult(
            message=(
                f"We don't have any Reference Signatures on file for {result.student_index} yet — "
                "add known-good samples before checking this signature."
            )
        )

    if result.outcome is VerificationOutcome.NO_PROBE:
        return InvestigateResult(
            message=(
                f"That student ({result.student_index}) has no signature to check yet — "
                "process a signing sheet they appear on first."
            )
        )

    # UNKNOWN
    students = list(result.valid_students)
    if not students:
        return InvestigateResult(message=_NO_DATA_PREFIX)
    return InvestigateResult(
        message=f"{_NO_DATA_PREFIX} Students we do know: {_listing(students)}"
    )
