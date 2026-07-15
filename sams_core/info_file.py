import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

from sams_core.errors import InputError
from sams_core.models import InfoFile, Session, StudentRecord

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FILENAME_DATE_RE = re.compile(r"^(\d{1,2})[.\-_](\d{1,2})[.\-_](\d{4})$")


def _get_attr(element: ET.Element, name: str) -> str | None:
    value = element.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _validate_iso_date(value: str, source: str) -> str:
    if not _ISO_DATE_RE.match(value):
        raise InputError(f"{source} '{value}' is not a valid ISO 8601 date (YYYY-MM-DD)")
    year, month, day = (int(part) for part in value.split("-"))
    try:
        date(year, month, day)
    except ValueError as exc:
        raise InputError(f"{source} '{value}' is not a valid calendar date") from exc
    return value


def parse_info_file(path: str) -> InfoFile:
    """Parse and validate an Info File against the PRD Appendix A schema."""
    file_path = Path(path)
    if not file_path.is_file():
        raise InputError(f"Info File not found: {path}")

    try:
        root = ET.parse(file_path).getroot()
    except ET.ParseError as exc:
        raise InputError(f"Info File is not valid XML: {path}") from exc

    if root.tag != "subject":
        raise InputError(f"Info File root element must be <subject>, found <{root.tag}>")

    subject_code = _get_attr(root, "code")
    subject_name = _get_attr(root, "name")
    if not subject_code or not subject_name:
        raise InputError("Info File <subject> is missing required 'code' or 'name' attribute")

    session_el = root.find("session")
    if session_el is None:
        raise InputError("Info File is missing the required <session> element")

    session_date = _get_attr(session_el, "date")
    if session_date is not None:
        _validate_iso_date(session_date, "Info File session/@date")

    session = Session(
        subject_code=subject_code,
        subject_name=subject_name,
        date=session_date,
        time=_get_attr(session_el, "time"),
        lecturer=_get_attr(session_el, "lecturer"),
    )

    students_el = root.find("students")
    if students_el is None:
        raise InputError("Info File is missing the required <students> element")

    student_els = students_el.findall("student")
    if not student_els:
        raise InputError("Info File <students> contains no <student> records")

    students = []
    for student_el in student_els:
        no = _get_attr(student_el, "no")
        index = _get_attr(student_el, "index")
        title = _get_attr(student_el, "title")
        name = _get_attr(student_el, "name")
        if not no or not index or not title or not name:
            raise InputError(
                "Info File <student> is missing a required attribute "
                "(no, index, title, name)"
            )
        if not (index.isascii() and index.isdigit()) or len(index) != 8:
            raise InputError(
                f"Info File <student index=\"{index}\"> must be an 8-digit Student Index"
            )
        students.append(StudentRecord(no=no, index=index, title=title, name=name))

    return InfoFile(session=session, students=tuple(students))


def resolve_sheet_identifier(
    info_file: InfoFile,
    date_flag: str | None = None,
    image_path: str | None = None,
) -> str:
    """Resolve the Sheet Identifier: Info File date -> --date flag -> filename stem (AD-11)."""
    if info_file.session.date:
        return info_file.session.date

    if date_flag is not None:
        return _validate_iso_date(date_flag, "--date")

    if image_path:
        stem = Path(image_path).stem
        match = _FILENAME_DATE_RE.search(stem)
        if match:
            day, month, year = match.groups()
            candidate = f"{year}-{int(month):02d}-{int(day):02d}"
            return _validate_iso_date(candidate, f"filename-derived date from '{stem}'")

    raise InputError(
        "Could not resolve a Sheet Identifier: Info File has no session/@date, "
        "no --date flag was given, and the image filename carries no date"
    )
