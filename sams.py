#!/usr/bin/env python
"""Entry point: process a Signing Sheet with a validated Info File."""
import argparse
import sys

from cli_display import close_windows, hold_windows_until_dismissed, print_run_summary, show_stage_live
from sams_core.artifacts import reset_sheet_output, save_stage
from sams_core.detect import save_crops
from sams_core.errors import InputError, SamsError
from sams_core.image_io import load_image
from sams_core.info_file import parse_info_file, resolve_sheet_identifier
from sams_core.pipeline import run_pipeline_with_detection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sams.py")
    parser.add_argument("image", help="Signing Sheet image (.png/.jpeg/.jpg)")
    parser.add_argument("info_file", help="Info File (info.xml)")
    parser.add_argument("--date", help="Sheet Identifier if the Info File lacks session/@date")
    args = parser.parse_args(argv)

    try:
        image = load_image(args.image)
        info_file = parse_info_file(args.info_file)
        sheet_id = resolve_sheet_identifier(info_file, args.date, args.image)
        reset_sheet_output(sheet_id)  # re-runs must never mix stale artifacts with fresh ones
        stages, run = run_pipeline_with_detection(image, len(info_file.students))
        for stage in stages:  # lazy: each stage displays the moment it is computed (FR-11)
            show_stage_live(stage)
            save_stage(sheet_id, stage)
        # Crops named by Student Index (AD-10, Epic 3's probes) when rows map onto the roster.
        indices = [s.index for s in info_file.students] if len(run.cell_results) == len(info_file.students) else None
        crop_paths = save_crops(sheet_id, run.cell_results, student_indices=indices)
        print_run_summary(info_file, sheet_id, run.sheet_result, run.cell_results, crop_paths)
        hold_windows_until_dismissed()
    except KeyboardInterrupt:
        close_windows()
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # AD-6: one-line stderr, correct exit code, never a stack trace
        close_windows()
        prefix = "" if isinstance(exc, SamsError) else "Unexpected error: "
        print(f"{prefix}{exc}", file=sys.stderr)
        return 2 if isinstance(exc, InputError) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
