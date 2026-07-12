---
status: ready-for-dev
epic: 3
story: '3.1'
title: Maintain Reference Signatures per student
frs: [FR-9]
owner: M6 (Topic 6 — Signature Verification)
sprint: Week 1 Day 1 (curation) + Week 2 Day 6 (registration API)
---

# Story 3.1: Maintain Reference Signatures per student

## Story

As an operator,
I want known-good Reference Signatures stored and retrievable per Student Index,
So that a suspicious signature has something trustworthy to be compared against.

## Acceptance Criteria

**Given** the FR-9 protocol
**When** the team populates `references/<student_index>/` with signature crops from sample sheets 1–3 (using the crops Story 1.4 saves) and commits them
**Then** dropping image files into `references/<index>/` is the complete ingestion path — the engine registers path metadata into the Local DB on first use (no image blobs in the DB) and retrieves them by either index form.

**Given** the dataset protocol
**Then** reference and probe sets are disjoint by sheet: references from sheets 1–3, probes from sheets 4–5, impostor probes from other students — no signature is ever compared against itself.

**Given** a known student whose `references/<index>/` folder is empty or missing
**When** references are requested
**Then** the engine returns a no-data result (same family as unknown index), never an exception.

## Dev Notes

- **Create:** `references/<student_index>/` folder structure (committed to repo); registration/read API on `repository.py` + `verification.py` loader.
- **AD-10:** references live on the FILESYSTEM, pre-populated by the team from sheets 1–3; engine only reads + registers path metadata; probe crops come from `output/<sheet>/crops/<index>.png` (Story 1.4). No blobs in DB.
- **Curation can start Day 1** — cropping signatures from sheets 1–3 by hand needs no pipeline code. Don't wait for 1.4; its automated crops refine the set later.
- **Protocol discipline (SM-4):** keep a manifest noting which sheet each reference came from, so the disjoint split (1–3 refs / 4–5 probes) is provable in Story 3.3 and the report.
- **AD-6:** empty/missing references for a known student = no-data result — CLI prints friendly message exit 0; Web renders the no-data state (4.6).
- **Note:** the PRD flags an `[ASSUMPTION]` that sheet-crop references satisfy the brief's "collect signatures of the given student" — if anyone can hand-collect genuine samples, add them; otherwise proceed with the protocol.

## Dependencies

- **Requires:** nothing for curation (Day 1); 1.4 crops + 1.5 repository for registration.
- **Enables:** 3.2, 3.3, 4.6.

## Definition of Done

`references/` committed with ≥1 reference per student from sheets 1–3 + provenance manifest; retrieval by either index form unit-tested; empty-folder no-data path tested.
