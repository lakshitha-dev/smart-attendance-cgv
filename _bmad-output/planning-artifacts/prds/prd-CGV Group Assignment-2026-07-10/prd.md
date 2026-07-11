---
title: Student Attendance Management System (SAMS)
status: final
created: 2026-07-10
updated: 2026-07-10
---

# PRD: Student Attendance Management System (SAMS)

## 0. Document Purpose

This PRD scopes the **development/prototype** deliverable of the CS402.3 (Computer Graphics & Visualization) group coursework — a Python prototype that reads photographed signing sheets, decides present/absent per student via image processing, stores results in a local database, and visualizes attendance. It is written for the 10-member development group to align on scope, roles, and the exact behaviour each deliverable must exhibit. The **report** deliverable (screenshots, testing write-up, individual contribution) is explicitly out of scope for this document — see §5. FRs are grouped under features and numbered globally (FR-N) for stable reference; assumptions the team should confirm are tagged inline `[ASSUMPTION]` and indexed in §9. The assessment criteria from the brief are treated as first-class success metrics (§7). Appendix A defines the normative `info.xml` schema.

## 1. Vision

Admin staff photograph paper signing sheets with their phones and hand over a folder of images plus an XML file of student records. Marking attendance by hand from those photos is slow and error-prone. SAMS turns that manual chore into a repeatable pipeline: feed it a sheet image and the Info File, and it processes the image step by step — greyscale, denoise, binarize, deskew, locate the signature table, and inspect each signature cell — then decides who signed and who didn't, and records the result in a local database.

Beyond bare attendance, SAMS makes the data legible: it renders a clear attendance summary graph for any student, and an advanced verification component compares a student's captured signature against reference samples to flag mismatches (a possible proxy signer). The prototype is built in Python around a shared core engine, demonstrating solid image-processing technique and clean, object-oriented code — the two things the coursework grades most heavily.

Because the admin staff capture sheets on their smartphones, SAMS exposes a **mobile-accessible Web UI**: the admin opens it in a phone or desktop browser, uploads the sheet photo and the Info File, watches the Processing Pipeline stages render live, and reads the present/absent result and attendance charts on screen. The three brief-specified command-line programs (`sams.py`, `infovis.py`, `investigate.py`) remain as a thin CLI over the same engine, so the exact commands in the coursework brief still work for the marker. Success is a working solution that correctly classifies attendance across all five provided sample sheets, clearly shows its image-processing steps while running, and is operable by a non-technical admin through the Web UI.

> `[NOTE FOR PM]` **The Web UI is a deliberate bet, not a grading requirement.** The assessment table awards marks for image-processing technique, OOP/code quality, testing, and the three executable CLI programs — nothing for a browser UI. The Web UI buys demo polish and real usability for the admin persona at the cost of engine-hardening time. It is therefore **sequenced last**: Web UI work begins only after SM-1, SM-2, and SM-3 pass on all five sample sheets (see §6.3). Fallback if the timeline compresses: ship engine + CLI only — that alone fully satisfies the brief.

## 2. Target User

### 2.1 Jobs To Be Done

- **Functional:** Convert a phone photo of a signing sheet into an accurate present/absent record per student, without transcribing by hand — straight from the phone's browser where the photo already lives.
- **Functional:** See the attendance history/summary for a specific student as a graph, quickly.
- **Functional (advanced):** Confirm that a signature on the sheet plausibly belongs to the enrolled student, and be warned when it doesn't.
- **Contextual:** Watch the image-processing pipeline progress so the operator (and the marker) can trust and demonstrate what the program did.
- **Builder's JTBD:** As the development group, produce clean, OOP-structured, testable Python code that demonstrably applies image-processing and data-visualization techniques (the graded LOs).

### 2.2 Non-Users (v1)

- Students themselves — they interact only with the paper sheet, never the software.
- Institutional/LMS administrators — no integration with any school system in v1.

### 2.3 Key User Journeys

