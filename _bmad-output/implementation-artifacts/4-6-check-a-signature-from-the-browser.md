---
status: ready-for-dev
epic: 4
story: '4.6'
title: Check a signature from the browser
frs: [FR-14]
uxdrs: [UX-DR11, UX-DR12, UX-DR15]
owner: M7 (Investigate page)
sprint: Week 2, Day 8 · 🔒 gated
---

# Story 4.6: Check a signature from the browser

## Story

As Nadeesha,
I want to compare a student's sheet signature against their reference side by side,
So that I can act on proxy-signer suspicions with visible evidence.

## Acceptance Criteria

**Given** the Investigate page
**When** I enter a Student Index (either form)
**Then** the Reference Signature and probe signature render side by side (stacked on narrow phones), clearly captioned, with alt text on both; below them the similarity score sits on a scale with the threshold marked (displayed 0–100), then the plain verdict sentence ("Match — this looks like their usual signature." / "Mismatch — this doesn't look like their usual signature. Worth checking in person.").

**Given** the engine's `VerificationResult`
**Then** the score and threshold outcome are identical to `investigate.py`'s (same engine call, no re-implementation)
**And** with multiple references, the probe shows against the best match with the rest in a collapsed expander.

**Given** no data (unknown index, no probe, or empty references)
**Then** the no-data pattern renders — never an error.

## Dev Notes

- **Thin page:** input → `verification.py` (same call as `investigate.py`) → render `VerificationResult`. Best-match selection already happened in the engine (AD-9) — the page only displays `result.best` + expander of `result.all_scores`.
- **Captions:** "Reference Signature" / "Signature from sheet"; alt text: "Reference Signature for 10009301", "Signature from sheet 2019-05-31" (UX-DR15).
- **Score scale:** engine's 0–1 score displayed normalized to 0–100 with the threshold marked on the scale (UX assumption, display-side only — the stored threshold stays 0–1).
- **Verdict sentences verbatim from EXPERIENCE.md** — no jargon, no "confidence below threshold".
- **Loading:** native spinner + "Comparing signatures…".
- **Images are evidence:** square corners inside a 10px frame (DESIGN.md Shapes) — don't decorate.

## Dependencies

- **Requires:** 4.1 (scaffold), 3.1 + 3.2 (references, scorer).
- **Enables:** UJ-3 on the phone; 4.7 parity check.

## Definition of Done

Same index gives identical score/verdict in CLI and browser; multi-reference expander works; no-data paths for unknown index / no probe / empty references all render the calm pattern; stacks correctly on phone width.
