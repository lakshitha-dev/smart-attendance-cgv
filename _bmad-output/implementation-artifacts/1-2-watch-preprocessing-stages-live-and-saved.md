---
status: review
epic: 1
story: '1.2'
title: Watch preprocessing stages live and saved
frs: [FR-2, FR-11, FR-16]
owner: M3 (Topic 3 — Image Preprocessing Pipeline), with M5 on stage display
sprint: Week 1, Days 2–3
baseline_commit: 6c6b54b07465fcd221055ad39251964eedb33834
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

## Tasks / Subtasks

- [x] Extend `models.py`: add `StageArtifact(order: int, slug: str, label: str, image: ndarray)` frozen dataclass (AD-2)
- [x] Add pipeline tunables to `config.py`: denoise kernel, adaptive-threshold block size/C, sheet-crop segmentation params, deskew angle thresholds (AD-5, no numeric literals in stage code)
- [x] Implement `sams_core/pipeline.py`: single ordered 7-slot registry (AD-3) with the first 5 slots wired to pure stage functions (original, greyscale, denoised, binarized, deskewed) and slots 6-7 reserved (`None`) for Stories 1.3/1.4; `run_pipeline()` generator yields `StageArtifact` in order
- [x] Implement sheet-boundary crop (background exclusion) inside the greyscale stage: segment the paper from the desk background via HSV saturation and crop to its bounding box, padded so boundary-touching ink survives
- [x] Implement `sams_core/artifacts.py`: `save_stage(sheet_id, stage)` writes `output/<Sheet Identifier>/NN-slug.png`, converting RGB→BGR (grayscale passes through) for `cv2.imwrite`
- [x] Wire `sams.py`: after input validation, iterate `run_pipeline()`, show each stage live in a `cv2.imshow` window titled with the stage label, save via `artifacts.py`, final keypress dismissal; keep entry script thin
- [x] Manually run all 5 sample sheets end-to-end; visually verify background exclusion + boundary-ink retention in saved artifacts
- [x] Unit tests: stage functions (headless, pure ndarray-in/ndarray-out), registry order/slugs, `artifacts.py` file-naming/no-overwrite-across-sheets
- [x] Run full test suite; verify AC coverage; zero `cv2.imshow` in `sams_core`

## Dependencies

- **Requires:** 1.1 (scaffold, input loading).
- **Enables:** 1.3, 1.4, 4.3.

## Definition of Done

All five sample sheets run through the five stages with live windows + saved `output/<sheet>/NN-slug.png`; stage functions unit-testable headlessly; zero `cv2.imshow` in `sams_core`.

## Dev Agent Record

### Implementation Plan