*Two personas: the non-technical **admin staff member** on the Web UI, and the **marker/technical operator** on the CLI. Both surfaces drive the same Core Engine.*

- **UJ-1. Nadeesha records a session's attendance from her phone.**
  Nadeesha, the school's admin assistant, has just photographed the signed sheet for the 31/05 CGV lecture on her phone. She opens the SAMS Web UI in her phone browser, uploads the photo and the class Info File (`info.xml`), and taps *Process*. The screen shows each pipeline stage as it happens (original → greyscale → denoised → binarized → deskewed → detected table grid → per-cell inspection), then a present/absent list per student. The results are saved to the Local DB automatically. She repeats this for the other sheets. *Edge case:* a badly skewed or dim photo — the pipeline deskews/normalizes; if a cell falls in the Ambiguous band (FR-4) the row is flagged, and Nadeesha resolves it to Present or Absent with one tap (FR-13). Realizes FR-1 through FR-6, FR-11, FR-12, FR-13.

- **UJ-2. Nadeesha reviews one student's attendance.**
  A lecturer asks about student `10009301`. In the Web UI, Nadeesha enters the Student Index (either form — `10009301` or the short `002`) and gets the attendance graph: per-session present/absent timeline with the overall attendance rate. Realizes FR-7, FR-8, FR-14.

- **UJ-3. Nadeesha verifies a suspicious signature.**
  Suspecting a proxy signer for student `10009301`, she opens the *Investigate* view, enters the index, and the system compares the signature captured from the probe sheet(s) against stored Reference Signatures and reports match/mismatch with a numeric similarity score. Realizes FR-9, FR-10, FR-14.

- **UJ-4. The marker runs the brief's exact commands.**
  Dr. Ranaweera (or a grader) unzips the submission on a fresh machine, installs dependencies in one step, and tests the prototype from a terminal: `python sams.py 10.07.2019.png info.xml`, then `python infovis.py 001`, then `python investigate.py 001`. Each command runs the same Core Engine as the Web UI — with no web dependencies required — and produces the same detections, graphs, and verification verdicts. Realizes FR-1 through FR-11, FR-15, FR-16.

## 3. Glossary

*Downstream code and docs must use these terms exactly.*

