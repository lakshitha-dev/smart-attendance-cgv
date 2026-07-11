---
status: ready-for-dev
epic: 1
story: '1.4'
title: Classify each Signature Cell — Present, Absent, or Ambiguous
frs: [FR-4, FR-11, FR-16]
owner: M5 (Topic 5 — Signature Detection & Classification), with M1 on attribution
sprint: Week 1, Days 3–5
---

# Story 1.4: Classify each Signature Cell — Present, Absent, or Ambiguous

## Story

As an operator,
I want handwritten ink measured and attributed per Signature Cell with the inspection visible,
So that present/absent is decided automatically and uncertain cells are flagged rather than guessed.

## Acceptance Criteria

**Given** localized cells with grid lines masked
**When** detection runs
**Then** handwritten ink (any pen colour) is segmented into connected components, each attributed to exactly one Signature Cell (majority-area rule, centroid tie-break, dilated ROIs for spillover) — a straddling signature (samples 1 and 5) counts for exactly one row, and no component is evidence for two cells.

**Given** attributed ink per cell
**When** classification runs
**Then** coverage ≥ upper threshold → Present, ≤ lower threshold → Absent, between → Ambiguous, with both thresholds as documented named constants in `config.py`.

**Given** the pipeline completes
**Then** a "per-cell inspection" composite overlay is emitted as the final `StageArtifact` (7 registry stages total)
**And** per-cell signature crops are saved via `artifacts.py` to `output/<Sheet Identifier>/crops/<student_index>.png` (not as StageArtifacts) — ready for Epic 3.

## Dev Notes

- **Create:** `sams_core/detect.py`; extend `artifacts.py` with crop writer.
- **Attribution policy (PRD FR-4, verbatim):** connected components AFTER grid-line masking (from 1.3); each component → ONE cell by majority area, centroid tie-break; cell ROIs dilated to capture spillover including into the right margin; a single component is NEVER presence evidence for two cells. Lecturer's Metadata-Row signature never counted.
- **Classification bands (AD-5):** `INK_COVERAGE_PRESENT_THRESHOLD`, `INK_COVERAGE_ABSENT_THRESHOLD` in `config.py`, documented. Ambiguous is a first-class status, never coerced.
- **Any pen colour:** measure post-binarization ink, not colour-filtered.
- **7th stage:** "per-cell inspection" = ONE composite overlay image (per AD-3, exactly 7 registry stages; crops flow through `artifacts.py` separately, AD-10).
- **Crops (AD-10):** `output/<Sheet Identifier>/crops/<student_index>.png` — these become Epic 3's probes and the source for reference curation.
- **SM-C1:** no per-sheet thresholds, no pixel coordinates. Initial threshold values are provisional — tuning happens in Story 1.6 AFTER `ground_truth.csv` is committed.

## Dependencies

- **Requires:** 1.3 (cells + grid masks), 1.2 (binarized image).
- **Enables:** 1.5, 1.6, 3.1, 3.2.

## Definition of Done

Classification runs on all five sheets; straddling-signature cases (sheets 1 and 5) attribute to exactly one row; composite inspection stage displays and saves; crops saved per student; attribution logic unit-tested.
