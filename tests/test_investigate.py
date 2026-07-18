"""CLI adapter tests for investigate.py (Story 3.2): index-form parity, the
plain Match/Mismatch verdict, and AD-6 no-data paths that still exit 0."""

from pathlib import Path

import pytest

import investigate
from sams_core import config
from sams_core.models import StudentRecord
from sams_core.repository import AttendanceRepository

REFERENCES_DIR = config.REFERENCES_DIR
PROBES_DIR = Path(__file__).resolve().parent / "data" / "probes"
_HAS_FIXTURES = REFERENCES_DIR.is_dir() and PROBES_DIR.is_dir()
_needs_fixtures = pytest.mark.skipif(
    not _HAS_FIXTURES, reason="reference/probe fixtures not present"
)


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


def _seed_with_probe(repo, index="10009301", no="002"):
    repo.upsert_students([StudentRecord(no=no, index=index, title="Mr", name="Shehan")])
    repo.register_signature_image(
        index, "2019-07-05", config.SIGNATURE_KIND_PROBE,
        PROBES_DIR / "2019-07-05" / f"{index}.png",
    )


@_needs_fixtures
def test_short_form_and_eight_digit_form_produce_identical_output(repo, capsys):
    _seed_with_probe(repo)

    assert investigate.main(["002"], repository=repo) == 0
    short = capsys.readouterr().out
    assert investigate.main(["10009301"], repository=repo) == 0
    full = capsys.readouterr().out

    assert short == full
    assert "Similarity score:" in short
    assert "10009301" in short


@_needs_fixtures
def test_output_states_a_plain_match_or_mismatch_verdict(repo, capsys):
    _seed_with_probe(repo)
    assert investigate.main(["10009301"], repository=repo) == 0
    out = capsys.readouterr().out
    assert ("Match — this looks like their usual signature." in out) or (
        "Mismatch — this doesn't look like their usual signature." in out
    )
    assert "threshold" in out.lower()


def test_unknown_index_reports_no_data_and_exits_zero(repo, capsys):
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])
    exit_code = investigate.main(["99999999"], repository=repo)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No data found" in captured.out
    assert captured.err == ""


def test_empty_db_reports_no_students_and_exits_zero(repo, capsys):
    exit_code = investigate.main(["002"], repository=repo)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No students in the Local DB yet." in captured.out
    assert captured.err == ""


def test_known_student_without_references_is_calm_no_data(repo, capsys, tmp_path, monkeypatch):
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])
    empty_refs = tmp_path / "references"
    empty_refs.mkdir()
    monkeypatch.setattr(config, "REFERENCES_DIR", empty_refs)

    exit_code = investigate.main(["002"], repository=repo)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No Reference Signatures on file" in captured.out
    assert captured.err == ""


@_needs_fixtures
def test_known_student_with_references_but_no_probe_is_calm_no_data(repo, capsys):
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])
    exit_code = investigate.main(["002"], repository=repo)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No signature to check" in captured.out
    assert captured.err == ""


def test_engine_error_prints_one_line_and_exits_nonzero(repo, capsys, monkeypatch):
    """AD-6/NFR-10: an engine fault reaches the operator as one calm stderr line
    and a deliberate exit code, never a traceback."""
    from sams_core.errors import ProcessingError

    monkeypatch.setattr(
        investigate,
        "verify_signature",
        lambda alias, repository=None: (_ for _ in ()).throw(
            ProcessingError("Local DB unavailable")
        ),
    )
    exit_code = investigate.main(["002"], repository=repo)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Local DB unavailable" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


def test_bad_usage_exits_two(repo, capsys):
    with pytest.raises(SystemExit) as exc:
        investigate.main([], repository=repo)
    assert exc.value.code == 2