- `models.py`: added `StageArtifact(order, slug, label, image: np.ndarray)` frozen dataclass per AD-2.
- `pipeline.py`: single `_REGISTRY` tuple of `(order, slug, label, stage_fn | None)` covering all 7 glossary stages; slots 6-7 (`table-grid`, `per-cell-inspection`) carry `stage_fn=None` as an explicit placeholder for Stories 1.3/1.4. `run_pipeline()` is a generator that stops at the first `None` slot, so it naturally yields exactly the 5 implemented stages today and will yield more as later stories fill in the registry — no pipeline-runner changes needed then.
- Per-stage algorithm choices (deliberately story-level per Dev Notes):
  - **Background exclusion (AD-3/AC2), folded into the `greyscale` stage:** tried an edge+contour quadrilateral search first (Canny → `findContours` → `approxPolyDP`) but it never found a clean 4-point boundary on the real sample photos (largest candidate contour topped out at ~14% of frame area — the desk/paper edge isn't a continuous strong edge under this lighting). Replaced it with HSV-saturation segmentation: the paper is near-neutral (low saturation) while the desk background carries more colour, so Otsu-thresholding the saturation channel + morphological close/open reliably isolates the paper's silhouette (76-94% area fraction across all 5 sheets, matching visual expectation). Crop to its bounding box, padded by `CROP_PADDING_PX` so ink touching the table's outer boundary survives. This also incidentally removes a recurring background artifact (a diagonal dashed mark + corner glyphs, identical across all 5 photos — clearly something in the desk background, not the sheet) that was otherwise surviving thresholding and appearing in every saved stage.
  - **Denoising:** first implementation used `cv2.fastNlMeansDenoising`, which measured at ~19s/image at the sample sheets' native resolution (~4000x3000) — unusable for a "live" per-stage CLI display and it made the test suite take 164s. Replaced with `cv2.medianBlur` (near-instant, ~5s for all 5 sheets end-to-end), adequate for phone-camera sensor noise ahead of thresholding.
  - **Binarization:** adaptive Gaussian threshold (`cv2.ADAPTIVE_THRESH_GAUSSIAN_C`) over global Otsu, because the sample photos show uneven desk lighting across a single frame (confirmed visually — background regions binarize clean under adaptive threshold with no per-sheet tuning).
  - **Deskew:** first implementation measured tilt via `cv2.minAreaRect` over all binarized foreground pixels, but this was dominated by scattered text/annotations/margin marks scattered across the whole page and produced wildly wrong angles (~-77° raw, and even after applying the classic quadrant-normalization formula, rotating in the wrong direction and making skew worse). Replaced with a Hough-line-based estimator: `cv2.HoughLinesP` over the binarized ink mask, keep only long near-horizontal lines (the table's own grid lines dominate), rotate by the median angle. Verified visually straight on all 5 sheets.
- `artifacts.py`: `save_stage()` writes `output/<Sheet Identifier>/NN-slug.png`; RGB→BGR conversion for 3-channel stages, greyscale passes through unconverted. Mirrors `image_io.py`'s non-ASCII-path-safe pattern from Story 1.1 (`cv2.imencode` + `Path.write_bytes`-equivalent `tofile`, rather than `cv2.imwrite` directly).
- `sams.py`: added the pipeline loop after Sheet Identifier resolution — `cv2.imshow` per stage (titled with the stage label) + `cv2.waitKey(1)` to pump the window live during processing, `save_stage()` call, then a final `cv2.waitKey(0)` gated on `sys.stdin.isatty()` (so a real operator gets the "final keypress dismissal" UX Dev Notes call for, while a non-interactive invocation — the test suite, a CI run, a scripted batch — returns immediately instead of hanging forever waiting for a keypress nobody can send). Still 49 lines, under the AD-1 entry-script budget.

### Completion Notes

- All 3 ACs verified: (1) `run_pipeline()` yields `StageArtifact(order, slug, label, image)` for original→greyscale→denoised→binarized→deskewed in order (`tests/test_pipeline.py`), CLI shows each in a live `cv2.imshow` window titled with its label during processing, `artifacts.py` saves each to `output/<Sheet Identifier>/NN-slug.png`; (2) manually ran all 5 sample sheets end-to-end (both via the test suite and a standalone script whose saved PNGs I visually inspected) — every sheet completes, the desk background (including a recurring background artifact mark) is cropped out, and ink touching the table's outer border (e.g. signatures crossing the right border on sheets 1/3/4) is retained, not clipped; (3) `grep`-equivalent test (`test_no_cv2_imshow_in_sams_core`) confirms zero `cv2.imshow` in `sams_core`; all 5 stage functions take one ndarray and return one ndarray; every tunable lives in `config.py`.
- 11 new tests added (`tests/test_pipeline.py`, `tests/test_artifacts.py`); full suite is 45 tests, all passing in ~9s (was 164s during development with the first-draft `fastNlMeansDenoising` choice, before switching to median blur).
- Two significant course-corrections during implementation, both driven by testing against the real sample sheets rather than assumptions: the background-crop approach (quad/perspective → saturation/bounding-box) and the deskew angle estimator (`minAreaRect` → Hough lines). Both are documented above and in code comments so a future story doesn't rediscover the same dead ends.
- No regressions: all 34 Story 1.1 tests still pass unmodified.

### File List

- `sams_core/models.py` (modified — added `StageArtifact`)
- `sams_core/config.py` (modified — added pipeline stage tunables)
- `sams_core/pipeline.py` (new)
- `sams_core/artifacts.py` (new)
- `sams.py` (modified — wired pipeline display/save loop)
- `tests/test_pipeline.py` (new)
- `tests/test_artifacts.py` (new)

### Change Log

- 2026-07-13: Implemented Story 1.2 — `StageArtifact` contract, 7-slot canonical stage registry (5 stages wired), background-exclusion crop, denoise/binarize/deskew stages, stage-image writer, live CLI display, and 11 new passing tests. Status set to review.
