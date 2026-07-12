---
status: done
epic: 1
story: '1.1'
title: Run sams.py with validated inputs
frs: [FR-1]
owner: M1 (Topic 1 — Project Foundation & Input Handling)
sprint: Week 1, Days 1–3
baseline_commit: c389fee23e8e4d7c5aa306b24b6d26aaa729e8ab
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

## Tasks / Subtasks

- [x] Scaffold repo per Structural Seed: `sams.py`, `sams_core/__init__.py`, `config.py`, `errors.py`, `models.py`, `info_file.py`, `image_io.py`, `requirements.txt`
- [x] Build 5 real `info.xml` fixtures (paired with `sample_signin-sheets/1..5.jpeg`, each carrying `session/@date`) + invalid fixtures for error-path tests
- [x] Implement `models.py`: `AttendanceStatus` enum, `StudentRecord`, `Session` frozen dataclasses
- [x] Implement `errors.py`: `SamsError` → `InputError`, `ProcessingError`
- [x] Implement `config.py`: DB path, output dir constants (relative to project root)
- [x] Implement `info_file.py`: Appendix A XML parsing + validation, Sheet Identifier resolution chain (session date → `--date` → filename stem)
- [x] Implement `image_io.py`: load/validate `.png`/`.jpeg`/`.jpg`, raising `InputError` on missing/unreadable files
- [x] Implement `sams.py` thin CLI adapter (<50 lines): parse args, call engine, print/exit per AD-6
- [x] Unit tests: `info_file.py` parsing (valid/invalid) and Sheet Identifier chain
- [x] Integration tests: CLI exit codes on real fixtures (valid + invalid paths)
- [x] Run full test suite; verify AC coverage

### Review Findings

