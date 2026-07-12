# 🎯 SAMS — 8 Independent Sprints (Pick 1 per Member)

**Project:** Student Attendance Management System (CS402.3 Group Coursework)
**Model:** Each member owns ONE sprint = one complete feature, implemented **end-to-end by that member alone**: all its user stories, development, and testing. No waiting on other members.
**How to pick:** send your top 2 preferences; clashes resolved by strongest one-sentence case.

## 🔑 How independence works — the Day-1 Fixture Kit

A processing pipeline can't be split with zero connections — so we cut the connections with **fixtures**, agreed and committed by everyone together on Day 1 (half-day, all hands):

1. **Frozen contracts** — `models.py` dataclasses, DB schema, `StageArtifact` shape, function signatures. Agreed once, then nobody's code waits on anybody's.
2. **Committed fixtures** — stand-ins for other sprints' outputs: the 5 sample sheets + 5 `info.xml` files, hand-deskewed sheet images, cropped cell images, hand-cropped signature samples, a seeded sample database, and a recorded stage-image sequence.
3. **You build and test against fixtures** — your sprint is "done" when it passes its own tests on fixture inputs.
4. **Integration window (last 2 days)** — fixtures are swapped for real upstream outputs; the accuracy gate runs on the real chain.

⚠️ **Trade-off to accept knowingly:** full independence means some sprints are image-processing-heavy and others visualization-heavy — pure both-concern balance is weaker than in a paired model. Mitigation: every sprint below includes a named **cross-concern element** for your report chapter, and the stage displays / charts / score plots legitimately count as Data Visualization.

---

## Sprint 1. 🏗️ Foundation, Contracts & Input Validation

**Stories:** 1.1 · **You build:** the repo scaffold, all shared contracts (`models.py`, `errors.py`, `config.py`), `info_file.py` XML parsing, `sams.py` input validation with clean errors and the Sheet Identifier date logic, plus their unit tests.
**Independent because:** your inputs are the raw fixtures themselves. ⚠️ You go FIRST — contracts must be committed by end of Day 1 (agreed jointly at the Day-1 session, you implement them).
**Cross-concern element:** you define the `StageArtifact` visual contract every display consumes.
**Difficulty:** ⭐⭐ + deadline pressure · **Chosen by:** ___________

## Sprint 2. 🎞️ Image Preprocessing

**Stories:** 1.2 · **You build:** greyscale → denoise → binarize → deskew stages as pure functions, the pipeline stage registry, live OpenCV stage windows, saved stage images (`output/<sheet>/NN-slug.png`), plus tests on all 5 sheets.
**Independent because:** input = the 5 raw sample photos (fixtures). Output feeds others, but you test visually + programmatically alone.
**Cross-concern element:** the live stage display and saved report screenshots ARE the "show processing progress" visualization requirement.
**Difficulty:** ⭐⭐⭐ · **Chosen by:** ___________

## Sprint 3. 📐 Table & Cell Localization

**Stories:** 1.3 · **You build:** student-table detection below the metadata row, grid detection, per-row Signature Cell extraction, grid-line masking, the "detected table grid" overlay stage, row-count-mismatch warnings, plus tests on all 5 sheets.
**Independent because:** input = committed hand-deskewed sheet images (fixture kit) — you never wait for Sprint 2.
**Cross-concern element:** the grid-overlay visualization stage.
**Difficulty:** ⭐⭐⭐⭐ · **Chosen by:** ___________

## Sprint 4. ✍️ Signature Detection & Classification

**Stories:** 1.4 · **You build:** ink segmentation (any pen colour), component-to-cell attribution (straddling signatures!), Present/Absent/Ambiguous coverage-band classification, the per-cell inspection overlay stage, signature crop extraction, plus tests.
**Independent because:** input = committed cell-crop + grid-mask fixtures — you never wait for Sprint 3.
**Cross-concern element:** the per-cell inspection composite is the pipeline's most report-worthy visual.
**Difficulty:** ⭐⭐⭐⭐ · **Chosen by:** ___________

## Sprint 5. 🗃️ Data Layer, Integration & the Accuracy Gate

