---
status: ready-for-dev
epic: 3
story: '3.2'
title: Compare a probe signature and report the verdict
frs: [FR-10]
owner: M6 (Topic 6 — Signature Verification), with M5 on comparison method
sprint: Week 2, Days 6–7
---

# Story 3.2: Compare a probe signature and report the verdict

## Story

As an operator,
I want to run `python investigate.py <index>` and get a similarity score plus a match/mismatch verdict,
So that I have evidence — not just a hunch — when I suspect a proxy signer.

## Acceptance Criteria

**Given** Reference Signatures and a probe crop for a student
**When** `python investigate.py <index>` runs (either index form)
**Then** `verification.py` compares the probe against all references, selects the best match inside the engine (frontends never re-implement match logic), and returns a `VerificationResult(best, all_scores, matched, threshold)`
**And** the similarity score is normalized to 0–1 with higher = more similar, `matched = score >= threshold`, and any distance metric is inverted inside the engine before leaving it.

**Given** the comparison method (OpenCV feature-based or image-similarity metric; ML optional)
**Then** the method and its threshold are documented in code, with the threshold as a named constant in `config.py`.

**Given** the CLI adapter
**When** the result returns
**Then** `investigate.py` (<50 lines) prints the numeric score and a plain match/mismatch verdict; a student with no probe or no references gets the no-data response, exit 0.

## Dev Notes

- **Create:** `sams_core/verification.py`, `investigate.py` (root entry, thin); extend `models.py` with `ReferenceScore(reference_path, score: float 0–1)` and `VerificationResult(best, all_scores, matched, threshold)`.
- **AD-9 score semantics (strict):** 0–1, HIGHER = more similar; `matched = score >= threshold`; distance metrics normalized/inverted INSIDE `verification.py`. Multi-reference best-match selection lives in the engine — the Web UI (4.6) only renders.
- **Method (deferred by architecture, your call):** candidates — ORB/SIFT feature matching, normalized cross-correlation on size-normalized binary crops, HOG + cosine similarity, or structural similarity. **Known risk (PRD):** tiny low-texture scribbles defeat classic feature matching — timebox the spike (Day 6), pick the method with best genuine/impostor separation, document honestly.
- **Preprocessing for comparison:** normalize crops (binarize, crop-to-ink bounding box, resize) before scoring — put params in `config.py` (AD-5, incl. `SIMILARITY_THRESHOLD`).
- **AD-6:** no probe yet / no references = no-data result family, exit 0.

## Dependencies

- **Requires:** 3.1 (references), 1.4 (probe crops).
- **Enables:** 3.3, 4.6.

## Definition of Done

`investigate.py 001` and `investigate.py 10000409` produce identical score + verdict; method + threshold documented in code; engine comparison headless-tested with fixture crops.
