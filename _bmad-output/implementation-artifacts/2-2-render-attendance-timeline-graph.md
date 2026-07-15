---
status: ready-for-dev
epic: 2
story: '2.2'
title: Render the attendance timeline graph
frs: [FR-8]
owner: M7 (Topic 7 — Attendance Visualization), with M3 support
sprint: Week 1, Days 3–5
---

# Story 2.2: Render the attendance timeline graph

## Story

As an operator,
I want the student's attendance shown as a labelled per-Session graph,
So that I can answer "how's this student's attendance?" at a glance — the brief's visualization deliverable.

## Acceptance Criteria

**Given** Attendance Records for a student
**When** the graph renders
**Then** `visualization.py` returns a Matplotlib `Figure` (never calls `plt.show`) showing the per-Session Present/Absent timeline, one colour-coded mark per recorded sheet, with Ambiguous distinct on its own mid-band between Present and Absent
**And** the overall attendance-rate percentage is annotated, with title, axis labels, and a legend whose status entries carry icon + text label (✓ Present / ✕ Absent / ? Ambiguous — greyscale-survivable).

**Given** the CLI adapter
**When** `infovis.py` receives the Figure
**Then** it displays it via Matplotlib's `show` — the same Figure object the Web UI later renders via `st.pyplot` (FR-14 data-layer parity).

**Given** the chart renders
**Then** it reads exclusively from Attendance Records in the Local DB — no image re-processing occurs.

## Dev Notes

- **Create:** `sams_core/visualization.py` (returns `Figure`, AD-7 — `plt.show` only in the CLI adapter).
- **Committed default chart (PRD FR-8):** per-Session timeline — x = Session dates (Sheet Identifiers), y = status; Ambiguous on its own mid-band with distinct `?` marks; overall attendance-rate % annotated; title + axes + legend.
- **Status colours (UX DESIGN.md):** Present `#256E4C`, Absent `#A63D2A`, Ambiguous `#7A6212`; legend entries carry icon + text (✓/✕/?) — colour never the sole carrier (UX-DR8 chart rule).
- **Attendance-rate definition:** decide and document how Ambiguous counts (recommend: excluded from the rate denominator note, or shown as "n pending") — state it on the chart caption; keep consistent with the Web UI later.
- **Figure is the parity artifact:** Web Lookup (4.5) must render THIS figure object — don't leak styling into the CLI adapter.

## Dependencies

- **Requires:** 2.1 (records query).
- **Enables:** 4.5.

## Definition of Done

Labelled figure renders for a student with data across multiple sessions (incl. an Ambiguous record); greyscale printout still readable; `visualization.py` headless-tested (figure inspected, not shown).
