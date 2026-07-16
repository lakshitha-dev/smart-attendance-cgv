---
status: review
epic: 2
story: '2.2'
title: Render the attendance timeline graph
frs: [FR-8]
owner: M7 (Topic 7 — Attendance Visualization), with M3 support
sprint: Week 1, Days 3–5
baseline_commit: 5cfb9692a1659e308dc2f10b2d13caf42e9c048d
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

## Tasks/Subtasks

- [x] Force a headless Matplotlib backend for the test suite
  - [x] `tests/conftest.py` sets the Agg backend when `SAMS_HEADLESS=1`, mirroring the existing cv2 gating
- [x] Create `sams_core/visualization.py` (AD-7: engine returns `Figure`, never shows it)
  - [x] `render_attendance_timeline(records)` — one colour-coded mark per Session, x = Sheet Identifiers
  - [x] Ambiguous on its own mid-band between Present and Absent
  - [x] Status colours from Dev Notes (`#256E4C`/`#A63D2A`/`#7A6212`); legend entries carry icon + text (✓/✕/?) — UX-DR8, greyscale-survivable
  - [x] Title + axis labels
  - [x] Overall attendance-rate percentage annotated, with documented Ambiguous handling (excluded from the rate, reported as pending)
  - [x] Function never calls `plt.show()`
- [x] Add `show_figure` to `cli_display.py` (AD-7: display stays in the adapter)
  - [x] Calls `plt.show()`, gated on `SAMS_HEADLESS` like the existing cv2 window helpers
- [x] Wire `infovis.py` to render + display the figure
  - [x] After printing records, call `visualization.render_attendance_timeline` then `cli_display.show_figure`
  - [x] No image re-processing — reads only the Attendance Records already fetched via Story 2.1's `query_attendance`
- [x] Tests
  - [x] `visualization.py` headless: figure returned, never shown, correct mark count/colours/positions for a multi-session case incl. Ambiguous
  - [x] Legend carries icon + text for all three statuses
  - [x] Attendance-rate annotation present and correctly computed (Ambiguous excluded, reported as pending)
  - [x] CLI test: `infovis.main` calls `show_figure` with a `Figure` for a known index
- [x] Run full regression suite; confirm no existing tests broke

## Dev Agent Record

### Implementation Plan

- `sams_core/visualization.py` is a pure function of `Sequence[AttendanceRecord]` → `Figure`: no DB access, no display calls (AD-7). Status → (y-position, colour, icon, label) is a small lookup table so the mid-band/colour/icon rules live in one place.
- `cli_display.py` gains `show_figure(fig)`, mirroring the existing `_gui_disabled`/`SAMS_HEADLESS` gate already used for the OpenCV stage windows, so the test suite never blocks or pops a window.
- `tests/conftest.py` forces the Matplotlib Agg backend whenever `SAMS_HEADLESS=1` (must happen before any `pyplot` import in the process — conftest loads before test modules).
- `infovis.py` stays a thin adapter: one additional call each to the engine (`render_attendance_timeline`) and the display helper (`show_figure`) after the existing record printing.

### Completion Notes

- `render_attendance_timeline` reads only the `Sequence[AttendanceRecord]` passed in (Story 2.1's `query_attendance` output) — no DB access, no image re-processing, satisfying the third AC directly.
- Ambiguous sits on its own mid-band (y=0, strictly between Absent y=-1 and Present y=1); status colours (`#256E4C`/`#A63D2A`/`#7A6212`) and legend icon+text (✓/✕/?) match the UX-DR8 spec verbatim and were verified against the exact hex values via `matplotlib.colors.to_rgba` in tests.
- Attendance rate = Present / (Present + Absent); Ambiguous is excluded from both sides and reported separately as "n pending" in the same caption, per the Dev Notes' recommendation — kept as one documented rule for the Web UI (4.5) to reuse unchanged.
- Visual smoke check (figure saved to PNG and inspected) caught the caption text initially overlapping the rotated x-axis tick labels; fixed by widening the figure (4 → 4.5in tall) and moving the caption further below the axes (y=-0.32 → -0.5 in axes-fraction coords) so `fig.tight_layout()` reserves enough bottom margin — confirmed clean in a re-rendered PNG.
- `infovis.py` grew by 2 lines (render + show) to 32 lines total, still well under the thin-adapter budget; `show_figure` reuses the existing `SAMS_HEADLESS` convention so the CLI test suite never blocks on or opens a window.
- `tests/conftest.py` now forces the Matplotlib Agg backend whenever `SAMS_HEADLESS=1`, before any `pyplot` import in the process — required so `visualization.py` is "headless-tested (figure inspected, not shown)" per the DoD.
- Full regression suite: 129 passed, 0 failed (120 prior + 9 new: 7 in `test_visualization.py`, 2 in `test_infovis.py`).

## File List

- `sams_core/visualization.py` (new — `render_attendance_timeline`)
- `cli_display.py` (modified — added `show_figure`)
- `infovis.py` (modified — renders + displays the timeline figure after printing records)
- `tests/conftest.py` (modified — forces Matplotlib Agg backend under `SAMS_HEADLESS=1`)
- `tests/test_visualization.py` (new — headless figure-inspection tests)
- `tests/test_infovis.py` (modified — added figure-display wiring tests)

## Change Log

- 2026-07-16: Implemented Story 2.2 — `sams_core/visualization.py` (`render_attendance_timeline`, AD-7), `cli_display.show_figure`, and `infovis.py` wiring to render + display the per-Session attendance timeline with Ambiguous mid-band, UX-DR8 colours/icons, and attendance-rate annotation. Fixed a caption/x-tick-label overlap found during a manual visual check. Full regression suite passes (129/129).
