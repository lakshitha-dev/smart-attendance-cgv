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
