---
status: done
epic: 1
story: '1.5'
title: Persist attendance and report results
frs: [FR-5, FR-6]
owner: M2 (Topic 2 — Data, Database & the Accuracy Test)
sprint: Week 1, Days 3–5
---

# Story 1.5: Persist attendance and report results

## Story

As an operator,
I want classifications mapped to Student Records and saved to the Local DB with a readable summary,
So that attendance is durably recorded and visible without opening the database.

## Acceptance Criteria

**Given** classifications and the Info File's `no` ordinals
**When** mapping runs
**Then** each decision maps by row order to one Student Index; the canonical 8-digit index is the only form stored.

**Given** `repository.py` as the sole `sqlite3` importer
**When** results persist
**Then** the schema auto-creates on first run, one Attendance Record per Student Record upserts keyed (Student Index, Sheet Identifier) with session metadata, connections are per-operation, and re-processing updates rather than duplicates.

**Given** a sheet with saved operator resolutions
**When** re-processed without `--overwrite`, **then** resolutions survive
**And** when re-processed with `--overwrite`, they are replaced.

**Given** processing succeeds via the single `process_sheet()` entry point (persists internally; partial iteration/abort never persists)
**Then** the CLI prints the success line (record count + Sheet Identifier) and a per-student stdout summary — Student Index, name, Present/Absent/Ambiguous — with Ambiguous first-class, never coerced.

## Dev Notes

- **Create:** `sams_core/mapping.py`, `sams_core/repository.py`; extend `models.py` with `AttendanceRecord` (carries session/subject metadata); implement `process_sheet(image_path/bytes, info_file, sheet_id_override=None, overwrite=False)` in the engine (AD-12) — the ONE call both frontends make; stage emission is a side channel.
- **AD-4 (repository contract):** only module importing `sqlite3`; `ensure_schema` on open; upsert keyed (Student Index, Sheet Identifier); `resolved_by_operator` flag survives re-processing unless `overwrite=True`; read APIs `list_students()`, `has_operator_resolutions(sheet_id)`; write API `resolve(sheet_id, student_index, status, by_operator=True)` with undo restoring Ambiguous; **per-operation connections via context manager** (Streamlit threads + concurrent CLI safety); no image blobs in the DB.
- **Index resolution:** canonical 8-digit index is the ONLY stored/queried key; the short ordinal (`002`) resolves via ONE engine resolver before any read/write — no adapter parses index forms (AD-4).
- **Row-count mismatch:** map by row order, carry warning from `SheetResult.warnings` into the CLI output (UX error-catalog wording: "matched by row order — please double-check").
- **DB path** from `config.py`, relative to project root; bootstraps automatically (FR-15).

## Tasks / Subtasks

### Review Findings (code review 2026-07-16, post sprint-5 merge)

- [x] [Review][Patch] Persistence phase is not atomic: upsert_students + save_attendance + N register_signature_image each commit independently — a mid-persist failure leaves partial state, violating AD-12's "abort never persists"; do all step-6 writes in ONE transaction [sams_core/pipeline.py:375, sams_core/repository.py:39]
- [x] [Review][Patch] Re-runs wipe crops the DB still references and mismatch runs skip registration, leaving dangling signature_images rows — clear the sheet's stale registrations inside the persist transaction [sams_core/pipeline.py:349,378]
- [x] [Review][Patch] `resolve()`/`undo_resolution()` silently no-op on nonexistent rows (rowcount ignored) and undo on a never-resolved row destroys the machine verdict — return success, guard undo with `resolved_by_operator = 1` [sams_core/repository.py:204-248]
- [x] [Review][Patch] Short-ordinal resolution is global across all rosters ever ingested and returns an arbitrary student on ambiguity; `CAST(no AS INTEGER)` maps garbage to 0 — detect ambiguity and refuse with candidates listed [sams_core/repository.py:144]
- [x] [Review][Patch] `save_attendance` hardcodes `resolved_by_operator=0`, discarding the model's flag — write the record's value [sams_core/repository.py:180]
- [x] [Review][Patch] Preserved-resolution skip branch freezes stale session metadata on resolved rows — update metadata while preserving status + flag [sams_core/repository.py:174]
- [x] [Review][Patch] CLI prints fresh machine statuses and "Saved N" even when operator resolutions were preserved (DB disagrees with stdout) — save_attendance returns (saved, preserved) counts, surface a preserved-rows warning + honest count [sams_core/repository.py:167, cli_display.py:73]
- [x] [Review][Patch] Duplicate Student Index / duplicate `no` in one Info File silently collapses records, crops, and roster rows — validate uniqueness at parse time [sams_core/info_file.py:86]
- [x] [Review][Patch] Non-contiguous or duplicate `row_index` values raise raw IndexError / silently drop detections despite length-equality guards — validate range + uniqueness in mapping [sams_core/mapping.py:99, sams_core/pipeline.py:378]
- [x] [Review][Patch] Row-count mismatch reported twice in two wordings (locate's + mapping's UX-catalog line) — collapse to one in process_sheet, keeping the UX wording for CLI output [sams_core/pipeline.py:364]
- [x] [Review][Patch] Schema allows NULL keys (SQLite PK quirk) — declare NOT NULL on key columns [sams_core/repository.py:62]
- [x] [Review][Patch] No busy timeout and raw `sqlite3.OperationalError` escapes the engine's error hierarchy — set connect timeout, wrap as ProcessingError [sams_core/repository.py:47]
- [x] [Review][Patch] `_connect` rollback misses KeyboardInterrupt (`except Exception`) — catch BaseException [sams_core/repository.py:49]
- [x] [Review][Patch] `list_students` ORDER BY `no` sorts text lexicographically ("10" < "2") — order by the stable canonical index [sams_core/repository.py:120]
- [x] [Review][Patch] Crop-location line dropped from the run summary (operators/Epic 3 lose the only pointer to the crops dir) — restore it [cli_display.py:73]
- [x] [Review][Patch] `process_sheet` (AD-12's core guarantees) has zero automated tests despite the injectable repository seam — add happy-path, abort-never-persists, and overwrite-semantics tests [tests/]
- [x] [Review][Defer] Sheet Identifier = bare date makes two same-date sessions collide (artifacts + DB rows overwrite) — the date-as-key decision is PRD §3/AD-11 architecture scope; raise via correct-course if multi-subject use is real [sams_core/pipeline.py:344]
- [x] [Review][Defer] Pre-existing sams.db with older schema fails with raw sqlite errors — schema versioning is beyond coursework scope; the DB is disposable/bootstrapable [sams_core/repository.py:62]
- [x] [Review][Defer] On row-count mismatch, attendance persists by row order while crops refuse index names and skip registration — defensible asymmetry (wrong-name evidence worse than missing) but revisit when Epic 3 consumes probes [sams_core/mapping.py:92]

## Dependencies

- **Requires:** 1.4 (classifications), 1.1 (Student Records, Sheet Identifier).
- **Enables:** 1.6, 2.1, 4.2–4.4.

## Definition of Done

Full `sams.py` chain persists all five sheets; re-run without/with `--overwrite` behaves per AC; stdout summary readable; repository unit-tested headlessly (temp DB), including resolve/undo and upsert semantics.
