#!/usr/bin/env python
"""Entry point (thin adapter, AD-1): parse args, call the engine's `process_sheet`
(AD-12) once, render stdout + live stage windows. No engine logic lives here."""
import argparse
import sys

import cv2

from sams_core.errors import InputError, SamsError
from sams_core.info_file import parse_info_file
from sams_core.pipeline import process_sheet


def _show_stage(stage):
    """Live CLI stage window (FR-11), shrunk to fit screen; full-res saved by the engine."""
    img = stage.image if stage.image.ndim == 2 else cv2.cvtColor(stage.image, cv2.COLOR_RGB2BGR)
    scale = min(1.0, 1000 / max(img.shape[:2]))
    if scale < 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    cv2.namedWindow(stage.label, cv2.WINDOW_NORMAL)
    cv2.imshow(stage.label, img)
    cv2.waitKey(1)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sams.py")
    parser.add_argument("image", help="Signing Sheet image (.png/.jpeg/.jpg)")
    parser.add_argument("info_file", help="Info File (info.xml)")
    parser.add_argument("--date", help="Sheet Identifier if the Info File lacks session/@date")
    parser.add_argument("--overwrite", action="store_true", help="replace saved operator resolutions")
    parser.add_argument("--no-display", action="store_true", help="skip live windows (headless-safe)")
    args = parser.parse_args(argv)
    try:
        info_file = parse_info_file(args.info_file)
        result = process_sheet(args.image, info_file, args.date, args.overwrite,
                               on_stage=None if args.no_display else _show_stage)
        if not args.no_display:
            if sys.stdin.isatty():  # hold windows for the operator
                cv2.waitKey(0)
            cv2.destroyAllWindows()
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except SamsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # AD-6: never a raw stack trace
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {len(result.records)} Attendance Records. Sheet Identifier: {result.sheet_id}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for record in result.records:
        print(f"{record.student_index}  {record.student_name}: {record.status.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
