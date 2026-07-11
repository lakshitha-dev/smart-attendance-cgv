---
status: ready-for-dev
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

## Dependencies

- **Requires:** 1.4 (classifications), 1.1 (Student Records, Sheet Identifier).
- **Enables:** 1.6, 2.1, 4.2–4.4.

## Definition of Done

Full `sams.py` chain persists all five sheets; re-run without/with `--overwrite` behaves per AC; stdout summary readable; repository unit-tested headlessly (temp DB), including resolve/undo and upsert semantics.
