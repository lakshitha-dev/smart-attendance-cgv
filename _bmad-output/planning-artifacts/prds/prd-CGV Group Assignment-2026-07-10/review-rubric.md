# PRD Quality Review — Student Attendance Management System (SAMS)

## Overall verdict

This PRD holds up well for its stakes: it has a real thesis (grade-anchored, one Core Engine behind two frontends), FRs with genuinely testable consequences, and unusually honest scope machinery (Non-Goals, tagged assumptions, open questions that are actually open). Two things are at risk: the committed higher-grade component (`investigate.py`) rests on a reference-signature capture pathway the PRD never defines, and ambiguous-cell handling is half-decided — asserted in UJ-1 and FR-13 while simultaneously listed as Open Question 5. Neither breaks the PRD, but both will surface as confusion the moment the 10-member group splits the work.

## Decision-readiness — adequate

The PRD makes real decisions and says so: `investigate.py` is "committed for this build" with the risk named in the same breath (§4.4 Notes: "the main lever for a higher mark but also the riskiest technically"); the Web UI framework is recommended, not smuggled in as settled (`[ASSUMPTION: Streamlit]`, OQ-6 offers Flask as a genuine alternative); SM-C1 names an honest trade-off (accuracy on the five samples vs. a general technique). The Open Questions are real questions — OQ-2 and OQ-4 in particular would change the build.

Two things keep it from strong. First, the largest scope decision in the document — adding a mobile Web UI (§4.6, FR-12–14, roughly a third of the FR surface) on top of a brief that specifies only three CLI programs — is asserted in the Vision (§1) without its cost being weighed. The brief grades technique, executability, and code quality; the PRD never asks whether Web UI effort trades against detection robustness for a 10-member group, it only guarantees the CLI still works. Second, OQ-5 asks how ambiguous cells should be handled ("flag for manual review, or force a decision?") while UJ-1 already answers it ("the row is flagged for her review rather than silently guessed") and FR-13 requires "flagged/ambiguous rows are visually distinguished." The decision is half-made in three places; a reader cannot tell whether flagging is committed behaviour or an open design choice.

### Findings
- **medium** Web UI scope decision lacks a stated trade-off (§1 Vision, §4.6) — the PRD's biggest scope addition beyond the brief is presented as settled ("SAMS exposes a **mobile-accessible web UI**") with no acknowledgment of what it costs against the graded criteria. *Fix:* add one honest paragraph (or a `[NOTE FOR PM]`) naming the bet: Web UI effort buys SM-6 and demo polish, at the cost of engine-hardening time; state the fallback if the group runs short (CLI-only still satisfies the brief).
- **medium** Ambiguous-cell handling both decided and open (UJ-1, FR-13 vs. OQ-5) — UJ-1 says ambiguous rows are "flagged for her review rather than silently guessed" and FR-13 requires flagged rows "visually distinguished," yet OQ-5 asks whether to "flag for manual review, or force a decision." *Fix:* either commit to flagging (make it an FR consequence with a defined ambiguity criterion and delete OQ-5) or strip the flagging behaviour from UJ-1/FR-13 and leave OQ-5 genuinely open.

## Substance over theater — strong

Nothing here is furniture. The two personas (§2.3 intro) each earn their place: Nadeesha's phone-photo context directly produces the mobile Web UI requirement and its NFRs (§4.6: "single-column layout, large touch targets"), and the marker persona produces FR-15's parity guarantee and UJ-4's exact brief commands. The NFRs are conspicuously product-specific — "moderate skew/perspective, uneven lighting, desk background, punch holes, and handwritten margin notes" (§4.1 Feature-specific NFRs) could only have been written by someone who looked at the actual sample sheets. The Vision (§1) names the pipeline stages and the three concrete programs; it could not be swapped into another PRD. SM-C1 is an earned counter-metric ("Do not overfit detection to the five sample sheets... hard-coded pixel coordinates"), not a template artifact. No findings.

