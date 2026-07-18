#!/usr/bin/env python
"""Entry point (thin adapter, AD-1): parse the index argument, call the
engine's single verification API, hand off to display. No index-parsing,
comparison, or best-match logic lives here (AD-9). Errors translate per AD-6:
one-line stderr, exit 2 (input) / 1 (other) / 130 (interrupt) — never a stack
trace. A no-data verdict (unknown index, no references, no probe) exits 0."""
import sys
from argparse import ArgumentParser

from cli_display import print_verification_result
from sams_core.errors import InputError, SamsError
from sams_core.repository import AttendanceRepository
from sams_core.verification import verify_signature


def main(argv: list[str] | None = None, repository: AttendanceRepository | None = None) -> int:
    parser = ArgumentParser(prog="investigate.py")
    parser.add_argument("index", help="Student No (e.g. 001) or 8-digit Student Index")
    args = parser.parse_args(argv)

    repo = repository if repository is not None else AttendanceRepository()
    try:
        result = verify_signature(args.index, repository=repo)
        print_verification_result(result)  # FOUND verdict or AD-6 no-data, exit 0
        return 0
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except InputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except SamsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # AD-6: no raw traceback on any surface
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(errors="replace")  # cp1252 consoles vs diacritics
    sys.exit(main())