- **Signing Sheet** — A single physical attendance sheet with a static, known tabular layout; captured as one image file (typically a phone photo, JPEG or PNG).
- **Signature Cell** — The rectangular region in a Signing Sheet row reserved for one student's handwritten signature.
- **Student Record** — One student's identifying data (Student Index, Name, Title, and row ordinal `No`) supplied in the Info File.
- **Info File** — The operator-supplied XML file (`info.xml`) mapping the student rows to Student Records and carrying the subject and **Session** metadata. Normative schema in Appendix A, pending module-leader override.
- **Student Index** — The unique identifier for a student: the 8-digit **Student No** (e.g. `10009301`). The brief's short form (e.g. `001`) is the row ordinal `No` / short alias defined in the Info File. **Both forms must resolve** everywhere an index is accepted (CLI arguments, Web UI inputs, DB queries).
- **Session** — One taught class occurrence: subject code + date. Defined in the Info File.
- **Sheet Identifier** — The canonical key for one processed Signing Sheet: the Session date in ISO 8601 (`YYYY-MM-DD`) from the Info File's `<session date="...">` element. It is **never** OCR'd from the handwritten date on the sheet. If the Info File lacks a date, the operator supplies one (CLI flag / Web UI field); final fallback is the image filename stem.
- **Attendance Record** — A stored result: (Student Index, Sheet Identifier, Status), plus subject/session metadata. **Status ∈ {Present, Absent, Ambiguous}**; Ambiguous rows await operator resolution (FR-13).
- **Present / Absent / Ambiguous** — Present = the Signature Cell's attributed ink is at or above the upper threshold; Absent = at or below the lower threshold; Ambiguous = ink coverage falls between the two thresholds (FR-4).
- **Metadata Row** — The header block above the student table (Signing Sheet title, university/programme, and the Date | Time | Lecturer's Name | Lecturer Signature row). It is **not** a student row and must be excluded from attendance detection.
- **Processing Pipeline** — The ordered image-processing stages that transform a Signing Sheet image into per-cell attendance decisions: greyscale → noise reduction → binarization → deskew/perspective correction → table localization → cell extraction → ink attribution → classification.
- **Reference Signature** — A stored known-good signature sample for a Student Index, used by `investigate.py` for comparison. Sourced per the FR-9 protocol.
- **Local DB** — The on-disk SQLite database storing Attendance Records and Reference Signature metadata. Created automatically on first run if absent.
- **Core Engine** — The shared Python package implementing the Processing Pipeline, detection, persistence, visualization, and verification logic. Both frontends call it; it contains no UI code and never opens display windows itself (FR-16).
- **Web UI** — The browser-based frontend for admin staff (mobile and desktop): upload, live pipeline display, results, charts, and investigation views. `[ASSUMPTION: Streamlit]`
- **CLI** — The three brief-specified command-line programs (`sams.py`, `infovis.py`, `investigate.py`), thin wrappers over the Core Engine.

## 4. Features

*One Core Engine, two frontends. Features 4.1–4.5 describe the Core Engine capabilities (surfaced through both the CLI programs `sams.py` / `infovis.py` / `investigate.py` and the Web UI); 4.6 is the Web UI; 4.7 is the dual-frontend architecture and packaging. FRs numbered globally.*

### 4.1 Sheet Ingestion & Image Preprocessing (`sams.py`)

**Description:** `sams.py` takes a Signing Sheet image and an Info File as CLI arguments and prepares the image for analysis. It loads both inputs, validates them, and runs the Processing Pipeline, displaying each stage as it goes (realizes UJ-1). Uses Glossary terms exactly.

#### FR-1: Load and validate inputs

The operator can run `python sams.py <image> <info.xml>` and the program loads the Signing Sheet image (JPEG or PNG) and parses the Info File into Student Records and Session metadata per the Appendix A schema.

**Consequences (testable):**
- Given a valid image path and Info File, both load without error; the count of parsed Student Records and the resolved Sheet Identifier are reported.
- Given a missing/unreadable image or an Info File that fails Appendix A validation, the program exits with a clear error message and non-zero exit code (no raw stack trace).
- Both `.png` and `.jpeg`/`.jpg` inputs are accepted (the brief's example is `.png`; the provided samples are `.jpeg`).

#### FR-2: Image preprocessing pipeline

The program transforms the raw photo into a clean, analyzable image through ordered stages: greyscale conversion, noise reduction, thresholding/binarization, and geometric normalization (deskew / perspective correction to account for phone-photo angle). Uses OpenCV + NumPy.

**Consequences (testable):**
- The pipeline runs end to end on all five provided sample sheets without failing.
- Each named stage produces a distinct intermediate image that can be displayed and saved.
- Photo background clearly outside the sheet (desk surface, page edges, punch holes) is excluded before analysis. Ink **near or touching the table boundary is retained** — it may be a signature spilling out of its cell (see FR-4 ink attribution); only ink far from the table (e.g. corner page annotations like "10b 1st") is discarded.

#### FR-3: Table & signature-cell localization

The Signing Sheet has a static known layout: a header block, a **Metadata Row** table (Date | Time | Lecturer's Name | Lecturer Signature), then the student table with five columns — **No | Student No | Title | Student Name | Signature**. The program locates the *student* table, detects its grid, and extracts each row's Signature Cell (last column) as a region of interest tied to the correct row order.

**Consequences (testable):**
- **Mechanism is explicit and testable:** the student table is selected as the 5-column grid below the Metadata Row band (the Metadata Row table has 4 columns); detected grid lines are masked out of cell ROIs before ink measurement so printed borders are never counted as ink.
- The Metadata Row / lecturer signature is never counted as a student row.
- Column layout is fixed; **row count is dynamic** — the number of detected student rows matches the rows present on each sheet (discrepancies vs the Info File are reported, not silently dropped).
- Each extracted Signature Cell corresponds to the correct row position (and its Student No / Student Name columns) for downstream mapping to a Student Record.
- Localization does **not** rely on OCR of printed header text (the template contains typos — "Signatue", "Lecture's Name" — making header-text matching a dead end).

**Feature-specific NFRs:**
- Robust to typical phone-photo variance seen in the samples: moderate skew/perspective, uneven lighting, desk background, punch holes, handwritten margin notes, white-out patches, and non-pen marks (e.g. a red grader annotation); varying resolution across the five sample sheets.

### 4.2 Attendance Detection & Persistence (`sams.py`)

**Description:** After localization, the program attributes handwritten ink to Signature Cells, classifies each cell Present / Absent / Ambiguous, maps each decision to a Student Record via the Info File, and writes Attendance Records to the Local DB (realizes UJ-1).

#### FR-4: Signature presence detection with ink attribution

For each Signature Cell, the program measures handwritten ink (any pen colour) beyond the printed template and classifies the cell.

**Ink-attribution policy (real signatures straddle cells on the sample sheets):**
- Handwritten ink is segmented into connected components after grid-line masking (FR-3).
- Each component is attributed to **one** Signature Cell — the cell containing the majority of its area (centroid as tie-break). Cell ROIs are dilated to capture ink that spills slightly over borders, including into the right margin outside the table.
- A single component is never counted as presence evidence for two cells.

**Classification:** ink coverage ≥ upper threshold → Present; ≤ lower threshold → Absent; between the thresholds → **Ambiguous** (flagged for operator resolution, FR-13). Thresholds are tunable constants documented in code. `[ASSUMPTION: coverage-band ambiguity criterion]`

**Consequences (testable):**
- Against the committed ground-truth answer key (§7 SM-1), every clearly signed cell classifies Present and every empty cell Absent, on all five sample sheets.
- Detection tolerates different pen colours (not restricted to black ink).
- A signature straddling two rows (present on samples 1 and 5) is attributed to exactly one row.
- The lecturer's signature in the Metadata Row is never treated as a student attendance mark.

**Out of Scope:**
- Reading/OCR-ing the *text* of the signature (comparison-based verification is FR-9/FR-10, not transcription).

#### FR-5: Map detections to Student Records

The program associates each classification with the correct Student Index using row order and the Info File's `no` ordinal.

**Consequences (testable):**
- Row order reliably maps each Signature Cell to one Student Index; a mismatch between detected row count and Info File record count is flagged.

#### FR-6: Persist attendance to Local DB

The program stores an Attendance Record per student for the processed sheet, keyed by **(Student Index, Sheet Identifier)**, with subject/session metadata from the Info File.

**Consequences (testable):**
- After a run, the Local DB contains one Attendance Record per Student Record in the Info File, each with Status ∈ {Present, Absent, Ambiguous}.
- Re-processing the same sheet (same Sheet Identifier) **updates** the existing records — no duplicates. Operator resolutions of Ambiguous rows (FR-13) survive unless the operator confirms an overwrite.
- The Local DB file and schema are created automatically on first run if absent.

### 4.3 Attendance Visualization (`infovis.py`)

**Description:** `infovis.py` takes a Student Index and renders the attendance summary graph from the Local DB (realizes UJ-2).

#### FR-7: Query attendance by student

The operator can run `python infovis.py <index>` — where `<index>` is either the 8-digit Student No or the short `No` ordinal/alias (both resolve per §3) — and the program retrieves all Attendance Records for that student.

**Consequences (testable):**
- `python infovis.py 001` and `python infovis.py 10000409` return the same records for the same student.
- Given an unknown index, the program reports "no data" (listing valid indices) rather than erroring.

#### FR-8: Render attendance graph

The program displays the attendance summary using Matplotlib. **Committed default chart:** a per-Session present/absent timeline (one mark per recorded sheet, colour-coded, Ambiguous distinct) with the overall attendance-rate percentage annotated; title, axis labels, and legend included. OQ-2 may upgrade this default; it does not remove the need for one.

**Consequences (testable):**
- A labelled graph (title, axes, legend) is produced for a student with data, showing per-Session status and overall attendance rate.
- The chart renders from Attendance Records only (no image re-processing).

### 4.4 Signature Recognition & Verification (`investigate.py`)

**Description:** `investigate.py` compares a student's captured signature(s) against stored Reference Signatures and reports match/mismatch — the higher-grade component, committed for this build (realizes UJ-3).

#### FR-9: Maintain reference signatures

The system stores one or more Reference Signatures per Student Index and defines how they enter the system.

**Ingestion path & dataset protocol (default — enrichment welcome):**
- Reference Signatures are image files under `references/<student_index>/`, registered into the Local DB on first use.
- **Default source split (avoids self-verification):** references = signature crops from sample sheets **1–3**; probes (the signatures under investigation) = crops from sheets **4–5**; the mismatch test set = *other students'* signatures used as impostor probes. Hand-collected genuine samples may enrich the reference set if available. `[ASSUMPTION: sheet-crop protocol satisfies the brief's "collect signatures of the given student" — confirm with module leader]`

**Consequences (testable):**
- Reference Signatures can be added by dropping files into `references/<index>/` and are retrievable by Student Index (either index form).
- Reference and probe sets are disjoint by sheet (no signature is compared against itself).

#### FR-10: Compare and report match

The operator can run `python investigate.py <index>` (either index form) and the program compares the probe signature(s) against the Reference Signature(s) and reports the verdict.

**Consequences (testable):**
- Output is a **numeric similarity score plus a thresholded match/mismatch verdict**; the method and threshold are documented and justified against the FR-9 dataset split.
- For a genuine matching signature the program reports a match; for an impostor probe (another student's signature) it reports a mismatch — measured on the FR-9 protocol sets (SM-4).
- The comparison method is feature-based or ML-based. `[ASSUMPTION: OpenCV feature matching / image-similarity metric; ML optional]`

**Notes:**
- This is the highest-risk, highest-reward component: tiny low-texture scribbles are hard for classic feature matching. Budget spike time early; if similarity quality is poor, the FR-9 protocol and honest reporting of the threshold trade-off still earn the "attempt" credit the brief describes.

### 4.5 Processing Progress Display (cross-cutting, `sams.py`)

**Description:** While `sams.py` runs, it visibly shows the Processing Pipeline stages so the operator/marker can follow and demonstrate what happened (realizes UJ-1; directly supports the "screenshots of the entire step-by-step process" grading criterion).

#### FR-11: Show step-by-step processing progress

The program **displays each major pipeline stage live, on screen, while processing** — original, greyscale, denoised, binarized, deskewed, detected table grid, per-cell inspection — and additionally saves each stage as a labelled image file.

**Consequences (testable):**
- Running `sams.py` shows each named stage on screen while the program is running (the brief requires live progress; saving alone does not satisfy this FR).
- Stages appear in pipeline order and are individually identifiable (labelled); saved copies land in an output folder for report screenshots.

### 4.6 Admin Web UI

**Description:** The browser-based frontend for admin staff, usable from the smartphone that took the sheet photo as well as from a desktop. It wraps the Core Engine's capabilities in an upload → watch → review flow (realizes UJ-1, UJ-2, UJ-3). Built **only after** the engine + CLI pass SM-1–SM-3 (§6.3). `[ASSUMPTION: Streamlit — fastest path to image-step display, file upload, and chart embedding; confirm with group]`

#### FR-12: Upload and process a sheet from the browser

An admin staff member can open the Web UI in a mobile or desktop browser, upload a Signing Sheet image and an Info File, and trigger processing as an **explicit one-shot action** (processing and DB writes happen once per press, never as a side-effect of UI interaction or rerun). Realizes UJ-1.

**Consequences (testable):**
- The upload accepts the sample JPEG/PNG photos and an `info.xml`; processing starts only on the explicit action.
- Interacting with unrelated widgets after processing does not re-run the pipeline or rewrite the DB.
- Invalid inputs produce a human-readable on-screen error, not a crash.
- Works in a phone browser (responsive layout, touch-friendly controls).

#### FR-13: Live pipeline display, results, and Ambiguous resolution

During processing, the Web UI renders the stage images the Core Engine emits (FR-16) in pipeline order, then the per-student result table; results are persisted to the Local DB. Ambiguous rows are visually distinguished and the operator can resolve each to Present or Absent. Realizes UJ-1.

**Consequences (testable):**
- Each stage renders in the browser in pipeline order, labelled — sourced from the engine's emitted artifacts, not a second display implementation.
- The result table lists every Student Record with its Status; Ambiguous rows are visually distinct and offer a one-tap Present/Absent resolution that updates the Attendance Record.

#### FR-14: Student lookup views (visualization & investigation)

An admin staff member can enter a Student Index (either form) in the Web UI to view the attendance summary graph (FR-8) and to run signature verification (FR-10), without using a terminal. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- **Parity is defined at the data layer:** the Web UI chart is rendered from the same engine query/figure the CLI uses, and the verification verdict shows the same score and threshold outcome — verified by comparing engine outputs, not pixels.

**Feature-specific NFRs:**
- Runs locally (`localhost`/LAN) for a single operator (§5).
- Usable on a phone screen: single-column layout, large touch targets, no horizontal scrolling for core flows.

### 4.7 Dual-Frontend Architecture, Parity & Packaging

**Description:** All processing, persistence, visualization, and verification logic lives in the Core Engine as an OOP Python package. The Web UI and the CLI are both thin frontends over it — this is the primary vehicle for the "coding styles, OOP concepts" grading criterion, and it guarantees the brief's exact commands still work (realizes UJ-4).

#### FR-15: CLI wrappers with engine parity and clean packaging

The marker can run `python sams.py <image> <info.xml>`, `python infovis.py <index>`, and `python investigate.py <index>` on a fresh machine and get the same detections, graphs, and verdicts the Web UI produces, from the same Core Engine and Local DB.

**Consequences (testable):**
- Each CLI command is a thin entry point (argument parsing + engine calls + display); no detection/persistence logic is duplicated in either frontend.
- Processing the same sheet via CLI and via Web UI yields identical Attendance Records.
- **Dependency isolation:** the Core Engine and CLI import only OpenCV, NumPy, Matplotlib, and the standard library (sqlite3, xml). Web UI dependencies (Streamlit) are an optional extra; the three CLI commands run on a machine where no web dependency is installed.
- **Fresh-setup packaging:** the prototype runs from a freshly unzipped copy with a one-step documented install (`pip install -r requirements.txt`, pinned); the Local DB bootstraps automatically; all paths are relative to the project root.

#### FR-16: Engine-emitted stage artifacts (single display contract)

The Core Engine exposes pipeline progress as a sequence of labelled stage images (callback/generator), and never opens display windows itself (`cv2.imshow` is forbidden inside the engine). The CLI renders these in OpenCV windows (FR-11); the Web UI renders the same artifacts in the browser (FR-13).

**Consequences (testable):**
- One stage-emission code path serves both frontends; stage names and order are identical in CLI and Web UI output.
- The engine is importable and testable headlessly (no GUI required to run its test suite).

## 5. Non-Goals (Explicit)

- **The report deliverable is not in scope for this PRD** — no screenshots write-up, testing narrative, discussion, or individual-contribution sections are produced by this document or the software. `[NON-GOAL for this PRD]`
- No **native mobile app** — the smartphone need is met by the mobile-accessible Web UI; no app-store distribution.
- No cloud deployment, user accounts, authentication, authorization, audit trails, or multi-user concurrency — the Web UI runs locally (`localhost`/LAN) for a single operator.
- No integration with any LMS, institutional database, or cloud service; the DB is local only.
- No live camera capture in v1 — the program consumes pre-supplied image files (the admin uploads the photo they already took). In-browser camera capture is a possible v2 stretch. `[NON-GOAL for MVP]`
- No handwriting-to-text OCR anywhere — not of signatures, and **not of the handwritten sheet date** (the Sheet Identifier comes from the Info File, §3).

## 6. MVP Scope

### 6.1 In Scope

- **Core Engine** — full Processing Pipeline with stage emission (FR-16), three-state detection with ink attribution (FR-1 → FR-6), attendance query + committed default graph (FR-7, FR-8), signature verification with the FR-9 dataset protocol (FR-9, FR-10 — committed as the higher-grade component).
- **CLI** — `sams.py`, `infovis.py`, `investigate.py` as thin engine wrappers with live stage display, parity, and fresh-setup packaging (FR-11, FR-15).
- **Web UI** — mobile-accessible upload → live pipeline → results + Ambiguous resolution, plus student lookup views (FR-12 → FR-14), sequenced per §6.3.
- Correct operation across all **five** provided sample sheets in `sample_signin-sheets/` (the contents of the brief's `CGV Signing Sheets.zip`), scored against the committed ground-truth answer key (SM-1).
- Clean, object-oriented Python structure with tests. The prototype is 60% of the module's coursework marks, and code quality / OOP concepts are heavily weighted criteria within that 60%.

### 6.2 Out of Scope for MVP

- Handling sheet layouts other than the single static known layout (fixed columns; dynamic row count is in scope per FR-3).
- Batch processing many sheets in one command/upload (per-sheet invocation is sufficient for v1).
- In-browser live camera capture, authentication, cloud hosting (see §5).

### 6.3 Delivery Constraints

- **Sequencing gate:** Web UI (FR-12 → FR-14) starts only after SM-1, SM-2, and SM-3 pass on all five sample sheets. The engine and CLI alone fully satisfy the brief; the Web UI is additive.
- **Ground-truth first:** the team adjudicates and commits `ground_truth.csv` (sheet × student → Present/Absent/Disputed) **before** tuning detection thresholds (SM-1).
- **Team decomposition:** the brief requires all ten members to contribute to both image processing and visualization. Work-package decomposition to satisfy this is deferred to the epics/stories phase, but epics must be shaped so every member has touchpoints in both graded concerns.

## 7. Success Metrics

*Anchored to the coursework assessment criteria (Prototype 60%, image-processing technique, executable program).*

**Primary**
- **SM-1**: Attendance-detection accuracy — correct classification for every student across all five sample sheets, measured against the committed `ground_truth.csv` (adjudicated by the team before threshold tuning; Disputed rows scored separately and reported, not counted as errors). Target: 100% on non-Disputed rows. Validates FR-4, FR-5.
- **SM-2**: Executable deliverables — `sams.py`, `infovis.py`, and `investigate.py` run from the command line exactly as specified in the brief and produce their outputs on a fresh setup (clean machine, one-step install, no web dependencies). Target: all three run clean. Validates FR-1, FR-7, FR-8, FR-10, FR-15.
- **SM-3**: Demonstrated image-processing technique — the pipeline can show every stage from greyscale through per-cell inspection, live and as saved images. Target: each stage individually demonstrable (supports report screenshots). Validates FR-2, FR-3, FR-11, FR-16.
- **SM-4**: Signature-verification capability — `investigate.py` correctly distinguishes genuine probes from impostor probes on the FR-9 protocol split (references: sheets 1–3; probes: sheets 4–5; impostors: other students). Target: correct match/mismatch verdicts on that split, with the threshold documented. Validates FR-9, FR-10.

**Secondary**
- **SM-5**: Code quality — OOP structure, consistent style, and passing tests. Target: cohesive class design (Core Engine cleanly separated from both frontends), headless-testable engine, no dead scripts, tests green. Validates the "quality of the program" criterion, FR-15, FR-16.
- **SM-6**: Admin usability *(demo aid, maps to no assessment criterion — see §1 note)* — a non-technical operator completes the upload → results flow on a phone browser without instructions beyond the UI itself. Target: end-to-end run on one sample sheet from a phone. Validates FR-12, FR-13, FR-14.

**Counter-metrics (do not optimize)**
- **SM-C1**: Do not overfit detection to the five sample sheets (e.g. hard-coded pixel coordinates, per-sheet special-casing, or thresholds tuned per image) at the expense of a general, technique-driven approach. Counterbalances SM-1 — a robust method scores better on LO3 than a brittle one that happens to pass.
- **SM-C2**: Do not let Web UI polish consume engine-hardening time. Counterbalances SM-6; enforced by the §6.3 sequencing gate.

## 8. Open Questions

1. **OQ-1: Module-leader `info.xml`** — the brief's Figure 1 was never supplied. Appendix A is the normative schema the group builds against; if the module leader later provides an official file, the parser adapts to it. Owner: group lead → module leader.
2. **OQ-2: Visualization upgrade** — FR-8's committed default (per-Session timeline + attendance rate) is the build target; confirm with the module leader whether a specific chart type is expected. Owner: visualization lead.
3. **OQ-3: Web UI framework** — Streamlit is recommended (native image/chart/upload support, minimal code); confirm with the group, or choose Flask if the team wants to demonstrate hand-built web skills. Owner: group vote before the §6.3 gate opens.

## 9. Assumptions Index

*Confirmed by the user on 2026-07-10 (no longer open): Info File is XML; stack is Python + OpenCV/NumPy + Matplotlib + SQLite; `investigate.py` is committed in scope; Web UI is in scope as a web app (smartphone scenario); sheet layout per `sample_signin-sheets/` (header + Metadata Row + 5-column student table).*

Remaining inline assumptions to confirm:
- §3 / §4.6 — Web UI framework is Streamlit (see OQ-3).
- FR-4 — Ambiguity criterion is an ink-coverage band between the Absent and Present thresholds (tunable constants).
- FR-9 — Default reference/probe split (sheets 1–3 vs 4–5) is acceptable to the module leader as "collecting signatures of the given student"; hand-collected samples enrich it if obtainable.
- FR-10 — Signature comparison uses OpenCV feature matching / an image-similarity metric, with ML optional; threshold documented against the FR-9 split.
- Appendix A — The group-authored `info.xml` schema stands unless the module leader supplies an official one (OQ-1).

## Appendix A — Normative `info.xml` Schema

*Group-authored; the source of truth for Student Records, Session metadata, and the Sheet Identifier until the module leader provides an official file (OQ-1). All FRs parse against this shape. `[ASSUMPTION: this schema stands unless an official Figure 1 file supersedes it]`*

```xml
<?xml version="1.0" encoding="UTF-8"?>
<subject code="CS402.3" name="Computer Graphics and Visualization">
  <session date="2019-05-31" time="13:00" lecturer="Dr. Rasika Ranaweera"/>
  <students>
    <!-- no    = row ordinal on the sheet; also the short CLI alias (e.g. "001") -->
    <!-- index = 8-digit Student No printed on the sheet -->
    <student no="001" index="10000409" title="Ms" name="M S Dilshanika Perera"/>
    <student no="002" index="10009301" title="Mr" name="C W M A Shehan Abeyrathne"/>
    <student no="003" index="10009302" title="Mr" name="B A K M Chithrananda"/>
    <student no="004" index="10009303" title="Ms" name="W Shashini Minosha De Silva"/>
    <student no="005" index="10009304" title="Mr" name="K L Udara Maduranga Liyanage"/>
    <student no="006" index="10009306" title="Mr" name="Hansa Anuradha Wickramanayake"/>
  </students>
</subject>
```

**Rules:** `session/@date` is ISO 8601 and becomes the Sheet Identifier (§3). `student/@no` and `student/@index` are both accepted wherever a Student Index is input (FR-7, FR-10, FR-14). One `info.xml` describes one Session; the same student list may be reused across sessions with a different `session` element.
