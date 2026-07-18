"""SAMS.dc.html design (Session history page): `history_logic` owns the
grouping/aggregates (Streamlit-free), the page is a thin adapter over it.
Covers the session grouping, ordering, rates, the calm empty state (which
must never create a DB file), and headless AppTest smoke of the page.
"""

from pathlib import Path

import pytest

from sams_core.models import AttendanceRecord, AttendanceStatus, StudentRecord
from sams_core.repository import AttendanceRepository
from webui.history_logic import NO_SESSIONS, history, session_details, weekday_of

ROOT = Path(__file__).resolve().parent.parent
WEBUI = ROOT / "webui"

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


_ROSTER = (("10000409", "001", "Alice"), ("10009301", "002", "Bea"))

# (sheet_id, (Alice's status, Bea's status)) — oldest first.
_SESSIONS = (
    ("2019-05-31", (AttendanceStatus.PRESENT, AttendanceStatus.ABSENT)),
    ("2019-06-21", (AttendanceStatus.PRESENT, AttendanceStatus.PRESENT)),
    ("2019-07-10", (AttendanceStatus.AMBIGUOUS, AttendanceStatus.ABSENT)),
)


def _seed(repo) -> None:
    repo.upsert_students(
        [StudentRecord(no=no, index=index, title="Mr", name=name) for index, no, name in _ROSTER]
    )
    repo.save_attendance(
        [
            AttendanceRecord(
                student_index=index,
                student_name=name,
                sheet_id=sheet_id,
                status=status,
                subject_code="CS402.3",
                subject_name="Computer Graphics",
            )
            for sheet_id, statuses in _SESSIONS
            for (index, _, name), status in zip(_ROSTER, statuses)
        ]
    )


# --- history_logic ------------------------------------------------------------


def test_history_empty_db_gives_calm_message_and_creates_no_file(tmp_path):
    db_path = tmp_path / "sams.db"
    data = history(AttendanceRepository(db_path=db_path))
    assert data.message == NO_SESSIONS
    assert data.sessions == []
    assert not db_path.exists(), "a read-only history view must not create a DB file"


def test_session_details_groups_counts_and_rates(repo):
    _seed(repo)
    sessions = session_details(repo)

    assert [s.sheet_id for s in sessions] == ["2019-05-31", "2019-06-21", "2019-07-10"]
    first, second, third = sessions
    assert (first.present, first.absent, first.ambiguous, first.total) == (1, 1, 0, 2)
    assert first.rate == 50
    assert second.rate == 100
    assert (third.present, third.ambiguous) == (0, 1)
    assert third.rate == 0
    assert [r.student_index for r in first.records] == ["10000409", "10009301"]


def test_history_orders_newest_first_and_averages(repo):
    _seed(repo)
    data = history(repo)

    assert data.message is None
    assert [s.sheet_id for s in data.sessions] == ["2019-07-10", "2019-06-21", "2019-05-31"]
    assert data.total_sessions == 3
    assert data.average_rate == 50  # (50 + 100 + 0) / 3


def test_weekday_of_iso_date_and_non_date():
    assert weekday_of("2019-05-31") == "Friday"
    assert weekday_of("sheet-A") == ""  # a display gap, never an error


# --- Page (headless AppTest) ----------------------------------------------------


def _page(tmp_path, monkeypatch) -> AppTest:
    from sams_core import config

    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "sams.db")
    return AppTest.from_file(str(WEBUI / "pages" / "History.py"), default_timeout=30)


def test_page_empty_state_prompts_calmly(tmp_path, monkeypatch):
    at = _page(tmp_path, monkeypatch).run()
    assert not at.exception
    assert NO_SESSIONS in " ".join(el.value for el in at.markdown)


def test_page_lists_sessions_students_and_chips(tmp_path, monkeypatch):
    _seed(AttendanceRepository(db_path=tmp_path / "sams.db"))
    at = _page(tmp_path, monkeypatch).run()

    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    for token in ("sessions recorded", "average attendance", "ATTENDANCE TREND"):
        assert token in body
    for token in ("Alice", "Bea", "10000409", "10009301", "✓ Present", "✕ Absent"):
        assert token in body
    # Each session renders as a card (summary row in markdown) with a nested
    # Students expander (SAMS design).
    assert [e.label for e in at.expander] == ["Students (2)"] * 3
    assert body.index("2019-07-10") < body.index("2019-06-21") < body.index("2019-05-31")
    assert "1/2 present" in body and "50%" in body
