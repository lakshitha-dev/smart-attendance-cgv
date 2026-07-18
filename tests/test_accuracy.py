"""Story 1.6: the executable SM-1..SM-3 accuracy gate (PRD §6.3).

Imports sams_core only — plus the documented story-1.1 exception: SM-2 invokes
`sams.py` as a subprocess, because a CLI's exit-code/stdout contract can only
be observed by running it. Runs headlessly. ALL persistence — the DB and the
output artifacts — is redirected to temp locations (AD-9): a test run must
never mutate the repo's real `sams.db` or `output/` tree.

This gate is the Web UI gate decision — green means Week 2 proceeds; red
activates the sprint plan's descope ladder. See TUNING_LOG.md (with its
2026-07-16 addendum) for the tuning history.
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sams_core import artifacts, config
from sams_core.image_io import load_image
from sams_core.info_file import parse_info_file
from sams_core.pipeline import process_sheet, run_pipeline_with_detection
from sams_core.repository import AttendanceRepository

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"
GROUND_TRUTH_PATH = Path(__file__).resolve().parent / "data" / "ground_truth.csv"
SHEET_NUMBERS = (1, 2, 3, 4, 5)

_VALID_STATUSES = {"Present", "Absent", "Ambiguous", "Disputed"}
_EXPECTED_HEADER = ["sheet_id", "student_index", "status"]


def _load_ground_truth() -> dict[tuple[str, str], str]:
    """{(sheet_id, student_index): status}, validated strictly at load time.

    The data contract (ground_truth-README.md) is a plain, header-first CSV:
    no comment lines, no duplicates, statuses from the fixed vocabulary.
    Violations fail the gate LOUDLY — silently skipping malformed rows would
    let the gate go green with rows unscored.
    """
    truth: dict[tuple[str, str], str] = {}
    with GROUND_TRUTH_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == _EXPECTED_HEADER, (
            f"ground_truth.csv header drifted: {reader.fieldnames} != {_EXPECTED_HEADER}"
        )
        for line_no, row in enumerate(reader, start=2):
            sheet_id = (row["sheet_id"] or "").strip()
            student_index = (row["student_index"] or "").strip()
            status = (row["status"] or "").strip()
            assert sheet_id and student_index and status, (
                f"ground_truth.csv line {line_no} is malformed: {dict(row)}"
            )
            assert not sheet_id.startswith("#"), (
                f"ground_truth.csv line {line_no} looks like a comment — the data "
                "contract forbids comment lines (see ground_truth-README.md)"
            )
            assert status in _VALID_STATUSES, (
                f"ground_truth.csv line {line_no}: unknown status {status!r} "
                f"(expected one of {sorted(_VALID_STATUSES)})"
            )
            key = (sheet_id, student_index)
            assert key not in truth, (
                f"ground_truth.csv line {line_no}: duplicate adjudication for {key}"
            )
            truth[key] = status
    return truth


@pytest.fixture(scope="module")
def isolated_output_dir(tmp_path_factory):
    """Redirect OUTPUT_DIR for this module: `process_sheet` resets per-sheet
    output folders, and the gate must never rmtree/rewrite the repo's real
    `output/` tree (AD-9 isolation covers artifacts, not just the DB)."""
    out = tmp_path_factory.mktemp("output")
    saved_config, saved_artifacts = config.OUTPUT_DIR, artifacts.OUTPUT_DIR
    config.OUTPUT_DIR = out
    artifacts.OUTPUT_DIR = out
    yield out
    config.OUTPUT_DIR = saved_config
    artifacts.OUTPUT_DIR = saved_artifacts


@pytest.fixture(scope="module")
def processed_sheets(tmp_path_factory, isolated_output_dir):
    """Run the engine (process_sheet, AD-12) over all five sheets once,
    capturing per-sheet failures so one bad sheet still leaves the other
    four sheets' results reportable."""
    repo = AttendanceRepository(db_path=tmp_path_factory.mktemp("db") / "sams.db")
    results: dict = {}
    failures: dict = {}
    for n in SHEET_NUMBERS:
        try:
            info_file = parse_info_file(str(SAMPLES / f"{n}.xml"))
            results[n] = process_sheet(str(SAMPLES / f"{n}.jpeg"), info_file, repository=repo)
        except Exception as exc:  # collected, reported by SM-1 with full context
            failures[n] = f"{type(exc).__name__}: {exc}"
    return results, failures


