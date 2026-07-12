# Validation Report — Student Attendance Management System (SAMS)

- **PRD:** `_bmad-output/planning-artifacts/prds/prd-CGV Group Assignment-2026-07-10/prd.md`
- **Rubric:** `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-07-10
- **Grade:** Poor (pre-fix — driven by 3 adversarial criticals; all critical/high findings fixed in the PRD immediately after this run)

## Overall verdict

The rubric review finds a genuinely usable coursework PRD: grade-anchored thesis (one Core Engine behind two frontends), FRs with testable consequences, honest scope machinery. Rubric-level risks: `investigate.py`'s reference-signature pathway undefined; ambiguous-cell handling half-decided.

The adversarial reviewer — who inspected the five real sample photos — materially shifts the picture with 3 criticals: the sheet identifier keying FR-6/7/8 has no obtainable source; real signatures straddle rows and spill outside the table, breaking the "ink in cell = Present" model (and FR-2's margin-exclusion rule would delete a real signature); and the `info.xml` schema is deferred while blocking eight FRs. The brief-coverage audit confirms **nothing from the brief is missing** (26 covered / 4 partial / 0 missing / 0 contradicted) but flags the Web UI as the largest un-briefed effort-diversion risk, mitigated by FR-15 CLI parity.

## Dimension verdicts

- Decision-readiness — adequate
- Substance over theater — strong
- Strategic coherence — strong
- Done-ness clarity — adequate
- Scope honesty — strong
- Downstream usability — strong
- Shape fit — strong

## Findings by severity

### Critical (3)

**[Adversarial]** — Sheet identifier has no obtainable source (§3, FR-6)
Dates are handwritten in three formats, OCR is a Non-Goal, real files are `1.jpeg`–`5.jpeg`. FR-6 persistence/idempotency, FR-7 queries, FR-8 graphs all key on a value nobody can produce.
Fix: session date carried in `info.xml` (and/or CLI/UI-supplied), canonical ISO 8601; restate FR-6's key.

**[Adversarial]** — Signature bleed-over invalidates the per-cell model; FR-2's margin exclusion deletes real signatures (FR-2/3/4)
Samples show signatures straddling row boundaries, overlapping, spilling outside the table border.
Fix: ink-attribution policy (connected components by centroid/majority area, dilated ROIs, table-adjacent ink = candidate signature); soften FR-2 margin exclusion.

**[Adversarial]** — `info.xml` schema undefined; blocks FR-1/5/6/7/9/10/12/15 (OQ-1)
The group must author the file anyway; deferring it prevents a 10-person team from parallelizing.
Fix: normative sample schema in a PRD appendix, pending module-leader override.

### High (7 — deduped to 5)

**[Rubric + Coverage + Adversarial]** — Reference Signatures: ingestion undefined + circular source + no mismatch test set (FR-9/10, OQ-2, SM-4)
Fix: protocol — references cropped from sheets 1–3, probes from 4–5, mismatch set = other students; defined ingestion path; documented metric + threshold.

**[Adversarial]** — Student Index `001` vs `10009301`: grader running the brief verbatim gets "no data" (§3, OQ-4, FR-7)
Fix: both forms resolve — short `No` ordinal/alias mapped via `info.xml` + 8-digit Student No.

**[Adversarial]** — FR-11 vs FR-13 Streamlit execution-model conflict (`cv2.imshow` can't run in server; rerun model collides with idempotency)
Fix: engine emits labelled stage artifacts via callback/generator; frontends only render; no `cv2.imshow` in engine; one-shot processing action in UI.

**[Coverage + Adversarial + Rubric]** — Web UI is un-briefed scope with no stated trade-off; earns zero rubric marks (§4.6, SM-6)
Fix: keep, but hard-gate behind SM-1–SM-3 passing; cap scope; CLI must run with zero web dependencies.

**[Adversarial]** — SM-1 ground truth assumed but genuinely ambiguous on the samples; "every error explainable" makes it unfalsifiable
Fix: committed `ground_truth.csv` adjudicated before tuning; Disputed rows scored separately.

### Medium (13 — deduped to 9)

1. **[Rubric + Adversarial]** Ambiguous-cell handling decided in UJ-1/FR-13, open in OQ-5; no criterion; binary data model can't store "flagged." Fix: third state + criterion + review flow, or drop the promise.
2. **[Rubric + Adversarial]** FR-8 chart is adjectival/TBD for a co-equal graded technology. Fix: commit a default chart.
3. **[Rubric]** "Sheet identifier" used as idempotency key without Glossary entry/derivation. Fix: define it (folds into Critical #1 fix).
4. **[Coverage]** Live progress display weakened to "display **or** save"; brief requires showing progress while running. Fix: live display mandatory.
5. **[Coverage]** Group-of-ten dual-contribution constraint not operationalized. Fix: note deferring decomposition constraint to epics.
6. **[Adversarial + Coverage]** Fresh-setup/packaging unsupported: web imports can kill the graded CLI commands; formats unstated. Fix: dependency-isolation FR + requirements manifest + DB bootstrap + accepts .png/.jpeg.
7. **[Adversarial]** Metadata table vs student table localization mechanism unstated (two look-alike grids; white-out; red grader ink). Fix: name the mechanism (5-column grid selection; grid-line masking).
8. **[Adversarial]** FR-14 "identical in content" untestable. Fix: parity at the data layer.
9. **[Rubric]** Web UI trade-off unstated in §1. Fix: honest `[NOTE FOR PM]` naming the bet + fallback.

### Low (8 — deduped to 7)

1. Grade-weight drift: §6.1 "code quality/OOP is 60%" vs Prototype-as-a-whole 60%.
2. No fallback stated for blocked `investigate.py` (folds into High #1 fix).
3. FR-10 similarity indication has no shape (score + thresholded verdict).
4. Row-count generality: column layout fixed, row count dynamic — say it.
5. Header typos ("Signatue", "Lecture's Name") — warn off header-text OCR.
6. Date-format normalization — ISO 8601 canonical.
7. Packaging FR explicit (zip → unzip → one-step install → run).

## Mechanical notes

- §9 "ground truth" entry has no inline `[ASSUMPTION]` tag in the body (roundtrip failure).
- Glossary case drift: "info file" vs "Info File" in Student Record.
- SM-2 validates list omits FR-10 despite requiring `investigate.py` to run.
- FR-11/FR-13 stage lists omit noise reduction and deskew that FR-2 defines.
- `sample_signin-sheets/` vs brief's `CGV Signing Sheets.zip` — confirm the folder matches the zip.
- All UJ protagonists named; all ID chains contiguous and resolving.

## Reviewer files

- `review-rubric.md`
- `review-adversarial.md`
- `review-brief-coverage.md`
