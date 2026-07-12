---
status: ready-for-dev
epic: 4
story: '4.1'
title: Open SAMS in the browser
frs: [FR-12]
uxdrs: [UX-DR1, UX-DR2, UX-DR12]
owner: M8 (Topic 8 — Web App & Packaging)
sprint: Week 2, Days 6–7 · 🔒 gated by Story 1.6 green
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
