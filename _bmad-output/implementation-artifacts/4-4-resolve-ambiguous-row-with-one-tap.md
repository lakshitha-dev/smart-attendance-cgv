---
status: ready-for-dev
epic: 4
story: '4.4'
title: Resolve an Ambiguous row with one tap
frs: [FR-13]
uxdrs: [UX-DR9, UX-DR12]
owner: M1 (Topic 1 — resolve flow)
sprint: Week 2, Day 8 · 🔒 gated
---

# Story 4.4: Resolve an Ambiguous row with one tap

## Story

As Nadeesha,
I want unclear signatures flagged with a one-tap fix and an Undo,
So that I settle uncertain rows in seconds while holding the paper sheet.

## Acceptance Criteria

**Given** a result row with status Ambiguous
**Then** it renders visually distinct (straw fill `#FDFBF2`, ochre border `#E3D9B4`, plain question "We couldn't read this signature clearly. Which is right?") with two neutral-outlined buttons "✓ Present" / "✕ Absent" (min-height 46px, neutral ink text).

**When** I tap one
**Then** `repository.resolve(sheet_id, student_index, status, by_operator=True)` updates the Attendance Record instantly — no confirm dialog — and the row flips with an inline "Saved as Present. Undo" (~5 s or until next interaction).

**When** I tap Undo
**Then** the record returns to Ambiguous.

**Given** all Ambiguous rows resolved
**Then** the page says "All done. Every student on this sheet is marked." — and these resolutions survive later re-processing unless explicitly overwritten (Story 4.2's warning).

## Dev Notes

- **AD-4 APIs:** `resolve(sheet_id, student_index, status, by_operator=True)`; undo = restore Ambiguous (clears the operator flag or re-resolves to AMBIGUOUS per repository design — keep `resolved_by_operator` semantics so 1.5's survival rule works).
- **Resolve buttons are NEUTRAL:** hairline outline `#E9E8E3`, label text in neutral ink `#33383F` — the ✓/✕ glyph + word carries meaning; button chrome takes NO status colour (DESIGN.md Ambiguous-row spec).
- **No confirm dialog** — resolution is the one instant action, and it carries Undo (Interaction Primitives). Undo visible ~5 s or until next interaction (build-time constant; put it in one place).
- **Careful with the 4.2 fence:** resolving a row causes a Streamlit rerun — it must NOT re-trigger processing. Row state re-reads from the DB (rows reflect saved state, UX-DR7).
- **Status change announced as on-page text** ("Saved as Present.") — not colour/motion only (UX-DR15).

## Dependencies

- **Requires:** 4.3 (row list), 1.5 (`resolve` API).
- **Enables:** complete UJ-1 corridor flow; 4.7 checks.

## Definition of Done

Tap → instant flip + Undo works both directions; DB verified after each transition; re-processing after a resolution triggers the 4.2 overwrite warning; all-resolved message appears.
