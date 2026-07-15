# Reconciliation — CS402.3 Coursework brief vs DESIGN.md / EXPERIENCE.md

Date: 2026-07-10. Scope: UX / display / visualization requirements only.

## Dropped (brief requires it; spines miss it)

1. **CLI textual attendance output missing.** The brief's core demand for `sams.py` is to "identify who was present and who was absent, i.e. Andare was absent." The CLI Display Contract (EXPERIENCE.md) specifies only stage windows, saved stage images, and Local DB writes — it never says the CLI presents the per-student Present/Absent result to the person running it. A grader running the exact command sees pipeline images but no attendance answer unless they open the Web UI or the DB. The CLI needs a specified results output (console list or equivalent).

2. **Ambiguous status has no CLI story.** The Ambiguous state and its one-tap resolution exist only on the Web UI Process page. The graded CLI path is silent on what `sams.py` does when a signature is Ambiguous: what it displays, what lands in the DB, and what `infovis.py` shows for an unresolved record. The brief expects the program itself to decide present/absent; the spines must say how Ambiguous manifests in CLI output (e.g. printed as "? Ambiguous — resolve in Web UI" and charted as the distinct Ambiguous mark the Lookup graph already defines).

3. **Five-sheet testing vs single output folder.** The brief requires testing results/screenshots "for the given input images (all five signing sheets found in 'CGV Signing Sheets.zip')." The saved-copies contract names stage files in pipeline order (`05-deskewed.png`) "into an output folder under the project root" with no per-sheet scoping — processing sheet 2 overwrites sheet 1's images, destroying the report screenshots the same paragraph promises. Saved stages need Sheet-Identifier-scoped folders/filenames.

4. **Recognition requires collecting multiple signatures.** The brief: "You must collect signatures [plural] of the given student, compare, and report." The Investigate panel shows exactly one Reference Signature vs one probe signature. The spines never address where reference signatures come from, that more than one may exist, or how multiple references are displayed/aggregated into the score.

5. **Colour-pen input variation is invisible (minor).** The brief twice stresses that students sign "using different color pens." Neither spine acknowledges pen colour anywhere — not in the stage vocabulary (the original→greyscale step implicitly discards colour, unexplained), not in microcopy, not as a display consideration. Low risk, but the report's "discussion of steps" story is stronger if a stage label or caption acknowledges colour handling.

## Contradictions

- **No hard contradictions found.** Commands (`python sams.py 10.07.2019.png info.xml`, `python infovis.py 001`, `python investigate.py 001`) match the brief exactly; live in-progress stage display, greyscale/binarization vocabulary, local DB, per-student graph, and step-by-step screenshots are all explicitly covered.
- **Soft tension:** the brief frames the program's job as a binary "present or absent" determination; the spines introduce a third persisted status (Ambiguous) that only a human on the Web UI can clear. Defensible as honesty about confidence, but combined with Dropped #2 it means the graded artifact can end a run without the answer the brief asks for. Resolve by specifying the CLI/DB behavior for Ambiguous.

## Verdict

The spines land the brief's headline UX requirements — live step-by-step processing display, exact CLI command forms, the per-student attendance graph, report screenshot sourcing, and shared terminology — but the CLI half of the contract is under-specified: no CLI results output (1), no CLI Ambiguous behavior (2), and un-scoped stage-image saving that breaks the five-sheet testing evidence (3). Fix 1–3 before build; 4–5 are smaller spec additions. No spine statement outright contradicts the brief.
