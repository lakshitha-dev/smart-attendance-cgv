---
status: ready-for-dev
epic: 2
story: '2.1'
title: Query a student's attendance by either index form
frs: [FR-7]
owner: M7 (Topic 7 — Attendance Visualization)
sprint: Week 1, Days 2–5 (chart built against seeded DB; wired to real DB after 1.5)
---

# Story 2.1: Query a student's attendance by either index form

## Story

As an operator,
I want to run `python infovis.py <index>` with either the 8-digit Student No or the short ordinal,
So that I can pull up any student's attendance records the way the brief's command specifies.

## Acceptance Criteria

**Given** a Local DB populated by Epic 1
**When** `python infovis.py 001` and `python infovis.py 10000409` run for the same student
**Then** both resolve through the single engine index resolver (no adapter parses index forms) and return the identical set of Attendance Records.

**Given** an unknown index
**When** the command runs
**Then** the program reports "no data" listing the valid indices from `repository.list_students()` (short form + 8-digit, e.g. `001 (10000409)`), exits 0, and never raises an error tone.

**Given** the Ports & Adapters rule
**Then** `infovis.py` stays a thin adapter (<50 lines): parse argument → call engine query → hand off to display.

## Dev Notes

- **Create:** `infovis.py` (root entry, thin); engine query API on `repository.py`.
- **AD-4:** index resolution happens in ONE engine resolver (both `10009301` and `002` forms) before any DB read; DB stores only the canonical 8-digit index.
- **AD-6:** unknown index is a **no-data result**, never an exception — CLI prints friendly list + exits 0. Same pattern the Web Lookup page reuses later (4.5).
- **Parallelization tip (2-week plan):** don't wait for Story 1.5 — seed a temp DB by hand (repository schema lands Day 2–3) and build against it; swap to real data after integration Day 5.

## Dependencies

- **Requires:** 1.5 (repository; stub/seeded DB acceptable until integration).
- **Enables:** 2.2, 4.5.

## Definition of Done

Both index forms return identical records (unit test); unknown-index message lists valid indices; entry script <50 lines.
