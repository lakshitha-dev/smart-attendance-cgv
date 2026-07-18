---
status: review
epic: 4
story: '4.2'
title: Upload a sheet and process it with one tap
frs: [FR-12]
uxdrs: [UX-DR3, UX-DR4, UX-DR5, UX-DR12]
owner: M8 (Topic 8), with M2 on upload/DB wiring
sprint: Week 2, Days 6–7 · 🔒 gated
baseline_commit: 7521ec7
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

## Tasks / Subtasks

- [x] Task 1: Engine — `parse_info_file_bytes` (info_file.py refactored to share `_build_info_file`) so the Web UI validates the uploaded XML with the same schema/errors as the CLI (AD-12; no path needed)
- [x] Task 2: `webui/process_logic.py` — Streamlit-free orchestration: parse_info (AD-11 date resolution, never filename), run_process (overwrite gate via has_operator_resolutions, engine call, UX-DR12 error-catalog mapping)
- [x] Task 3: Process page wiring — two slots + slate Ready, AD-11 date field only when the Info File lacks a date, one-shot fence via st.button + session_state, UX-DR5 overwrite gate (Keep resolutions / Overwrite everything), error surface preserving inputs
- [x] Task 4: Pure tests (test_process_logic.py) — parse/date/overwrite/error mapping + one real end-to-end engine run
- [x] Task 5: AppTest tests (test_webui_process.py) — empty state, no-side-effect-on-load, rerun-storm renders stored outcome with zero re-processing, overwrite gate, error surfacing

## Dev Agent Record

### Implementation Plan

Same thin-adapter split the Lookup/Investigate pages use: a Streamlit-free
`process_logic.py` owns sequencing + copy, the page owns widgets + the rerun
fence. The one hard part (AC2) is the fence — solved with Streamlit's own
button semantics: `st.button` returns True only on the press rerun, so the
engine call sits in `if process_clicked:` and the OUTCOME is stashed in
session_state for all subsequent reruns to re-render without re-calling.

### Completion Notes

- One-shot fence proven by AppTest: injecting a stored outcome and re-running
  (the scroll/expand rerun storm) calls the engine ZERO times; a plain load
  also never calls it.
- AD-11 honoured: `parse_info` resolves the Sheet Identifier from the Info
  File's date, else from an operator-entered date — `resolve_sheet_identifier`
  is called with `date_flag=` only, NEVER `image_path=`, so the upload filename
  can never become the Sheet Identifier in the Web UI.
- Overwrite gate (UX-DR5): run_process returns needs_overwrite_choice and does
  not process when has_operator_resolutions is true and no decision was made;
  the page shows Keep resolutions (primary) / Overwrite everything (outline).
- Error catalog (UX-DR12) verbatim for bad image / bad info file / missing
  date; decode-level only (a dim/skewed photo proceeds); inputs stay in slots.
- Engine addition: `parse_info_file_bytes` (info_file.py refactored to a shared
  `_build_info_file`); image bytes were already supported by process_sheet.
- Scope honoured: the rich stage strip (UX-DR6) and results row list (UX-DR7)
  are Story 4.3 — 4.2 shows a spinner + a saved-count confirmation.
- Full suite 223 passed (14 new); live streamlit HTTP 200 smoke.

### File List

- sams_core/info_file.py (parse_info_file_bytes + _build_info_file refactor)
- webui/process_logic.py (new)
- webui/pages/Process.py (wired the run; was the 4.1 empty-state shell)
- tests/test_process_logic.py (new)
- tests/test_webui_process.py (new)
- _bmad-output/implementation-artifacts/4-2-upload-and-process-with-one-tap.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-07-18: Story 4.2 implemented — engine parse_info_file_bytes, process_logic
  orchestration, one-tap fenced Process run with AD-11 date field, UX-DR5
  overwrite gate and UX-DR12 error catalog. 223/223 green; HTTP 200 smoke.
