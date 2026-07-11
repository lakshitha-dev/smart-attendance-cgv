# Final Pre-Publication Reconciliation — SAMS PRD

- **PRD:** `prd.md` (this folder), version dated 2026-07-10
- **Brief:** `C:\dev\CGV Group Assignment\CS402.3 Coursework.md`
- **Validation report:** `validation-report.md` (this folder)
- **Run at:** 2026-07-10

## Verdict

**PASS — publish.** All 3 Critical and all 5 deduped High findings are resolved in the current PRD text; the brief's development-relevant requirements are fully covered with no contradictions, including all four previously partial items (live display, signature-collection protocol, group-of-ten decomposition, packaging/fresh-setup). Two cosmetic residuals remain (assumption-tag roundtrip for FR-9/Appendix A; FR-9 interpretation of "collect signatures" is an acknowledged assumption pending module-leader confirmation) — neither blocks publication.

## Brief coverage residuals

Trace of every development-relevant brief requirement against the current PRD (report deliverable excluded by user decision; report-*enabling* capabilities in scope):

| Brief requirement | PRD coverage | Status |
|---|---|---|
| Working prototype with backend coding | §0, §1, §4 (Core Engine + CLI), SM-2 | Covered |
| Process sheet image + text file → present/absent per student | FR-1–FR-6 | Covered |
| Smartphone snapshots as input (photo variance) | §4.1 feature NFR (skew, lighting, background, resolution); FR-2 deskew/perspective | Covered |
| Text file of student indices + subject info | Info File (§3), Appendix A normative schema | Covered |
| Python, `python sams.py 10.07.2019.png info.xml` | FR-1, FR-15 (exact commands), UJ-4; FR-1 accepts .png and .jpeg | Covered |
| **Show progress while running (greyscale, binarization, etc.)** *(was partial)* | FR-11: "displays each major pipeline stage **live, on screen, while processing**… saving alone does not satisfy this FR"; FR-16 single display contract | **Covered — resolved** |
| Map processed data via info.xml, store in local DB | FR-5, FR-6, Appendix A | Covered |
| `python infovis.py 001` — summary graph for a student | FR-7, FR-8 (committed default chart: per-Session timeline + attendance rate) | Covered |
| Data-visualization techniques | FR-8 (Matplotlib, labelled chart), SM-3 | Covered |
| `python investigate.py 001` — distinguish signatures, higher grades | FR-9, FR-10, SM-4; committed in scope (§9 preamble) | Covered |
| **"Collect signatures of the given student, compare, report if not matching"** *(was partial)* | FR-9 ingestion path (`references/<student_index>/`) + dataset protocol (refs = sheets 1–3, probes = 4–5, impostors = other students; hand-collected samples may enrich); FR-10 score + thresholded verdict | **Covered — resolved** (interpretation flagged as §9 assumption pending module leader) |
| **Groups of ten, everyone contributes to both concerns** *(was partial)* | §6.3: "epics must be cut so every member has touchpoints in both graded concerns" (decomposition deferred to epics phase, explicitly) | **Covered — resolved** |
| Input different images, get summary (prototype deliverable) | FR-3 dynamic row count; §6.1 all five sheets; SM-C1 anti-overfitting | Covered |
| All five signing sheets in `CGV Signing Sheets.zip` testable | §6.1 (`sample_signin-sheets/` = contents of the zip), SM-1 across all five | Covered |
| Step-by-step process screenshots producible (report dependency) | FR-11: saved labelled stage images "for report screenshots"; SM-3 | Covered |
| Assessment criteria: OOP/coding style, executable, IP libraries & techniques | §7 SM-1–SM-5 anchored to the rubric; §6.1; FR-15/FR-16 | Covered |
| **ZIP submission → prototype runs after unzip** *(was partial)* | FR-15: "runs from a freshly unzipped copy with a one-step documented install (`pip install -r requirements.txt`, pinned); Local DB bootstraps automatically; all paths relative"; UJ-4 | **Covered — resolved** |
| Report deliverable (write-up, discussion, individual contribution pages, front page, references) | §5 explicit Non-Goal | Excluded by user decision |

