---
status: done
epic: 1
story: '1.3'
title: Locate the student table and Signature Cells
frs: [FR-3]
owner: M4 (Topic 4 — Table & Signature-Cell Detection), with M8 on grid masking
sprint: Week 1, Days 2–4
---

# Story 1.3: Locate the student table and Signature Cells

## Story

As an operator,
I want the student table and each row's Signature Cell located on the normalized sheet,
So that each signature is checked against the correct student row.

## Acceptance Criteria

**Given** the deskewed image
**When** localization runs
**Then** the 5-column student table (No | Student No | Title | Student Name | Signature) is selected as the grid below the 4-column Metadata Row band, and a "detected table grid" `StageArtifact` is emitted showing the overlay
**And** detected grid lines are masked out of cell ROIs so printed borders are never counted as ink
**And** the Metadata Row / lecturer signature is never treated as a student row.

**Given** a sheet whose detected row count differs from the Info File record count
**When** processing continues
**Then** the discrepancy lands in `SheetResult.warnings` (flagged, not dropped, not an exception).

**Given** all five sample sheets
**Then** localization succeeds with the correct dynamic row count on each, without OCR of printed header text and without hard-coded pixel coordinates (SM-C1).

## Dev Notes

- **Create:** `sams_core/locate.py`; extend `models.py` with `SheetResult` skeleton (`warnings: list[str]`).
- **Selection mechanism (explicit per PRD FR-3):** the student table is the 5-column grid BELOW the Metadata Row band (which is a 4-column table: Date | Time | Lecturer's Name | Lecturer Signature). Column layout fixed; **row count dynamic**.
- **Do NOT OCR header text** — the printed template contains typos ("Signatue", "Lecture's Name"); header-text matching is a dead end.
- **Grid masking:** mask detected grid lines out of cell ROIs before any ink measurement (Story 1.4 depends on this).
- **Registers the 6th stage** ("detected table grid") in the AD-3 registry — overlay drawn on a copy, RGB uint8.
- **AD-6:** row-count mismatch is a warning in `SheetResult.warnings`, never an exception; processing continues matched by row order.
- **Tunables** (line-detection params, band thresholds) → `config.py` only; no pixel coordinates (SM-C1 / NFR-8).

## Tasks / Subtasks

### Review Findings (code review 2026-07-13, fix-localization-detection)

- [x] [Review][Patch] Grid mask absorbs long handwriting strokes — built from ALL long ink runs on the page, not just detected table lines; a straight signature underline ≥ width//15 px is subtracted from ink and erased from crops [sams_core/locate.py:178]
- [x] [Review][Patch] `cell_rois` published even for fallback-selected non-5-column tables — a long vertical pen stroke can become a "column" and the signature column collapses to a sliver [sams_core/locate.py:237]
- [x] [Review][Patch] Rewritten locate.py has zero unit tests (DoD violation; the diff also deleted the only scripts exercising it) — add tests/test_locate.py covering 5-below-4 selection, header exclusion, dynamic rows, mismatch warning [tests/]
- [x] [Review][Patch] Per-region drift dilation biases border-line positions ~7px inward (mask cropped before dilating) and repeats full-frame work per candidate region — dilate masks once, globally [sams_core/locate.py:97]
- [x] [Review][Patch] `_grid_mask` recomputes the h|v OR and dilation `_find_tables` already produced — compute the combined grid once [sams_core/locate.py:114,178]
- [x] [Review][Patch] No-table case omits the row-count-mismatch warning the AC requires (only the generic "no structure" message) [sams_core/locate.py:230]
- [x] [Review][Patch] `table_bbox` published from the join-dilated component stats, overshooting the printed table ~5px/side — derive from line extents [sams_core/locate.py:120]
- [x] [Review][Patch] `models.py` still documents `detected_grid_lines` as sheet-global; it is now student-table-only [sams_core/models.py:69]
- [x] [Review][Defer] Metadata + student tables merging into one component (vertical gap ≤ ~11px join kernel) leaves leading metadata bands as phantom student rows with only generic warnings — needs structural handling; mitigated now by explicit warning when no separate metadata band is found; revisit during Story 1.6 evaluation [sams_core/locate.py:115]
- [x] [Review][Defer] Deskew (Hough, DESKEW_*) and locate (morphology, LOCATE_*) are two independently tuned detectors for the same table lines — unify into one line-evidence helper later [sams_core/pipeline.py:92]

## Dependencies

- **Requires:** 1.2 (deskewed output; can develop against sheet-1 deskew from Day 2).
- **Enables:** 1.4.

## Definition of Done

Correct dynamic row count on all five sheets; grid overlay stage visible and saved; lecturer row excluded; row-count-mismatch path unit-tested; no per-sheet constants.
