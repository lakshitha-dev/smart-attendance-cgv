"""Story 1.6: the executable SM-1..SM-3 accuracy gate (PRD §6.3).

Imports sams_core only, runs headlessly, uses a temp DB (AD-9). This test is the
Web UI gate decision — green here means Week 2 proceeds; red activates the
sprint plan's descope ladder. See TUNING_LOG.md for the current diagnosis.
"""
import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

from sams_core.errors import SamsError
from sams_core.image_io import load_image
from sams_core.info_file import parse_info_file
from sams_core.models import AttendanceStatus
from sams_core.pipeline import process_sheet
from sams_core.repository import AttendanceRepository

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"
GROUND_TRUTH_PATH = Path(__file__).resolve().parent / "data" / "ground_truth.csv"
SHEET_NUMBERS = (1, 2, 3, 4, 5)


def _load_ground_truth() -> dict[tuple[str, str], str]:
    """{(sheet_id, student_index): status} from the committed adjudication key."""
    truth = {}
    with GROUND_TRUTH_PATH.open(newline="") as f:
        for row in csv.DictReader(line for line in f if not line.lstrip().startswith("#")):
            truth[(row["sheet_id"], row["student_index"])] = row["status"]
    return truth


@pytest.fixture(scope="module")
def processed_sheets(tmp_path_factory):
    """Run the engine (process_sheet, AD-12) over all five sample sheets once."""
    repo = AttendanceRepository(db_path=tmp_path_factory.mktemp("db") / "sams.db")
    results = {}
    for n in SHEET_NUMBERS:
        info_file = parse_info_file(str(SAMPLES / f"{n}.xml"))
        result = process_sheet(str(SAMPLES / f"{n}.jpeg"), info_file, repository=repo)
        results[n] = result
    return results


# --- SM-1: 100% classification accuracy on non-Disputed rows ----------------


def test_sm1_classification_accuracy_on_non_disputed_rows(processed_sheets):
    truth = _load_ground_truth()
    mismatches = []
    disputed = []
    scored = 0

    for n, result in processed_sheets.items():
        for record in result.records:
            key = (result.sheet_id, record.student_index)
            expected = truth.get(key)
            if expected is None:
                continue  # not adjudicated; nothing to score
            if expected == "Disputed":
                disputed.append((result.sheet_id, record.student_index, record.status.value))
                continue
            scored += 1
            if record.status.value != expected:
                mismatches.append(
                    (result.sheet_id, record.student_index, expected, record.status.value)
                )

    if disputed:
        print(f"\nDisputed rows (excluded from SM-1, reported separately): {len(disputed)}")
        for sheet_id, index, actual in disputed:
            print(f"  {sheet_id} {index}: engine={actual}")

    if mismatches:
        print(f"\nSM-1 FAILURE — {len(mismatches)}/{scored} non-Disputed rows misclassified:")
        header = f"{'sheet_id':12} {'student_index':14} {'expected':10} {'actual':10}"
        print(header)
        print("-" * len(header))
        for sheet_id, index, expected, actual in mismatches:
            print(f"{sheet_id:12} {index:14} {expected:10} {actual:10}")

    accuracy = (scored - len(mismatches)) / scored if scored else 0.0
    assert not mismatches, (
        f"SM-1 requires 100% accuracy on non-Disputed rows; got {accuracy:.1%} "
        f"({scored - len(mismatches)}/{scored}). See table above and TUNING_LOG.md."
    )


# --- SM-3: exactly 7 StageArtifacts per sheet, in registry order -------------

_EXPECTED_STAGES = (
    (1, "original", "Original"),
    (2, "greyscale", "Greyscale"),
    (3, "denoised", "Denoised"),
    (4, "binarized", "Binarized"),
    (5, "deskewed", "Deskewed"),
    (6, "table-grid", "Table Grid"),
    (7, "per-cell-inspection", "Per-Cell Inspection"),
)


@pytest.mark.parametrize("n", SHEET_NUMBERS)
def test_sm3_exactly_seven_stage_artifacts_in_registry_order(n):
    from sams_core.pipeline import run_pipeline_with_detection

    image = load_image(str(SAMPLES / f"{n}.jpeg"))
    info_file = parse_info_file(str(SAMPLES / f"{n}.xml"))

    stages, _, _ = run_pipeline_with_detection(image, len(info_file.students))
    stages = list(stages)

    assert len(stages) == 7
    actual = [(s.order, s.slug, s.label) for s in stages]
    assert actual == list(_EXPECTED_STAGES)


# --- SM-2: CLI entry script smoke test (subprocess, headless-safe) -----------


def test_sm2_sams_cli_smoke_test_executes_headlessly():
    """`sams.py` has no --db-path flag (AD-4: DB path comes from config.py only), so
    this subprocess run persists to the real `config.DB_PATH`. Bootstrapping that
    file is exactly what FR-15 requires on a fresh machine, so leaving it behind
    is correct behaviour, not a side effect to hide — nothing here is cleaned up."""
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "sams.py"),
            str(SAMPLES / "1.jpeg"),
            str(SAMPLES / "1.xml"),
            "--no-display",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Attendance Records" in result.stdout
    assert "2019-05-31" in result.stdout
