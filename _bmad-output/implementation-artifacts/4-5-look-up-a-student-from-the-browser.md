---
status: ready-for-dev
epic: 4
story: '4.5'
title: Look up a student from the browser
frs: [FR-14]
uxdrs: [UX-DR10, UX-DR12]
owner: M6 (Lookup page)
sprint: Week 2, Day 8 · 🔒 gated
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
