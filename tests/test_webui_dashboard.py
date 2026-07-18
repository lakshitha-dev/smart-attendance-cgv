"""SAMS.dc.html design (Dashboard landing page): `dashboard_logic` owns every
number (Streamlit-free), the page is a thin adapter over it. Covers the range
presets, per-student rates + low-attendance flags, the signature-alert seam
(patched — the engine's verification is Epic 3's, not re-tested here), the
calm empty state (which must never create a DB file), and headless AppTest
smoke of the page.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from sams_core.models import AttendanceRecord, AttendanceStatus, StudentRecord, VerificationOutcome
from sams_core.repository import AttendanceRepository
from webui.history_logic import NO_SESSIONS
import webui.dashboard_logic as dl

ROOT = Path(__file__).resolve().parent.parent
WEBUI = ROOT / "webui"

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return AttendanceRepository(db_path=tmp_path / "sams.db")


_ROSTER = (("10000409", "001", "Alice"), ("10009301", "002", "Bea"))

# (sheet_id, (Alice's status, Bea's status)) — Alice 4/4, Bea 1/4 (25%).
_SESSIONS = (
    ("2019-05-31", (AttendanceStatus.PRESENT, AttendanceStatus.PRESENT)),
    ("2019-06-21", (AttendanceStatus.PRESENT, AttendanceStatus.ABSENT)),
    ("2019-07-10", (AttendanceStatus.PRESENT, AttendanceStatus.ABSENT)),
    ("2019-07-12", (AttendanceStatus.PRESENT, AttendanceStatus.ABSENT)),
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


# --- load_dashboard / range_view -------------------------------------------------


def test_load_dashboard_empty_db_gives_calm_message_and_creates_no_file(tmp_path):
    db_path = tmp_path / "sams.db"
    data = dl.load_dashboard(AttendanceRepository(db_path=db_path))
    assert data.message == NO_SESSIONS
    assert not db_path.exists(), "a read-only dashboard visit must not create a DB file"


def test_range_view_all_time_rates_flags_and_latest(repo):
    _seed(repo)
    view = dl.range_view(dl.load_dashboard(repo), 0, 3)

    assert view.summary == "All 4 sessions"
    assert view.session_count == 4
    assert view.roster_count == 2
    assert view.average_rate == 62  # (100 + 25) / 2
    assert [f.student_index for f in view.low_attendance] == ["10009301"]
    assert view.low_attendance[0].rate == 25
    assert view.latest.sheet_id == "2019-07-12"


def test_range_view_partial_window_summary_counts_and_spans(repo):
    _seed(repo)
    view = dl.range_view(dl.load_dashboard(repo), 1, 2)
    assert view.summary == "2 sessions · 2019-06-21 → 2019-07-10"


def test_range_view_swaps_an_inverted_window(repo):
    _seed(repo)
    assert dl.range_view(dl.load_dashboard(repo), 2, 1).summary == (
        "2 sessions · 2019-06-21 → 2019-07-10"
    )


def test_range_view_latest_window_reflags_from_that_session_only(repo):
    _seed(repo)
    view = dl.range_view(dl.load_dashboard(repo), 3, 3)

    assert view.summary == "2019-07-12"
    assert view.session_count == 1
    assert [f.student_index for f in view.low_attendance] == ["10009301"]
    assert view.low_attendance[0].rate == 0


def test_range_view_skips_students_with_no_rows_in_range(repo):
    _seed(repo)
    repo.upsert_students([StudentRecord(no="003", index="10009302", title="Ms", name="Cy")])

    view = dl.range_view(dl.load_dashboard(repo), 0, 3)

    assert view.roster_count == 3
    # Cy has no saved rows: missing data is never flagged as low attendance.
    assert [f.student_index for f in view.low_attendance] == ["10009301"]


# --- Signature alerts (seam patched — AD-9: engine logic is Epic 3's) ------------


def test_signature_alerts_flags_only_found_mismatches(repo, monkeypatch):
    _seed(repo)
    fakes = {
        "10000409": SimpleNamespace(
            outcome=VerificationOutcome.FOUND, matched=True, best=SimpleNamespace(score=0.84)
        ),
        "10009301": SimpleNamespace(
            outcome=VerificationOutcome.FOUND, matched=False, best=SimpleNamespace(score=0.49)
        ),
    }
    monkeypatch.setattr(dl, "verify_signature_run", lambda index, _repo: fakes[index])

    alerts = dl.signature_alerts(dl.load_dashboard(repo), repo)

    assert [(a.student_index, a.score) for a in alerts] == [("10009301", 49)]


def test_signature_alerts_treats_no_data_outcomes_as_no_alert(repo, monkeypatch):
    _seed(repo)
    monkeypatch.setattr(
        dl,
        "verify_signature_run",
        lambda index, _repo: SimpleNamespace(outcome=VerificationOutcome.NO_PROBE),
    )
    assert dl.signature_alerts(dl.load_dashboard(repo), repo) == []


# --- Page (headless AppTest) ------------------------------------------------------


def _page(tmp_path, monkeypatch) -> AppTest:
    from sams_core import config

    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "sams.db")
    return AppTest.from_file(str(WEBUI / "pages" / "Dashboard.py"), default_timeout=30)


def test_page_empty_state_prompts_calmly_with_quick_actions(tmp_path, monkeypatch):
    at = _page(tmp_path, monkeypatch).run()
    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    assert NO_SESSIONS in body
    assert "QUICK ACTIONS" in body
    assert any("Mark attendance" in b.label for b in at.button)


def test_page_renders_overview_and_flags(tmp_path, monkeypatch):
    _seed(AttendanceRepository(db_path=tmp_path / "sams.db"))
    monkeypatch.setattr(
        dl,
        "verify_signature_run",
        lambda index, _repo: SimpleNamespace(outcome=VerificationOutcome.NO_PROBE),
    )
    at = _page(tmp_path, monkeypatch).run()

    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    for token in (
        "students on roster",
        "sessions recorded",
        "average attendance",
        "need attention",
        "LATEST SESSION",
        "NEEDS ATTENTION",
    ):
        assert token in body
    labels = {b.label for b in at.button}
    assert "Bea · 25% →" in labels  # low-attendance deep link
    # The DATE RANGE selects span the saved sessions, defaulting to the whole
    # window (summary "All 4 sessions").
    selects = at.selectbox
    assert len(selects) == 2
    assert selects[0].value == "2019-05-31" and selects[1].value == "2019-07-12"
    assert "All 4 sessions" in body
