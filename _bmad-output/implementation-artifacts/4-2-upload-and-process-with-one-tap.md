---
status: ready-for-dev
epic: 4
story: '4.2'
title: Upload a sheet and process it with one tap
frs: [FR-12]
uxdrs: [UX-DR3, UX-DR4, UX-DR5, UX-DR12]
owner: M8 (Topic 8), with M2 on upload/DB wiring
sprint: Week 2, Days 6–7 · 🔒 gated
---

# Story 4.2: Upload a sheet and process it with one tap

## Story

As Nadeesha,
I want to upload the sheet photo and Info File and tap Process once,
So that processing happens exactly when I say so — and never accidentally.

## Acceptance Criteria

**Given** the Process page
**When** I add files to the two labelled slots ("Signing Sheet" JPEG/PNG, "Info File" info.xml)
**Then** each accepted slot shows filename + a quiet "✓ Ready" in slate (never Present green), invalid files get slot-level plain-language errors from the UX error catalog (decode-level rejection only — a dim or skewed photo proceeds), and a date field appears only when the Info File lacks a session date (the Web UI never falls back to the filename).

**Given** both inputs ready
**When** I tap the Process button (themed primary, full column width, min-height 52px, disabled until ready)
**Then** `process_sheet()` runs exactly once per press, fenced in session state: scrolling, expanding a stage image, resolving a row, or any Streamlit rerun never re-triggers the pipeline or rewrites the DB.

**Given** the Sheet Identifier already has saved operator resolutions (`has_operator_resolutions`)
**When** I tap Process
**Then** nothing processes until I choose between Keep resolutions (emphasized safe default) and Overwrite everything (neutral-outlined) — modal-style centered on desktop.

**Given** a processing failure
**Then** a human-readable page-level message appears (never a stack trace), and my uploaded inputs are preserved for fix-and-retry.

## Dev Notes

- **One-shot fence (the hard part):** Streamlit reruns the script on every interaction. Fence with session-state keys (e.g. `run_id`/`processed` token set on button press, consumed once); DB writes happen inside `process_sheet()` (AD-12), so the fence only needs to stop repeat CALLS.
- **Error catalog (UX-DR12, verbatim):** bad image → "We couldn't read that file as a photo. Please add a JPEG or PNG of the Signing Sheet." · bad Info File → "This info file doesn't look right — we couldn't find the student list in it. Check it's the info.xml for this class."
- **Overwrite copy (UX-DR5):** "You've already fixed some answers for this sheet by hand." Buttons: **Keep resolutions** (primary/emphasized) / Overwrite everything (neutral outline).
- **AD-11:** Web date field appears only when Info File lacks `session/@date`; NEVER use the upload filename as the Sheet Identifier in the Web UI.
- **"✓ Ready" is slate `#44526A`, not green** — confirmations never borrow status colours (DESIGN.md rule).
- **AD-4:** `has_operator_resolutions(sheet_id)` is the pre-Process check — needs the Sheet Identifier resolved BEFORE processing (engine `info_file` helper on the uploaded XML).

## Dependencies

- **Requires:** 4.1; engine `process_sheet()` (1.5), Sheet Identifier resolver (1.1).
- **Enables:** 4.3, 4.4.

## Definition of Done

Phone-browser test: upload → Process runs once; rerun-storm test (scroll/expand/interact) triggers zero re-processing; overwrite warning fires only when resolutions exist; both error-catalog paths render.
