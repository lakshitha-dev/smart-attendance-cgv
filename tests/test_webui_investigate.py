"""Story 4.6 — the Web Investigate page and its Streamlit-free logic.

Covers `investigate_logic.investigate` (both index forms, every no-data shape),
CLI/Web verdict + score parity (FR-14), and the real Streamlit page headlessly.
"""

from pathlib import Path

import pytest

from sams_core import config
from sams_core.models import StudentRecord
from sams_core.repository import AttendanceRepository
from webui.investigate_logic import display_score, investigate, verdict_sentence

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


# --- investigate() pure logic -------------------------------------------------


@_needs_fixtures
def test_investigate_found_returns_result_not_message(repo):
    _seed_with_probe(repo)
    outcome = investigate("10009301", repo)
    assert outcome.message is None
    assert outcome.result is not None
    assert outcome.result.best is not None


@_needs_fixtures
def test_investigate_both_index_forms_return_identical_score(repo):
    _seed_with_probe(repo)
    by_short = investigate("002", repo)
    by_full = investigate("10009301", repo)
    assert by_short.result.best.score == by_full.result.best.score
    assert by_short.result.matched == by_full.result.matched


def test_investigate_empty_db_reports_no_students_calmly(repo):
    outcome = investigate("002", repo)
    assert outcome.result is None
    assert "No students in the local database yet" in outcome.message


def test_investigate_unknown_index_lists_valid_students_never_error(repo):
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])
    outcome = investigate("99999999", repo)
    assert outcome.result is None
    assert "We don't have a signature to check" in outcome.message
    assert "002 (10009301)" in outcome.message


def test_investigate_ambiguous_ordinal_says_so(repo):
    repo.upsert_students(
        [
            StudentRecord(no="002", index="10009301", title="Mr", name="A"),
            StudentRecord(no="002", index="20000002", title="Ms", name="B"),
        ]
    )
    outcome = investigate("2", repo)
    assert "more than one student" in outcome.message
    assert "10009301" in outcome.message and "20000002" in outcome.message


def test_investigate_no_references_is_distinct_no_data(repo, tmp_path, monkeypatch):
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])
    empty_refs = tmp_path / "references"
    empty_refs.mkdir()
    monkeypatch.setattr(config, "REFERENCES_DIR", empty_refs)
    outcome = investigate("002", repo)
    assert "don't have any Reference Signatures on file" in outcome.message


@_needs_fixtures
def test_investigate_references_but_no_probe_is_distinct_no_data(repo):
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])
    outcome = investigate("002", repo)
    assert "no signature to check yet" in outcome.message


# --- CLI/Web parity (FR-14) ---------------------------------------------------


@_needs_fixtures
def test_web_and_cli_agree_on_score_and_verdict(repo):
    """Same engine call: the Web page and investigate.py must show the same
    0-100 score and the same verdict sentence for the same student."""
    _seed_with_probe(repo)
    from sams_core.verification import verify_signature

    cli_result = verify_signature("10009301", repository=repo)
    web_outcome = investigate("10009301", repo)

    assert display_score(web_outcome.result.best.score) == display_score(cli_result.best.score)
    assert verdict_sentence(web_outcome.result.matched) == verdict_sentence(cli_result.matched)


# --- The Streamlit page itself (AppTest, headless) ----------------------------


def _app_test(tmp_path, monkeypatch):
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SAMS_DB_PATH", str(tmp_path / "sams.db"))
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "sams.db")
    page = Path(__file__).resolve().parent.parent / "webui" / "pages" / "Investigate.py"
    return AppTest.from_file(str(page), default_timeout=60)


def test_page_empty_state_prompts_calmly(tmp_path, monkeypatch):
    at = _app_test(tmp_path, monkeypatch).run()
    assert not at.exception
    body = " ".join(el.value for el in at.markdown)
    assert "Type a student's number to check their signature." in body


def test_page_unknown_index_shows_no_data_never_an_error(tmp_path, monkeypatch):
    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    repo.upsert_students([StudentRecord(no="002", index="10009301", title="Mr", name="A")])

    at = _app_test(tmp_path, monkeypatch).run()
    at.text_input[0].set_value("99999999").run()

    assert not at.exception
    assert not at.error
    body = " ".join(el.value for el in at.markdown)
    assert "We don't have a signature to check" in body


@_needs_fixtures
def test_page_found_renders_verdict_without_error(tmp_path, monkeypatch):
    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    _seed_with_probe(repo)

    at = _app_test(tmp_path, monkeypatch).run()
    at.text_input[0].set_value("10009301").run()

    assert not at.exception
    assert not at.error
    headers = " ".join(el.value for el in at.subheader)
    assert "Match" in headers or "Mismatch" in headers