## Strategic coherence — strong

The thesis is explicit and everything hangs off it: maximize the graded criteria via one clean OOP Core Engine, with `investigate.py` committed as the deliberate higher-grade lever (§4.4 Notes) and §4.7 existing precisely to serve "the 'coding styles, OOP concepts' grading criterion." Success Metrics are anchored to the assessment criteria rather than generic activity metrics (§7 header: "Anchored to the coursework assessment criteria"), each SM names the FRs it validates, and a counter-metric exists. MVP scope (§6) is coherent problem-solving scope with a clean out-of-scope list.

### Findings
- **low** Grade-weight claim drifts (§6.1 vs. §0/§7) — §6.1 says "code quality/OOP is 60% of the grade" while §0 and §7 attribute the 60% to the prototype as a whole ("Prototype 60%"). A team taking §6.1 literally could over-invest in style at the expense of detection accuracy. *Fix:* correct §6.1 to "the prototype is 60% of the grade, and code quality/OOP is a heavily weighted criterion within it."

## Done-ness clarity — adequate

Most FRs would survive an unforgiving engineer. FR-1, FR-3, FR-4, FR-6, FR-11, FR-13, and FR-15 have consequences that are directly checkable ("exits with a clear error message and non-zero exit code," "The Metadata Row / lecturer signature is not counted as a student row," "Processing the same sheet via CLI and via Web UI yields identical Attendance Records"). SM-1 gives detection a hard target ("100% on the known sample set, or every error explainable").

The soft spots cluster exactly where the grade risk is highest. FR-9's only consequence is "Reference Signatures can be captured/stored and retrieved by Student Index" — there is no FR, CLI flag, or Web UI flow anywhere in the document by which a reference signature *enters* the system. For the feature the PRD itself calls the main lever for a higher mark, an engineer cannot start it. FR-8 leans on "a suitable graph" and "meaningfully communicates attendance" — flagged by an assumption and OQ-3, but still adjectives where a decision should be. And "genuinely ambiguous" cells (UJ-1) have no criterion — an engineer cannot implement flagging without knowing what triggers it.

### Findings
- **high** Reference-signature ingestion is undefined (FR-9, §4.4) — no mechanism exists in any FR for getting a Reference Signature into the system (file drop? CLI command? Web UI upload? cropped from processed sheets?). OQ-2 covers *where the data comes from*, but even once answered, no requirement covers *how it is loaded*. This blocks the committed higher-grade component. *Fix:* add a consequence or sub-FR to FR-9 specifying the ingestion path (e.g. "references are image files placed in `references/<index>/`, registered on first `investigate.py` run"), even provisionally under an `[ASSUMPTION]`.
- **medium** FR-8 done-state is adjectival — "a suitable graph," "meaningfully communicates attendance" gives an engineer no default to build. OQ-3 is legitimately open, but the FR needs a committed default pending the answer. *Fix:* commit a default chart (e.g. per-sheet present/absent bar with attendance-rate annotation) as the build target, with OQ-3 as a possible override.
- **medium** No ambiguity criterion (FR-4, UJ-1, FR-13) — "genuinely ambiguous" and "flagged/ambiguous rows" are used as if defined, but nothing states what makes a cell ambiguous (ink-density band? confidence range?). *Fix:* define ambiguity operationally in FR-4 (even as a tunable band, e.g. "ink coverage between the Present and Absent thresholds"), or explicitly defer with an `[ASSUMPTION]` tag tied to OQ-5.
- **low** FR-10 "similarity indication" has no shape — score, percentage, or verbal band is unspecified, so "identical in content" parity in FR-14 can't be verified against it. *Fix:* one line: the comparison yields a numeric similarity score plus a thresholded match/mismatch verdict.

## Scope honesty — strong

