---
status: done
epic: 4
story: '4.4'
title: Resolve an Ambiguous row with one tap
frs: [FR-13]
uxdrs: [UX-DR9, UX-DR12]
owner: M1 (Topic 1 — resolve flow)
sprint: Week 2, Day 8 · 🔒 gated
baseline_commit: 351ba3e
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

## Tasks / Subtasks

- [x] Task 1: process_logic resolve helpers — saved_rows (DB-backed row list, UX-DR7), resolve_row (AD-4 resolve, operator-flagged), undo_row (restore Ambiguous); UX-DR9 copy + colour constants
- [x] Task 2: Results renderer reads SAVED DB state so a resolution flips its row (was rendering the stale detected records)
- [x] Task 3: Ambiguous row — straw fill #FDFBF2 / ochre border #E3D9B4, the verbatim question, two NEUTRAL-outlined ✓ Present / ✕ Absent buttons; one tap resolves instantly (no confirm) and reruns
- [x] Task 4: Inline "Saved as X. Undo" on-page text (UX-DR15) after a resolution; Undo restores Ambiguous; notice cleared on next interaction / input change / fresh run
- [x] Task 5: "All done. Every student on this sheet is marked." when no Ambiguous rows remain
- [x] Task 6: Tests — resolve/undo DB round-trip (pure) + AppTest button-driven resolve→flip→undo, ambiguous-row rendering, all-marked message

## Dev Agent Record

### Completion Notes

- Rows now render from repository.get_attendance(sheet_id) (UX-DR7 "rows reflect
  saved DB state"), so tapping ✓/✕ flips the row on the rerun — verified by an
  AppTest that clicks the real button and asserts the DB status changed both ways.
- resolve() marks resolved_by_operator (AD-4), so 1.5's survival rule protects
  the resolution from re-processing and Story 4.2's overwrite gate fires on a
  later run — the corridor closes.
- Resolve is the one instant action (no confirm dialog, Interaction Primitives)
  and carries Undo; the "Saved as X." notice is on-page TEXT (UX-DR15), shown
  until the next interaction (single build-time behaviour, no colour/motion-only
  signal).
- Resolve buttons are neutral (default secondary outline); the ✓/✕ glyph + word
  carry meaning, button chrome takes no status colour (DESIGN.md).
- The 4.2 fence holds: resolving reruns the script but process_clicked is False,
  so nothing re-processes; the strip re-renders collapsed from disk.
- **Latent bug fixed in passing:** the committed 4.3 Process page referenced
  `AttendanceRepository()` in the process-click path but never imported it — a
  NameError that only fires on a real upload (headless AppTest can't upload, so
  it never surfaced). Now imported; pyflakes confirms no other undefined names.
- Full suite 238 passed (+4); live streamlit HTTP 200.

### File List

- webui/process_logic.py (saved_rows/resolve_row/undo_row + UX-DR9 constants)
- webui/pages/Process.py (DB-backed results, Ambiguous resolve rows, undo notice; AttendanceRepository import restored)
- tests/test_process_logic.py (resolve/undo DB round-trip)
- tests/test_webui_process.py (rewritten to a page_repo fixture; resolve/undo AppTests)
- _bmad-output/implementation-artifacts/4-4-resolve-ambiguous-row-with-one-tap.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-07-18: Story 4.4 implemented — DB-backed results list, one-tap Ambiguous
  resolve with straw/ochre treatment and neutral buttons, inline Saved/Undo,
  all-marked message. Fixed a latent missing-import in the 4.3 process path.
  238/238; HTTP 200.

### Review Findings (bmad code review 2026-07-18, Sprint-8 — solo /code-review + 3 layers)

- [x] [Review][Patch] HIGH: results rendered ALL DB rows for the sheet_id (= the session DATE), so a second sheet on the same date merged both classes' rows (inflated count, stale Ambiguous rows with live resolve buttons) — now iterate THIS run's `result.records` and pull each row's live DB status, scoping to the current roster [webui/pages/Process.py]
- [x] [Review][Patch] Rows sorted by 8-digit index, not roster/detected order — the same result.records iteration restores the physical-sheet order the operator reads down [webui/pages/Process.py]
- [x] [Review][Patch] Undo was single-slot + transient: resolving a second row erased the first's Undo, and Undo vanished after any non-resolving rerun — now EVERY operator-resolved row carries a persistent Undo (reads resolved_by_operator), so any resolution stays reversible while results are on screen [webui/pages/Process.py]
- [x] [Review][Patch] A failed resolve (repository.resolve returns False, zero-row match) was a silent dead tap — the row stayed Ambiguous and never showed the notice; now the return is checked and a "couldn't save that" warning surfaces [webui/pages/Process.py, webui/process_logic.py]
- [x] [Review][Patch] "All done. Every student on this sheet is marked." fired on a clean sheet that never had ambiguity — now gated on `no ambiguous AND any operator-resolved` (UX-DR9's "given all Ambiguous rows resolved") [webui/pages/Process.py]
- [x] [Review][Patch] `_render_results` had no guard for sheet_id None (would dump the entire DB via get_attendance) — explicit guard added [webui/pages/Process.py]
- [x] [Review][Patch] Summary (live DB) and banners (frozen run) could describe different snapshots — both now derive from the current roster, so counts and the mismatch banner agree [webui/pages/Process.py]
- [x] [Review][Patch] resolve/undo return values ignored (solo #1) — folded into the failed-resolve and failed-undo handling above [webui/pages/Process.py]
- [x] [Review][Patch] Dead HAIRLINE constant (defined/exported, never used) removed [webui/process_logic.py]
- [x] [Review][Patch] Repeated AttendanceRepository() construction per render — `_render_results` now builds one and threads it to the row renderers [webui/pages/Process.py]
- [x] [Review][Patch] Dateless Info XML re-parsed every rerun — memoized by (file_id, session_date) [webui/pages/Process.py]
- [x] [Review][Patch] present/absent resolve blocks duplicated — collapsed to a two-entry loop [webui/pages/Process.py]
- [x] [Review][Patch] New tests: cross-sheet scoping, every-resolved-row-keeps-Undo (multi-row), resolve→reprocess→overwrite-gate (DoD), clean-sheet-no-all-done [tests/test_webui_process.py]
- [x] [Review][Dismissed] "~5s auto-hide" Undo window (UX-DR9/Dev Notes) — a server-side 5s timer isn't achievable in pure Streamlit; the persistent-per-row Undo strictly improves reachability over a disappearing window, so no timer constant is needed
- [x] [Review][Dismissed] undo_resolution hard-codes AMBIGUOUS ("reset to Ambiguous", not "restore previous") — safe in 4.4 because resolve buttons appear only on Ambiguous rows; a true restore-previous would need storing the prior status (repository/1.5 scope)
- [x] [Review][Defer] Orphan attendance rows persist in the DB when a sheet is re-processed with a different roster on the same date (visible to infovis/lookup, not just this page) — a facet of the already-deferred "Sheet Identifier = bare date" collision item; engine-side persist_run cleanup belongs to a 1.5 correct-course [sams_core/repository.py]
- [x] [Review][Note] Fence + double-process paths independently verified SAFE by the Blind Hunter (st.button single-True semantics; _settle_after/_overwrite_run cannot double-fire) — no change needed

