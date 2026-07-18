"""Story 4.7 (FR-15/SM-6): cross-frontend parity, verified at the data layer.

The CLI (`sams.py` → `process_sheet` with a path) and the Web UI
(`webui.process_logic.run_process` → `process_sheet` with bytes) must land
IDENTICAL Attendance Records in the Local DB for the same sheet, and Lookup /
Investigate must read back the same records the CLI would. Both frontends call
the one engine entry point (AD-12), so parity is structural — this test pins it
against a real sample sheet so a future divergence fails loudly.
"""

from pathlib import Path

import pytest

from sams_core.info_file import parse_info_file
from sams_core.models import LookupOutcome
from sams_core.pipeline import process_sheet
from sams_core.repository import AttendanceRepository

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"


def _rows(repo, sheet_id):
    """Comparable attendance tuples (index, status, resolved flag) in a stable order."""
    return sorted(
        (r.student_index, r.status.value, r.resolved_by_operator)
        for r in repo.get_attendance(sheet_id=sheet_id)
    )


def test_cli_and_web_paths_persist_identical_attendance(tmp_path, monkeypatch):
    """Process sheet 1 the CLI way (path) and the Web way (bytes via
    process_logic.run_process) into two temp DBs; the rows must match exactly."""
    from webui.process_logic import parse_info, run_process

    monkeypatch.setenv("SAMS_OUTPUT_DIR", str(tmp_path / "out"))
    import sams_core.config as cfg

    monkeypatch.setattr(cfg, "OUTPUT_DIR", tmp_path / "out")

    image_path = SAMPLES / "1.jpeg"
    xml_path = SAMPLES / "1.xml"

    # CLI path: engine called with a filesystem path (as sams.py does).
    cli_repo = AttendanceRepository(db_path=tmp_path / "cli.db")
    process_sheet(str(image_path), parse_info_file(str(xml_path)), repository=cli_repo)

    # Web path: engine called with uploaded bytes (as the Process page does).
    web_repo = AttendanceRepository(db_path=tmp_path / "web.db")
    parsed = parse_info(xml_path.read_bytes())
    outcome = run_process(image_path.read_bytes(), parsed, web_repo)

    assert outcome.error is None
    sheet_id = outcome.sheet_id
    assert sheet_id == "2019-05-31"
    assert _rows(cli_repo, sheet_id) == _rows(web_repo, sheet_id)
    assert len(_rows(cli_repo, sheet_id)) == 6  # the sheet's six students


def test_web_lookup_reads_back_what_the_cli_persisted(tmp_path, monkeypatch):
    """A student queried through the Web Lookup engine call returns the same
    Attendance Records the CLI processing wrote (FR-14 data-layer parity)."""
    monkeypatch.setenv("SAMS_OUTPUT_DIR", str(tmp_path / "out"))
    import sams_core.config as cfg

    monkeypatch.setattr(cfg, "OUTPUT_DIR", tmp_path / "out")

    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    process_sheet(
        str(SAMPLES / "1.jpeg"), parse_info_file(str(SAMPLES / "1.xml")), repository=repo
    )

    # Both index forms resolve to the same records via the one engine query API.
    by_short = repo.query_attendance("001")
    by_full = repo.query_attendance("10000409")
    assert by_short.outcome is LookupOutcome.FOUND
    assert by_short.records == by_full.records
    assert by_short.records[0].sheet_id == "2019-05-31"
