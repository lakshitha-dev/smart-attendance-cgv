---
status: ready-for-dev
epic: 4
story: '4.7'
title: Use SAMS comfortably on phone, desktop, and projector
frs: [FR-14, FR-15]
uxdrs: [UX-DR13, UX-DR14, UX-DR15]
nfrs: [SM-6, NFR-12]
owner: M8 (Topic 8), with M6 on parity check
sprint: Week 2, Day 9 · 🔒 gated
---

# Story 4.7: Use SAMS comfortably on phone, desktop, and projector

## Story

As Nadeesha (and the demo presenter),
I want every page to work single-handed on my phone, mouse-and-keyboard at my desk, and readable on a projector,
So that the same app serves the corridor, the office, and the viva.

## Acceptance Criteria

**Given** a phone viewport (<~768 px)
**Then** every page is a single column in task order, sidebar collapsed to hamburger, touch targets ≥ 44 px, no horizontal scrolling in any core flow.

**Given** a desktop viewport (≥~768 px)
**Then** the specified two-column layouts apply (Process: uploads + stage strip left, results right; Lookup: full-width graph, indices in two columns; Investigate: larger side-by-side + full-width scale), content centered at ~1100 px, every column pair degrading back to phone stacking order; hover tint is enhancement-only; critical info readable from 2–3 m (nothing below 14 px equivalent).

**Given** the accessibility floor
**Then** statuses are never colour-only anywhere (rows, summary counts, chart legends — greyscale-survivable), all inputs have visible labels, every action is keyboard-operable via real buttons in reading order, every stage image carries alt text ("Stage 5 of 7 — Deskewed sheet"), and status changes are announced as on-page text.

**Given** the same sheet processed via CLI and via Web UI
**Then** the Local DB holds identical Attendance Records — FR-15's cross-frontend parity consequence, verified at the data layer.

## Dev Notes

- **Desktop layouts (EXPERIENCE.md Responsive & Platform):** `st.columns` with 24px gutter; only column layouts that degrade gracefully to a stack. Process two-column, Lookup full-width graph + two-column indices list, Investigate grown side-by-side.
- **Parity test (do this as a script):** wipe/temp DB → process sheet N via CLI → dump attendance rows; wipe → process same sheet via Web (or call `process_sheet` the way the page does) → dump → diff. Identical rows = pass. Same for a Lookup figure and an Investigate verdict.
- **Greyscale check:** screenshot each page, desaturate, confirm statuses still readable (icon+label carry it).
- **Keyboard pass:** Tab/Enter through upload → Process → resolve → Undo → Lookup → Investigate on desktop; custom rows must use real `st.button`s (they do, per 4.3/4.4).
- **Hover:** row tint `#F3F2EE` desktop-only enhancement; never information-bearing.
- **Banned (UX-DR14):** carousels, auto-play, info-bearing toasts, confirm dialogs for reversible actions, multi-step wizards — audit the pages.

## Dependencies

- **Requires:** 4.1–4.6 complete.
- **Enables:** viva demo; SM-6; submission confidence.

## Definition of Done

Phone + desktop walkthrough of all three pages recorded (screenshots for the report); parity diff empty; greyscale + keyboard audits pass; no core-flow horizontal scroll at 360 px width.
