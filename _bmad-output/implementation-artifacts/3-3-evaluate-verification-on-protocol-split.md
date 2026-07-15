---
status: ready-for-dev
epic: 3
story: '3.3'
title: Evaluate verification on the protocol split
frs: [FR-9, FR-10]
nfrs: [SM-4]
owner: M4 + M7 (evaluation + score-distribution plots)
sprint: Week 2, Days 6–8
---

# Story 3.3: Evaluate verification on the protocol split

## Story

As the development group,
I want the verifier evaluated against genuine and impostor probes with the threshold justified,
So that SM-4 is demonstrated and the report can defend the method honestly.

## Acceptance Criteria

**Given** the committed FR-9 split (references: sheets 1–3; probes: sheets 4–5; impostors: other students' signatures)
**When** the evaluation runs as a pytest module importing `sams_core` only
**Then** genuine probes report match and impostor probes report mismatch on that split (SM-4), with results reported per student.

**Given** the chosen threshold
**Then** its value is justified in documentation against the split's score distributions (genuine vs impostor), including honest reporting of any trade-off if score separation is poor — the documented attempt is itself the graded outcome.

**Given** tuning is needed
**When** the threshold changes
**Then** only the named constant in `config.py` moves — the same value `investigate.py` and the future Web UI read (no per-frontend thresholds).

## Dev Notes

- **Create:** `tests/test_verification.py` (imports `sams_core` only, AD-9); a small evaluation script/notebook output producing **score-distribution plots** (genuine vs impostor histograms with the threshold line) via `visualization.py`-style Figure code — these plots go straight into the report (data-visualization credit for M4/M7).
- **Evaluation matrix:** for each student with references — genuine probe scores (their own sheets 4–5 crops) vs impostor scores (other students' crops). Report per-student verdicts + overall separation.
- **Threshold justification:** pick the threshold from the distributions (e.g., midpoint of separation or an F1-style argument); write 3–5 sentences in the PR that can be lifted into the report. If separation is poor, SAY SO — the brief credits the honest attempt (PRD FR-10 note).
- **SM-4 target:** correct match/mismatch verdicts on the protocol split, threshold documented.

## Dependencies

- **Requires:** 3.2 (scorer), 3.1 (references + manifest).
- **Enables:** report's testing section; confidence in 4.6.

## Definition of Done

pytest evaluation green (or failures honestly documented with distributions); score-distribution figure saved for the report; threshold constant final in `config.py` with written justification.
