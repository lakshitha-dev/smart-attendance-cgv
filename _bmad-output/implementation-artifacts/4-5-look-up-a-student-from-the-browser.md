---
status: done
epic: 4
story: '4.5'
title: Look up a student from the browser
frs: [FR-14]
uxdrs: [UX-DR10, UX-DR12]
owner: M6 (Lookup page)
sprint: Week 2, Day 8 · 🔒 gated
baseline_commit: 5cfb9692a1659e308dc2f10b2d13caf42e9c048d
---

# Story 4.5: Look up a student from the browser

## Story

As Nadeesha,
I want to type a student's number and see their attendance graph,
So that I can answer a lecturer's question from wherever I am.

## Acceptance Criteria

**Given** the Lookup page's single labelled "Student number" input
**When** I enter either index form (`10009301` or `002`)
**Then** the page renders the same engine Figure `infovis.py` shows (data-layer parity via `st.pyplot`) — per-Session timeline, Ambiguous mid-band, attendance rate annotated.

**Given** an unknown number
**Then** the "no data" message lists the valid indices — never an error tone; loading shows the native spinner with "Looking that up…".

## Dev Notes

- **Thin page:** input → engine query (same resolver as 2.1) → `visualization.py` Figure → `st.pyplot`. ZERO chart logic in the page — parity is the whole point (FR-14).
- **Input label visible** (not placeholder-only): "Student number" (UX-DR15).
- **No-data copy (UX-DR12):** "We don't have any attendance saved for that number. Students we do know: 001 (10000409), 002 (10009301)…" — from `repository.list_students()`, calm tone, never an error state.
- **Empty state:** just the prompt sentence + input, nothing else.
- **Engine faults:** "Something went wrong reading the saved records." — the only other error surface (State Patterns).

## Dependencies

- **Requires:** 4.1 (page scaffold), 2.1 + 2.2 (query + Figure).
- **Enables:** UJ-2 on the phone; 4.7 parity check.

## Definition of Done

Both index forms render the identical figure the CLI shows (compare saved PNGs); unknown-index and empty states match UX copy; works on phone width.

## Scope Note

Story 4.1 (page scaffold) is still `ready-for-dev` — no `webui/` app, no `requirements-web.txt`, no theme config exist yet. Per explicit user direction, this story builds **only** the minimal scaffold this Lookup page needs (`webui/app.py` landing stub + `webui/pages/Lookup.py`), not 4.1's full scope (three-page nav shell, `.streamlit/config.toml` Quiet Clerk theme, Process/Investigate empty-state stubs). Those remain 4.1's responsibility when it is implemented.

## Tasks/Subtasks

- [x] Add `requirements-web.txt` pinning `streamlit==1.59.1` (Dev Notes) and install it
- [x] `webui/lookup_logic.py` — pure, Streamlit-free lookup logic (testable without a Streamlit runtime)
  - [x] `lookup(alias, repository)` reuses Story 2.1's `repository.query_attendance` (the same resolver) — zero index-form parsing here
  - [x] Unknown index / no records: no-data message listing valid indices verbatim per UX-DR12 ("We don't have any attendance saved for that number. Students we do know: …")
  - [x] Empty-DB case: calm no-students message, never an error tone
