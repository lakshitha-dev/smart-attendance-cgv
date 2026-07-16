---
status: done
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

## Tasks / Subtasks

### Review Findings (code review 2026-07-16, post sprint-5 merge)

- [x] [Review][Patch] The SM-1 gate is structurally vacuous under key drift: unmatched records are skipped and nothing asserts the denominator — assert scored == non-Disputed truth count AND that every truth row was consumed (bidirectional) [tests/test_accuracy.py:61,86]
- [x] [Review][Patch] CSV loader unhardened: locale encoding (Excel BOM breaks it), no header check, no status-vocabulary validation, duplicate keys last-win, short rows silently unscored, and it strips '#' comments the README says cannot exist — utf-8-sig, validate header/rows/statuses, reject duplicates, fail on comments [tests/test_accuracy.py:31]
- [x] [Review][Patch] TUNING_LOG.md is factually wrong as merged ("gate is RED 76.7%", zero v_lines, thresholds 0.020/0.006, recommends LOCATE_HOUGH_* constants that no longer exist) — add a prominent dated addendum correcting status to GREEN 30/30 and mapping stale claims to the rework [TUNING_LOG.md:3]
- [x] [Review][Patch] The decisive band retune (0.020/0.006 → 0.030/0.015) is recorded nowhere in the tuning log, which affirmatively claims the bands were "left unchanged" — document it in the addendum with justification (DoD: tuning log for the report) [TUNING_LOG.md:95, sams_core/config.py:118]
- [x] [Review][Patch] Provenance claims are anachronistic vs git history (config says "tuned 2026-07-13 against the committed CSV"; the CSV's first commit is 2026-07-16, one second before the tuned values) — reword config + README to state adjudication happened in the working tree with commit ordering as attestation, not proof [sams_core/config.py:65, tests/data/ground_truth-README.md:6]
- [x] [Review][Patch] Gate destroys the repo's real `output/` tree and SM-2 writes the real sams.db, contradicting the module's "temp DB (AD-9)" claim — add SAMS_DB_PATH/SAMS_OUTPUT_DIR env seams in config.py and point fixture + subprocess at tmp dirs [tests/test_accuracy.py:44,124, sams_core/config.py:7]
- [x] [Review][Patch] SM-2 subprocess: headless/env inherited by accident, no output encoding (UnicodeEncodeError on non-cp1252 names → false red), TimeoutExpired loses all diagnostics, and assertions can't detect a broken-but-not-crashed CLI — explicit env, encoding="utf-8", timeout handler, assert per-record output [tests/test_accuracy.py:129]
- [x] [Review][Patch] One failing sheet aborts all SM-1 reporting (module fixture error discards the other four sheets' results) — capture per-sheet failures and report them in the gate output [tests/test_accuracy.py:37]
- [x] [Review][Patch] Disputed handling is silent when zero rows are Disputed (DoD says "Disputed report printed") — always print the Disputed count [tests/test_accuracy.py:73]
- [x] [Review][Patch] SM-3 never checks the run holder the 7-stage contract feeds — assert sheet_result/cell_results populated after exhaustion [tests/test_accuracy.py:113]
- [x] [Review][Patch] Dead imports (defaultdict, SamsError, AttendanceStatus) betray trimmed-out validation [tests/test_accuracy.py:10]
- [x] [Review][Patch] README's two adjudication notes contradict each other on which sheet holds the straddling signature (06-21 rows 2–3 vs 07-05 row 3) — reconcile the prose; the status columns agree [tests/data/ground_truth-README.md:9]
- [x] [Review][Defer] DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION=0.72 was tuned while the fallback fired on every sheet; post-rework the fallback is a rare path and the value is untested on current geometry — re-validate if localization ever fails on a real sheet [sams_core/config.py:83]

## Dependencies

- **Requires:** 1.4, 1.5 (full chain), Day-1 fixtures (info.xml × 5, ground_truth.csv).
- **Enables:** the §6.3 gate for Epic 4; regression safety for all tuning.

## Definition of Done

`pytest` green on all five sheets at 100% non-Disputed accuracy; Disputed report printed; stage-contract assertion in place; tuning log (which constants moved and why) noted in the PR for the report's testing section.
