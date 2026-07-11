---
status: ready-for-dev
epic: 1
story: '1.2'
title: Watch preprocessing stages live and saved
frs: [FR-2, FR-11, FR-16]
owner: M3 (Topic 3 — Image Preprocessing Pipeline), with M5 on stage display
sprint: Week 1, Days 2–3
---

# Story 1.2: Watch preprocessing stages live and saved

## Story

As an operator,
I want each preprocessing stage displayed live while the program runs and saved as a labelled image,
So that I can follow what SAMS did to my photo and capture report screenshots.

## Acceptance Criteria

**Given** validated inputs
**When** processing runs
**Then** `pipeline.py`'s single ordered registry emits `StageArtifact(order, slug, label, image)` for original → greyscale → denoised → binarized → deskewed, in order
**And** the CLI shows each stage live in an OpenCV window titled with its stage name (during processing, not after)
**And** `artifacts.py` saves each stage as `output/<Sheet Identifier>/NN-slug.png` so five sheets never overwrite each other's screenshots.

**Given** all five sample sheets
**When** each is processed
**Then** preprocessing completes end-to-end on every sheet; photo background outside the sheet is excluded while ink near/touching the table boundary is retained.

**Given** the engine code
**Then** `cv2.imshow` never appears inside `sams_core`; stages are pure ndarray-in/ndarray-out functions; all tunables live in `config.py` (no numeric literals in stage code).

## Dev Notes

- **Create:** `sams_core/pipeline.py` (canonical stage registry, AD-3), `sams_core/artifacts.py` (stage writer, AD-7); extend `models.py` with `StageArtifact(order: int, slug: str, label: str, image: ndarray)`.
- **AD-3:** pipeline is a generator (or callback-fed runner) yielding `StageArtifact` from ONE ordered registry — names/slugs/order defined exactly once, glossary-verbatim. Full registry is 7 stages; this story implements the first five (table-grid stage comes with Story 1.3, per-cell inspection with 1.4 — registry designed for all 7 now).
- **AD-2 image contract:** `StageArtifact.image` is display-ready uint8, 2D grayscale or 3-channel **RGB**; adapters convert (CLI RGB→BGR for `cv2.imshow`; `artifacts.py` converts for `cv2.imwrite`).
- **AD-7:** CLI stage windows shown live DURING processing, titled with stage names (saving alone does not satisfy FR-11). Non-blocking display with final keypress dismissal is the UX-assumed default.
- **Robustness targets (NFR-1):** moderate skew/perspective, uneven lighting, desk background, punch holes, margin notes, white-out, red grader marks, varying resolution across the 5 samples.
- **Per-stage algorithm choices** (Otsu vs adaptive threshold, denoise kernel) are deliberately story-level decisions — pick, document in code, put every tunable in `config.py` (AD-5, no per-sheet values).
- **UX-DR16:** stage vocabulary shared verbatim between CLI window titles, saved filenames, and (later) Web strip labels.

## Dependencies

- **Requires:** 1.1 (scaffold, input loading).
- **Enables:** 1.3, 1.4, 4.3.

## Definition of Done

All five sample sheets run through the five stages with live windows + saved `output/<sheet>/NN-slug.png`; stage functions unit-testable headlessly; zero `cv2.imshow` in `sams_core`.