- [x] Minimal `webui/app.py` + `webui/pages/Lookup.py` (thin adapter, AD-1/AD-8)
  - [x] Labelled "Student number" text input (UX-DR15: visible label, not placeholder-only)
  - [x] Empty state: prompt sentence + input, nothing else
  - [x] Loading: native spinner, "Looking that up…"
  - [x] Success: `st.pyplot` renders the exact `visualization.render_attendance_timeline` Figure — zero chart logic in the page
  - [x] Engine fault (`SamsError`): "Something went wrong reading the saved records."
  - [x] sys.path bootstrap so `sams_core`/`webui` import correctly under `streamlit run` (page scripts execute with the script's own directory on `sys.path`, not the project root)
- [x] Tests
  - [x] Unit: `lookup("002", repo) == lookup("10009301", repo)` for the same student (both index forms)
  - [x] Unit: unknown index → message lists valid indices, never raises
  - [x] Unit: empty DB → calm no-students message
  - [x] Parity: `webui` Lookup figure PNG bytes == `infovis.py`/`visualization.py` CLI figure PNG bytes for both index forms (DoD: "compare saved PNGs")
- [x] Manual browser verification: run the Streamlit dev server, exercise known index / unknown index / empty state, confirm phone-width layout
- [x] Run full regression suite; confirm no existing tests broke

## Dev Agent Record

### Implementation Plan

- `webui/lookup_logic.py` is deliberately Streamlit-free: a `lookup(alias, repository) -> LookupResult` pure function so the page's branching/copy logic is unit-testable without a Streamlit runtime, mirroring how `cli_display.py` separates rendering from `infovis.py`'s thin `main()`.
- `webui/pages/Lookup.py` only wires widgets to `lookup_logic.lookup()` and `sams_core.visualization.render_attendance_timeline` — no chart or copy logic lives in the page itself (AD-1/AD-8, and the story's explicit "ZERO chart logic in the page" instruction).
- Both `webui/app.py` and `webui/pages/Lookup.py` insert the project root onto `sys.path` before importing `sams_core`/`webui`, since Streamlit's multipage runner does not put the project root on `sys.path` by default — a known gotcha for this repo layout (`sams_core/` and `webui/` are siblings at the root, not one nested inside the other).
- Data-layer parity (FR-14) falls out structurally from calling Story 2.1's `query_attendance` and Story 2.2's `render_attendance_timeline` directly — no new engine code was needed for this story.

### Completion Notes

- The Lookup page is genuinely thin: `webui/pages/Lookup.py` contains no index-parsing, no chart logic, and no no-data copy assembly — it only wires the text input to `lookup_logic.lookup()` and pipes the result to `st.pyplot`/`st.write`. `webui/lookup_logic.py` (Streamlit-free) owns the copy/branching so it is unit-testable without a Streamlit runtime.
- Data-layer parity (FR-14) is structural, not incidental: both the CLI (`infovis.py`) and the Lookup page call the exact same `AttendanceRepository.query_attendance` (Story 2.1's resolver) and `sams_core.visualization.render_attendance_timeline` (Story 2.2). Verified two ways: (1) a unit test asserting byte-identical PNG output for CLI vs. Lookup figures across both index forms, and (2) a live manual run — typing `10000409` then `001` for the same student in the running Streamlit app produced the identical cached image hash (`d7c3da92963d992bbc5bbdb9cdb9897a.png`), and the rendered chart showed the correct name and index.
- Manual browser verification (dev server via `.claude/launch.json`, `streamlit run webui/app.py`) against the real seeded `sams.db`: empty state shows only the prompt sentence + input; known index (both forms) renders the timeline figure; unknown index (`999`) shows the verbatim UX-DR12 no-data copy listing all 6 known students, never an error tone; phone-width (375px) resize confirmed the title/label/input render correctly under Streamlit's native responsive layout (no custom CSS was added, so this exercises the platform default, not new code).
- Followed the user's explicit scope decision to build only what 4.5 needs (`webui/app.py` landing stub + `webui/pages/Lookup.py` + `lookup_logic.py` + `requirements-web.txt`), not Story 4.1's full three-page shell/theme — recorded in the Scope Note above so 4.1 isn't mistaken for already done.
- Full regression suite: 133 passed, 0 failed (129 prior + 4 new in `tests/test_webui_lookup.py`).

## File List

- `webui/__init__.py` (new)
- `webui/app.py` (new — minimal landing stub)
- `webui/lookup_logic.py` (new — pure lookup/no-data logic)
- `webui/pages/Lookup.py` (new — thin Streamlit page)
- `requirements-web.txt` (new — pins `streamlit==1.59.1` on top of `requirements.txt`)
- `.claude/launch.json` (new — dev-server config for `streamlit run webui/app.py`)
- `tests/test_webui_lookup.py` (new — `lookup()` unit tests + CLI/Web PNG-parity test)

## Change Log

- 2026-07-16: Implemented Story 4.5 — minimal `webui/` scaffold (`app.py`, `pages/Lookup.py`, `lookup_logic.py`), reusing Story 2.1's `query_attendance` resolver and Story 2.2's `render_attendance_timeline` for FR-14 data-layer parity with the CLI. Verified both index forms and the unknown-index no-data path via unit tests and a live manual run against the real seeded DB. Story 4.1 (full page shell/theme) intentionally left out of scope per explicit user direction — see Scope Note.

### Review Findings (code review 2026-07-16, Sprint-6 merge)

- [x] [Review][Patch] Matplotlib backend never forced server-side: GUI backend auto-selected inside Streamlit's worker thread (TkAgg raises "main thread is not in main loop"; hard failure on headless deploys) — force Agg before importing the renderer [webui/pages/Lookup.py:18]
- [x] [Review][Patch] Every lookup leaks a Figure into pyplot's registry (st.pyplot does not close explicit figures) — close after rendering [webui/pages/Lookup.py:39]
- [x] [Review][Patch] Corrupt/non-DB sams.db raises sqlite3.DatabaseError which is neither wrapped by the engine (only OperationalError is) nor caught by the page (only SamsError) — raw traceback in the browser — broaden the engine catch to sqlite3.Error and add a page-level fallback handler [sams_core/repository.py:58, webui/pages/Lookup.py:31]
- [x] [Review][Patch] Unknown/ambiguous/empty-DB/zero-attendance all collapse to one misleading message ("We don't have any attendance saved for that number" — false for ambiguous ordinals; empty-DB case never says there are no students despite the subtask being checked off) — branch on the new LookupResult outcomes [webui/lookup_logic.py:40]
- [x] [Review][Patch] Whitespace-only input bypasses the empty-state prompt — strip before the guard [webui/pages/Lookup.py:25]
- [x] [Review][Patch] "Students we do know" listing is unbounded (200 students = one multi-thousand-char paragraph on a phone) and hardcodes a truncation ellipsis that falsely implies more — cap with honest truncation, fall back for NULL `no` [webui/lookup_logic.py:44]
- [x] [Review][Patch] The Streamlit page itself has zero test coverage — not even import — the DoD's copy claims rest on one manual run; add streamlit.testing.v1.AppTest tests for empty state, unknown index, and successful render [tests/test_webui_lookup.py]
- [x] [Review][Patch] Spinner covers the cheap DB query but not the slow matplotlib render (cold import 1-2s of dead air) — move the render inside the spinner [webui/pages/Lookup.py:28]
- [x] [Review][Patch] No st.set_page_config — the tab/sidebar say "app" — set a proper title on both pages [webui/app.py:14]
- [x] [Review][Patch] conftest honors only SAMS_HEADLESS=="1" — "true"/"yes" silently keep the GUI backend — accept truthy values [tests/conftest.py:8]
- [x] [Review][Dismissed] CLI/Web parity test tautological — parity is architectural (same engine function); a cross-process PNG compare adds little
- [x] [Review][Dismissed] sys.path bootstrap duplication — Streamlit runs pages as scripts; the real cure is an editable install (defer to packaging story 1-7 / shell story 4-1)
- [x] [Review][Dismissed] .claude/launch.json "unreviewed" — it IS committed in 2189aa9; it was merely outside this review's diff scope
- [x] [Review][Dismissed] Operator-resolved marker on the web chart — no spec clause requires it (verified against 4.5 ACs, UX-DR10, EXPERIENCE.md)
- [x] [Review][Defer] Sequencing: 4.5 shipped webui/app.py + requirements-web.txt that the sprint plan assigns to Sprint 8 / Story 4.1, and its stub landing page must be REPLACED (not extended) by 4.1's Process-landing three-page contract — flag to 4.1's owner; also 4.5 was built on 2.1/2.2 while both were still in review (resolved by this same review cycle)