**MISSING: none. CONTRADICTED: none.** All four previously partial items now have explicit, testable PRD text.

Residual (non-blocking): the brief's "You must collect signatures of the given student" is satisfied via sheet-crop protocol rather than a separate collection exercise; the PRD honestly flags this in §9 as an assumption needing module-leader confirmation and allows hand-collected enrichment. This is an acknowledged open confirmation, not a gap.

## Fix verification table

### Criticals (3/3 resolved)

| # | Finding | Status | Resolving PRD text |
|---|---|---|---|
| C1 | Sheet identifier has no obtainable source (§3, FR-6) | **RESOLVED** | §3 Sheet Identifier: "the Session date in ISO 8601 (`YYYY-MM-DD`) from the Info File's `<session date=\"...\">` element. It is **never** OCR'd from the handwritten date… If the Info File lacks a date, the operator supplies one (CLI flag / Web UI field); final fallback is the image filename stem." FR-6 restates the key: "keyed by **(Student Index, Sheet Identifier)**". Appendix A rules: "`session/@date` is ISO 8601 and becomes the Sheet Identifier (§3)." §5 Non-Goal reinforces: no OCR "of the handwritten sheet date". |
| C2 | Signature bleed-over invalidates per-cell model; FR-2 margin exclusion deletes real signatures | **RESOLVED** | FR-4 "Ink-attribution policy": "segmented into connected components after grid-line masking… Each component is attributed to **one** Signature Cell — the cell containing the majority of its area (centroid as tie-break). Cell ROIs are dilated to capture ink that spills slightly over borders, including into the right margin outside the table. A single component is never counted as presence evidence for two cells." FR-2 softened: "Ink **near or touching the table boundary is retained** — it may be a signature spilling out of its cell… only ink far from the table (e.g. corner page annotations like '10b 1st') is discarded." Testable consequence: "A signature straddling two rows (present on samples 1 and 5) is attributed to exactly one row." |
| C3 | `info.xml` schema undefined, blocks FR-1/5/6/7/9/10/12/15 | **RESOLVED** | Appendix A — "Normative `info.xml` Schema… the source of truth for Student Records, Session metadata, and the Sheet Identifier until the module leader provides an official file (OQ-1). All FRs parse against this shape." Full sample XML with `no`/`index`/`title`/`name` attributes and `session` element supplied. FR-1: "parses the Info File into Student Records and Session metadata per the Appendix A schema"; OQ-1 restated as override-only. |

### Highs (5/5 resolved)

