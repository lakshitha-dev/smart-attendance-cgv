# Brief Coverage Audit — SAMS PRD

Audited: `prd.md` (2026-07-10) against `CS402.3 Coursework.md`.
Scope per user decision: development/prototype deliverable only; report-writing deliverables excluded, but development capabilities the report depends on are in scope.

## Verdict

The PRD covers every development-relevant requirement in the brief — nothing is missing or contradicted; 26 requirements are fully covered and 4 are partial. The dominant risk is not a gap but an addition: the mobile Web UI (FR-12–FR-14, ~a third of the FR surface) has no basis in the brief and diverts a marks-free share of a 10-person effort, though FR-15 CLI parity soundly mitigates the marker-facing risk.

## Trace table

| # | Brief requirement (source) | PRD coverage | Status |
|---|---|---|---|
| 1 | Prototype = working software with backend coding (Coursework intro) | §0, §1, SM-2 | COVERED |
| 2 | Student attendance management system based on signing sheets (Scenario) | §1 Vision, §4.1–4.2 | COVERED |
| 3 | Signing sheets have a specific, static layout (Scenario) | Glossary "Signing Sheet", FR-3, §6.2 (single static layout only) | COVERED |
| 4 | Students sign using different colour pens (Scenario, Big Picture) | FR-4 consequence "tolerates different pen colours (not restricted to black ink)" | COVERED |
| 5 | Admin takes smartphone snapshots; program consumes provided image files (Scenario) | §1, FR-1, §4.1 NFR (phone-photo variance); §5 no live camera | COVERED |
| 6 | Admin provides a text file with student indices + subject info; Processing section fixes it as `info.xml` (Scenario, Processing, Fig. 1) | Glossary "Info File" (XML), FR-1; schema tracked in OQ-1 | COVERED (schema open) |
| 7 | Process image and text content; identify present/absent based on appearance of a signature (Scenario) | FR-2, FR-3, FR-4, FR-5 | COVERED |
| 8 | Key technology 1: image processing (Scenario) | FR-2–FR-4, SM-3 | COVERED |
| 9 | Key technology 2: data visualization (Scenario, Visualization) | FR-7, FR-8, FR-14, SM-2 | COVERED |
| 10 | Program preferably written in Python (Processing) | §9 confirmed stack (Python + OpenCV/NumPy + Matplotlib + SQLite) | COVERED |
| 11 | Exact command `python sams.py 10.07.2019.png info.xml` (Processing) | FR-1, FR-15, UJ-4 | COVERED |
| 12 | "While the program is running you need to show the progress" — greyscale, binarization, etc. (Processing) | FR-11, FR-2 consequences | PARTIAL — FR-11 says "displays **or saves**"; save-only would not satisfy "while running" (see Finding 3) |
| 13 | Use info.xml to map the processed data (Processing, Fig. 1) | FR-5 | COVERED |
| 14 | Store the attendance in a local DB (Processing) | FR-6, Glossary "Local DB" (SQLite) | COVERED |
| 15 | Second program: attendance summary for a given student, displayed as a suitable graph using data-visualization knowledge (Visualization) | FR-7, FR-8 | COVERED |
| 16 | Exact command `python infovis.py 001` (Visualization) | FR-7, FR-15; index-form ambiguity flagged in OQ-4 | COVERED |
| 17 | Attempt to distinguish signatures using advanced library or self-created → higher grades (Recognition) | FR-10 + §4.4 note (committed, higher-grade lever) | COVERED |
| 18 | "You must collect signatures of the given student" (Recognition) | FR-9 (store/retrieve Reference Signatures); collection method deferred to OQ-2 | PARTIAL — storage is specified, but the mandated *collection* workflow is not an FR and OQ-2 is acknowledged as blocking (see Finding 5) |
| 19 | Compare and report if signatures are not matching (Recognition) | FR-10 consequences (match/mismatch + documented method/threshold) | COVERED |
| 20 | Exact command `python investigate.py 001` (Recognition) | FR-10, FR-15 | COVERED |
| 21 | Groups of ten, each playing a different role, but everybody contributes to image processing and visualization (Grouping) | §0 mentions "10-member development group to align on scope, roles" — nothing more | PARTIAL — no requirement/structure ensuring the work decomposes so all 10 touch both graded concerns (see Finding 2) |
| 22 | Prototype deliverable: input different images and get a summary of attendance (Deliverables) | §1, §6.1, SM-1, SM-2; per-sheet invocation (batch out of scope §6.2 — acceptable, brief doesn't require batch) | COVERED |
| 23 | Report dependency: software can produce/save step-by-step processing screenshots (Report, Assessment 25%) | FR-11 (display/save labelled stages), FR-13, SM-3 ("supports screenshots") | COVERED |
| 24 | Report dependency: testing results for all five signing sheets in the zip (Report) | §6.1 "correct operation across all five", FR-2 consequence, SM-1, §9 ground-truth assumption | COVERED |
| 25 | Assessment: coding styles, OOP concepts (Prototype 60%) | §4.7, SM-5, §6.1 | COVERED |
| 26 | Assessment: testing results as part of program quality (Prototype 60%) | SM-5 ("tests green"), §6.1 ("with tests") | COVERED |
| 27 | Assessment: executable program (Prototype 60%) | SM-2 (runs clean on a fresh setup, exact brief commands) | COVERED |
| 28 | Assessment: use of image-processing libraries (Prototype 60%) | FR-2 (OpenCV + NumPy) | COVERED |
| 29 | Assessment: use of image-processing techniques (Prototype 60%) | FR-2, FR-3, SM-3, SM-C1 (anti-overfitting counter-metric) | COVERED |
| 30 | Submission: prototype uploaded as a zip file, i.e. must run from a packaged copy (Submission Type) | SM-2 "run clean on a fresh setup" implies it; no FR for packaging, dependency manifest, or setup docs | PARTIAL (low — see Finding 4) |

**Counts: 26 COVERED · 4 PARTIAL · 0 MISSING · 0 CONTRADICTED**

## Findings

1. **[high] Web UI is un-briefed scope** — Feature 4.6 (FR-12, FR-13, FR-14), half of 4.7, UJ-1–UJ-3's browser framing, and SM-6 build a mobile web frontend the brief never asks for; the brief's 60% prototype marks reward image-processing technique, OOP, testing, and the three CLI programs. For a graded university deliverable this is the single largest effort-diversion risk, plus it adds a framework dependency (Streamlit, unconfirmed — OQ-6) that could complicate "executable program" on the marker's machine. — *Fix: either explicitly demote the Web UI to a stretch goal behind a completed CLI + engine, or keep it but add a hard dependency-ordering statement (Core Engine + CLI are MVP-gating; Web UI ships only after SM-1/SM-2/SM-3 are met) and ensure the CLI runs with zero Web UI dependencies installed.*

2. **[medium] Group-of-ten contribution constraint not operationalized** — The brief requires 10 members, each with a distinct role, and *everybody* contributing to both image processing and visualization. The PRD only name-checks "10-member development group … roles" in §0. Since each member's grade (15%) depends on demonstrable contribution to both concerns, the PRD's scope should decompose in a way that makes that possible. — *Fix: add a short "Team & work decomposition" constraint (or explicit note deferring it to epics/stories) requiring work packages that give all ten members touchpoints in both image processing and visualization.*

3. **[medium] Live progress display weakened to "display or save"** — The brief: "While the program is running you need to show the progress of the image processing." FR-11's consequence permits "window display **and/or** saved intermediate image files", so a save-only implementation would technically satisfy the FR while failing the brief. — *Fix: make live on-screen display of each stage mandatory in FR-11; saving intermediates is supplemental (and still valuable for report screenshots).*

4. **[low] Packaging / fresh-setup run not an explicit requirement** — The prototype must be submitted as a zip and run on the marker's machine. SM-2's "run clean on a fresh setup" gestures at this, but no FR covers a dependency manifest (requirements.txt), documented setup, or relative-path/DB-bootstrap behaviour when unzipped elsewhere. — *Fix: add a consequence under FR-15 or an NFR: the prototype runs from a fresh unzipped copy with documented one-step dependency install; the Local DB is created automatically if absent.*

5. **[medium] Committed higher-grade component rests on an unresolved blocker** — `investigate.py` is committed in scope (FR-9/FR-10, SM-4) and the brief mandates "you must collect signatures", but the collection method is an open question (OQ-2) the PRD itself calls blocking, with no fallback. — *Fix: pick a default now (crop Reference Signatures from the five sample sheets, hand-collected samples as enrichment) and record it as the assumption, so FR-9 is buildable without waiting on OQ-2.*

## Over-scope / misreadings

**Over-scope (brief does not ask for it):**
- **Mobile Web UI + dual-frontend architecture** (§4.6, FR-12–FR-14, parts of §4.7, SM-6, phone-usability NFRs) — see Finding 1. Mitigations already in the PRD: FR-15 CLI parity guarantees the brief's exact commands work; localhost-only, no auth. The risk is effort allocation and dependency weight, not marker-facing behaviour.
- **Ambiguous-cell flag-for-review flow** (UJ-1 edge case, FR-13 "flagged rows", OQ-5) — not in the brief; small and arguably improves testing-results credibility. Acceptable, keep lightweight.
- **Idempotent re-processing / upsert semantics** (FR-6 assumption) — beyond the brief but sensible for repeated marker runs; low risk.
- *Not* over-scope despite not being named in the brief: deskew/perspective correction, denoising, SQLite as the Local DB — all directly justified by the phone-photo scenario, "local DB" wording, and the image-processing-techniques criterion.

**Misreadings: none material.** Verified points:
- The brief's Scenario says "text file" while its Processing section and command line fix `info.xml`; the PRD's commitment to XML (Glossary, §9 confirmation) is the correct reconciliation, not a misreading.
- The brief's short index `001` vs the sample sheets' 8-digit Student No is correctly caught and deferred (Glossary "Student Index", OQ-4) rather than silently resolved.
- Figure 1 (info.xml schema) is absent from the markdown brief; the PRD correctly treats the schema as undefined (OQ-1) rather than inventing one.
- Trivial naming drift only: PRD references `sample_signin-sheets/` where the brief names `CGV Signing Sheets.zip` — confirm the folder actually matches the zip's five sheets.
