#!/usr/bin/env python
"""Detection-accuracy evaluation for the report (SM-1 evidence, human-readable).

Processes the five sample Signing Sheets through the SAME engine `sams.py`
uses, compares every resulting status against the adjudicated ground truth
(tests/data/ground_truth.csv), prints a per-sheet results table, and saves
output/detection_results.csv for the report's testing-results section.
Disputed ground-truth rows are excluded from scoring (exactly as the SM-1
test gate does) but still shown.

This is a thin evaluation harness over `sams_core` (AD-9): detection and
persistence come from the engine alone. All persistence is redirected to a
temporary location — running this never mutates the repo's real sams.db or
output/ tree (only the results CSV is written).

Usage:
    python evaluate_detection.py
"""
import csv
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "sample_signin-sheets"
GROUND_TRUTH = ROOT / "tests" / "data" / "ground_truth.csv"
RESULTS_CSV = ROOT / "output" / "detection_results.csv"
SHEET_NUMBERS = (1, 2, 3, 4, 5)

from sams_core import config  # noqa: E402
from sams_core.info_file import parse_info_file  # noqa: E402
from sams_core.pipeline import process_sheet  # noqa: E402
from sams_core.repository import AttendanceRepository  # noqa: E402


def load_ground_truth() -> dict[tuple[str, str], str]:
    """{(sheet_id, student_index): status} from the committed adjudication."""
    with GROUND_TRUTH.open(newline="", encoding="utf-8") as handle:
        return {
            (row["sheet_id"], row["student_index"]): row["status"]
            for row in csv.DictReader(handle)
        }


def main() -> int:
    truth = load_ground_truth()
    out_rows = []
    scored = correct = disputed = 0

    with tempfile.TemporaryDirectory(prefix="sams-eval-") as tmp:
        # Redirect ALL engine persistence away from the repo's real state.
        config.DB_PATH = Path(tmp) / "sams.db"
        config.OUTPUT_DIR = Path(tmp) / "output"
        repository = AttendanceRepository()

        for number in SHEET_NUMBERS:
            info = parse_info_file(SAMPLES / f"{number}.xml")
            result = process_sheet(
                SAMPLES / f"{number}.jpeg", info, repository=repository
            )
            sheet_id = result.records[0].sheet_id if result.records else "?"
            print(f"\nSheet {number} ({number}.jpeg) - session {sheet_id}")
            sheet_scored = sheet_correct = 0
            for record in result.records:
                expected = truth.get((record.sheet_id, record.student_index), "?")
                name = (record.student_name or record.student_index)[:34]
                if expected == "Disputed":
                    disputed += 1
                    verdict = "-- (Disputed, excluded)"
                else:
                    sheet_scored += 1
                    if record.status.value == expected:
                        sheet_correct += 1
                        verdict = "OK"
                    else:
                        verdict = "MISS"
                print(
                    f"  {record.student_index}  {name:<34} "
                    f"expected {expected:<9} detected {record.status.value:<9} {verdict}"
                )
                out_rows.append(
                    [
                        record.sheet_id,
                        record.student_index,
                        record.student_name or "",
                        expected,
                        record.status.value,
                        verdict,
                    ]
                )
            for warning in result.warnings:
                print(f"  note: {warning}")
            scored += sheet_scored
            correct += sheet_correct
            print(f"  sheet accuracy: {sheet_correct}/{sheet_scored}")

    accuracy = correct / scored if scored else 0.0
    print(
        f"\nOverall: {correct}/{scored} scored rows correct ({accuracy:.1%}); "
        f"{disputed} Disputed row(s) excluded."
    )

    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["sheet_id", "student_index", "name", "expected", "detected", "verdict"]
        )
        writer.writerows(out_rows)
    print(f"Saved {RESULTS_CSV.relative_to(ROOT)}")

    return 0 if correct == scored else 1


if __name__ == "__main__":
    sys.exit(main())
