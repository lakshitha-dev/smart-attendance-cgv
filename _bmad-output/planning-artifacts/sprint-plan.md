# SAMS — Sprint Plan v4: 8 Independent Feature-Sprints (8 Members, 2 Weeks)

**Project:** Student Attendance Management System (CS402.3 Group Coursework)
**Model:** each member owns ONE self-contained feature-sprint end-to-end (all its user stories, development, and testing), built **independently in parallel** against the Day-1 Fixture Kit. Sprint definitions and selection live in `topic-selection.md`.
**Timeline:** 2 weeks (10 working days)
**Supersedes:** v3 (parallel work packages with cross-support). Chosen by the team for maximum member independence; the both-concern trade-off and its mitigation are documented in `topic-selection.md`.

## The 8 Sprints (one per member)

| Sprint | Feature (end-to-end) | Stories | Independence input (fixture) |
|---|---|---|---|
| 1 | Foundation, contracts & input validation | 1.1 | raw sample sheets + info.xml |
| 2 | Image preprocessing + stage display | 1.2 | the 5 raw sample photos |
| 3 | Table & cell localization | 1.3 | hand-deskewed sheet images |
| 4 | Signature detection & classification | 1.4 | cell-crop + grid-mask fixtures |
| 5 | Data layer, accuracy gate & **integration lead** | 1.5, 1.6 | fixture classification results + ground truth |
| 6 | Attendance visualization (CLI + Web Lookup) | 2.1, 2.2, 4.5 | seeded sample database |
| 7 | Signature verification (CLI + Web Investigate) | 3.1–3.3, 4.6 | hand-cropped signature fixtures |
| 8 | Web Process experience & packaging | 4.1–4.4, 4.7, 1.7 | stub engine replaying recorded stages + seeded DB |

All 19 stories covered. Story files with full acceptance criteria + dev notes: `_bmad-output/implementation-artifacts/`.

## Timeline

| Days | Phase |
|---|---|
| **Day 1** | **All-hands half-day.** Agree & freeze contracts (`models.py`, DB schema, `StageArtifact`, function signatures — Sprint 1 commits them by tonight). Build the Fixture Kit together: 5× `info.xml` (with session dates — filenames carry none), `ground_truth.csv` adjudicated **before any threshold tuning**, hand-deskewed images, cell crops, signature crops (Sprint 7 owner leads), seeded DB, recorded stage sequence. |
| **Days 2–7** | **Independent build.** Everyone implements their own sprint against fixtures, writes their own tests. Daily 15-min stand-up limited to contract questions and blockers. No cross-sprint code dependencies allowed — if you need something from another sprint, you need a fixture, not their code. |
| **Days 8–9** | **Integration window** (led by Sprint 5). Swap fixtures for real outputs in chain order 2→3→4→5; run the accuracy gate on the real chain; 🔒 wire Sprint 8 to the real engine ONLY after the gate is green (PRD §6.3); run the CLI↔Web parity check; each member fixes their own seam bugs same-day. |
| **Days 9–10** | **Report & submit.** Each member: ~2-page individual chapter on their sprint (due Day 9 evening). Group: stage screenshots for all five sheets, testing results, challenges discussion, front page (names/roles/indices/subject), references. Package: prototype ZIP + Word report → outer ZIP → LMS (Day 10). |

## Rules That Keep This Model Working

1. **Contracts are law after Day 1.** Changing `models.py` or the DB schema needs Sprint 1 + Sprint 5 owners' sign-off, broadcast at stand-up.
2. **Fixtures, not favors.** Blocked on another sprint's output? Extend the fixture kit — never import their unfinished code.
3. **Your sprint includes its own tests.** "Done" = your stories' acceptance criteria pass on fixture inputs, headlessly where the architecture requires it.
4. **The accuracy gate governs the Web UI.** Sprint 8 builds against the stub all week; real-engine wiring waits for the gate (fallback: engine + CLI alone fully satisfies the brief).
5. **Golden constants:** ground truth before tuning; no per-sheet hacks or pixel coordinates; every tunable in `config.py`.
6. **Integration days are sacred.** Days 8–9 are for seams and the gate — no new features.

## File Ownership Map (who may edit what)

**Rule: one file, one owner.** You edit only your sprint's files. Work on your own git branch (`sprint-3-localization`), merge via PR. If you need a change in someone else's file, ask the owner — don't edit it yourself.

| File / folder | Owner | Others' access |
|---|---|---|
| `sams.py`, `sams_core/info_file.py`, `sams_core/errors.py`, `sams_core/models.py` | Sprint 1 | Read-only. Need a new dataclass/field? Request to Sprint 1 (same-day turnaround at stand-up). |
| `sams_core/config.py` | Sprint 1 (structure) | **Append-only:** each sprint adds its OWN clearly-commented constants block (`# --- Sprint 4: detection thresholds ---`). Never touch another sprint's block — append-only means no merge conflicts. |
| `sams_core/pipeline.py` (stage registry) | Sprint 2 | The 7-slot registry is written Day 1 with all slot names fixed. Sprints 3 & 4 implement their stage functions in THEIR OWN files (`locate.py`, `detect.py`); pipeline.py just imports them — one import line each, added by Sprint 2 on request. |
| `sams_core/locate.py` | Sprint 3 | read-only |
| `sams_core/detect.py`, `sams_core/mapping.py` (mapping consumed by Sprint 5) | Sprint 4 / Sprint 5 | read-only |
| `sams_core/artifacts.py` | Sprint 2 (stage saving) | Sprint 4's crop-saving function added via one small PR reviewed by Sprint 2 |
| `sams_core/repository.py` | Sprint 5 | All APIs (`list_students`, `resolve`, registration…) are in the Day-1 contract; Sprints 6/7/8 only CALL them, never edit |
| `sams_core/visualization.py`, `infovis.py`, `webui/pages/lookup.py` | Sprint 6 | read-only |
| `sams_core/verification.py`, `investigate.py`, `references/`, `webui/pages/investigate.py` | Sprint 7 | read-only |
| `webui/app.py`, `webui/pages/process.py`, `.streamlit/config.toml`, `requirements*.txt`, README | Sprint 8 | read-only (Lookup/Investigate pages are separate files owned by 6 & 7 — no collision) |
| `tests/` | Each sprint owns its own test file (`test_locate.py`, `test_detect.py`…) | `test_accuracy.py` + `ground_truth.csv` owned by Sprint 5 |

**Why this works:** the architecture already split the code one-module-per-concern, and Streamlit pages are separate files per page. The only genuinely shared files (`models.py`, `config.py`, `pipeline.py`) are handled by frozen-contract + append-only + owner-PR rules — so two members almost never edit the same file, and when they must, it's a one-line reviewed change.

## Risk Register

| Risk | Mitigation |
|---|---|
| Sprint 1 late → everyone blocked | Contracts agreed jointly Day 1 morning; Sprint 1 only implements them; skeleton committed same day |
| Fixture drift (fixture ≠ real output shape) | Contracts define shapes; Sprint 5 spot-checks one real handoff mid-week (Day 5 mini-check recommended) |
| Sprint 7 similarity quality poor | Highest-risk sprint starts Day 1 with curation; honest threshold documentation still earns the brief's "attempt" credit |
| Integration surprises on Day 8 | Chain order 2→3→4→5 integrated one seam at a time; each owner on call for their seam |
| Member unavailable mid-week | Their sprint is self-contained — another member can pick up the story files + fixtures without untangling shared code |
| Both-concern coverage weaker per member | Each sprint's named cross-concern element goes in the report chapter (see `topic-selection.md`) |
