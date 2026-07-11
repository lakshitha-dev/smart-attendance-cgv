---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - '_bmad-output/planning-artifacts/prds/prd-CGV Group Assignment-2026-07-10/prd.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-CGV Group Assignment-2026-07-10/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/ux-designs/ux-CGV Group Assignment-2026-07-10/DESIGN.md'
  - '_bmad-output/planning-artifacts/ux-designs/ux-CGV Group Assignment-2026-07-10/EXPERIENCE.md'
  - 'CS402.3 Coursework.md'
---

# CGV Group Assignment - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the CGV Group Assignment — SAMS (Student Attendance Management System), decomposing the requirements from the PRD, UX Design contract (DESIGN.md + EXPERIENCE.md), Architecture Spine, and the CS402.3 coursework brief into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-1: Load and validate inputs — `python sams.py <image> <info.xml>` loads the Signing Sheet image (JPEG and PNG both accepted) and parses the Info File into Student Records and Session metadata per the Appendix A schema; valid inputs report parsed record count and resolved Sheet Identifier; invalid inputs exit with a clear error message and non-zero exit code, never a raw stack trace.

FR-2: Image preprocessing pipeline — ordered stages (greyscale → noise reduction → thresholding/binarization → deskew/perspective correction) using OpenCV + NumPy; runs end-to-end on all five sample sheets; each stage produces a distinct, displayable, savable intermediate image; background outside the sheet is excluded while ink near/touching the table boundary is retained.

FR-3: Table & signature-cell localization — locate the 5-column student table (No | Student No | Title | Student Name | Signature) below the 4-column Metadata Row band; mask detected grid lines out of cell ROIs; never count the Metadata Row/lecturer signature as a student row; fixed columns, dynamic row count (discrepancies vs Info File reported, not dropped); each Signature Cell tied to correct row position; no OCR of printed header text.

FR-4: Signature presence detection with ink attribution — segment handwritten ink (any pen colour) into connected components after grid-line masking; attribute each component to exactly one Signature Cell (majority area, centroid tie-break, dilated ROIs for spillover); classify by ink coverage: ≥ upper threshold → Present, ≤ lower threshold → Absent, between → Ambiguous; 100% correct on the committed ground-truth key across all five sheets; straddling signatures attributed to exactly one row.

FR-5: Map detections to Student Records — associate each classification with the correct Student Index via row order and the Info File `no` ordinal; row-count mismatch vs Info File is flagged, not silently dropped.

FR-6: Persist attendance to Local DB — one Attendance Record per Student Record keyed (Student Index, Sheet Identifier) with session/subject metadata; re-processing the same Sheet Identifier updates (upsert), never duplicates; operator resolutions of Ambiguous survive unless overwrite is explicitly confirmed; DB file and schema auto-created on first run.

FR-7: Query attendance by student — `python infovis.py <index>` accepts both index forms (8-digit Student No and short `No` ordinal); both return the same records; unknown index reports "no data" listing valid indices rather than erroring.

FR-8: Render attendance graph — Matplotlib per-Session Present/Absent timeline (colour-coded, Ambiguous distinct on its own mid-band) with overall attendance-rate percentage annotated; title, axis labels, legend; renders from Attendance Records only, no image re-processing.

FR-9: Maintain reference signatures — Reference Signatures stored as image files under `references/<student_index>/`, registered into the Local DB on first use; default dataset split: references from sheets 1–3, probes from sheets 4–5, impostor probes from other students; reference and probe sets disjoint by sheet; retrievable by either index form.

FR-10: Compare and report match — `python investigate.py <index>` (either index form) compares probe signature(s) against Reference Signature(s); outputs a numeric similarity score plus a thresholded match/mismatch verdict; method and threshold documented against the FR-9 split; genuine probes match, impostor probes mismatch (SM-4); feature-based or ML-based comparison.

FR-11: Show step-by-step processing progress — `sams.py` displays each major pipeline stage live on screen while processing (original, greyscale, denoised, binarized, deskewed, detected table grid, per-cell inspection), in order, individually labelled; each stage additionally saved as a labelled image file to an output folder for report screenshots (saving alone does not satisfy this FR).

FR-12: Upload and process a sheet from the browser — Web UI accepts sample JPEG/PNG photos and `info.xml` upload in mobile or desktop browser; processing is an explicit one-shot action (once per press, never a side-effect of Streamlit reruns or unrelated widget interaction); invalid inputs produce human-readable on-screen errors; responsive, touch-friendly layout.

FR-13: Live pipeline display, results, and Ambiguous resolution — Web UI renders engine-emitted stage images in pipeline order (single display contract, not a second implementation), then the per-student result table; results persisted to Local DB; Ambiguous rows visually distinct with one-tap Present/Absent resolution that updates the Attendance Record.

FR-14: Student lookup views — Web UI accepts a Student Index (either form) for the attendance summary graph (FR-8) and signature verification (FR-10) without a terminal; parity defined at the data layer: same engine query/figure and same score/threshold outcome as the CLI.

FR-15: CLI wrappers with engine parity and clean packaging — the three brief-verbatim commands run on a fresh machine producing the same detections, graphs, and verdicts as the Web UI from the same Core Engine and Local DB; each CLI is a thin entry point with no duplicated logic; Core Engine + CLI import only OpenCV/NumPy/Matplotlib/stdlib (sqlite3, xml); Streamlit is an optional extra; one-step documented install (`pip install -r requirements.txt`, pinned); DB bootstraps automatically; all paths relative to project root.

FR-16: Engine-emitted stage artifacts (single display contract) — the Core Engine exposes pipeline progress as a sequence of labelled stage images via callback/generator and never opens display windows itself (`cv2.imshow` forbidden in engine); one stage-emission code path serves both frontends with identical stage names and order; engine importable and testable headlessly.

