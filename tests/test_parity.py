"""Story 4.7 (FR-15/SM-6): cross-frontend parity, verified at the data layer.

The CLI (`sams.py` → `process_sheet` with a path) and the Web UI
(`webui.process_logic.run_process` → `process_sheet` with bytes) must land
IDENTICAL Attendance Records in the Local DB for the same sheet, and the Web
Lookup adapter must read back what the CLI persisted. Both frontends call the
one engine entry point (AD-12), so parity is structural — these tests pin it
against a real sample sheet so a future divergence fails loudly.
"""

import dataclasses
from pathlib import Path

import pytest

from sams_core.info_file import parse_info_file
from sams_core.models import LookupOutcome
from sams_core.pipeline import process_sheet
from sams_core.repository import AttendanceRepository

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"

pytestmark = pytest.mark.skipif(
    not (SAMPLES / "1.jpeg").exists(), reason="sample sheets not present in this checkout"
)


@pytest.fixture
def isolated_output(tmp_path, monkeypatch):
    """Redirect artifact writes to a temp dir. artifacts.py binds OUTPUT_DIR by
    value at import (`from sams_core.config import OUTPUT_DIR`), so ONLY patching
    artifacts.OUTPUT_DIR actually redirects reset_sheet_output/save_stage/
    save_crop — patching config alone is a silent no-op that mutates the real
    output/ tree (AD-9)."""
    import sams_core.artifacts as artifacts
    import sams_core.config as config

    out = tmp_path / "out"
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", out)
    monkeypatch.setattr(config, "OUTPUT_DIR", out)
    return out


def _rows(repo, sheet_id):
    """Every persisted field of each Attendance Record, in a stable order —
    so a divergence in name / subject / session metadata is caught too, not
    just status."""
    return sorted(
        (dataclasses.astuple(record) for record in repo.get_attendance(sheet_id=sheet_id)),
    )


def test_cli_and_web_paths_persist_identical_attendance(tmp_path, isolated_output):
    """Process sheet 1 the CLI way (path) and the Web way (bytes via
    process_logic.run_process) into two temp DBs; every field of every row
    must match, for the whole roster."""
    from webui.process_logic import parse_info, run_process

    image_path = SAMPLES / "1.jpeg"
    xml_path = SAMPLES / "1.xml"
    roster_size = len(parse_info_file(str(xml_path)).students)

    cli_repo = AttendanceRepository(db_path=tmp_path / "cli.db")
    process_sheet(str(image_path), parse_info_file(str(xml_path)), repository=cli_repo)

    web_repo = AttendanceRepository(db_path=tmp_path / "web.db")
    outcome = run_process(image_path.read_bytes(), parse_info(xml_path.read_bytes()), web_repo)

    assert outcome.error is None
    assert outcome.sheet_id == "2019-05-31"
    assert _rows(cli_repo, "2019-05-31") == _rows(web_repo, "2019-05-31")
    assert len(_rows(cli_repo, "2019-05-31")) == roster_size


def test_cli_and_web_agree_on_an_operator_supplied_date(tmp_path, isolated_output):
    """AD-11 divergence case: a DATELESS Info File. The CLI resolves the Sheet
    Identifier from its --date (sheet_id_override); the Web path from the
    operator-entered date — NEVER the upload filename. Both must land the same
    sheet_id and identical rows, proving the override path agrees."""
    from webui.process_logic import parse_info, run_process

    image_path = SAMPLES / "1.jpeg"
    dateless_xml = (SAMPLES / "1.xml").read_bytes().replace(b' date="2019-05-31"', b"")
    assert b'date="2019-05-31"' not in dateless_xml  # genuinely dateless now

    dateless_path = tmp_path / "dateless.xml"
    dateless_path.write_bytes(dateless_xml)
    operator_date = "2019-07-10"

    cli_repo = AttendanceRepository(db_path=tmp_path / "cli.db")
    process_sheet(
        str(image_path),
        parse_info_file(str(dateless_path)),
        sheet_id_override=operator_date,
        repository=cli_repo,
    )

    web_repo = AttendanceRepository(db_path=tmp_path / "web.db")
    parsed = parse_info(dateless_xml, session_date=operator_date)
    assert parsed.sheet_id == operator_date  # Web uses the entered date, not a filename
    outcome = run_process(image_path.read_bytes(), parsed, web_repo)

    assert outcome.sheet_id == operator_date
    assert _rows(cli_repo, operator_date) == _rows(web_repo, operator_date)


def test_web_lookup_adapter_reads_back_what_the_cli_persisted(tmp_path, isolated_output):
    """Query through the ACTUAL Web Lookup adapter (webui.lookup_logic.lookup),
    not the repository directly — both index forms return the records the CLI
    processing wrote (FR-14 data-layer parity)."""
    from webui.lookup_logic import lookup

    repo = AttendanceRepository(db_path=tmp_path / "sams.db")
    process_sheet(
        str(SAMPLES / "1.jpeg"), parse_info_file(str(SAMPLES / "1.xml")), repository=repo
    )

    by_short = lookup("001", repo)
    by_full = lookup("10000409", repo)
    assert by_short.message is None and by_full.message is None  # FOUND, not no-data
    assert by_short.records == by_full.records
    assert by_short.records[0].sheet_id == "2019-05-31"

    # The engine query API agrees with the adapter it wraps.
    assert repo.query_attendance("001").outcome is LookupOutcome.FOUND
