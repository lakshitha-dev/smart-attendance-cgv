---
status: done
epic: 4
story: '4.3'
title: Watch the pipeline and read the results
frs: [FR-13]
uxdrs: [UX-DR6, UX-DR7, UX-DR8, UX-DR12]
owner: M1 + M3 (stage strip + results list)
sprint: Week 2, Days 6–7 · 🔒 gated
baseline_commit: 5575589
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

## Tasks / Subtasks

- [x] Task 1: Streaming stage strip — st.status ("the strip IS the loading state", no indeterminate spinner) fed by the engine's on_stage callback, each StageArtifact rendered via st.image in pipeline order, current stage named in the status label; the "WHAT WE DID WITH YOUR PHOTO" overline (the one uppercase); "All finished — your results are below." on completion
- [x] Task 2: Strip re-render on reruns — stage descriptors stashed in session_state, collapsed labelled expanders re-rendered from the engine's saved PNGs on disk (no reprocessing, no big ndarrays in session_state)
- [x] Task 3: Results row list — process_logic.results_summary (UX-DR7 line with Ambiguous call-to-action), STATUS_CHIP map (UX-DR8 icon+label+colour), container rows (name / index caption / right-aligned chip), "Results saved." exactly once
- [x] Task 4: Row-count-mismatch flag banner above results (UX-DR12: a flag, not a failure)
- [x] Task 5: Tests — pure results_summary (singular/plural/ambiguous) + STATUS_CHIP coverage; AppTest for the results list (chips, names, indices, summary, saved-once) and the mismatch banner

## Dev Agent Record

### Completion Notes

- Stage streaming uses st.status (auto-collapses on completion) so the strip
  itself is the loading indicator (UX-DR6) — no separate spinner. Images come
  solely from the engine's on_stage emission (AD-2 RGB, st.image as-is).
- The engine already saves each stage to output/<sheet_id>/NN-slug.png, so
  reruns re-render the strip as collapsed expanders straight from disk — the
  fence holds (zero reprocessing), and session_state stays light (descriptors
  only, never 7 full-res arrays).
- UX-DR8 chips: icon + label ALWAYS together (greyscale-survivable), colour via
  the app.py CSS classes, no filled backgrounds; a test pins that every status
  has an icon/label/class and the label matches the canonical status.
- results_summary handles 1 vs N and the Ambiguous "needs a quick look"
  call-to-action; "Results saved." is emitted once (engine already persisted).
- Row-count mismatch surfaces as a warning banner above the list, verbatim from
  SheetResult.warnings (the engine's UX-catalog wording).
- Full suite 231 passed (+8); live streamlit HTTP 200.
- Scope: Ambiguous rows still render as plain rows here — the resolve buttons
  (UX-DR9) are Story 4.4; the chip container is built to host them.

### File List

- webui/process_logic.py (STATUS_CHIP, results_summary, mismatch_warnings; on_stage already forwarded)
- webui/pages/Process.py (streaming strip, collapsed re-render, results row list)
- tests/test_process_logic.py (results_summary + STATUS_CHIP tests)
- tests/test_webui_process.py (results-list + mismatch-banner AppTests)
- _bmad-output/implementation-artifacts/4-3-watch-pipeline-and-read-results.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-07-18: Story 4.3 implemented — streaming st.status stage strip with
  disk-backed collapsed re-render, UX-DR7 results row list with UX-DR8 chips,
  summary line, mismatch flag banner, "Results saved." once. 231/231; HTTP 200.

### Review Findings (code review 2026-07-18, Sprint-8)

- [x] [Review][Patch] Overwrite gate flashed a red "Couldn't finish" strip before the dialog (empty _stream_run returning result=None) — the overwrite check now runs BEFORE any streaming (process_logic.needs_overwrite); a gated sheet never opens a status strip [webui/pages/Process.py, webui/process_logic.py]
- [x] [Review][Patch] The overwrite re-process showed NO strip / a stale other-sheet's strip (process_stages set only on the direct path) — the chosen run now streams on the main page via _stream_run too, setting its own descriptors [webui/pages/Process.py]
- [x] [Review][Patch] Staleness reset never cleared process_stages (a prior sheet's strip could render under new results) — it now pops process_stages and _overwrite_run too [webui/pages/Process.py]
- [x] [Review][Patch] Markdown injection through the student name (`**{name}**` rendered live links / image beacons / broke bold) — rows are now a single HTML block with html.escape on name AND index (markdown/markup can neither format nor inject) [webui/pages/Process.py]
- [x] [Review][Patch] Empty records showed a cheerful "0 students checked / Results saved." — now a calm "couldn't find any students" info message, no false save [webui/pages/Process.py]
- [x] [Review][Patch] Chip colour depended on app.py CSS absent under standalone/AppTest render — the exact UX-DR8 hex is now carried in STATUS_CHIP and rendered INLINE (coloured everywhere, and testable) [webui/process_logic.py, webui/pages/Process.py]
- [x] [Review][Patch] "Stage N of 7" was a hardcoded magic number — derived from the engine's new public pipeline.STAGE_COUNT (AD-3) [sams_core/pipeline.py, webui/process_logic.py]
- [x] [Review][Patch] Completion line "All finished — your results are below." rendered twice (status label + subheader) — the status label is now a neutral "All finished"; the canonical line lives once in the results block [webui/pages/Process.py]
- [x] [Review][Patch] mismatch_warnings mislabelled/passed through all warnings — renamed result_banners (surfaces the row-count-mismatch AND preserved-resolutions notices as flags, honestly) [webui/process_logic.py]
- [x] [Review][Patch] _render_saved_strip showed silent empty expanders when PNGs were gone — now a "no longer on disk" caption [webui/pages/Process.py]
- [x] [Review][Patch] Current-stage caption not in muted ink #7B818A — rendered via a muted-ink placeholder (MUTED_INK) updated per stage [webui/pages/Process.py]
- [x] [Review][Patch] Overline was an h6 heading, not the muted-ink tracked overline — rendered as the DESIGN.md overline component (muted ink, 0.06em tracking, uppercase) [webui/pages/Process.py]
- [x] [Review][Patch] Student Index lacked tabular figures (UX-DR7) — inline font-variant-numeric: tabular-nums on the index span [webui/pages/Process.py]
- [x] [Review][Patch] Tests masked the empty-records defect and never checked chip colour — added name-injection escaping, empty-records-info, needs_overwrite, and exact-hex chip tests [tests/]
- [x] [Review][Dismissed] "Alt text per stage image" (UX-DR15) — st.image exposes no HTML alt attribute; the visible caption is the textual description (platform limitation, same as the Investigate page)
- [x] [Review][Dismissed] Per-stage expanders DURING the live run — streaming shows images live (watch each appear), then the settle-rerun renders the completed stages as collapsed expanders; "completed → expanders" holds on the settled view

