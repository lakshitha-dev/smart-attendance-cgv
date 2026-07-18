---
status: review
epic: 4
story: '4.7'
title: Use SAMS comfortably on phone, desktop, and projector
frs: [FR-14, FR-15]
uxdrs: [UX-DR13, UX-DR14, UX-DR15]
nfrs: [SM-6, NFR-12]
owner: M8 (Topic 8), with M6 on parity check
sprint: Week 2, Day 9 · 🔒 gated
baseline_commit: 807d137
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

## Tasks / Subtasks

- [x] Task 1: Cross-frontend parity (FR-15/SM-6) — automated test proving the CLI path (process_sheet with a path) and the Web path (process_logic.run_process with bytes) persist BYTE-IDENTICAL attendance rows for the same sheet, and that Web Lookup reads back what the CLI wrote (both index forms)
- [x] Task 2: Accessibility-floor guards (UX-DR15) — status chips always icon+label (greyscale-survivable), every input has a visible label, actions are real st.buttons (no HTML onclick), stage images caption "Stage N of 7 — Label"
- [x] Task 3: Banned-primitives audit (UX-DR14) — no st.balloons/snow/toast/camera_input; resolve/undo are direct buttons (no confirm dialog for reversible actions)
- [ ] Task 4: [Manual/browser] phone (360px) + desktop walkthrough screenshots for the report; greyscale desaturation check; keyboard Tab/Enter pass — REQUIRES a real browser/device, cannot be done headlessly (see hand-off below)

## Dev Agent Record

### Completion Notes

Automated-verified (this pass):
- **Parity (FR-15/SM-6):** tests/test_parity.py processes sheet 1 via the CLI
  path and the Web path into two temp DBs and asserts identical (index, status,
  resolved) rows — 6/6 match; both frontends call the one engine entry point
  (AD-12), so parity is structural and now pinned. Lookup read-back parity for
  both index forms also covered.
- **Accessibility floor (UX-DR15):** icon+label chips (greyscale-survivable),
  visible labels on every input, real st.buttons in reading order, stage-image
  captions carry "Stage N of 7 — Label". tests/test_webui_accessibility.py.
- **Banned primitives (UX-DR14):** guarded — no balloons/snow/toast/camera;
  resolve/undo have no confirm dialog.
- Full suite 250 passed; live streamlit HTTP 200.

Honest hand-off — NOT verified here (needs a real browser/device, which the
headless harness structurally cannot drive):
- Phone 360px single-column / no-horizontal-scroll walkthrough + screenshots.
- Desktop two-column visual confirmation and 2–3 m projector readability.
- Greyscale desaturation screenshots; keyboard Tab/Enter pass.
- **Known Streamlit constraint for that reviewer:** st.columns do NOT auto-stack
  on narrow viewports. The pages are deliberately single-column flows (phone-safe,
  projector-readable, centered at 1100px); Investigate's ref-vs-probe st.columns(2)
  stays side-by-side (shrinking) on phone rather than stacking. Forcing a
  non-stacking two-column Process layout would REGRESS the phone
  no-horizontal-scroll AC, so single-column was chosen deliberately. The browser
  reviewer should confirm this trade-off is acceptable for the demo, or decide a
  custom-CSS media-query layout is warranted.
- **Alt text:** st.image exposes no HTML alt attribute (Streamlit limit); the
  required "Stage N of 7 — Label" text is carried as the image caption (visible +
  screen-reader-available). If true alt is required, it needs a custom component.

### File List

- tests/test_parity.py (new — CLI/Web data-layer parity)
- tests/test_webui_accessibility.py (new — UX-DR14/DR15 guards)
- _bmad-output/implementation-artifacts/4-7-responsive-accessible-on-all-surfaces.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-07-18: Story 4.7 — automated parity + accessibility/banned-primitive
  guards (250/250). Visual/responsive/keyboard audits handed off for a browser
  pass (documented, not faked); single-column layout rationale recorded.
