#!/usr/bin/env python
"""Entry point: process a Signing Sheet with a validated Info File."""
import argparse
import sys

import cv2

from sams_core.artifacts import save_stage
from sams_core.errors import InputError, SamsError
from sams_core.image_io import load_image
from sams_core.info_file import parse_info_file, resolve_sheet_identifier
from sams_core.pipeline import run_pipeline


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
        for stage in run_pipeline(image):
            display = stage.image if stage.image.ndim == 2 else cv2.cvtColor(stage.image, cv2.COLOR_RGB2BGR)
            cv2.imshow(stage.label, display)
            cv2.waitKey(1)
            save_stage(sheet_id, stage)
        if sys.stdin.isatty():  # no one to dismiss the windows in a non-interactive run
            cv2.waitKey(0)
        cv2.destroyAllWindows()
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except SamsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # AD-6: never a raw stack trace, even for unexpected failures
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    print(f"Parsed {len(info_file.students)} Student Records. Sheet Identifier: {sheet_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