### NonFunctional Requirements

NFR-1: Robustness to phone-photo variance — the pipeline tolerates moderate skew/perspective, uneven lighting, desk background, punch holes, handwritten margin notes, white-out patches, non-pen marks (e.g. red grader annotation), and varying resolution across the five sample sheets (PRD §4.1 feature NFR).

NFR-2: Detection accuracy (SM-1) — 100% correct classification on non-Disputed rows across all five sample sheets, measured against a team-adjudicated `ground_truth.csv` committed before threshold tuning; Disputed rows scored separately and reported.

NFR-3: Executable deliverables (SM-2) — all three CLI programs run clean from the brief's exact commands on a fresh setup (clean machine, one-step install, no web dependencies).

NFR-4: Demonstrable technique (SM-3) — every pipeline stage from greyscale through per-cell inspection is individually demonstrable, live and as saved images (supports the report's step-by-step screenshots, 25% of coursework marks).

NFR-5: Verification capability (SM-4) — `investigate.py` produces correct match/mismatch verdicts on the FR-9 protocol split with the threshold documented.

NFR-6: Code quality (SM-5) — cohesive OOP class design, Core Engine cleanly separated from both frontends, consistent style, headless-testable engine, no dead scripts, tests green (code quality is a heavily weighted criterion within the 60% prototype marks).

NFR-7: Admin usability (SM-6) — a non-technical operator completes the upload → results flow on a phone browser with no instructions beyond the UI itself.

NFR-8: No overfitting (SM-C1) — no hard-coded pixel coordinates, per-sheet special-casing, or per-image thresholds; all tunables are global named constants; a general technique-driven approach over a brittle sample-tuned one.

NFR-9: Sequencing guard (SM-C2 / PRD §6.3) — Web UI work begins only after SM-1, SM-2, SM-3 pass on all five sample sheets; fallback deliverable is engine + CLI only, which alone fully satisfies the brief.

NFR-10: Error hygiene — no raw stack trace ever reaches the operator or grader on any surface; CLI errors are one-line human-readable messages with meaningful exit codes (0 ok, 2 input error, 1 other); Web UI errors use the UX error catalog.

NFR-11: Local-only operation — Web UI runs on `localhost`/LAN for a single operator; no cloud, accounts, authentication, or multi-user concurrency; Local DB (SQLite) only.

NFR-12: Web UI phone usability — single-column layout on phone, touch targets ≥ 44px, no horizontal scrolling for core flows.

### Additional Requirements

*From the Architecture Spine (ARCHITECTURE-SPINE.md) and coursework brief. No starter template — greenfield build following the spine's Structural Seed layout.*

- AR-1 (AD-1): Ports & Adapters boundary — all logic in `sams_core/`; entry scripts and Streamlit pages stay thin (parse → call engine → render; entry scripts < 50 lines); `sams_core` never imports Streamlit or any UI framework.
- AR-2 (AD-2): Cross-boundary data passes only as frozen dataclasses + enums in `sams_core/models.py`: `AttendanceStatus`, `StudentRecord`, `AttendanceRecord`, `StageArtifact(order, slug, label, image)` (image display-ready uint8, 2D grayscale or 3-channel RGB; adapters own toolkit conversion), `SheetResult` (with `warnings: list[str]`), `ReferenceScore`, `VerificationResult`.
- AR-3 (AD-3): One canonical pipeline registry in `pipeline.py` — generator/callback yielding `StageArtifact` from a single ordered registry; exactly 7 stages (original → greyscale → denoised → binarized → deskewed → detected table grid → per-cell inspection); stages are pure functions ndarray-in/ndarray-out; per-cell inspection is one composite overlay; signature crops are NOT StageArtifacts (flow via artifacts.py).
- AR-4 (AD-4): Single DB gateway — `repository.py` is the only module importing sqlite3; `ensure_schema` on open; upsert keyed (Student Index, Sheet Identifier); `resolved_by_operator` survives re-processing unless `overwrite=True`; read APIs `list_students()` and `has_operator_resolutions(sheet_id)`; write API `resolve(sheet_id, student_index, status, by_operator=True)` with undo restoring Ambiguous; canonical 8-digit index is the only stored/queried key form — the short ordinal is resolved by one engine resolver before any read/write; per-operation connections via context manager (no cached/global connections).
- AR-5 (AD-5): Config ownership — every tunable (Ambiguous coverage bands, similarity threshold, binarization/deskew params, DB path, output dir) is a named constant in `sams_core/config.py`; no numeric literals in stage/verification code; all paths relative to project root.
- AR-6 (AD-6): Error strategy — exception hierarchy in `sams_core/errors.py` (`SamsError` → `InputError`, `ProcessingError`); exceptions only for cannot-proceed failures; non-fatal anomalies are `SheetResult.warnings`; unknown Student Index is a no-data result carrying valid indices (never an exception); engine raises, never prints/exits/shows UI; CLI translates to one-line stderr + exit codes; success line reports record count + resolved Sheet Identifier.
- AR-7 (AD-7): Display boundary — `visualization.py` returns Matplotlib `Figure` objects; `artifacts.py` owns saving stage images to `output/<Sheet Identifier>/NN-slug.png`; CLI renders OpenCV windows live during processing (titled with stage names) + stdout summary; Web renders `st.image`/`st.pyplot`.
- AR-8 (AD-8): Dependency isolation — `requirements.txt` pins cv2/numpy/matplotlib for engine + CLI (the grader path, zero web dependencies); Streamlit only in `requirements-web.txt`, imported only from `webui/`.
- AR-9 (AD-9): Testing seam — pytest; tests import `sams_core` only; `tests/test_accuracy.py` computes SM-1..SM-3 against `tests/data/ground_truth.csv` across all five sheets (the §6.3 gate is executable); multi-reference comparison and best-match selection live in `verification.py`; similarity score is 0–1, higher = more similar, `matched = score >= threshold`, distance metrics normalized/inverted inside the engine.
- AR-10 (AD-10): Signature image data ownership — references on filesystem at `references/<student_index>/`, pre-populated from sheets 1–3 and committed; probe crops saved by `artifacts.py` to `output/<Sheet Identifier>/crops/<student_index>.png`; both registered as path metadata in the DB; no image blobs in the DB; empty/missing references = no-data result.
- AR-11 (AD-11): Sheet Identifier resolution in the engine (`info_file.py`) before the pipeline runs — chain: Info File session date → operator-supplied (CLI `--date` flag / Web date field) → image filename stem normalized to ISO 8601 (CLI only; the Web UI never uses the filename).
- AR-12 (AD-12): Single engine entry point — `process_sheet(image_path/bytes, info_file, sheet_id_override=None, overwrite=False)` is the one call both frontends make; runs the pipeline, persists internally on success, returns `SheetResult`; stage emission is a side channel; partial iteration/abort never persists.
- AR-13 (Stack): Python 3.12/3.13 only; opencv-python 4.13.0.92; numpy 2.5.1; matplotlib 3.11.0 (exact pin); streamlit 1.59.1 (web extra only); sqlite3/xml stdlib; pytest dev-only.
- AR-14 (Structural Seed): repo layout per the spine — root entry scripts, `sams_core/` (config, errors, models, info_file, pipeline, locate, detect, mapping, repository, visualization, verification, artifacts), `webui/` (app.py + pages/), `references/`, `tests/` (+ `tests/data/ground_truth.csv`), `requirements.txt`, `requirements-web.txt`.
- AR-15 (Naming): PRD §3 glossary terms verbatim in code, docs, DB columns, and UI copy; stage slugs from the AD-3 registry; artifact files `NN-slug.png`; stdlib `logging`.
- AR-16 (Brief/packaging): submission is an outer LMS ZIP containing the prototype zip + MS Word report; group of 10, each member contributing to both image processing and visualization — epics must give every member touchpoints in both graded concerns.

### UX Design Requirements

*From the UX design contract (DESIGN.md + EXPERIENCE.md). The CLI Display Contract items are UX-owned graded behavior; the Web UI items activate after the §6.3 gate.*

UX-DR1: Streamlit theme + design tokens — `.streamlit/config.toml` `[theme]` mapping the Quiet Clerk palette (primaryColor #44526A, backgroundColor #FAFAF8, secondaryBackgroundColor #FFFFFF, textColor #33383F, default sans font); light mode only, pinned so browser dark-mode never inverts it; minimal CSS block for status chips and row styling; spacing/radius tokens per DESIGN.md (page-margin 18px, card-padding 16px, content max-width ~1100px, radii 10/12/14px).

UX-DR2: Three-page multipage IA — Streamlit native sidebar with Process (landing, "Mark today's attendance"), Lookup ("Look up a student"), Investigate ("Check a signature"); no modals except the overwrite warning; no nested navigation.

UX-DR3: File slots — two labelled `st.file_uploader` slots ("Signing Sheet" JPEG/PNG, "Info File" info.xml); filename + quiet "✓ Ready" in slate (never Present green) on accept; slot-level validation feedback before Process where possible; a date field appears only when the Info File lacks a session date.

UX-DR4: One-shot Process button — themed primary button, full column width, min-height 52px, one per page maximum; disabled until both inputs ready; run fenced in session state so reruns/scrolling/expanding/resolving never re-trigger the pipeline or rewrite the DB (FR-12).

UX-DR5: Overwrite warning — when the Sheet Identifier has saved operator resolutions, an explicit pre-process choice: "Keep resolutions" (emphasized safe default) vs "Overwrite everything" (neutral-outlined); nothing processes until chosen; presents modal-style centered on desktop.

UX-DR6: Pipeline stage strip — streaming: each labelled stage image appears as the engine emits it, in pipeline order, current stage named in muted ink while running; completed stages collapse into labelled expanders; the strip IS the loading state (no indeterminate spinner as primary signal); images are the engine's emitted artifacts only.

UX-DR7: Results row list — custom container rows (not a raw dataframe): student name (label type), Student Index (caption, tabular figures), right-aligned status chip; rows reflect saved DB state; desktop hover tint #F3F2EE as enhancement only; results summary line ("42 students checked. One needs a quick look from you.").

UX-DR8: Status chips — icon + text label + colour, always all three (✓ Present #256E4C, ✕ Absent #A63D2A, ? Ambiguous #7A6212); coloured text/glyph on the row surface, no filled backgrounds; must survive greyscale; status colours never used for anything that isn't an Attendance Record status.

UX-DR9: Ambiguous row resolution — pale straw fill (#FDFBF2) + ochre border (#E3D9B4), plain-language question line, two neutral-outlined resolve buttons ("✓ Present" / "✕ Absent", min-height 46px, neutral ink text); one tap updates the Attendance Record instantly (no confirm dialog) followed by inline "Saved as Present. Undo" (~5s or until next interaction); Undo restores Ambiguous.

UX-DR10: Lookup page — single labelled "Student number" input accepting both index forms; the engine's FR-8 Matplotlib figure rendered as-is (per-Session timeline, Ambiguous on its own mid-band, attendance rate annotated); unknown index → "no data" message listing valid indices, never an error tone; empty state is a prompt sentence only.

UX-DR11: Investigate panel — Reference Signature and probe signature side by side (stacked on narrow phones), clearly captioned; numeric similarity score on a scale with the decision threshold marked (displayed normalized 0–100); plain-language Match/Mismatch verdict sentences; multiple references → probe vs best match by default with remaining references in a collapsed expander; same score/threshold outcome as `investigate.py`.

UX-DR12: Microcopy catalog — the Voice & Tone table and 4-item error catalog implemented verbatim: plain-language sentence-case copy, no jargon/exclamation/emoji; errors are full sentences naming what happened and what to do next; decode-level rejection only (dim/blurry/skewed photos proceed and may surface as Ambiguous, never as input errors); row-count mismatch is a prominent flag banner above results, not a failure; inputs preserved on error for fix-and-retry.

UX-DR13: Responsive layouts — phone (<~768px): single column, task-order stacking, sidebar hamburger; desktop (≥~768px): sidebar visible, content centered at ~1100px; Process desktop = two columns (upload + stage strip left, results right); Lookup desktop = full-width graph, valid-indices list in two columns; Investigate desktop = larger side-by-side + full-width scale; every column pair degrades to phone stacking order; projector-readable (nothing critical below 14px equivalent).

UX-DR14: Interaction primitives — touch targets ≥ 44px everywhere; tap/click only (no long-press/swipe/drag); explicit action semantics (nothing processes/writes without a deliberate tap; only Ambiguous resolution is instant, and it carries Undo); banned: carousels, auto-play, information-bearing toasts, confirm dialogs for reversible actions, multi-step wizards.

UX-DR15: Accessibility floor — statuses never colour-only (icon + label in rows, summary counts, chart legends; UI survives greyscale); visible text labels on all inputs (not placeholder-only); keyboard operable on desktop (real buttons, Tab/Enter in reading order); alt text on every stage image ("Stage 5 of 7 — Deskewed sheet") and both Investigate images; status changes announced as on-page text.

UX-DR16: CLI Display Contract (graded, gate-independent) — live OpenCV stage windows during processing, each titled with its stage name; every stage also saved as `output/<Sheet Identifier>/NN-stage.png` (per-sheet folders so five sheets never overwrite each other's report screenshots); stage vocabulary shared verbatim across CLI window titles, filenames, Web strip labels, and alt text; per-student stdout attendance summary after processing; one-line human errors + non-zero exit codes; success reports record count + Sheet Identifier; `--date` flag when the Info File lacks a date; re-run keeps operator resolutions by default, `--overwrite` to replace; Ambiguous printed as first-class in the CLI summary and never silently coerced.

### FR Coverage Map

FR-1: Epic 1 - Load and validate image + Info File inputs
FR-2: Epic 1 - Image preprocessing pipeline stages
FR-3: Epic 1 - Table and signature-cell localization
FR-4: Epic 1 - Signature presence detection with ink attribution
FR-5: Epic 1 - Map detections to Student Records
FR-6: Epic 1 - Persist attendance to Local DB (upsert + resolution survival)
FR-7: Epic 2 - Query attendance by student (both index forms)
FR-8: Epic 2 - Render attendance graph (timeline + rate, Ambiguous distinct)
FR-9: Epic 3 - Maintain reference signatures (sheets 1–3 / 4–5 protocol)
FR-10: Epic 3 - Compare and report match with documented threshold
FR-11: Epic 1 - Live step-by-step stage display + saved stage images
FR-12: Epic 4 - Browser upload and one-shot processing
FR-13: Epic 4 - Live pipeline strip, results list, Ambiguous resolution
FR-14: Epic 4 - Web Lookup and Investigate views (data-layer parity)
FR-15: Epic 1 - CLI wrappers, dependency isolation, fresh-setup packaging (cross-frontend parity consequence completed in Epic 4)
FR-16: Epic 1 - Engine-emitted stage artifacts, single display contract

*NFRs and UX-DRs thread through as story-level acceptance criteria: NFR-1/2/8 + UX-DR16 (CLI Display Contract) land in Epic 1; NFR-5 in Epic 3; NFR-7/12 + UX-DR1..15 in Epic 4; NFR-3/6/10/11 and AR conventions bind every epic.*

## Epic List

### Epic 1: Process a Signing Sheet into Attendance Records (CLI)

An operator runs `python sams.py <image> <info.xml>` on a fresh machine and watches the pipeline work: live labelled stage windows, saved stage images per sheet, a per-student stdout summary, and Attendance Records persisted to the Local DB — classification accurate across all five sample sheets against the committed ground-truth key. Includes the greenfield scaffold (Structural Seed, requirements.txt, config/models/errors), the ground-truth-first protocol (committed before threshold tuning), and packaging/dependency isolation from day one.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-11, FR-15, FR-16

### Epic 2: Look Up a Student's Attendance (`infovis.py`)

An operator runs `python infovis.py <index>` (either index form) and gets the labelled Matplotlib attendance timeline — per-Session Present/Absent with Ambiguous on its own mid-band and the overall attendance rate annotated — rendered straight from the Local DB Epic 1 populated; unknown indices get a friendly no-data response listing valid indices.
**FRs covered:** FR-7, FR-8

### Epic 3: Investigate a Suspicious Signature (`investigate.py`)

An operator runs `python investigate.py <index>` and gets a numeric similarity score plus a thresholded match/mismatch verdict, built on the disjoint reference/probe protocol (references from sheets 1–3, probes from sheets 4–5, impostor probes from other students) with the method and threshold documented. Highest-risk component, isolated so a verification spike never blocks Epics 1–2.
**FRs covered:** FR-9, FR-10

### Epic 4: Mark Attendance from the Phone (Admin Web UI) — gated by PRD §6.3

Nadeesha opens the Streamlit app in her phone or desktop browser, uploads the sheet photo and Info File, watches the stage strip stream as the engine emits stages, reads the per-student results, resolves Ambiguous rows with one tap + Undo, and uses the Lookup and Investigate pages — all with data-layer parity to the CLI and the Quiet Clerk design contract. Work starts only after SM-1, SM-2, SM-3 pass on all five sample sheets; the fallback deliverable (engine + CLI) already fully satisfies the brief.
**FRs covered:** FR-12, FR-13, FR-14 (completes FR-15 parity: CLI and Web produce identical Attendance Records)

## Epic 1: Process a Signing Sheet into Attendance Records (CLI)

An operator runs `python sams.py <image> <info.xml>` on a fresh machine and watches the pipeline work: live labelled stage windows, saved stage images per sheet, a per-student stdout summary, and Attendance Records persisted to the Local DB — classification accurate across all five sample sheets against the committed ground-truth key.

### Story 1.1: Run `sams.py` with validated inputs

As a marker/operator,
I want to run `python sams.py <image> <info.xml>` and have both inputs loaded and validated,
So that processing starts from trustworthy inputs and bad inputs fail with clear messages instead of stack traces.

**Acceptance Criteria:**

**Given** the repo scaffolded per the Structural Seed (`sams.py`, `sams_core/` with `config.py`, `errors.py`, `models.py`, `info_file.py`, pinned `requirements.txt` per AR-13)
**When** `python sams.py <valid image> <valid info.xml>` runs
**Then** the image loads (`.png` and `.jpeg`/`.jpg` both accepted) and the Info File parses into `StudentRecord` dataclasses plus Session metadata per the Appendix A schema
**And** the CLI reports the parsed Student Record count and the resolved Sheet Identifier, exiting 0.

**Given** a missing/unreadable image or an Info File failing Appendix A validation
**When** the command runs
**Then** a one-line human-readable error goes to stderr with exit code 2 — never a raw stack trace (`SamsError` hierarchy; the engine raises, only the CLI prints/exits).

**Given** an Info File lacking a session date
**When** run with `--date 2019-05-31`
**Then** that date becomes the Sheet Identifier
**And** when run without `--date`, the image filename stem is normalized to ISO 8601 (`10.07.2019.png` → `2019-07-10`) per the AR-11 resolution chain.

**Given** AR-1
**Then** `sams.py` stays a thin adapter under 50 lines.

### Story 1.2: Watch preprocessing stages live and saved

As an operator,
I want each preprocessing stage displayed live while the program runs and saved as a labelled image,
So that I can follow what SAMS did to my photo and capture report screenshots.

**Acceptance Criteria:**

**Given** validated inputs
**When** processing runs
**Then** `pipeline.py`'s single ordered registry emits `StageArtifact(order, slug, label, image)` for original → greyscale → denoised → binarized → deskewed, in order
**And** the CLI shows each stage live in an OpenCV window titled with its stage name (during processing, not after)
**And** `artifacts.py` saves each stage as `output/<Sheet Identifier>/NN-slug.png` so five sheets never overwrite each other's screenshots.

**Given** all five sample sheets
**When** each is processed
**Then** preprocessing completes end-to-end on every sheet; photo background outside the sheet is excluded while ink near/touching the table boundary is retained (NFR-1).

**Given** the engine code
**Then** `cv2.imshow` never appears inside `sams_core`; stages are pure ndarray-in/ndarray-out functions; all tunables live in `config.py` (no numeric literals in stage code).

### Story 1.3: Locate the student table and Signature Cells

As an operator,
I want the student table and each row's Signature Cell located on the normalized sheet,
So that each signature is checked against the correct student row.

**Acceptance Criteria:**

**Given** the deskewed image
**When** localization runs
**Then** the 5-column student table (No | Student No | Title | Student Name | Signature) is selected as the grid below the 4-column Metadata Row band, and a "detected table grid" `StageArtifact` is emitted showing the overlay
**And** detected grid lines are masked out of cell ROIs so printed borders are never counted as ink
**And** the Metadata Row / lecturer signature is never treated as a student row.

**Given** a sheet whose detected row count differs from the Info File record count
**When** processing continues
**Then** the discrepancy lands in `SheetResult.warnings` (flagged, not dropped, not an exception).

**Given** all five sample sheets
**Then** localization succeeds with the correct dynamic row count on each, without OCR of printed header text and without hard-coded pixel coordinates (NFR-8).

### Story 1.4: Classify each Signature Cell — Present, Absent, or Ambiguous

As an operator,
I want handwritten ink measured and attributed per Signature Cell with the inspection visible,
So that present/absent is decided automatically and uncertain cells are flagged rather than guessed.

**Acceptance Criteria:**

**Given** localized cells with grid lines masked
**When** detection runs
**Then** handwritten ink (any pen colour) is segmented into connected components, each attributed to exactly one Signature Cell (majority-area rule, centroid tie-break, dilated ROIs for spillover) — a straddling signature (samples 1 and 5) counts for exactly one row, and no component is evidence for two cells.

**Given** attributed ink per cell
**When** classification runs
**Then** coverage ≥ upper threshold → Present, ≤ lower threshold → Absent, between → Ambiguous, with both thresholds as documented named constants in `config.py`.

**Given** the pipeline completes
**Then** a "per-cell inspection" composite overlay is emitted as the final `StageArtifact` (7 registry stages total)
**And** per-cell signature crops are saved via `artifacts.py` to `output/<Sheet Identifier>/crops/<student_index>.png` (not as StageArtifacts) — ready for Epic 3.

### Story 1.5: Persist attendance and report results

As an operator,
I want classifications mapped to Student Records and saved to the Local DB with a readable summary,
So that attendance is durably recorded and visible without opening the database.

**Acceptance Criteria:**

**Given** classifications and the Info File's `no` ordinals
**When** mapping runs
**Then** each decision maps by row order to one Student Index; the canonical 8-digit index is the only form stored.

**Given** `repository.py` as the sole `sqlite3` importer
**When** results persist
**Then** the schema auto-creates on first run, one Attendance Record per Student Record upserts keyed (Student Index, Sheet Identifier) with session metadata, connections are per-operation, and re-processing updates rather than duplicates.

**Given** a sheet with saved operator resolutions
**When** re-processed without `--overwrite`
**Then** resolutions survive
**And** when re-processed with `--overwrite`, they are replaced (UX-DR16 semantics).

**Given** processing succeeds via the single `process_sheet()` entry point (persists internally; partial abort never persists — AR-12)
**Then** the CLI prints the success line (record count + Sheet Identifier) and a per-student stdout summary — Student Index, name, Present/Absent/Ambiguous — with Ambiguous first-class, never coerced.

### Story 1.6: Prove detection accuracy on all five sheets

As the development group,
I want an executable accuracy gate against a committed ground truth,
So that SM-1..SM-3 pass by test run, not by eyeball — and the Web UI gate decision is objective.

**Acceptance Criteria:**

**Given** a team-adjudicated `tests/data/ground_truth.csv` (sheet × student → Present/Absent/Disputed) committed before any threshold tuning
**When** `pytest tests/test_accuracy.py` runs
**Then** classification accuracy is computed across all five sample sheets: 100% on non-Disputed rows (SM-1), Disputed rows scored separately and reported, never counted as errors.

**Given** the test suite
**Then** tests import `sams_core` only (no CLI/web) and run headlessly, and the suite also asserts the 7-stage emission contract per sheet (SM-3 executable).

**Given** accuracy shortfalls during tuning
**When** thresholds are adjusted
**Then** changes touch only global named constants in `config.py` — no per-sheet special-casing (NFR-8 / SM-C1).

### Story 1.7: Run everything on a fresh machine

As the marker,
I want the prototype to run from a fresh unzip with a one-step install,
So that grading works exactly as the brief's commands describe.

**Acceptance Criteria:**

**Given** a clean machine with Python 3.12/3.13 and a fresh unzip
**When** `pip install -r requirements.txt` then `python sams.py 10.07.2019.png info.xml` run
**Then** the install is one step (pinned versions, zero web dependencies), the Local DB bootstraps automatically, all paths resolve relative to the project root, and the full pipeline runs per the brief.

**Given** the codebase
**Then** engine + CLI import only OpenCV/NumPy/Matplotlib/stdlib; entry scripts remain thin (<50 lines); a README documents the install and run commands. (The same packaging conventions carry `infovis.py` and `investigate.py` when Epics 2–3 add them — this story verifies the path for what exists now.)

## Epic 2: Look Up a Student's Attendance (`infovis.py`)

An operator runs `python infovis.py <index>` (either index form) and gets the labelled Matplotlib attendance timeline — per-Session Present/Absent with Ambiguous on its own mid-band and the overall attendance rate annotated — rendered straight from the Local DB Epic 1 populated.

### Story 2.1: Query a student's attendance by either index form

As an operator,
I want to run `python infovis.py <index>` with either the 8-digit Student No or the short ordinal,
So that I can pull up any student's attendance records the way the brief's command specifies.

**Acceptance Criteria:**

**Given** a Local DB populated by Epic 1
**When** `python infovis.py 001` and `python infovis.py 10000409` run for the same student
**Then** both resolve through the single engine index resolver (AR-4 — no adapter parses index forms) and return the identical set of Attendance Records.

**Given** an unknown index
**When** the command runs
**Then** the program reports "no data" listing the valid indices from `repository.list_students()` (short form + 8-digit, e.g. `001 (10000409)`), exits 0, and never raises an error tone (AR-6).

**Given** AR-1
**Then** `infovis.py` stays a thin adapter (<50 lines): parse argument → call engine query → hand off to display.

### Story 2.2: Render the attendance timeline graph

As an operator,
I want the student's attendance shown as a labelled per-Session graph,
So that I can answer "how's this student's attendance?" at a glance — the brief's visualization deliverable.

**Acceptance Criteria:**

**Given** Attendance Records for a student
**When** the graph renders
**Then** `visualization.py` returns a Matplotlib `Figure` (never calls `plt.show` — AR-7) showing the per-Session Present/Absent timeline, one colour-coded mark per recorded sheet, with Ambiguous distinct on its own mid-band between Present and Absent
**And** the overall attendance-rate percentage is annotated, with title, axis labels, and a legend whose status entries carry icon + text label (✓ Present / ✕ Absent / ? Ambiguous — UX-DR8 chart rule, greyscale-survivable).

**Given** the CLI adapter
**When** `infovis.py` receives the Figure
**Then** it displays it via Matplotlib's `show` — the same Figure object the Web UI will later render via `st.pyplot` (FR-14 data-layer parity).

**Given** the chart renders
**Then** it reads exclusively from Attendance Records in the Local DB — no image re-processing occurs.

## Epic 3: Investigate a Suspicious Signature (`investigate.py`)

An operator runs `python investigate.py <index>` and gets a numeric similarity score plus a thresholded match/mismatch verdict, built on the disjoint reference/probe protocol (references from sheets 1–3, probes from sheets 4–5, impostor probes from other students) with the method and threshold documented.

### Story 3.1: Maintain Reference Signatures per student

As an operator,
I want known-good Reference Signatures stored and retrievable per Student Index,
So that a suspicious signature has something trustworthy to be compared against.

**Acceptance Criteria:**

**Given** the FR-9 protocol
**When** the team populates `references/<student_index>/` with signature crops from sample sheets 1–3 (using the crops Story 1.4 saves) and commits them
**Then** dropping image files into `references/<index>/` is the complete ingestion path — the engine registers path metadata into the Local DB on first use (AR-10; no image blobs in the DB) and retrieves them by either index form.

**Given** the dataset protocol
**Then** reference and probe sets are disjoint by sheet: references from sheets 1–3, probes from sheets 4–5, impostor probes from other students — no signature is ever compared against itself.

**Given** a known student whose `references/<index>/` folder is empty or missing
**When** references are requested
**Then** the engine returns a no-data result (same family as unknown index — AR-6), never an exception.

### Story 3.2: Compare a probe signature and report the verdict

As an operator,
I want to run `python investigate.py <index>` and get a similarity score plus a match/mismatch verdict,
So that I have evidence — not just a hunch — when I suspect a proxy signer.

**Acceptance Criteria:**

**Given** Reference Signatures and a probe crop for a student
**When** `python investigate.py <index>` runs (either index form)
**Then** `verification.py` compares the probe against all references, selects the best match inside the engine (frontends never re-implement match logic — AR-9), and returns a `VerificationResult(best, all_scores, matched, threshold)`
**And** the similarity score is normalized to 0–1 with higher = more similar, `matched = score >= threshold`, and any distance metric is inverted inside the engine before leaving it.

**Given** the comparison method (OpenCV feature-based or image-similarity metric; ML optional)
**Then** the method and its threshold are documented in code, with the threshold as a named constant in `config.py` (AR-5).

**Given** the CLI adapter
**When** the result returns
**Then** `investigate.py` (<50 lines) prints the numeric score and a plain match/mismatch verdict; a student with no probe or no references gets the no-data response, exit 0.

### Story 3.3: Evaluate verification on the protocol split

As the development group,
I want the verifier evaluated against genuine and impostor probes with the threshold justified,
So that SM-4 is demonstrated and the report can defend the method honestly.

**Acceptance Criteria:**

**Given** the committed FR-9 split (references: sheets 1–3; probes: sheets 4–5; impostors: other students' signatures)
**When** the evaluation runs as a pytest module importing `sams_core` only
**Then** genuine probes report match and impostor probes report mismatch on that split (SM-4), with results reported per student.

**Given** the chosen threshold
**Then** its value is justified in documentation against the split's score distributions (genuine vs impostor), including honest reporting of any trade-off if score separation is poor — the documented attempt is itself the graded outcome.

**Given** tuning is needed
**When** the threshold changes
**Then** only the named constant in `config.py` moves — the same value `investigate.py` and the future Web UI read (no per-frontend thresholds).

## Epic 4: Mark Attendance from the Phone (Admin Web UI) — gated by PRD §6.3

Nadeesha opens the Streamlit app in her phone or desktop browser, uploads the sheet photo and Info File, watches the stage strip stream as the engine emits stages, reads the per-student results, resolves Ambiguous rows with one tap + Undo, and uses the Lookup and Investigate pages — all with data-layer parity to the CLI and the Quiet Clerk design contract. Work starts only after Story 1.6's accuracy suite passes on all five sheets (SM-1..SM-3).

### Story 4.1: Open SAMS in the browser

As Nadeesha (admin staff),
I want SAMS to open in my phone or desktop browser with three clearly named pages,
So that I can reach my task without anyone explaining the software to me.

**Acceptance Criteria:**

**Given** `pip install -r requirements-web.txt` on top of the base install (Streamlit only here — the grader path stays web-free, AR-8)
**When** `streamlit run webui/app.py` starts and a browser opens the app
**Then** a Streamlit multipage app renders with native sidebar navigation: Process (landing, "Mark today's attendance"), Lookup ("Look up a student"), Investigate ("Check a signature") — no other navigation, no modals except the overwrite warning (UX-DR2).

**Given** `.streamlit/config.toml`
**Then** the Quiet Clerk theme is applied (primaryColor `#44526A`, backgroundColor `#FAFAF8`, secondaryBackgroundColor `#FFFFFF`, textColor `#33383F`, default sans font), light mode pinned so browser dark-mode never inverts it, plus the minimal CSS block for chips/rows (UX-DR1).

**Given** first open with no inputs
**Then** each page shows its specified empty state: Process = upload hint + two empty file slots + disabled Process button; Lookup/Investigate = a single prompt sentence + input (UX-DR12 microcopy verbatim). `webui/` imports the engine only — no detection/persistence/visualization logic in pages (AR-1).

### Story 4.2: Upload a sheet and process it with one tap

As Nadeesha,
I want to upload the sheet photo and Info File and tap Process once,
So that processing happens exactly when I say so — and never accidentally.

**Acceptance Criteria:**

**Given** the Process page
**When** I add files to the two labelled slots ("Signing Sheet" JPEG/PNG, "Info File" info.xml)
**Then** each accepted slot shows filename + a quiet "✓ Ready" in slate (never Present green — UX-DR3), invalid files get slot-level plain-language errors from the UX error catalog (decode-level rejection only — a dim or skewed photo proceeds), and a date field appears only when the Info File lacks a session date (AR-11: the Web UI never falls back to the filename).

**Given** both inputs ready
**When** I tap the Process button (themed primary, full column width, min-height 52px, disabled until ready — UX-DR4)
**Then** `process_sheet()` runs exactly once per press, fenced in session state: scrolling, expanding a stage image, resolving a row, or any Streamlit rerun never re-triggers the pipeline or rewrites the DB (FR-12).

**Given** the Sheet Identifier already has saved operator resolutions (`has_operator_resolutions` — AR-4)
**When** I tap Process
**Then** nothing processes until I choose between Keep resolutions (emphasized safe default) and Overwrite everything (neutral-outlined) — the UX-DR5 warning, modal-style centered on desktop.

**Given** a processing failure
**Then** a human-readable page-level message appears (never a stack trace), and my uploaded inputs are preserved for fix-and-retry (UX-DR12).

### Story 4.3: Watch the pipeline and read the results

As Nadeesha,
I want to watch each processing stage appear and then read every student's result,
So that I trust what SAMS did and see who was present at a glance.

**Acceptance Criteria:**

**Given** processing starts
**When** the engine emits each `StageArtifact`
**Then** the stage strip streams them in pipeline order under "What we did with your photo", current stage named in muted ink while running, completed stages collapsing into labelled expanders — the strip is the loading state (no indeterminate spinner as primary signal), images sourced solely from the engine's emission contract (UX-DR6, FR-13).

**Given** processing completes
**Then** "All finished — your results are below." with the summary line ("42 students checked. One needs a quick look from you."), and a custom container row list (not a raw dataframe): student name, Student Index (caption, tabular figures), right-aligned status chip — icon + text + colour, always all three (UX-DR7, UX-DR8); results already persisted by the engine, stated once ("Results saved.").

**Given** a row-count mismatch warning in `SheetResult.warnings`
**Then** a prominent flag banner sits above the results ("matched by row order — please double-check") — a flag, not a failure (UX-DR12).

### Story 4.4: Resolve an Ambiguous row with one tap

As Nadeesha,
I want unclear signatures flagged with a one-tap fix and an Undo,
So that I settle uncertain rows in seconds while holding the paper sheet.

**Acceptance Criteria:**

**Given** a result row with status Ambiguous
**Then** it renders visually distinct (straw fill `#FDFBF2`, ochre border, plain question "We couldn't read this signature clearly. Which is right?") with two neutral-outlined buttons "✓ Present" / "✕ Absent" (min-height 46px, neutral ink text — UX-DR9).

**When** I tap one
**Then** `repository.resolve(sheet_id, student_index, status, by_operator=True)` updates the Attendance Record instantly — no confirm dialog — and the row flips with an inline "Saved as Present. Undo" (~5 s or until next interaction).

**When** I tap Undo
**Then** the record returns to Ambiguous (AR-4 undo semantics).

**Given** all Ambiguous rows resolved
**Then** the page says "All done. Every student on this sheet is marked." — and these resolutions survive later re-processing unless I explicitly overwrite (Story 4.2's warning).

### Story 4.5: Look up a student from the browser

As Nadeesha,
I want to type a student's number and see their attendance graph,
So that I can answer a lecturer's question from wherever I am.

**Acceptance Criteria:**

**Given** the Lookup page's single labelled "Student number" input
**When** I enter either index form (`10009301` or `002`)
**Then** the page renders the same engine Figure `infovis.py` shows (FR-8/FR-14 data-layer parity via `st.pyplot`) — per-Session timeline, Ambiguous mid-band, attendance rate annotated.

**Given** an unknown number
**Then** the "no data" message lists the valid indices — never an error tone; loading shows the native spinner with "Looking that up…" (UX-DR10, UX-DR12).

### Story 4.6: Check a signature from the browser

As Nadeesha,
I want to compare a student's sheet signature against their reference side by side,
So that I can act on proxy-signer suspicions with visible evidence.

**Acceptance Criteria:**

**Given** the Investigate page
**When** I enter a Student Index (either form)
**Then** the Reference Signature and probe signature render side by side (stacked on narrow phones), clearly captioned, with alt text on both; below them the similarity score sits on a scale with the threshold marked (displayed 0–100), then the plain verdict sentence ("Match — this looks like their usual signature." / "Mismatch — … Worth checking in person.") (UX-DR11).

**Given** the engine's `VerificationResult`
**Then** the score and threshold outcome are identical to `investigate.py`'s (FR-14 parity — same engine call, no re-implementation)
**And** with multiple references, the probe shows against the best match with the rest in a collapsed expander.

**Given** no data (unknown index, no probe, or empty references)
**Then** the no-data pattern renders — never an error.

### Story 4.7: Use SAMS comfortably on phone, desktop, and projector

As Nadeesha (and the demo presenter),
I want every page to work single-handed on my phone, mouse-and-keyboard at my desk, and readable on a projector,
So that the same app serves the corridor, the office, and the viva.

**Acceptance Criteria:**

**Given** a phone viewport (<~768 px)
**Then** every page is a single column in task order, sidebar collapsed to hamburger, touch targets ≥ 44 px, no horizontal scrolling in any core flow (NFR-12, UX-DR13/14).

**Given** a desktop viewport (≥~768 px)
**Then** the specified two-column layouts apply (Process: uploads + stage strip left, results right; Lookup: full-width graph, indices in two columns; Investigate: larger side-by-side + full-width scale), content centered at ~1100 px, every column pair degrading back to phone stacking order; hover tint is enhancement-only; critical info readable from 2–3 m (nothing below 14 px equivalent).

**Given** the accessibility floor (UX-DR15)
**Then** statuses are never colour-only anywhere (rows, summary counts, chart legends — greyscale-survivable), all inputs have visible labels, every action is keyboard-operable via real buttons in reading order, every stage image carries alt text ("Stage 5 of 7 — Deskewed sheet"), and status changes are announced as on-page text.

**Given** the same sheet processed via CLI and via Web UI
**Then** the Local DB holds identical Attendance Records — FR-15's cross-frontend parity consequence, verified at the data layer.
