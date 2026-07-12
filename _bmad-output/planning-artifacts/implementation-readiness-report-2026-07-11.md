---
stepsCompleted: ['step-01-document-discovery', 'step-02-prd-analysis', 'step-03-epic-coverage-validation', 'step-04-ux-alignment', 'step-05-epic-quality-review', 'step-06-final-assessment']
documentsIncluded:
  - '_bmad-output/planning-artifacts/prds/prd-CGV Group Assignment-2026-07-10/prd.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-CGV Group Assignment-2026-07-10/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/ux-designs/ux-CGV Group Assignment-2026-07-10/DESIGN.md'
  - '_bmad-output/planning-artifacts/ux-designs/ux-CGV Group Assignment-2026-07-10/EXPERIENCE.md'
  - '_bmad-output/planning-artifacts/epics.md'
---

# Implementation Readiness Assessment Report

**Date:** 2026-07-11
**Project:** CGV Group Assignment

## Document Inventory

| Type | Canonical Document | Status |
| --- | --- | --- |
| PRD | `prds/prd-CGV Group Assignment-2026-07-10/prd.md` | final (2026-07-10) |
| Architecture | `architecture/architecture-CGV Group Assignment-2026-07-10/ARCHITECTURE-SPINE.md` | final (2026-07-10) |
| UX Design | `ux-designs/ux-CGV Group Assignment-2026-07-10/DESIGN.md` + `EXPERIENCE.md` (spine pair) | final (2026-07-10) |
| Epics & Stories | `epics.md` — 4 epics, 19 stories | complete (2026-07-11) |

- **Duplicates:** none — no document exists in both whole and sharded form. Review/reconcile files alongside the canonical documents are workflow by-products, excluded from assessment.
- **Missing documents:** none — all four required document types present and final.

## PRD Analysis

### Functional Requirements

FR-1: Load and validate inputs — `python sams.py <image> <info.xml>` loads the Signing Sheet image and parses the Info File into Student Records and Session metadata per the Appendix A schema. Valid inputs: both load without error; parsed Student Record count and resolved Sheet Identifier reported. Invalid inputs: clear error message, non-zero exit code, no raw stack trace. Both `.png` and `.jpeg`/`.jpg` accepted.

FR-2: Image preprocessing pipeline — ordered stages: greyscale conversion, noise reduction, thresholding/binarization, geometric normalization (deskew/perspective correction), using OpenCV + NumPy. Runs end-to-end on all five sample sheets; each named stage produces a distinct displayable/savable intermediate image; background outside the sheet excluded; ink near/touching the table boundary retained (only far ink discarded).

FR-3: Table & signature-cell localization — locate the student table (5 columns: No | Student No | Title | Student Name | Signature) below the 4-column Metadata Row band; detect grid; extract each row's Signature Cell tied to correct row order; grid lines masked from cell ROIs; Metadata Row never counted as student row; fixed columns, dynamic row count (discrepancies vs Info File reported); no OCR of printed header text.

FR-4: Signature presence detection with ink attribution — ink (any pen colour) segmented into connected components after grid-line masking; each component attributed to exactly one Signature Cell (majority area, centroid tie-break, dilated ROIs); never double-counted. Classification: coverage ≥ upper threshold → Present; ≤ lower threshold → Absent; between → Ambiguous. Tunable documented constants. 100% vs committed ground-truth key on all five sheets; straddling signatures attributed to one row; lecturer signature never counted.

FR-5: Map detections to Student Records — row order + Info File `no` ordinal maps each Signature Cell to one Student Index; row-count vs record-count mismatch flagged.

FR-6: Persist attendance to Local DB — one Attendance Record per Student Record keyed (Student Index, Sheet Identifier) with subject/session metadata; re-processing updates (no duplicates); operator resolutions survive unless overwrite confirmed; DB file/schema auto-created on first run.

FR-7: Query attendance by student — `python infovis.py <index>` accepts both index forms; both return same records; unknown index → "no data" listing valid indices, not an error.

