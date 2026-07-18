---
status: done
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

### Review Findings (code review 2026-07-18, Sprint-8)

- [x] [Review][Patch] `_score_scale` built a full matplotlib figure inside the Investigate PAGE, violating this story's "no visualization logic in pages" AC — moved to `sams_core/visualization.render_score_scale` (AD-7: figures live in the engine's chart module exactly once); verdict colours now derive from the one `_STATUS_STYLE` table [webui/pages/Investigate.py:31]
- [x] [Review][Patch] `use_container_width` is deprecated on the 1.59.1 pin (already removed from some elements in 1.57) — replaced with `width="stretch"` on the Process button and all three Investigate images [webui/pages/Process.py:36, webui/pages/Investigate.py:82]
- [x] [Review][Patch] Armed Process button was a silent no-op (tap → rerun → nothing) — a click now renders calm interim copy: "Processing arrives in the next update — nothing was saved." [webui/pages/Process.py:47]
- [x] [Review][Patch] "Ready" note rendered Streamlit-gray, not the spec'd slate, and interpolated the raw filename into the markdown directive (scan[2].png broke rendering) — now `:primary[✓ Ready]` (theme slate) + filename as a code span with backticks stripped [webui/pages/Process.py:19]
- [x] [Review][Patch] Zero-byte upload showed "Ready" and armed the button — size>0 required; empty file gets "That file looks empty — please pick it again." [webui/pages/Process.py:14]
- [x] [Review][Patch] iPhone HEIC (the primary phone default) was rejected with only Streamlit's generic error — caption added: JPEG/PNG guidance with the 'Most Compatible' hint [webui/pages/Process.py:33]
- [x] [Review][Patch] `page_title="SAMS"` flattened every browser tab to one string (regression vs the per-page titles removed from Lookup/Investigate) — dropped; st.navigation now titles each tab per page [webui/app.py:17]
- [x] [Review][Patch] `.block-container { max-width: 1100px }` fought layout="centered"'s own ~46rem cap via internal-class specificity — layout="wide" + the cap now owns the width honestly; missing UX-DR1 tokens delivered (18px page margins, 16px card padding, 12/14px radii) [webui/app.py:17]
- [x] [Review][Patch] 200MB default upload limit unconfigured — `[server] maxUploadSize = 25` [.streamlit/config.toml]
- [x] [Review][Patch] Theme silently vanishes when streamlit is launched from another cwd (.streamlit/ is cwd-discovered) — README run-from-root note + config comment [README.md, .streamlit/config.toml]
- [x] [Review][Patch] "Browser dark-mode never inverts" overstated — comment softened: base="light" pins the DEFAULT; a user's explicit in-app Dark choice persists via browser storage [.streamlit/config.toml]
- [x] [Review][Patch] Router's non-default pages were never executed by any test (grep-only assurance) — `at.switch_page` now drives Lookup and Investigate through the router [tests/test_webui_shell.py]
- [x] [Review][Patch] Chip/row CSS was untested dead weight — CSS-token test pins the UX-DR1/DR8 values until 4.3 consumes them [tests/test_webui_shell.py]
- [x] [Review][Patch] Voice guard was line-regex with a startswith("!") escape hatch and blind to triple-quoted strings — replaced with an AST walk over every string constant [tests/test_webui_shell.py]
- [x] [Review][Patch] Dead sys.path shim in Process.py (imports only streamlit); deferred-work ledger stale on both webui items — shim removed, ledger annotated (app.py-stub item RESOLVED; bootstrap item partially addressed) [webui/pages/Process.py, deferred-work.md]
- [x] [Review][Dismissed] AppTest cannot simulate uploads — the enable-on-ready branch stays manually verified (platform limitation)
- [x] [Review][Dismissed] Extension-only upload filtering / magic-byte sniffing — decode-level rejection is 4.2's engine-side scope per UX-DR12
- [x] [Review][Dismissed] No CI runs the suite — out of coursework scope; the fresh-venv protocol is the documented gate

