#!/usr/bin/env python
"""Entry point (thin adapter, AD-1): parse args, call the engine's `process_sheet`
(AD-12) once, render stdout + live stage windows. No engine logic lives here."""
import argparse
import sys

from cli_display import close_windows, hold_windows_until_dismissed, print_run_summary, show_stage_live
from sams_core.errors import InputError, SamsError
from sams_core.info_file import parse_info_file
from sams_core.pipeline import process_sheet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sams.py")
    parser.add_argument("image", help="Signing Sheet image (.png/.jpeg/.jpg)")
    parser.add_argument("info_file", help="Info File (info.xml)")
    parser.add_argument("--date", help="Sheet Identifier if the Info File lacks session/@date")
    parser.add_argument("--overwrite", action="store_true", help="replace saved operator resolutions")
    parser.add_argument("--no-display", action="store_true", help="skip live stage windows (headless-safe)")
    args = parser.parse_args(argv)

    try:
        info_file = parse_info_file(args.info_file)
        result = process_sheet(
            args.image, info_file, args.date, args.overwrite,
            # Lazy stream: each stage displays the moment it is computed (FR-11).
            on_stage=None if args.no_display else show_stage_live,
        )
        print_run_summary(result)
        if not args.no_display:
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