| # | Finding | Status | Resolving PRD text |
|---|---|---|---|
| H1 | Reference Signatures: ingestion undefined, circular source, no mismatch test set | **RESOLVED** | FR-9: "Reference Signatures are image files under `references/<student_index>/`, registered into the Local DB on first use. **Default source split (avoids self-verification):** references = signature crops from sample sheets **1–3**; probes… = crops from sheets **4–5**; the mismatch test set = *other students'* signatures used as impostor probes." Consequence: "Reference and probe sets are disjoint by sheet (no signature is compared against itself)." FR-10: "numeric similarity score plus a thresholded match/mismatch verdict; the method and threshold are documented and justified against the FR-9 dataset split." SM-4 measures on that split. FR-10 Note supplies the fallback (honest threshold reporting still earns "attempt" credit). |
| H2 | Index `001` vs 8-digit form: grader gets "no data" | **RESOLVED** | §3 Student Index: "**Both forms must resolve** everywhere an index is accepted (CLI arguments, Web UI inputs, DB queries)." FR-7 consequence: "`python infovis.py 001` and `python infovis.py 10000409` return the same records for the same student." Appendix A rules: "`student/@no` and `student/@index` are both accepted wherever a Student Index is input (FR-7, FR-10, FR-14)." Unknown index reports "no data" listing valid indices. |
| H3 | FR-11 vs FR-13 Streamlit execution-model conflict (`cv2.imshow` in server; rerun vs idempotency) | **RESOLVED** | FR-16: "The Core Engine exposes pipeline progress as a sequence of labelled stage images (callback/generator), and never opens display windows itself (`cv2.imshow` is forbidden inside the engine)… One stage-emission code path serves both frontends." FR-12: processing is "an **explicit one-shot action** (processing and DB writes happen once per press, never as a side-effect of UI interaction or rerun)"; consequence: "Interacting with unrelated widgets after processing does not re-run the pipeline or rewrite the DB." FR-13 renders "the engine's emitted artifacts, not a second display implementation." |
| H4 | Web UI un-briefed scope, no trade-off stated, zero rubric marks | **RESOLVED** | §1 `[NOTE FOR PM]`: "The Web UI is a deliberate bet, not a grading requirement… sequenced last: Web UI work begins only after SM-1, SM-2, and SM-3 pass on all five sample sheets… Fallback if the timeline compresses: ship engine + CLI only — that alone fully satisfies the brief." §6.3 sequencing gate; FR-15 dependency isolation: "the three CLI commands run on a machine where no web dependency is installed"; SM-6 labelled "*(demo aid, maps to no assessment criterion…)*"; SM-C2 counter-metric. |
| H5 | SM-1 ground truth assumed but genuinely ambiguous; unfalsifiable | **RESOLVED** | SM-1: "measured against the committed `ground_truth.csv` (adjudicated by the team before threshold tuning; Disputed rows scored separately and reported, not counted as errors). Target: 100% on non-Disputed rows." §6.3 "Ground-truth first: the team adjudicates and commits `ground_truth.csv` (sheet × student → Present/Absent/Disputed) **before** tuning detection thresholds." |

### Mechanical notes spot-check

| Note | Status |
|---|---|
| §9 "ground truth" assumption roundtrip failure | **Resolved (superseded)** — ground truth is no longer an assumption at all; it is a committed delivery constraint (§6.3) and SM-1 mechanism. §9 no longer lists it. *New minor drift:* §9's remaining-assumptions list includes FR-9 (dataset split) and Appendix A (schema), but those two body sections carry no inline `[ASSUMPTION]` tag (Streamlit ×2, FR-4, FR-10 do). Cosmetic; both are clearly flagged in §9/OQ-1. |
| Glossary case drift "info file" vs "Info File" | **Resolved** — grep finds zero lowercase/mixed-case occurrences; "Info File" used consistently, including in the Student Record entry. |
| SM-2 validates list omits FR-10 | **Resolved** — SM-2 now reads "Validates FR-1, FR-7, FR-8, FR-10, FR-15." |
| FR-11/FR-13 stage-list drift (missing noise reduction, deskew) | **Resolved** — FR-11: "original, greyscale, denoised, binarized, deskewed, detected grid, per-cell result"; UJ-1 and FR-13 use the same engine-emitted sequence; consistent with FR-2 and the §3 Processing Pipeline definition. |
| `sample_signin-sheets/` vs `CGV Signing Sheets.zip` | **Resolved** — §6.1: "`sample_signin-sheets/` (the contents of the brief's `CGV Signing Sheets.zip`)". |

## Anything still broken

Nothing blocking. Two cosmetic/awareness items:

1. **Assumption-tag roundtrip (cosmetic):** §9 lists FR-9 and Appendix A as "remaining inline assumptions," but neither section carries an inline `[ASSUMPTION]` tag in the body (§0 promises inline tags are indexed in §9). Fix is one-line if desired: add `[ASSUMPTION: default reference/probe split]` to FR-9 and `[ASSUMPTION: group-authored schema]` to Appendix A — or reword §9's preamble.
2. **FR-9 "collect signatures" interpretation (acknowledged, not a defect):** the sheet-crop protocol satisfies the brief functionally, but the PRD itself flags module-leader confirmation as pending (§9). Carry into the epics phase as an open confirmation.
