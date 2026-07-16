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
