from pathlib import Path

import pytest

import sams
from sams_core.errors import ProcessingError

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"
FIXTURES = ROOT / "tests" / "data"


def test_main_valid_inputs_exits_zero(capsys):
    exit_code = sams.main([str(SAMPLES / "1.jpeg"), str(SAMPLES / "1.xml")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "6 Student Records" in captured.out
    assert "2019-05-31" in captured.out


def test_main_missing_image_exits_two_with_stderr(capsys):
    exit_code = sams.main([str(SAMPLES / "missing.jpeg"), str(SAMPLES / "1.xml")])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.err.strip() != ""
    assert captured.out == ""


def test_main_invalid_info_file_exits_two_with_stderr(capsys):
    exit_code = sams.main([str(SAMPLES / "1.jpeg"), str(FIXTURES / "info_malformed.xml")])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.err.strip() != ""


def test_main_date_flag_used_when_info_file_lacks_date(capsys):
    exit_code = sams.main(
        [
            str(SAMPLES / "1.jpeg"),
            str(FIXTURES / "info_no_date.xml"),
            "--date",
            "2019-05-31",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "2019-05-31" in captured.out


def test_main_never_raises_raw_exception(capsys):
    """AD-6: only SamsError -> stderr/exit; no stack trace escapes main()."""
    exit_code = sams.main([str(SAMPLES / "missing.jpeg"), str(FIXTURES / "missing.xml")])
    assert exit_code == 2


def test_main_processing_error_exits_one(monkeypatch, capsys):
    def _raise_processing_error(*args, **kwargs):
        raise ProcessingError("pipeline exploded")

    monkeypatch.setattr(sams, "parse_info_file", _raise_processing_error)

    exit_code = sams.main([str(SAMPLES / "1.jpeg"), str(SAMPLES / "1.xml")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "pipeline exploded" in captured.err


def test_main_unexpected_exception_exits_one_no_traceback(monkeypatch, capsys):
    def _raise_unexpected(*args, **kwargs):
        raise RuntimeError("something nobody expected")

    monkeypatch.setattr(sams, "parse_info_file", _raise_unexpected)

    exit_code = sams.main([str(SAMPLES / "1.jpeg"), str(SAMPLES / "1.xml")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "something nobody expected" in captured.err
    assert "Traceback" not in captured.err
