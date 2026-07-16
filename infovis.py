#!/usr/bin/env python
"""Entry point (thin adapter, AD-1): parse the index argument, call the
engine's single query API, hand off to display. No index-parsing or DB
logic lives here (AD-4). Errors translate per AD-6: one-line stderr,
exit 2 (input) / 1 (other) / 130 (interrupt) — never a stack trace."""
import sys
from argparse import ArgumentParser

from cli_display import print_attendance_records, print_lookup_outcome, show_figure
from sams_core.errors import InputError, SamsError
from sams_core.models import LookupOutcome
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_attendance_timeline


def main(argv: list[str] | None = None, repository: AttendanceRepository | None = None) -> int:
    parser = ArgumentParser(prog="infovis.py")
    parser.add_argument("index", help="Student No (e.g. 001) or 8-digit Student Index")
    args = parser.parse_args(argv)

    repo = repository if repository is not None else AttendanceRepository()
    try:
        result = repo.query_attendance(args.index)
        if result.outcome is not LookupOutcome.FOUND:
            print_lookup_outcome(result)  # AD-6: no-data, never an error tone
            return 0
        records = list(result.records)
        print_attendance_records(records)
        show_figure(render_attendance_timeline(records))
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
