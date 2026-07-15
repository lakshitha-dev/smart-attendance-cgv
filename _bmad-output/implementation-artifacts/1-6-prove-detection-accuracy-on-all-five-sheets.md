---
status: ready-for-dev
epic: 1
story: '1.6'
title: Prove detection accuracy on all five sheets
frs: [FR-4, FR-5]
nfrs: [SM-1, SM-2, SM-3, SM-C1]
owner: M2 (Topic 2 — Data, Database & the Accuracy Test), with M6 + M4 on tuning
sprint: Week 1, Day 5 (🚧 GATE)
---

# Story 1.6: Prove detection accuracy on all five sheets

## Story

As the development group,
I want an executable accuracy gate against a committed ground truth,
So that SM-1..SM-3 pass by test run, not by eyeball — and the Web UI gate decision is objective.

## Acceptance Criteria

**Given** a team-adjudicated `tests/data/ground_truth.csv` (sheet × student → Present/Absent/Disputed) committed **before** any threshold tuning
**When** `pytest tests/test_accuracy.py` runs
**Then** classification accuracy is computed across all five sample sheets: 100% on non-Disputed rows (SM-1), Disputed rows scored separately and reported, never counted as errors.

**Given** the test suite
**Then** tests import `sams_core` only (no CLI/web) and run headlessly, and the suite also asserts the 7-stage emission contract per sheet (SM-3 executable).

**Given** accuracy shortfalls during tuning
**When** thresholds are adjusted
**Then** changes touch only global named constants in `config.py` — no per-sheet special-casing (SM-C1).

## Dev Notes

- **Create:** `tests/test_accuracy.py`, `tests/data/ground_truth.csv` (adjudicated Day 1 in the all-hands fixture session — MUST be committed before anyone tunes thresholds; this ordering is a PRD §6.3 constraint).
- **AD-9:** pytest; tests import `sams_core` only; the PRD §6.3 Web-UI gate is THIS test being green — an executable decision, not an opinion.
- **Ground truth format:** sheet id × student index → Present/Absent/Disputed. Disputed rows excluded from the SM-1 score, reported separately.
- **Also assert (SM-3):** exactly 7 `StageArtifact`s emitted per sheet, in registry order, correct slugs/labels.
- **Also verify (SM-2 smoke):** the three CLI entry scripts execute (subprocess smoke test acceptable for `sams.py`; `infovis.py`/`investigate.py` added when Epics 2–3 land).
- **This is the two-week plan's Day-5 gate:** green → Week 2 proceeds with Web UI; not green → descope ladder activates (see `sprint-plan.md`).

## Dependencies

- **Requires:** 1.4, 1.5 (full chain), Day-1 fixtures (info.xml × 5, ground_truth.csv).
- **Enables:** the §6.3 gate for Epic 4; regression safety for all tuning.

## Definition of Done

`pytest` green on all five sheets at 100% non-Disputed accuracy; Disputed report printed; stage-contract assertion in place; tuning log (which constants moved and why) noted in the PR for the report's testing section.
