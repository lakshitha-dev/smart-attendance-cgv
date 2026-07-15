---
status: ready-for-dev
epic: 4
story: '4.3'
title: Watch the pipeline and read the results
frs: [FR-13]
uxdrs: [UX-DR6, UX-DR7, UX-DR8, UX-DR12]
owner: M1 + M3 (stage strip + results list)
sprint: Week 2, Days 6–7 · 🔒 gated
---

# Story 4.3: Watch the pipeline and read the results

## Story

As Nadeesha,
I want to watch each processing stage appear and then read every student's result,
So that I trust what SAMS did and see who was present at a glance.

## Acceptance Criteria

**Given** processing starts
**When** the engine emits each `StageArtifact`
**Then** the stage strip streams them in pipeline order under "What we did with your photo", current stage named in muted ink while running, completed stages collapsing into labelled expanders — the strip is the loading state (no indeterminate spinner as primary signal), images sourced solely from the engine's emission contract.

**Given** processing completes
**Then** "All finished — your results are below." with the summary line ("42 students checked. One needs a quick look from you."), and a custom container row list (not a raw dataframe): student name, Student Index (caption, tabular figures), right-aligned status chip — icon + text + colour, always all three; results already persisted by the engine, stated once ("Results saved.").

**Given** a row-count mismatch warning in `SheetResult.warnings`
**Then** a prominent flag banner sits above the results ("matched by row order — please double-check") — a flag, not a failure.

## Dev Notes

- **Streaming:** consume the engine's stage generator/callback as it yields — `st.image` per stage inside the fenced run; `st.expander` for completed stages; current-stage caption in muted ink `#7B818A` ("Reading your photo… (Deskewed)").
- **UX-DR8 status chips:** ✓ Present `#256E4C` / ✕ Absent `#A63D2A` / ? Ambiguous `#7A6212` — coloured text + glyph, NO filled backgrounds, icon + label ALWAYS together (greyscale-survivable). Status colours are used for statuses ONLY.
- **Rows are containers with real buttons, not `st.dataframe`** — Ambiguous rows must host resolve buttons (Story 4.4).
- **Overline** "WHAT WE DID WITH YOUR PHOTO" is the only uppercase in the system (DESIGN.md typography).
- **`st.image` consumes the RGB `StageArtifact.image` as-is** (AD-2) — no conversion in the page.
- **Stage captions may use the friendly forms** (e.g. greyscale: "Any pen colour works — the greyscale step evens it out.") from Voice & Tone.
- **Alt text per stage image:** "Stage N of 7 — <Label>" (UX-DR15).

## Dependencies

- **Requires:** 4.2 (fenced run), 1.2/1.4 (7-stage emission), 1.5 (persisted results).
- **Enables:** 4.4.

## Definition of Done

Phone test: stages stream in order, collapse to expanders; results list renders every Student Record with correct chips; row-count-mismatch banner verified with a doctored fixture; "Results saved." appears exactly once.
