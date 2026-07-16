---
status: done
epic: 2
story: '2.1'
title: Query a student's attendance by either index form
frs: [FR-7]
owner: M7 (Topic 7 — Attendance Visualization)
sprint: Week 1, Days 2–5 (chart built against seeded DB; wired to real DB after 1.5)
baseline_commit: 5cfb9692a1659e308dc2f10b2d13caf42e9c048d
---

# Story 2.1: Query a student's attendance by either index form

## Story

As an operator,
I want to run `python infovis.py <index>` with either the 8-digit Student No or the short ordinal,
So that I can pull up any student's attendance records the way the brief's command specifies.

## Acceptance Criteria

**Given** a Local DB populated by Epic 1
**When** `python infovis.py 001` and `python infovis.py 10000409` run for the same student
**Then** both resolve through the single engine index resolver (no adapter parses index forms) and return the identical set of Attendance Records.

**Given** an unknown index
**When** the command runs
**Then** the program reports "no data" listing the valid indices from `repository.list_students()` (short form + 8-digit, e.g. `001 (10000409)`), exits 0, and never raises an error tone.

**Given** the Ports & Adapters rule
**Then** `infovis.py` stays a thin adapter (<50 lines): parse argument → call engine query → hand off to display.

## Dev Notes

- **Create:** `infovis.py` (root entry, thin); engine query API on `repository.py`.
- **AD-4:** index resolution happens in ONE engine resolver (both `10009301` and `002` forms) before any DB read; DB stores only the canonical 8-digit index.
- **AD-6:** unknown index is a **no-data result**, never an exception — CLI prints friendly list + exits 0. Same pattern the Web Lookup page reuses later (4.5).
- **Parallelization tip (2-week plan):** don't wait for Story 1.5 — seed a temp DB by hand (repository schema lands Day 2–3) and build against it; swap to real data after integration Day 5.

## Dependencies

- **Requires:** 1.5 (repository; stub/seeded DB acceptable until integration).
- **Enables:** 2.2, 4.5.

## Definition of Done

Both index forms return identical records (unit test); unknown-index message lists valid indices; entry script <50 lines.

## Tasks/Subtasks

- [x] Add the single engine query API on `repository.py` (AD-4: one resolver call before any read)
  - [x] `query_attendance(alias)` resolves via `resolve_student_index` then reads via `get_attendance`
  - [x] Unresolvable alias returns an empty list (no-data result, never raises — AD-6)
- [x] Add CLI display helpers to `cli_display.py` (AD-7: rendering stays in the adapter)
  - [x] `print_attendance_records` renders the resolved records
  - [x] `print_no_data` renders the friendly message + valid indices from `list_students()` (`001 (10000409)` form)
- [x] Create `infovis.py` root entry script (<50 lines, thin adapter)
  - [x] Parse the single `index` argument
  - [x] Call `repo.query_attendance` (the one engine query call)
  - [x] Hand off to `cli_display` for output; exit 0 always (AD-6)
- [x] Tests
  - [x] Unit test: `query_attendance("002")` and `query_attendance("10009301")` return identical records
  - [x] Unit test: unknown alias returns no data (empty list)
  - [x] CLI test: `infovis.main` with short form and 8-digit form both print the same records, exit 0
  - [x] CLI test: `infovis.main` with unknown index prints valid-indices list, exit 0
- [x] Run full regression suite; confirm no existing tests broke

## Dev Agent Record

### Implementation Plan

- `AttendanceRepository.query_attendance(alias)` composes the existing `resolve_student_index` (the ONE resolver, AD-4) with `get_attendance`, so `infovis.py` never parses index forms itself and only makes a single engine call.
- `cli_display.py` gains two pure-formatting functions (no engine logic), mirroring the existing `print_run_summary` pattern used by `sams.py`.
- `infovis.py` mirrors `sams.py`'s thin-adapter shape: build an `argparse.ArgumentParser`, call the one engine query, branch on empty vs non-empty to choose the display helper, always `return 0` (AD-6 — an unknown index is a no-data result, not an error).

### Completion Notes