FR-8: Render attendance graph — Matplotlib; committed default: per-Session Present/Absent timeline (colour-coded, Ambiguous distinct) with overall attendance-rate annotated; title, axes, legend; renders from Attendance Records only.

FR-9: Maintain reference signatures — image files under `references/<student_index>/`, registered into Local DB on first use; default split: references = sheets 1–3 crops, probes = sheets 4–5 crops, impostor probes = other students' signatures; sets disjoint by sheet; retrievable by either index form.

FR-10: Compare and report match — `python investigate.py <index>` compares probe(s) vs Reference Signature(s); numeric similarity score + thresholded match/mismatch verdict; method and threshold documented against FR-9 split; genuine → match, impostor → mismatch (SM-4); feature-based or ML-based.

FR-11: Show step-by-step processing progress — each major pipeline stage displayed live on screen while processing (original, greyscale, denoised, binarized, deskewed, detected table grid, per-cell inspection), in order, labelled; each stage also saved as labelled image file; saving alone does not satisfy.

FR-12: Upload and process a sheet from the browser — Web UI upload of image + Info File; processing as explicit one-shot action (once per press; never a rerun side-effect); invalid inputs → human-readable on-screen error; works in phone browser (responsive, touch-friendly).

FR-13: Live pipeline display, results, and Ambiguous resolution — Web UI renders engine-emitted stage images in order, then per-student result table; persisted to Local DB; Ambiguous rows visually distinct with one-tap Present/Absent resolution updating the Attendance Record.

FR-14: Student lookup views — Web UI accepts Student Index (either form) for attendance graph (FR-8) and verification (FR-10); parity at the data layer (same engine query/figure, same score/threshold outcome).

FR-15: CLI wrappers with engine parity and clean packaging — three brief-verbatim commands on a fresh machine produce same detections/graphs/verdicts as Web UI from same engine and DB; thin entry points, no duplicated logic; engine+CLI import only OpenCV/NumPy/Matplotlib/stdlib; Streamlit optional extra; one-step pinned install; DB bootstraps; paths relative.

FR-16: Engine-emitted stage artifacts — engine exposes pipeline progress as labelled stage images (callback/generator); never opens display windows (`cv2.imshow` forbidden in engine); one emission path serves both frontends, identical names/order; engine headlessly importable and testable.

**Total FRs: 16**

### Non-Functional Requirements

NFR-A (PRD §4.1): Robust to phone-photo variance — moderate skew/perspective, uneven lighting, desk background, punch holes, margin notes, white-out patches, non-pen marks, varying resolution.

NFR-B (PRD §4.6): Web UI runs locally (localhost/LAN), single operator; usable on phone screen (single column, large touch targets, no horizontal scrolling in core flows).

NFR-C (SM-1): Attendance-detection accuracy — 100% on non-Disputed rows vs committed `ground_truth.csv`, adjudicated before threshold tuning.

NFR-D (SM-2): Executable deliverables — all three CLI programs run per the brief on a fresh setup (one-step install, no web dependencies).

NFR-E (SM-3): Demonstrated technique — every stage demonstrable live and as saved images.

NFR-F (SM-4): Verification capability — correct match/mismatch on the FR-9 split, threshold documented.

NFR-G (SM-5): Code quality — cohesive OOP design, engine separated from frontends, headless-testable, no dead scripts, tests green.

NFR-H (SM-6): Admin usability — non-technical operator completes upload → results on a phone with no external instructions.

NFR-I (SM-C1): No overfitting — no hard-coded pixel coordinates, per-sheet special-casing, or per-image thresholds.

NFR-J (SM-C2): Web UI polish must not consume engine-hardening time — enforced by §6.3 gate.

**Total NFRs: 10**

### Additional Requirements

