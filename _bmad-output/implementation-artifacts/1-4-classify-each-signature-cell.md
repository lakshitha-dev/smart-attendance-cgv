---
status: done
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

## Tasks / Subtasks

### Review Findings (code review 2026-07-13, fix-localization-detection)

- [x] [Review][Patch] FR-11 "live during processing" defeated: `run_pipeline_with_localization/_detection` materialize every stage via `list()` before the first window opens — restructure to a true streaming generator with a post-iteration result holder [sams_core/pipeline.py:192]
- [x] [Review][Patch] Empty `cell_rois["rows"]` list is falsy, so `_row_bands` falls back to raw h_lines and resurrects the header band locate deliberately excluded (phantom student row) — distinguish `None` from `[]` [sams_core/detect.py:101]
- [x] [Review][Patch] Coverage denominator uses the +60px margin-padded column span, contradicting the documented "un-dilated ROI area" semantics — compute cell area from the un-padded signature column [sams_core/detect.py:291]
- [x] [Review][Patch] Stage 6/7 identity (order/slug/label) defined in three places while the AD-3 registry slots sit at `None` — single-source them from the registry [sams_core/pipeline.py:143]
- [x] [Review][Patch] Every detect test exercises only the raw-h_lines fallback; the production `cell_rois` path (incl. straddle attribution and grid-whitened crops) has zero assertions — add cell_rois-path tests [tests/test_detect.py:20]
- [x] [Review][Patch] `crop_source` full-frame copy + scatter is exactly `cv2.bitwise_not(ink_mask)` computed three lines above — reuse it (keeps crops and measured ink from diverging) [sams_core/detect.py:275]
- [x] [Review][Patch] No display guard: `cv2.namedWindow` runs unconditionally (headless/CI crash; 7 GUI windows per CLI test) and mid-run exceptions leak open windows — gate display on interactivity, ensure teardown on error [cli_display.py:26, sams.py:27]
- [x] [Review][Patch] Operator sees no results until windows are dismissed (summary prints after the blocking waitKey); summary hardcodes `output/...` instead of using the returned crop paths, and "Saved 0 signature crops" presents total failure as normal [sams.py:33, cli_display.py:50]
- [x] [Review][Patch] Fallback `_signature_column_bounds` uses `v_lines[-1]` (the column's RIGHT border) as the LEFT edge when a full grid is present [sams_core/detect.py:79]
- [x] [Review][Patch] `save_crops` indexes `student_indices[row_index]` unguarded (IndexError → partial output); `show_stage_live` divides by zero on a degenerate image [sams_core/detect.py:332, cli_display.py:23]
- [x] [Review][Patch] `ground_truth.csv` leading `#` comment lines break `csv.DictReader`/pandas — move provenance to a sidecar README, keep the CSV clean for the Story 1.6 harness [tests/data/ground_truth.csv:1]
- [x] [Review][Patch] Config self-contradiction: "values below are PROVISIONAL … tuning happens in Story 1.6" still sits above the tuned-and-justified thresholds [sams_core/config.py:57]
- [x] [Review][Patch] Stale teammate docs reference the deleted scripts and removed `LOCATE_HOUGH_*` constants (FINAL_DELIVERY_CHECKLIST.md, IMPLEMENTATION_COMPLETE_1_3.md, VERIFICATION_1_3.md) — correct the dead references [FINAL_DELIVERY_CHECKLIST.md:217]
- [x] [Review][Defer] Crop files get Student Index names from a blind count-equality check — authoritative row→record mapping is Story 1.5's scope; revisit there [sams.py:31]
- [x] [Review][Defer] `connectedComponentsWithStats` + per-component masks run over the full 12MP frame when only the signature column matters — column-slice optimization; current runtime acceptable [sams_core/detect.py:284]
- [x] [Review][Defer] RGB→BGR conversion and ink-polarity inversion duplicated across artifacts.py / cli_display.py / detect.py / pipeline.py — extract shared helpers later [cli_display.py:22]

## Dependencies

- **Requires:** 1.3 (cells + grid masks), 1.2 (binarized image).
- **Enables:** 1.5, 1.6, 3.1, 3.2.

## Definition of Done

Classification runs on all five sheets; straddling-signature cases (sheets 1 and 5) attribute to exactly one row; composite inspection stage displays and saves; crops saved per student; attribution logic unit-tested.