# --- SM-1: 100% classification accuracy on non-Disputed rows ----------------


def test_sm1_classification_accuracy_on_non_disputed_rows(processed_sheets):
    results, failures = processed_sheets
    truth = _load_ground_truth()
    expected_scoreable = sum(1 for status in truth.values() if status != "Disputed")

    mismatches = []
    disputed = []
    consumed: set = set()
    scored = 0

    for n, result in results.items():
        for record in result.records:
            key = (result.sheet_id, record.student_index)
            expected = truth.get(key)
            if expected is None:
                # An engine record with no adjudication is a FAILURE, not a skip:
                # key drift (sheet-id format, index form) must never un-score the gate.
                mismatches.append(
                    (result.sheet_id, record.student_index, "<not adjudicated>", record.status.value)
                )
                continue
            consumed.add(key)
            if expected == "Disputed":
                disputed.append((result.sheet_id, record.student_index, record.status.value))
                continue
            scored += 1
            if record.status.value != expected:
                mismatches.append(
                    (result.sheet_id, record.student_index, expected, record.status.value)
                )

    # DoD: the Disputed report is printed unconditionally, zero or not.
    print(f"\nDisputed rows (excluded from SM-1, reported separately): {len(disputed)}")
    for sheet_id, index, actual in disputed:
        print(f"  {sheet_id} {index}: engine={actual}")

    if mismatches:
        print(f"\nSM-1 FAILURE — {len(mismatches)} problem row(s) of {scored} scored:")
        header = f"{'sheet_id':12} {'student_index':14} {'expected':16} {'actual':10}"
        print(header)
        print("-" * len(header))
        for sheet_id, index, expected, actual in mismatches:
            print(f"{sheet_id:12} {index:14} {expected:16} {actual:10}")

    assert not failures, f"process_sheet failed for sheet(s) {sorted(failures)}: {failures}"

    # Both directions must close: every truth row consumed, every scoreable row scored.
    unconsumed = sorted(set(truth) - consumed)
    assert not unconsumed, (
        f"{len(unconsumed)} adjudicated row(s) were never scored (first few: "
        f"{unconsumed[:5]}) — the gate's denominator does not cover the answer key"
    )
    assert scored == expected_scoreable, (
        f"scored {scored} rows but the answer key holds {expected_scoreable} "
        "non-Disputed rows — SM-1 must score every adjudicated row"
    )

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
    image = load_image(str(SAMPLES / f"{n}.jpeg"))
    info_file = parse_info_file(str(SAMPLES / f"{n}.xml"))

    stages, run = run_pipeline_with_detection(image, len(info_file.students))
    stages = list(stages)

    assert len(stages) == 7, f"sheet {n}: expected 7 stages, got {len(stages)}"
    actual = [(s.order, s.slug, s.label) for s in stages]
    assert actual == list(_EXPECTED_STAGES)
    # The stage stream exists to feed the run holder — verify the contract's
    # other half, not just the artifacts.
    assert run.sheet_result is not None, f"sheet {n}: run.sheet_result not populated"
    assert run.cell_results is not None and len(run.cell_results) > 0, (
        f"sheet {n}: run.cell_results not populated"
    )


# --- SM-2: CLI entry script smoke test (subprocess, headless-safe) -----------


def test_sm2_sams_cli_smoke_test_executes_headlessly(tmp_path):
    """Runs `sams.py` exactly as the marker would (FR-15/SM-2) — but with the
    DB and output redirected to a temp dir via the config env seams, so the
    smoke test never mutates the repo's real working data."""
    env = {
        **os.environ,
        "SAMS_HEADLESS": "1",  # explicit, not inherited by accident
        "PYTHONIOENCODING": "utf-8",
        "SAMS_DB_PATH": str(tmp_path / "sams.db"),
        "SAMS_OUTPUT_DIR": str(tmp_path / "output"),
    }
    try:
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
            encoding="utf-8",
            timeout=180,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            f"sams.py timed out after {exc.timeout}s; "
            f"stdout={exc.stdout!r} stderr={exc.stderr!r}"
        )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Sheet Identifier: 2019-05-31" in result.stdout
    assert "Saved 6 Attendance Records" in result.stdout
    status_lines = [
        line
        for line in result.stdout.splitlines()
        if line.rstrip().endswith(("Present", "Absent", "Ambiguous"))
    ]
    assert len(status_lines) == 6, (
        f"expected 6 per-student status lines, found {len(status_lines)}:\n{result.stdout}"
    )