**Stories:** 1.5, 1.6 · **You build:** the SQLite repository (upsert, `--overwrite`, resolve/undo APIs), detection→student mapping, the single `process_sheet()` entry point, per-student stdout summary, the ground-truth accuracy test suite — **and you run the final integration** where fixtures get swapped for the real chain.
**Independent because:** input = fixture classification results (CSV/JSON) until integration; ground truth is committed Day 1.
**Cross-concern element:** the accuracy report output + stdout summary formatting.
**Difficulty:** ⭐⭐⭐ + integration responsibility · **Chosen by:** ___________

## Sprint 6. 📊 Attendance Visualization (complete feature)

**Stories:** 2.1, 2.2, 4.5 · **You build:** `infovis.py` end-to-end — index resolution (both forms), no-data handling, the Matplotlib attendance timeline (Ambiguous mid-band, attendance rate, full labelling) — AND the Web Lookup page rendering the same figure. Plus tests.
**Independent because:** input = a seeded sample database (fixture kit). You never touch the pipeline.
**Cross-concern element (IP side):** document how classification statuses flow into your chart; assist ground-truth adjudication Day 1.
**Difficulty:** ⭐⭐⭐ · **Chosen by:** ___________

## Sprint 7. 🕵️ Signature Verification (complete feature)

**Stories:** 3.1, 3.2, 3.3, 4.6 · **You build:** the reference-signature store and protocol, the similarity comparison engine, `investigate.py`, the genuine/impostor evaluation with score-distribution plots and threshold justification — AND the Web Investigate page (side-by-side + score scale + verdict). Plus tests.
**Independent because:** input = hand-cropped signature fixtures from sheets 1–3/4–5, curated by you on Day 1 with no code needed.
**Cross-concern element:** score-distribution plots are genuine data visualization; comparison is genuine image processing — this sprint has the best built-in balance.
**Difficulty:** ⭐⭐⭐⭐⭐ (research risk — highest grade upside) · **Chosen by:** ___________

## Sprint 8. 📱 Web Process Experience & Packaging (complete feature)

**Stories:** 4.1, 4.2, 4.3, 4.4, 4.7, 1.7 · **You build:** the Streamlit app — theme, three-page shell, upload slots, one-shot Process fence, overwrite warning, streaming stage strip, results list with status chips, Ambiguous one-tap resolve + Undo, responsive/accessibility pass — plus fresh-machine packaging and the CLI↔Web parity check.
**Independent because:** input = a stub `process_sheet()` replaying the recorded stage-image sequence + seeded DB (fixture kit); swap to the real engine at integration. 🔒 Real-engine wiring only after Sprint 5's accuracy gate is green (coursework rule).
**Cross-concern element (IP side):** you wire and verify the real pipeline at integration and own the parity proof.
**Difficulty:** ⭐⭐⭐ (most stories, but pages are thin wrappers) · **Chosen by:** ___________

---

## Suggested Timeline (2 weeks)

| Days | What happens |
|---|---|
| **1** | All-hands half-day: agree contracts, build the full fixture kit (info.xml ×5, ground truth, deskewed images, cell crops, signature crops, seeded DB, recorded stages). Sprint 1 finishes contracts by tonight. |
| **2–7** | Everyone builds their sprint **in parallel, independently**, testing against fixtures. Daily 15-min stand-up (contract questions only). |
| **8–9** | **Integration window** (led by Sprint 5): swap fixtures for real outputs in chain order 2→3→4→5, run the accuracy gate, wire Sprint 8 to the real engine, run the parity check. Everyone fixes their own seam bugs. |
| **9–10** | Report: each member writes their ~2-page chapter on their sprint; assemble screenshots, testing results, discussion; package ZIP + Word → LMS. |

## Story Coverage Check

Sprints 1–8 cover all 19 stories: 1.1 / 1.2 / 1.3 / 1.4 / 1.5+1.6 / 2.1+2.2+4.5 / 3.1–3.3+4.6 / 4.1–4.4+4.7+1.7 ✅

## Assignment Tips

- Sprints 3, 4, 7 need the strongest OpenCV skills; Sprint 7 has the highest risk and highest grade upside.
- Sprint 1's owner must be fast and decisive — everyone consumes their contracts from Day 2.
- Sprint 5's owner is also the integration lead — pick someone comfortable debugging across the whole chain.
- Story files in `_bmad-output/implementation-artifacts/` carry full acceptance criteria and dev notes for every story in your sprint.
