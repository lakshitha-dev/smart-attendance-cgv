from dataclasses import dataclass
from enum import Enum

import numpy as np


class AttendanceStatus(Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    AMBIGUOUS = "Ambiguous"


@dataclass(frozen=True)
class StudentRecord:
    """One row of the Info File `students` table (PRD Appendix A)."""

    no: str  # row ordinal / short CLI alias, e.g. "001"
    index: str  # 8-digit Student Index, e.g. "10009301"
    title: str
    name: str


@dataclass(frozen=True)
class Session:
    """Subject + Session metadata from the Info File (PRD Appendix A)."""

    subject_code: str
    subject_name: str
    date: str | None  # ISO 8601, or None if the Info File omits it
    time: str | None = None
    lecturer: str | None = None


@dataclass(frozen=True)
class InfoFile:
    """Parsed Info File: Session metadata + Student Records."""

    session: Session
    students: tuple[StudentRecord, ...]


@dataclass(frozen=True)
class AttendanceRecord:
    """One student's attendance outcome for one Signing Sheet (FR-5, AD-2).

    Carries the Session/Subject metadata alongside the classification so a
    persisted Attendance Record is self-describing. `student_index` is always
    the canonical 8-digit Student Index (AD-4). `status` is first-class:
    Ambiguous is never coerced to Present/Absent.
    """

    student_index: str
    student_name: str
    sheet_id: str
    status: AttendanceStatus
    subject_code: str
    subject_name: str
    session_time: str | None = None
    lecturer: str | None = None
    resolved_by_operator: bool = False


@dataclass(frozen=True)
class StageArtifact:
    """One labelled pipeline stage frame (PRD FR-11/FR-16, AD-2/AD-3).

    `image` is display-ready uint8: 2D greyscale or 3-channel RGB (never BGR) —
    adapters own any toolkit-specific conversion (CLI/`artifacts.py` convert
    RGB->BGR for cv2, `st.image` consumes RGB as-is).
    """

    order: int
    slug: str  # glossary-verbatim, e.g. "greyscale" — used in filenames and window titles
    label: str  # glossary-verbatim display name, e.g. "Greyscale"
    image: np.ndarray


@dataclass
class SheetResult:
    """Result of processing a single signed-in sheet (Story 1.3/1.4).

    Tracks detected table structure, warnings (e.g., row-count mismatch),
    and cell-level ROI data for signature verification.
    """

    warnings: list[str]  # e.g., ["Detected 5 rows, Info File has 6 students"]
    detected_row_count: int  # dynamic count of STUDENT rows (header excluded)
    metadata_row_y_range: tuple[int, int] | None  # (y0, y1) of the 4-column metadata row
    student_table_y_range: tuple[int, int] | None  # (y0, y1) of the 5-column student table
    # internal: "mask" = printed-grid pixels (table lines only, image-sized);
    # "h_lines"/"v_lines" = the SELECTED STUDENT TABLE's lines (not sheet-global).
    detected_grid_lines: dict
    # Published only for a trusted 5-column table: {"rows": [(y0, y1)...] student
    # rows in order (header excluded), "signature_column": (x0, x1), "table_bbox"}.
    cell_rois: dict | None = None
    # Story 1.5 (additive, defaults required so 1.3/1.4 constructions keep working):
    sheet_id: str | None = None  # resolved Sheet Identifier (AD-11)
    records: tuple["AttendanceRecord", ...] = ()  # one per Student Record (FR-5)
    persisted_count: int | None = None  # attendance rows actually written this run
    preserved_count: int | None = None  # rows kept because of operator resolutions


class LookupOutcome(Enum):
    """Why a lookup returned what it did (Story 2.1 review fix): the four
    no-data shapes are DISTINCT operator situations and must never collapse
    into one message (AD-6 locates the no-data payload engine-side)."""

    FOUND = "found"
    NO_ATTENDANCE = "no-attendance"  # student on a roster, zero attendance rows
    UNKNOWN = "unknown"  # alias resolves to no known student
    AMBIGUOUS = "ambiguous"  # short ordinal matches more than one student
    EMPTY_DB = "empty-db"  # no students ingested yet (or no DB file at all)


class VerificationOutcome(Enum):
    """Why signature verification returned what it did (Story 3.2, AD-6/AD-9).

    Like `LookupOutcome`, the no-data shapes are DISTINCT operator situations
    and must never collapse into one message: an unknown index, a known student
    with no Reference Signatures, and a known student with no probe crop each
    call for their own calm copy. Only FOUND carries a comparable score."""

    FOUND = "found"  # references + a probe crop exist; a score was computed
    NO_REFERENCES = "no-references"  # known student, references/<index>/ empty or missing
    NO_PROBE = "no-probe"  # known student with references, but no probe crop yet
    UNKNOWN = "unknown"  # alias resolves to no known student
    AMBIGUOUS = "ambiguous"  # short ordinal matches more than one student
    EMPTY_DB = "empty-db"  # no students ingested yet (or no DB file at all)


@dataclass(frozen=True)
class ReferenceScore:
    """One probe-vs-Reference-Signature comparison (Story 3.2, AD-9).

    `score` is normalized to 0-1 with HIGHER = more similar; any distance metric
    is inverted inside `verification.py` before it becomes a `ReferenceScore`.
    `sheet_id` is the reference's source Sheet Identifier (its filename stem),
    kept so the report can prove the reference/probe split stayed disjoint (SM-4).
    """

    reference_path: str
    sheet_id: str | None
    score: float  # 0-1, higher = more similar


@dataclass(frozen=True)
class VerificationResult:
    """Typed result of `verification.verify_signature` (Story 3.2, AD-9/AD-6).

    Best-match selection happens INSIDE the engine (the frontends never
    re-implement match logic): `best` is the highest-scoring `ReferenceScore`
    and `all_scores` holds every comparison, sorted best-first. `matched` is
    exactly `best.score >= threshold`. For every no-data `outcome`, `best`/
    `all_scores` are empty and the no-data carriers (`candidates`,
    `valid_students`) let adapters render the retry hint without a second call.
    """

    alias: str
    outcome: VerificationOutcome
    student_index: str | None = None
    student_name: str | None = None
    probe_path: str | None = None
    probe_sheet_id: str | None = None
    best: ReferenceScore | None = None
    all_scores: tuple[ReferenceScore, ...] = ()
    matched: bool = False
    threshold: float = 0.0
    candidates: tuple[str, ...] = ()  # populated only for AMBIGUOUS
    valid_students: tuple[dict, ...] = ()  # roster listing for the no-data retry hint


@dataclass(frozen=True)
class AttendanceLookup:
    """Typed result of `repository.query_attendance` (AD-2/AD-6).

    `records` is populated only for FOUND. `candidates` carries the canonical
    indices an AMBIGUOUS ordinal matched. `valid_students` carries the roster
    listing (list_students shape) for the no-data outcomes so adapters never
    make a second engine call to present the retry hint.
    """

    alias: str
    outcome: LookupOutcome
    records: tuple[AttendanceRecord, ...] = ()
    candidates: tuple[str, ...] = ()
    valid_students: tuple[dict, ...] = ()
