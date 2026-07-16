#!/usr/bin/env python
"""Entry point (thin adapter, AD-1): parse the index argument, call the
engine's single query API, hand off to display. No index-parsing or DB
logic lives here (AD-4)."""
import sys
from argparse import ArgumentParser

from cli_display import print_attendance_records, print_no_data, show_figure
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_attendance_timeline


def main(argv: list[str] | None = None, repository: AttendanceRepository | None = None) -> int:
    parser = ArgumentParser(prog="infovis.py")
    parser.add_argument("index", help="Student No (e.g. 001) or 8-digit Student Index")
    args = parser.parse_args(argv)

    repo = repository if repository is not None else AttendanceRepository()
    records = repo.query_attendance(args.index)

    if not records:
        # AD-6: an unknown index is a no-data result, never an error tone.
        print_no_data(args.index, repo.list_students())
        return 0

    print_attendance_records(records)
    show_figure(render_attendance_timeline(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