- [x] [Review][Decision] `tests/test_cli.py` imports `sams` directly, conflicting with AD-9's literal "tests import `sams_core` only (no CLI/web)" rule — but AC2 (stderr message + exit code 2) can only be observed by invoking the CLI. **Resolved by user:** keep as a documented exception to AD-9 — the CLI adapter's own exit-code/stderr contract (AC2) can only be verified by invoking it; noted here rather than in AD-9 itself.
- [x] [Review][Patch] `sams.py:main()` has no catch-all exception handler — any non-`SamsError` exception (e.g. a TOCTOU race in `info_file.py` between `is_file()` and `ET.parse()`) escapes as a raw traceback, violating AC2 ("never a raw stack trace") [sams.py:16-24]
- [x] [Review][Patch] `cv2.imread` silently fails on non-ASCII/Unicode file paths (confirmed by live repro) and `image_io.load_image` mislabels this as "unreadable or corrupt" rather than a real corruption [sams_core/image_io.py:17-20]
- [x] [Review][Patch] Info File required-attribute checks (`subject/@code,@name`, `student/@no,@index,@title,@name`) only test falsy/empty, not whitespace-only values — `name="  "` passes validation [sams_core/info_file.py:39-40,79-84]
- [x] [Review][Patch] Student Index validation via `index.isdigit()` accepts non-ASCII Unicode digit characters (e.g. fullwidth digits), which parse fine via `int()` but produce a different string identity than the ASCII index used elsewhere for matching [sams_core/info_file.py:87]
- [x] [Review][Patch] Filename-date regex searches for the first date-shaped substring anywhere in the stem instead of requiring the whole stem to match, risking spurious matches on filenames with unrelated numeric runs [sams_core/info_file.py:12]
- [x] [Review][Patch] `--date ""` (explicit empty string) is treated the same as "flag not given" and silently falls through to the filename fallback instead of raising a clear error [sams_core/info_file.py:99]
- [x] [Review][Patch] The `except SamsError` (exit-1/`ProcessingError`) branch in `sams.py` has zero test coverage — nothing in this story raises `ProcessingError` yet [sams.py:22-23]
- [x] [Review][Defer] Duplicate Student Index/`no` values across `<student>` records within one Info File are not detected or rejected [sams_core/info_file.py] — deferred, pre-existing scope boundary (belongs to `mapping.py` per Structural Seed, not this story's Appendix A parsing)
- [x] [Review][Defer] `session/@time` has no format/range validation (e.g. `"25:99"` accepted as-is) [sams_core/info_file.py:57-63] — deferred, pre-existing; not used by any decision logic in this story

## Dependencies

- **Requires:** nothing (first story; includes Day-1 scaffold).
- **Enables:** every other story.

## Definition of Done

Merged; both valid/invalid input paths demonstrated on real fixtures; entry script <50 lines; unit tests for info_file parsing and Sheet Identifier chain pass headlessly.

## Dev Agent Record

### Implementation Plan

- Built the Ports & Adapters scaffold exactly per the Architecture Structural Seed: `sams_core/{config,errors,models,info_file}.py` hold all domain logic; `sams.py` is a 34-line thin adapter (parse args → call engine → print/exit).
- Added one module beyond the Dev Notes' literal file list: `sams_core/image_io.py`. Image load/validate needed a home that (a) raises `InputError` per AD-6 rather than letting `sams.py` do domain work, and (b) isn't `info_file.py` (XML-only per AD-11). A single-purpose loader module was the smallest change consistent with AD-1 (thin adapters, all logic in `sams_core`).
- Opened all five `sample_signin-sheets/*.jpeg` images to read the real handwritten session dates (they match the Appendix A worked example exactly for sheet 1) and authored `sample_signin-sheets/{1..5}.xml` as the team's shared, committed Info Files — paired 1:1 with the sample sheets per the Dev Notes fixture guidance and the readiness report's note that sample filenames carry no date. Dates: 1→2019-05-31, 2→2019-06-21, 3→2019-06-28, 4→2019-07-05, 5→2019-07-12; all 5 sheets share the same 6-student roster.
- Added `tests/data/*.xml` + `corrupt.png` fixtures purely for negative-path unit tests (malformed XML, missing attribute, empty student list, bad Student Index, missing date, unreadable image) — kept separate from the team-shared `sample_signin-sheets/` fixtures.
- Sheet Identifier resolution chain (AD-11) implemented as `resolve_sheet_identifier()` in `info_file.py`, called from `sams.py` before any pipeline would run: Info File `session/@date` → `--date` flag → image filename stem (regex handles `DD.MM.YYYY`/`DD-MM-YYYY`/`DD_MM_YYYY`), each candidate validated as a real ISO 8601 calendar date.
- `AttendanceStatus` added to `models.py` per Dev Notes even though unused this story (future stories depend on it); `Session`/`InfoFile` dataclasses added to carry Session metadata per AC1 (not explicitly named in Dev Notes' `models.py` bullet, but required by the AC text "plus Session metadata").

### Completion Notes

- All 4 ACs verified: (1) valid image+info.xml load, CLI reports "Parsed 6 Student Records. Sheet Identifier: 2019-06-28", exit 0; (2) missing image and malformed-XML info file each produce a one-line stderr message, exit 2, no stack trace; (3) `--date` flag and filename-stem fallback (`10.07.2019.png` → `2019-07-10`) both verified by unit test and manual CLI run; (4) `sams.py` is 34 lines.
- 27 pytest tests added across `tests/test_info_file.py`, `tests/test_image_io.py`, `tests/test_cli.py` — all pass. Manually re-ran the CLI against real fixtures for both the happy path and each error path (see command transcript in this session) to confirm behavior beyond what the test suite encodes.
- Dependencies installed and pinned versions confirmed working on this machine: opencv-python 4.13.0.92, numpy 2.5.1, matplotlib 3.11.0 (already present), pytest 9.1.1 (dev-only, unpinned per architecture stack table).
- No regressions possible — this is the first story; no prior code existed.

### File List

- `sams.py` (new)
- `sams_core/__init__.py` (new)
- `sams_core/config.py` (new)
- `sams_core/errors.py` (new)
- `sams_core/models.py` (new)
- `sams_core/info_file.py` (new)
- `sams_core/image_io.py` (new)
- `requirements.txt` (new)
- `sample_signin-sheets/1.xml` (new)
- `sample_signin-sheets/2.xml` (new)
- `sample_signin-sheets/3.xml` (new)
- `sample_signin-sheets/4.xml` (new)
- `sample_signin-sheets/5.xml` (new)
- `tests/__init__.py` (new)
- `tests/test_info_file.py` (new)
- `tests/test_image_io.py` (new)
- `tests/test_cli.py` (new)
- `tests/data/info_no_date.xml` (new)
- `tests/data/info_malformed.xml` (new)
- `tests/data/info_missing_attribute.xml` (new)
- `tests/data/info_empty_students.xml` (new)
- `tests/data/info_bad_index.xml` (new)
- `tests/data/corrupt.png` (new)
- `tests/data/info_whitespace_only.xml` (new — code review regression fixture)
- `tests/data/info_fullwidth_index.xml` (new — code review regression fixture)
- `.gitignore` (modified — added `.pytest_cache/`)
- `_bmad-output/implementation-artifacts/deferred-work.md` (new — code review deferrals)

### Change Log

- 2026-07-12: Implemented Story 1.1 — repo scaffold, Info File parsing + validation, Sheet Identifier resolution chain, thin CLI adapter, and 27 passing unit/integration tests. Status set to review.
- 2026-07-12: Code review (Blind Hunter + Edge Case Hunter + Acceptance Auditor) triaged to 1 decision-needed, 7 patch, 2 defer, 6 dismissed. User resolved the AD-9/AC2 test-boundary tension by keeping `tests/test_cli.py`'s direct CLI import as a documented exception. Applied all 7 patches: catch-all exception handler in `sams.py` (AC2 "never a raw stack trace" now holds for any failure, not just `InputError`); `image_io.py` now reads via `np.fromfile`+`cv2.imdecode` to support non-ASCII paths; `info_file.py` now strips whitespace-only attributes, rejects non-ASCII digit Student Indexes, anchors the filename-date regex to the whole stem, and treats an explicit empty `--date` as an error instead of silently falling through; added 7 regression tests (34 total, all passing) covering the new catch-all branch, the `ProcessingError` exit-1 branch, and each fixed edge case. 2 low-severity findings (duplicate Student Index detection, `session/@time` validation) deferred to `deferred-work.md` as out of this story's scope. Status set to done.
