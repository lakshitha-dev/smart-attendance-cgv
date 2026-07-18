from pathlib import Path

import pytest

from sams_core.errors import InputError
from sams_core.info_file import parse_info_file, resolve_sheet_identifier

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"
FIXTURES = ROOT / "tests" / "data"


@pytest.mark.parametrize("no", [1, 2, 3, 4, 5])
def test_parse_valid_info_file(no):
    info = parse_info_file(str(SAMPLES / f"{no}.xml"))
    assert len(info.students) == 6
    assert info.session.date is not None
    assert info.students[0].index == "10000409"
    assert info.students[1].no == "002"


def test_parse_missing_file():
    with pytest.raises(InputError, match="not found"):
        parse_info_file(str(SAMPLES / "does_not_exist.xml"))


def test_parse_malformed_xml():
    with pytest.raises(InputError, match="not valid XML"):
        parse_info_file(str(FIXTURES / "info_malformed.xml"))


def test_parse_missing_required_attribute():
    with pytest.raises(InputError, match="missing a required attribute"):
        parse_info_file(str(FIXTURES / "info_missing_attribute.xml"))


def test_parse_empty_students():
    with pytest.raises(InputError, match="no <student> records"):
        parse_info_file(str(FIXTURES / "info_empty_students.xml"))


def test_parse_bad_student_index():
    with pytest.raises(InputError, match="8-digit Student Index"):
        parse_info_file(str(FIXTURES / "info_bad_index.xml"))


def test_parse_whitespace_only_attribute_raises():
    with pytest.raises(InputError, match="missing a required attribute"):
        parse_info_file(str(FIXTURES / "info_whitespace_only.xml"))


def test_parse_non_ascii_digit_index_raises():
    with pytest.raises(InputError, match="8-digit Student Index"):
        parse_info_file(str(FIXTURES / "info_fullwidth_index.xml"))


def test_parse_info_file_without_date():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    assert info.session.date is None
    assert len(info.students) == 2


def test_sheet_identifier_from_session_date():
    info = parse_info_file(str(SAMPLES / "1.xml"))
    assert resolve_sheet_identifier(info) == "2019-05-31"


def test_sheet_identifier_from_date_flag_when_info_file_has_no_date():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    assert resolve_sheet_identifier(info, date_flag="2019-05-31") == "2019-05-31"


def test_sheet_identifier_from_filename_stem_fallback():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    identifier = resolve_sheet_identifier(info, image_path="10.07.2019.png")
    assert identifier == "2019-07-10"


def test_sheet_identifier_session_date_wins_over_date_flag_and_filename():
    info = parse_info_file(str(SAMPLES / "1.xml"))
    identifier = resolve_sheet_identifier(
        info, date_flag="2020-01-01", image_path="10.07.2019.png"
    )
    assert identifier == "2019-05-31"


def test_sheet_identifier_date_flag_wins_over_filename():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    identifier = resolve_sheet_identifier(
        info, date_flag="2020-01-01", image_path="10.07.2019.png"
    )
    assert identifier == "2020-01-01"


def test_sheet_identifier_unresolvable_raises():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    with pytest.raises(InputError, match="Could not resolve a Sheet Identifier"):
        resolve_sheet_identifier(info, image_path="1.jpeg")


def test_sheet_identifier_invalid_date_flag_raises():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    with pytest.raises(InputError, match="not a valid ISO 8601 date"):
        resolve_sheet_identifier(info, date_flag="31/05/2019")


def test_sheet_identifier_empty_date_flag_raises():
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    with pytest.raises(InputError, match="not a valid ISO 8601 date"):
        resolve_sheet_identifier(info, date_flag="")


def test_sheet_identifier_filename_partial_match_raises():
    """AD-11's date fallback must match the whole stem, not a substring within it."""
    info = parse_info_file(str(FIXTURES / "info_no_date.xml"))
    with pytest.raises(InputError, match="Could not resolve a Sheet Identifier"):
        resolve_sheet_identifier(info, image_path="sheet-10.07.2019-v2.png")
