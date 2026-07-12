---
status: ready-for-dev
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

## Dependencies

- **Requires:** 1.2 (deskewed output; can develop against sheet-1 deskew from Day 2).
- **Enables:** 1.4.

## Definition of Done

Correct dynamic row count on all five sheets; grid overlay stage visible and saved; lecturer row excluded; row-count-mismatch path unit-tested; no per-sheet constants.