- Both index forms (short ordinal and 8-digit) resolve through the existing `resolve_student_index` (the ONE resolver, AD-4) before any read; `query_attendance` returns byte-identical `AttendanceRecord` lists for either form of the same student — verified by unit test and by a manual `python infovis.py 001` / `python infovis.py 10000409` smoke run producing identical stdout.
- Unknown index never raises; `infovis.py` always exits 0 and prints the valid-indices list sourced from `repository.list_students()` in the `001 (10000409)` short-form + 8-digit format.
- `infovis.py` is 30 lines, under the 50-line thin-adapter budget; it parses the one `index` argument, makes a single `repo.query_attendance` call, and hands off to `cli_display` for all rendering.
- Full regression suite: 120 passed, 0 failed (includes the 5 new tests added for this story).

## File List

- `sams_core/repository.py` (modified — added `query_attendance`)
- `cli_display.py` (modified — added `print_attendance_records`, `print_no_data`)
- `infovis.py` (new — root entry script)
- `tests/test_repository.py` (modified — added `query_attendance` tests)
- `tests/test_infovis.py` (new — CLI-level tests)

## Change Log

- 2026-07-16: Implemented Story 2.1 — single engine query API (`repository.query_attendance`), CLI display helpers (`print_attendance_records`, `print_no_data`), thin `infovis.py` entry script, and unit/CLI tests covering both index forms and the unknown-index no-data path. Full regression suite passes (120/120).

### Review Findings (code review 2026-07-16, Sprint-6 merge)

- [x] [Review][Patch] `infovis.py` has zero exception handling — DB-locked `ProcessingError`, hand-edited-status `ValueError`, and Ctrl+C all escape as raw tracebacks, violating AD-6/NFR-10 and the exit-code contract `sams.py` implements — mirror sams.py's translation (2 input / 1 other / 130 interrupt) [infovis.py:13]
- [x] [Review][Patch] The empty-result path conflates four distinct states (unknown alias, ambiguous ordinal, known student with zero attendance, empty/missing DB) — the operator is told a valid input is invalid, and the valid-indices list can show the "invalid" ordinal twice — return a typed LookupResult with an outcome discriminator from `query_attendance` (AD-6 locates the no-data payload engine-side) and branch the copy per outcome in both adapters [sams_core/repository.py:176, cli_display.py:114, infovis.py:21]
- [x] [Review][Patch] `query_attendance` opens 2-3 connections (resolver + read + adapter's list_students) with a TOCTOU between them despite advertising "a single call" — do resolve+read+roster in ONE connection inside the new LookupResult implementation [sams_core/repository.py:176]
- [x] [Review][Patch] A read-only lookup silently CREATES sams.db + parent dirs when missing (typo'd cwd leaves stray DBs; missing-DB indistinguishable from empty) — detect the missing file on the query path and return the empty-DB outcome without connecting [sams_core/repository.py:51]
- [x] [Review][Patch] `resolved_by_operator` is invisible in CLI output — an operator-corrected status is indistinguishable from a machine verdict — print a marker [cli_display.py:90]
- [x] [Review][Patch] Nullable fields print literally: "None: Present" for NULL subject_code, "None (10000409)" in the valid-indices list for NULL `no`, dangling double space for missing roster name — add fallbacks [cli_display.py:87,120]
- [x] [Review][Patch] Zero-padded 8-digit ordinal discontinuity: "00000002" short-circuits as canonical and misses (while 7 and 9 digits resolve) — prefer known-index match, then ordinal, then 8-digit passthrough [sams_core/repository.py:163]
- [x] [Review][Patch] Windows cp1252 stdout can crash on names with diacritics — reconfigure stdout errors="replace" at the CLI entry [infovis.py:31]
- [x] [Review][Patch] Tests never cover: ambiguous ordinal end-to-end, whitespace input, known-student-zero-attendance, ProcessingError path, or any subprocess-level exit-code pinning — add them [tests/test_infovis.py, tests/test_repository.py]
- [x] [Review][Dismissed] argparse SystemExit from `main() -> int` — consistent with sams.py; exit codes are pinned at the subprocess boundary instead
- [x] [Review][Note] Dev Agent Record inaccuracies: claims "single engine call" (there are two: query + render) and omits shipped files; 2.1 and 2.2 were committed fused in 2189aa9, so neither increment is auditable standalone