- §5 Non-Goals: no report deliverable in software scope; no native app; no cloud/auth/multi-user; no LMS integration; no live camera capture; no handwriting OCR anywhere (including sheet date).
- §6.3 Delivery constraints: Web UI sequenced strictly after SM-1..SM-3 pass on all five sheets; ground truth committed before threshold tuning; 10-member decomposition — every member needs touchpoints in both image processing and visualization.
- §3 Glossary is normative — terms used verbatim downstream; Sheet Identifier = Info File session date (ISO 8601), never OCR'd; both Student Index forms resolve everywhere.
- Appendix A: normative `info.xml` schema (group-authored, pending module-leader override — OQ-1).
- Open questions: OQ-1 (official info.xml), OQ-2 (chart-type confirmation), OQ-3 (Streamlit vs Flask — resolved to Streamlit by UX/Architecture).
- Assumptions pending confirmation: Streamlit framework, coverage-band ambiguity criterion, sheet-crop reference protocol, OpenCV feature-matching approach, Appendix A schema standing.

### PRD Completeness Assessment

The PRD is unusually implementation-ready: FRs carry testable consequences, success metrics anchor to the grading rubric, non-goals fence scope explicitly, glossary is normative, and the info.xml schema is specified. Remaining open questions (OQ-1, OQ-2) are externally owned (module leader) with committed defaults — they do not block implementation. No gaps found that would impede epic coverage validation.

## Epic Coverage Validation

### Coverage Matrix

*Verified against actual story acceptance criteria, not only the epics document's own coverage map.*

| FR | PRD Requirement (abbrev.) | Epic Coverage | Status |
| --- | --- | --- | --- |
| FR-1 | Load & validate image + Info File, both formats, clean errors | Epic 1 Story 1.1 (all four consequences in ACs, incl. exit codes and `--date`) | ✓ Covered |
| FR-2 | Preprocessing pipeline stages, five-sheet robustness | Epic 1 Story 1.2 | ✓ Covered |
| FR-3 | Table & cell localization, grid masking, dynamic rows | Epic 1 Story 1.3 | ✓ Covered |
| FR-4 | Ink attribution + three-state classification | Epic 1 Story 1.4 (accuracy vs ground truth executed in Story 1.6) | ✓ Covered |
| FR-5 | Map detections to Student Records | Epic 1 Story 1.5 | ✓ Covered |
| FR-6 | Persist to Local DB, upsert, resolution survival | Epic 1 Story 1.5 | ✓ Covered |
| FR-7 | Query by either index form, no-data listing | Epic 2 Story 2.1 | ✓ Covered |
| FR-8 | Attendance timeline graph, Ambiguous distinct, rate annotated | Epic 2 Story 2.2 | ✓ Covered |
| FR-9 | Reference signature store + disjoint protocol | Epic 3 Story 3.1 | ✓ Covered |
| FR-10 | Similarity score + thresholded verdict, documented | Epic 3 Stories 3.2 + 3.3 (evaluation) | ✓ Covered |
| FR-11 | Live stage display + saved labelled images | Epic 1 Stories 1.2 + 1.3 + 1.4 (stages accrue as built; all 7 asserted in 1.6) | ✓ Covered |
| FR-12 | Browser upload, one-shot processing | Epic 4 Story 4.2 | ✓ Covered |
| FR-13 | Web stage strip, results, Ambiguous resolution | Epic 4 Stories 4.3 + 4.4 | ✓ Covered |
| FR-14 | Web Lookup + Investigate, data-layer parity | Epic 4 Stories 4.5 + 4.6 | ✓ Covered |
| FR-15 | CLI parity, dependency isolation, fresh-setup packaging | Epic 1 Story 1.7 + Epic 4 Story 4.7 (cross-frontend parity) | ✓ Covered |
| FR-16 | Engine-emitted stage artifacts, headless engine | Epic 1 Stories 1.2 + 1.4 (emission contract) + 1.6 (headless test assertion) | ✓ Covered |

### Missing Requirements

None. Every PRD FR traces to at least one story whose acceptance criteria address its testable consequences. No orphan FRs exist in the epics document that are absent from the PRD (numbering is shared and consistent).

### Coverage Statistics

- Total PRD FRs: 16
- FRs covered in epics: 16
- Coverage percentage: **100%**

## UX Alignment Assessment

### UX Document Status

