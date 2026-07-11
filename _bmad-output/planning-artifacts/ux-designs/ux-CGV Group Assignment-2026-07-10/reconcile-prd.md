---
title: SAMS — PRD ↔ UX Spine Reconciliation
project: CGV Group Assignment (CS402.3)
created: 2026-07-10
sources:
  - ../../prds/prd-CGV Group Assignment-2026-07-10/prd.md
  - ./DESIGN.md
  - ./EXPERIENCE.md
---

# Reconciliation: PRD vs DESIGN.md + EXPERIENCE.md

Scope: UX-relevant PRD content only. Engine internals (algorithms, DB schema, dataset protocol, test protocol, team decomposition) were deliberately excluded from the spines and are not reported as gaps.

## Dropped

1. **Sequencing gate + counter-metric (PRD §6.3, §1 note, SM-C2) — HIGH.** The PRD's hardest delivery rule — Web UI work starts *only after* SM-1/SM-2/SM-3 pass on all five sample sheets, with "ship engine + CLI only" as the fallback, and SM-C2 ("do not let Web UI polish consume engine-hardening time") — appears in neither spine. Both spines read as if the Web UI is an unconditional deliverable; a builder working from the spines alone has no signal that the entire Quiet Clerk surface is a gated, cuttable bet.

2. **Streamlit is an assumption, not a decision (PRD OQ-3, §9, `[ASSUMPTION: Streamlit]`) — HIGH.** The PRD holds the framework open pending a group vote (Flask is the named alternative). DESIGN.md hard-commits: "This is a Streamlit-native identity", tokens mapped to `config.toml [theme]` keys, "components are Streamlit's own widgets restyled at the edges, never rebuilt"; EXPERIENCE.md likewise states "UI system: Streamlit multipage app" as fact. The conditional status was dropped — if OQ-3 resolves to Flask, the design spine's token mapping and component strategy are invalid with no noted fallback.

3. **CLI error experience (FR-1 consequences) — MEDIUM.** The PRD requires, for the CLI: a clear error message, non-zero exit code, and *no raw stack trace* on a missing/unreadable image or an Info File failing Appendix A validation; plus reporting the parsed Student Record count and resolved Sheet Identifier on load. EXPERIENCE.md claims the CLI's display as UX-owned ("CLI Display Contract") but covers only stage display; the entire error catalog and voice/tone table are Web-only. The marker-facing error voice of `sams.py`/`infovis.py`/`investigate.py` landed nowhere.

4. **Sheet Identifier via CLI flag (PRD §3 Glossary) — LOW.** When the Info File lacks a date, the PRD says the operator supplies one via "CLI flag / Web UI field", with filename-stem as final fallback. The spines carry the Web UI date field and the filename fallback but omit the CLI flag path.

5. **Resolution survival on CLI re-processing (FR-6) — LOW.** The PRD's rule "operator resolutions of Ambiguous rows survive unless the operator confirms an overwrite" is surface-agnostic. EXPERIENCE.md specs the overwrite choice only as a Web UI modal ("Keep resolutions / Overwrite everything"); how the same guarantee manifests when the marker re-runs `sams.py` on the same Sheet Identifier is unspecified.

## Contradictions

1. **Dim-photo handling (PRD UJ-1 vs EXPERIENCE Flow 1 failure path) — LOW severity.** PRD UJ-1's edge case says a "badly skewed or dim photo" is *handled by the pipeline* (deskew/normalize; borderline cells fall into the Ambiguous band and get resolved). EXPERIENCE.md Flow 1's failure path routes a "dim or unreadable photo" to a slot-level input error ("she re-shoots and retries"). "Unreadable" matches FR-1; "dim" contradicts the PRD's stated behavior — dimness is a processing condition the pipeline is required to absorb, not an upload-validation failure (and slot-level validation could not detect it anyway).

*Internal-consistency note (not a PRD conflict):* DESIGN.md rules that status colours are "used only for status; never for decoration, buttons, or emphasis", yet specs the file-slot "✓ Ready" in `{colors.status-present}` and the resolve buttons outlined in Present/Absent colours. Worth tightening in DESIGN.md.

## Verdict

The spines land the PRD's Web UX faithfully and completely at the interaction level: FR-12–FR-14 (upload, one-shot semantics, streaming stage strip, Ambiguous resolution, both index forms, "no data" listings, parity language), the FR-16 single display contract, FR-11's live-display + saved-copies requirement, the glossary discipline, phone-usability NFRs, and SM-6's "the page is the instructions" all trace cleanly, with only additive assumptions (Undo timing, 0–100 score scale, non-blocking CLI windows) properly flagged. One soft contradiction (dim-photo routing). The real losses are qualitative and structural: **the spines silently promote the Web UI from a gated, cuttable bet to an unconditional commitment** — the §6.3 sequencing gate, the SM-C2 counter-metric, and the Streamlit-vs-Flask open question all failed to land — and the CLI's non-stage UX surface (error voice, date flag, overwrite behavior) fell between the two documents. Recommend adding a short "Delivery conditions" block to EXPERIENCE.md (gate, fallback, framework assumption) and extending the CLI Display Contract to cover CLI error output.
