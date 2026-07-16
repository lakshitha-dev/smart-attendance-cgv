import pytest
from matplotlib.figure import Figure

import infovis
from sams_core.models import AttendanceRecord, AttendanceStatus, StudentRecord
from sams_core.repository import AttendanceRepository


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


def _seed(repo):
    repo.upsert_students([StudentRecord(no="001", index="10000409", title="Mr", name="Alice")])
    repo.save_attendance(
        [
            AttendanceRecord(
                student_index="10000409",
                student_name="Alice",
                sheet_id="2019-05-31",
                status=AttendanceStatus.PRESENT,
                subject_code="CS402.3",
                subject_name="Computer Graphics",
            )
        ]
    )


def test_main_short_form_and_eight_digit_form_return_identical_output(repo, capsys):
    _seed(repo)

    exit_code_short = infovis.main(["001"], repository=repo)
    captured_short = capsys.readouterr().out

    exit_code_long = infovis.main(["10000409"], repository=repo)
    captured_long = capsys.readouterr().out

    assert exit_code_short == 0
    assert exit_code_long == 0
    assert captured_short == captured_long
    assert "10000409" in captured_short
    assert "Present" in captured_short


def test_main_unknown_index_reports_no_data_and_exits_zero(repo, capsys):
    _seed(repo)

    exit_code = infovis.main(["999"], repository=repo)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No data" in captured.out
    assert "001 (10000409)" in captured.out
    assert captured.err == ""


def test_main_empty_db_reports_no_students_and_exits_zero(repo, capsys):
    exit_code = infovis.main(["001"], repository=repo)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No students in the Local DB yet." in captured.out
    assert captured.err == ""


def test_main_shows_attendance_timeline_figure_for_known_index(repo, monkeypatch):
    _seed(repo)
    shown = []
    monkeypatch.setattr(infovis, "show_figure", lambda fig: shown.append(fig))

    exit_code = infovis.main(["001"], repository=repo)

    assert exit_code == 0
    assert len(shown) == 1
    assert isinstance(shown[0], Figure)


def test_main_does_not_render_figure_for_unknown_index(repo, monkeypatch):
    _seed(repo)
    shown = []
    monkeypatch.setattr(infovis, "show_figure", lambda fig: shown.append(fig))

    exit_code = infovis.main(["999"], repository=repo)

    assert exit_code == 0
    assert shown == []


def test_main_ambiguous_ordinal_names_candidates_and_exits_zero(repo, capsys):
    """Two rosters sharing no='001': the CLI must present ambiguity as its own
    situation — never 'no data' for an alias that matches real students."""
    _seed(repo)
    repo.upsert_students([StudentRecord(no="001", index="20000001", title="Ms", name="Bea")])

    exit_code = infovis.main(["001"], repository=repo)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "more than one student" in captured.out
    assert "10000409" in captured.out and "20000001" in captured.out
    assert "8-digit" in captured.out
    assert captured.err == ""


def test_main_known_student_without_attendance_is_not_reported_as_invalid(repo, capsys):
    repo.upsert_students([StudentRecord(no="001", index="10000409", title="Mr", name="Alice")])

    exit_code = infovis.main(["001"], repository=repo)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "no attendance saved yet" in captured.out
    assert "No data found" not in captured.out  # the index is NOT invalid
    assert captured.err == ""


def test_main_whitespace_padded_alias_resolves(repo, capsys):
    _seed(repo)
    exit_code = infovis.main(["  001  "], repository=repo)
    assert exit_code == 0
    assert "Present" in capsys.readouterr().out


def test_main_operator_resolved_rows_carry_a_marker(repo, capsys):
    _seed(repo)
    from sams_core.models import AttendanceStatus as S

    assert repo.resolve("2019-05-31", "10000409", S.ABSENT) is True

    infovis.main(["001"], repository=repo)

    assert "[operator-resolved]" in capsys.readouterr().out


def test_main_engine_error_prints_one_line_and_exits_nonzero(repo, capsys, monkeypatch):
    """AD-6/NFR-10: a locked or corrupt DB must reach the operator as one calm
    stderr line + a deliberate exit code, never a traceback."""
    from sams_core.errors import ProcessingError

    monkeypatch.setattr(
        type(repo),
        "query_attendance",
        lambda self, alias: (_ for _ in ()).throw(ProcessingError("Local DB unavailable")),
    )

    exit_code = infovis.main(["001"], repository=repo)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Local DB unavailable" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


def test_cli_exit_codes_pinned_at_the_subprocess_boundary(tmp_path):
    """The real process contract: 0 for a no-data lookup (AD-6), 2 for bad usage."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    env = {
        **os.environ,
        "SAMS_HEADLESS": "1",
        "PYTHONIOENCODING": "utf-8",
        "SAMS_DB_PATH": str(tmp_path / "sams.db"),
    }
    ok = subprocess.run(
        [sys.executable, str(root / "infovis.py"), "001"],
        capture_output=True, text=True, encoding="utf-8", timeout=120, env=env, cwd=str(root),
    )
    assert ok.returncode == 0
    assert "No students in the Local DB yet" in ok.stdout

    bad_usage = subprocess.run(
        [sys.executable, str(root / "infovis.py")],
        capture_output=True, text=True, encoding="utf-8", timeout=120, env=env, cwd=str(root),
    )
    assert bad_usage.returncode == 2