This is the PRD's best dimension. §5 does real work (native app, cloud, auth, live camera, OCR — each a plausible silent assumption, each explicitly killed, two with `[NON-GOAL]` tags). §9 cleanly separates confirmed decisions from live assumptions, and every live assumption points at its FR. The open-items density (6 OQs, 5 indexed assumptions) is right for coursework stakes, and OQ-2 is admirably blunt: "This blocks FR-9/FR-10." The only softness: having named that a committed MVP feature is blocked, the PRD proposes no fallback.

### Findings
- **low** No fallback for the blocked committed feature (§4.4 Notes, OQ-2) — the PRD commits `investigate.py`, names it riskiest, and names its blocker, but never says what happens if the reference dataset doesn't materialize (de-scope? crop from sample sheets as default?). *Fix:* one sentence in §4.4 Notes naming the default path (e.g. "if no dataset is agreed by [date], references are cropped from the sample sheets").

## Downstream usability — strong

The Glossary (§3) is genuinely load-bearing — features open with "Uses Glossary terms exactly," and the terms are used with discipline across FRs, UJs, and SMs. FR-1..15, UJ-1..4, SM-1..6 + SM-C1 are contiguous and unique; every UJ names its FRs and every SM names what it validates, and all cited IDs resolve. Sections stand alone well.

One term slipped through: "Sheet identifier" is capitalized and load-bearing — it is a field of Attendance Record (§3), the FR-6 idempotency key (`[ASSUMPTION: idempotency key]`), and hinted at in the Metadata Row entry ("the Date is a useful source") — but it has no Glossary entry and no defined derivation. Since re-run dedup keys on it, two engineers deriving it differently (date vs. filename) produce incompatible databases.

### Findings
- **medium** "Sheet identifier" undefined but used as the DB idempotency key (§3 Attendance Record, FR-6, §3 Metadata Row) — its derivation (sheet date? source filename? both?) is nowhere specified. *Fix:* add a Glossary entry defining it and its derivation rule (e.g. "the Date parsed from the Metadata Row, falling back to the image filename").

## Shape fit — strong

The shape matches the product: a hybrid capability spec (features organized around the three brief-specified programs, §4.1–4.5) with UJs added exactly where they carry weight (a non-technical operator on a phone, and the marker). UJ-4 — the marker running the brief's exact commands — is the smartest journey in the document, since that persona actually assigns the grade. Rigor is calibrated to coursework stakes: no invented compliance sections, no persona sprawl (two personas, both used), NFRs only where product-specific. For a chain-top PRD feeding architecture and stories for a 10-person split, the Glossary discipline and FR/consequence structure are the right investments. No findings.

## Mechanical notes

- **Assumptions Index roundtrip failure:** the §9 entry "Ground truth (who actually signed each of the five sample sheets) is known/derivable" has no inline `[ASSUMPTION]` tag anywhere in the body — it exists only in the index. All other index entries roundtrip correctly.
- **Glossary case drift:** §3's Student Record definition says "supplied in the info file" (lowercase) where the defined term is "Info File." Single occurrence.
- **SM-2 validates-list gap:** SM-2's text requires all three programs including `investigate.py` to run, but its validates list (FR-1, FR-7, FR-8, FR-15) omits FR-10. SM-4 covers verification correctness, but SM-2's *executability* claim for `investigate.py` is untraced.
- **Pipeline stage-list drift:** FR-2 defines four stages including noise reduction and deskew/perspective correction, but the display lists in FR-11 and FR-13 ("original, greyscale, binarized, detected grid, per-cell") omit both. Harmless for detection, but FR-11's consequence says "each named stage" — ambiguous whether deskew must be displayed.
- **UJ protagonists:** all four UJs have named protagonists (Nadeesha ×3, Dr. Ranaweera) carrying context inline. Clean.
- **Required sections:** all present for the agreed stakes; the report deliverable's exclusion is stated in §0 and re-anchored in §5, so the boundary won't be missed.
