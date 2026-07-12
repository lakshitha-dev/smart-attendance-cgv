from dataclasses import dataclass
from enum import Enum


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
