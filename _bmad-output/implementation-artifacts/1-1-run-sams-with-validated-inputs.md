---
status: ready-for-dev
epic: 1
story: '1.1'
title: Run sams.py with validated inputs
frs: [FR-1]
owner: M1 (Topic 1 — Project Foundation & Input Handling)
sprint: Week 1, Days 1–3
---

# Story 1.1: Run `sams.py` with validated inputs

## Story

As a marker/operator,
I want to run `python sams.py <image> <info.xml>` and have both inputs loaded and validated,
So that processing starts from trustworthy inputs and bad inputs fail with clear messages instead of stack traces.

## Acceptance Criteria

**Given** the repo scaffolded per the Structural Seed (`sams.py`, `sams_core/` with `config.py`, `errors.py`, `models.py`, `info_file.py`, pinned `requirements.txt`)
**When** `python sams.py <valid image> <valid info.xml>` runs
**Then** the image loads (`.png` and `.jpeg`/`.jpg` both accepted) and the Info File parses into `StudentRecord` dataclasses plus Session metadata per the PRD Appendix A schema
**And** the CLI reports the parsed Student Record count and the resolved Sheet Identifier, exiting 0.

**Given** a missing/unreadable image or an Info File failing Appendix A validation
**When** the command runs
**Then** a one-line human-readable error goes to stderr with exit code 2 — never a raw stack trace (`SamsError` hierarchy; the engine raises, only the CLI prints/exits).

**Given** an Info File lacking a session date
**When** run with `--date 2019-05-31`, **then** that date becomes the Sheet Identifier
**And** when run without `--date`, the image filename stem is normalized to ISO 8601 (`10.07.2019.png` → `2019-07-10`).

**Given** the Ports & Adapters rule, **then** `sams.py` stays a thin adapter under 50 lines.

## Dev Notes

- **Create:** repo scaffold per Architecture Structural Seed — `sams.py` (entry), `sams_core/__init__.py`, `sams_core/config.py`, `sams_core/errors.py`, `sams_core/models.py`, `sams_core/info_file.py`, `requirements.txt` (pinned: opencv-python 4.13.0.92, numpy 2.5.1, matplotlib 3.11.0; Python 3.12/3.13).
- **models.py (AD-2):** frozen dataclasses `StudentRecord`, `AttendanceStatus` enum (PRESENT/ABSENT/AMBIGUOUS) — add others as later stories need them. No bare dict/tuple contracts cross module boundaries.
- **errors.py (AD-6):** `SamsError` → `InputError`, `ProcessingError`. Engine raises, never prints/exits. CLI exit codes: 0 ok, 2 input error, 1 other.
- **info_file.py (AD-11):** parse Appendix A XML (`subject/session/students/student[@no,@index,@title,@name]`); Sheet Identifier resolution chain lives HERE, resolved BEFORE any pipeline runs: Info File `session/@date` → `--date` flag → filename stem (CLI only). Both `no` (short alias) and `index` (8-digit) index forms captured.
- **config.py (AD-5):** DB path, output dir constants — all paths relative to project root.
- **Glossary discipline:** PRD §3 terms verbatim in code/docs (Signing Sheet, Info File, Student Record, Sheet Identifier…).
- **Test fixtures needed:** the 5 `info.xml` files + sample sheets in `sample_signin-sheets/1.jpeg`..`5.jpeg` — note filenames carry NO date, so fixtures must include `session/@date` (see readiness report).

## Dependencies

- **Requires:** nothing (first story; includes Day-1 scaffold).
- **Enables:** every other story.

## Definition of Done

Merged; both valid/invalid input paths demonstrated on real fixtures; entry script <50 lines; unit tests for info_file parsing and Sheet Identifier chain pass headlessly.