**Found** — complete bmad-ux spine pair: `DESIGN.md` (Quiet Clerk visual identity, status final) + `EXPERIENCE.md` (experience spine incl. CLI Display Contract, status final).

### UX ↔ PRD Alignment

- **User journeys:** EXPERIENCE.md Key Flows 1–4 are inherited verbatim from PRD §2.3 (UJ-1..UJ-4), same protagonist, same climaxes. ✓
- **Glossary discipline:** UX uses PRD §3 terms verbatim as required by PRD §6.3. ✓
- **OQ-3 (framework):** PRD left Streamlit as an assumption/open question; the UX spine records it as confirmed by the team during UX design, and Architecture pins streamlit 1.59.1. Resolved downstream — the PRD text still lists OQ-3 as open, a cosmetic staleness only, no action required. ✓
- **UX elaborations beyond PRD** (overwrite warning + `--overwrite` flag, Undo affordance, per-sheet `output/<Sheet Identifier>/` folders, date-field fallback, Ambiguous mid-band charting, no-data patterns): all are consistent extensions of PRD FRs, none contradict a PRD requirement, and all were adopted into the Architecture (AD-4, AD-7, AD-11) and the epics (UX-DR1..16). ✓

### UX ↔ Architecture Alignment

- Architecture lists both UX spines as sources and explicitly ADOPTS UX-owned behavior: AD-4 (overwrite semantics from UX), AD-7 (display boundary per the CLI Display Contract), AD-11 (Web date field, no filename fallback in Web). ✓
- Repository API surface supports every UX behavior: `has_operator_resolutions` (pre-Process overwrite warning), `resolve(..., by_operator=True)` with undo restoring Ambiguous, `list_students()` (no-data listings). ✓
- Streaming stage strip is supported by the AD-3 generator/callback emission; Streamlit-native identity is supported by AD-8's `requirements-web.txt` isolation without breaking the grader path. ✓
- Naming nit checked: UX writes `NN-stage.png`, Architecture writes `NN-slug.png` — same contract (the stage's slug), vocabulary shared verbatim per the AD-3 registry. Consistent. ✓

### Warnings

None blocking. Three UX `[ASSUMPTION]` tags (Undo duration ~5 s, similarity score displayed 0–100, non-blocking CLI stage windows) are declared build-time constants and are carried into story ACs — implementers decide them without re-opening design.

## Epic Quality Review

### Epic Structure Validation

| Check | E1 | E2 | E3 | E4 | Verdict |
| --- | --- | --- | --- | --- | --- |
| User-value title & goal (not technical milestone) | ✓ | ✓ | ✓ | ✓ | PASS |
| Standalone (no future epic required) | ✓ | ✓ | ✓ | ✓ | PASS |
| Stories sized for single dev session | ✓ | ✓ | ✓ | ✓ | PASS |
| No forward dependencies within epic | ✓ | ✓ | ✓ | ✓ | PASS |
| DB objects created only when first needed | ✓ (schema in 1.5) | n/a | ✓ (registration in 3.1) | n/a | PASS |
| ACs in Given/When/Then, testable, error paths covered | ✓ | ✓ | ✓ | ✓ | PASS |
| FR traceability maintained | ✓ | ✓ | ✓ | ✓ | PASS |

- **Epic independence verified:** E1 delivers complete standalone value (and alone satisfies the coursework brief); E2 consumes only E1's DB; E3 consumes only E1's crops; E4 consumes E1–E3 engine capabilities (backward-only). No circular or forward epic dependencies.
- **Within-epic ordering verified story by story:** 1.1→1.7 strictly buildable in order; 2.2 uses 2.1's query; 3.2 uses 3.1's references and E1's crops; 4.4 acts on rows 4.3 renders; 4.7 verifies surfaces built in 4.1–4.6. Forward *references* in prose (e.g. Story 1.4 "ready for Epic 3", Story 2.2 "the Web UI will later render") are enabling notes, not dependencies — the stories complete without the referenced future work.
- **Starter template check:** Architecture specifies none (greenfield, Structural Seed layout). Story 1.1 scaffolds only what it needs — compliant; no big-upfront-setup violation.
- **Technical-epic check:** none found. Stories 1.6 and 3.3 are group-voiced ("As the development group…") but map directly to graded success metrics (SM-1..SM-4) — for coursework, the marker and group are legitimate users of these outcomes; PRD §2.1 names the Builder's JTBD explicitly. Accepted with rationale.

### Findings by Severity

#### 🔴 Critical Violations

None.

#### 🟠 Major Issues

None.

#### 🟡 Minor Concerns

1. **No `info.xml` exists in the project yet.** The PRD's Appendix A provides the normative schema and a complete example, but no actual Info File has been authored for any of the five sample sheets, and the sheets' real student rosters must be transcribed to build them. Stories 1.1/1.6 implicitly require these fixtures. *Recommendation:* treat "author per-sheet `info.xml` fixtures (with session dates) from the sample sheets" as an explicit early task in sprint planning — it gates Story 1.1's happy-path AC and all five-sheet ACs.
2. **Human prep tasks embedded in story preconditions.** `ground_truth.csv` adjudication (Story 1.6 precondition, must precede threshold tuning) and reference-crop curation from sheets 1–3 (Story 3.1) are team activities, not agent work. *Recommendation:* schedule both as parallel human tasks in sprint planning so no dev story stalls waiting on them.
3. **Sample filenames defeat the filename-date fallback.** The samples are `1.jpeg`..`5.jpeg`, so AR-11's final fallback (filename stem → ISO date) cannot produce Sheet Identifiers for them — the authored `info.xml` files (or `--date`) must carry the session dates. Covered by the AR-11 chain and Story 1.1's ACs, but worth stating so test fixtures are built with dates from day one.
4. **Constraint-style ACs.** A handful of ACs use "Given/Then" without a "When" (e.g. "Given AR-1, Then `sams.py` stays under 50 lines"). These are static conventions rather than behaviors; format deviation is deliberate and testable by inspection. No action needed.

### Best-Practices Compliance Summary

19/19 stories pass sizing, independence, and traceability checks. No remediation required before proceeding; the three actionable minor concerns are sprint-planning inputs, not document defects.

## Summary and Recommendations

### Overall Readiness Status

**READY** ✅

All four planning artifacts are final, mutually aligned, and traceable end to end: 16/16 FRs covered by stories (100%), all 10 NFRs and 16 UX-DRs threaded into acceptance criteria, architecture decisions adopted verbatim into story constraints, zero critical or major findings.

### Critical Issues Requiring Immediate Action

None. No blocking issues were found in any category.

### Recommended Next Steps

1. **Run sprint planning** (`bmad-sprint-planning`) and register three human/data-prep tasks alongside the dev stories: (a) author per-sheet `info.xml` fixtures with session dates for all five sample sheets (gates Story 1.1's five-sheet ACs — no Info File exists yet and the `1.jpeg`..`5.jpeg` filenames defeat the date fallback); (b) adjudicate and commit `tests/data/ground_truth.csv` **before** any threshold tuning (gates Story 1.6); (c) curate reference crops from sheets 1–3 into `references/<student_index>/` (gates Story 3.1).
2. **Sequence Epic 3's verification spike early** in the sprint order (the PRD flags it highest-risk; epic independence permits running it right after Stories 1.1–1.4 produce crops) while holding Epic 4 strictly behind the Story 1.6 gate (SM-1..SM-3 green on all five sheets).
3. **Map the 10 group members onto stories** during sprint planning so every member touches both graded concerns (image processing and visualization), per the coursework brief and AR-16.

### Final Note

This assessment identified 4 minor concerns across 1 category (sprint-planning inputs; none are document defects) and 0 critical or major issues. The planning set — PRD, UX contract, Architecture Spine, and 4 epics / 19 stories — is internally consistent and implementation-ready. Proceed to Phase 4.

**Assessed:** 2026-07-11 · **Assessor:** BMad Implementation Readiness workflow (PM role), with LakshithaWijerathneB
