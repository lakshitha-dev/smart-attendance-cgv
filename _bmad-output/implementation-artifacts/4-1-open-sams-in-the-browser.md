---
status: review
epic: 4
story: '4.1'
title: Open SAMS in the browser
frs: [FR-12]
uxdrs: [UX-DR1, UX-DR2, UX-DR12]
owner: M8 (Topic 8 — Web App & Packaging)
sprint: Week 2, Days 6–7 · 🔒 gated by Story 1.6 green
baseline_commit: 5fc30e0
---

# Story 4.1: Open SAMS in the browser

## Story

As Nadeesha (admin staff),
I want SAMS to open in my phone or desktop browser with three clearly named pages,
So that I can reach my task without anyone explaining the software to me.

## Acceptance Criteria

**Given** `pip install -r requirements-web.txt` on top of the base install (Streamlit only here — the grader path stays web-free)
**When** `streamlit run webui/app.py` starts and a browser opens the app
**Then** a Streamlit multipage app renders with native sidebar navigation: Process (landing, "Mark today's attendance"), Lookup ("Look up a student"), Investigate ("Check a signature") — no other navigation, no modals except the overwrite warning.

**Given** `.streamlit/config.toml`
**Then** the Quiet Clerk theme is applied (primaryColor `#44526A`, backgroundColor `#FAFAF8`, secondaryBackgroundColor `#FFFFFF`, textColor `#33383F`, default sans font), light mode pinned so browser dark-mode never inverts it, plus the minimal CSS block for chips/rows.

**Given** first open with no inputs
**Then** each page shows its specified empty state: Process = upload hint + two empty file slots + disabled Process button; Lookup/Investigate = a single prompt sentence + input. `webui/` imports the engine only — no detection/persistence/visualization logic in pages.

## Dev Notes

- **Create:** `webui/app.py`, `webui/pages/` (Process landing, Lookup, Investigate), `.streamlit/config.toml`, `requirements-web.txt` (streamlit 1.59.1).
- **UX-DR1 theme block** (DESIGN.md, copy verbatim): `[theme] primaryColor="#44526A" backgroundColor="#FAFAF8" secondaryBackgroundColor="#FFFFFF" textColor="#33383F" font="sans serif"`.
- **Empty-state microcopy (UX-DR12, verbatim):** Process hint: "Add the sheet photo and the info file, then tap Process. That's all you need to do." · Lookup: "Type a student's number to see their attendance." · Investigate: "Type a student's number to check their signature."
- **AD-1/AD-8:** pages are thin adapters — parse input → call engine → render. Streamlit imported ONLY under `webui/`. Known upstream wart: streamlit#11797 (deep-linking sub-pages with custom theme may bounce to default page) — non-blocking, don't fight it.
- **Page titles are sentence-case, calm** ("Mark today's attendance") — no jargon, no exclamation marks anywhere (Voice & Tone).

## Dependencies

- **Requires:** Story 1.6 gate GREEN (PRD §6.3); engine importable.
- **Enables:** 4.2–4.6.

## Definition of Done

App runs on phone + desktop browser; three pages navigate; theme pinned light; empty states match UX copy; zero engine logic in pages.

## Tasks / Subtasks

(Derived from the ACs — the story file predates the task-section convention.)

- [x] Task 1: .streamlit/config.toml — Quiet Clerk theme verbatim (UX-DR1) + base="light" pin
- [x] Task 2: Replace the 4.5-era app.py stub (deferred-work item) with an explicit st.navigation router: exactly Process (landing, default) / Lookup / Investigate, no other navigation (UX-DR2); single st.set_page_config; minimal chip/row CSS block (UX-DR1/DR8/DR14 tokens)
- [x] Task 3: webui/pages/Process.py — landing empty state (UX-DR12 hint verbatim, two labelled file slots per UX-DR3 with quiet slate "Ready" on accept, one full-width primary Process button disabled until both inputs per UX-DR4; processing itself is 4.2's scope)
- [x] Task 4: Adapt Lookup/Investigate pages to the router (set_page_config moved to app.py; empty-state prompts already verbatim)
- [x] Task 5: Headless AppTest suite for the shell — theme values, router page set, landing content, per-page empty states, thin-adapter guard (no cv2/numpy/sqlite3 in pages), Voice & Tone no-exclamation guard
- [x] Task 6: Verify the app serves — streamlit run webui/app.py headless, HTTP 200

## Dev Agent Record

### Implementation Plan

Red-green: tests/test_webui_shell.py written first (4 failed on the missing
theme/router/landing exactly as expected), then config.toml + Process page +
router, then green. st.navigation chosen over pages/ auto-discovery so the
sidebar carries EXACTLY the three sentence-case titles (auto-discovery would
have shown a fourth "app" entry — the 4.5-era stub's known defect).

### Completion Notes

- Deferred-work item resolved: the 4.5 stub app.py is REPLACED by the router;
  pages/ auto-discovery is disabled by the explicit st.navigation call, so
  "no other navigation" holds by construction.
- The single st.set_page_config now lives in app.py; Lookup/Investigate lost
  their own calls (duplicate calls error under a router). Pages still run
  standalone under AppTest.
- Empty states verified verbatim per UX-DR12 (all three sentences asserted in
  tests); Process button disabled-until-ready per UX-DR4; slot "Ready" note
  renders in slate, never Present green (UX-DR8 rule).
- Full suite: 206 passed (8 new shell tests). Live smoke: streamlit served
  HTTP 200 headless on :8599 with the venv-installed requirements-web.txt.
- Known upstream wart acknowledged (streamlit#11797 deep-linking) — not fought,
  per Dev Notes.

### File List

- .streamlit/config.toml (new)
- webui/app.py (stub replaced by the st.navigation router)
- webui/pages/Process.py (new)
- webui/pages/Lookup.py (set_page_config removed)
- webui/pages/Investigate.py (set_page_config removed)
- tests/test_webui_shell.py (new)
- _bmad-output/implementation-artifacts/4-1-open-sams-in-the-browser.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-07-18: Story 4.1 implemented — Quiet Clerk theme, three-page router
  replacing the 4.5 stub, Process landing empty state, 8 shell tests.
  206/206 suite green; live HTTP 200 smoke.
