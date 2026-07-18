---
status: done
epic: 1
story: '1.7'
title: Run everything on a fresh machine
frs: [FR-15]
owner: M1 + M2 (packaging pair)
sprint: Week 2, Day 9
baseline_commit: 468788a31d7732d86e0230394ed3cdc9e58df340
---

# Story 1.7: Run everything on a fresh machine

## Story

As the marker,
I want the prototype to run from a fresh unzip with a one-step install,
So that grading works exactly as the brief's commands describe.

## Acceptance Criteria

**Given** a clean machine with Python 3.12/3.13 and a fresh unzip
**When** `pip install -r requirements.txt` then `python sams.py 10.07.2019.png info.xml` run
**Then** the install is one step (pinned versions, zero web dependencies), the Local DB bootstraps automatically, all paths resolve relative to the project root, and the full pipeline runs per the brief.

**Given** the codebase
**Then** engine + CLI import only OpenCV/NumPy/Matplotlib/stdlib; entry scripts remain thin (<50 lines); a README documents the install and run commands. (The same packaging conventions carry `infovis.py` and `investigate.py` — by Day 9 all three exist; verify all three.)

## Dev Notes

- **AD-8 (dependency isolation):** `requirements.txt` = engine + CLI pins ONLY (opencv-python 4.13.0.92, numpy 2.5.1, matplotlib 3.11.0). Streamlit 1.59.1 lives ONLY in `requirements-web.txt` and is imported only from `webui/`. Verify with a venv that has no Streamlit: all three CLI commands must run.
- **Test protocol:** fresh venv (ideally a second machine or clean user account) → unzip → install → run all three brief commands + the pytest suite. Time it; note it for the report.
- **README:** install steps, the three commands verbatim from the brief, optional Web UI steps (`pip install -r requirements-web.txt`, `streamlit run webui/app.py`).
- **Check:** no absolute paths anywhere (`config.py` audit); DB and `output/` folders auto-create; entry scripts <50 lines each (AD-1).
- **Submission packaging (brief):** prototype ZIP + MS Word report → outer ZIP → LMS (Day 10 task, but the ZIP structure is verified here).

## Tasks / Subtasks

(Derived from the ACs + Dev Notes — the story file predates the task-section convention.)

- [x] Task 1: AD-8 dependency-isolation audit — requirements.txt pins engine+CLI only (opencv-python 4.13.0.92, numpy 2.5.1, matplotlib 3.11.0); streamlit only in requirements-web.txt; no streamlit/webui import reachable from sams_core/, sams.py, infovis.py, investigate.py; verified by grep + import test
- [x] Task 2: Path & bootstrap audit — no absolute paths anywhere; all of config.py relative to PROJECT_ROOT (env seams keep relative defaults); DB and output/ auto-create on first run; entry scripts <50 lines each (AD-1)
- [x] Task 3: README — install steps, the three brief commands verbatim, expected outputs, test suite instructions, optional Web UI steps (requirements-web.txt + streamlit run webui/app.py), submission ZIP structure
- [x] Task 4: Pin the test dependency so the fresh-machine test protocol is reproducible (requirements-dev.txt with pytest; NOT part of the marker's one-step install)
- [x] Task 5: Fresh-venv proof — clean venv with NO streamlit → pip install -r requirements.txt (timed) → run all three brief commands against the samples + full pytest suite; document results in Dev Agent Record
- [x] Task 6: Automated packaging guard — tests that pin AD-8 isolation (no web import in the engine/CLI import graph), entry-script line budgets, and pinned-versions format, so packaging cannot silently regress

## Dependencies

- **Requires:** 1.1–1.6 minimum; by Day 9 also 2.x and 3.x for the three-command check.
- **Enables:** submission; Story 4.7's parity verification.

## Definition of Done

Fresh-machine (or fresh-venv) run of all three CLI commands + tests documented with output; README merged; no web imports reachable from engine/CLI path.

## Dev Agent Record

### Implementation Plan

Audit-first: the packaging promises (AD-1/AD-8/FR-15) were encoded as executable
guards (tests/test_packaging.py) before touching docs, so every claim the README
makes is pinned by a test. Then the fresh-machine protocol was executed for real
in a clean venv rather than asserted.

### Debug Log

- Guard test v1 flagged prose mentions of "Streamlit" in engine docstrings —
  narrowed to actual import statements; the real reachability check is the
  fresh-interpreter import-graph probe.
- requirements.txt / requirements-web.txt / entry-script budgets were already
  compliant (45/48/43 lines); no production code changes were needed.

### Completion Notes

- AD-8 verified two ways: import-graph probe (imports all three entry scripts in
  one interpreter, asserts no streamlit/tornado/pydeck in sys.modules) and the
  fresh venv run below.
- Fresh-venv protocol (Windows 11, Python 3.13, venv with pip only):
  `pip install -r requirements.txt` completed in **107 s**, one step, pinned
  cv2 4.13.0 / numpy 2.5.1 / matplotlib 3.11.0; `import streamlit` fails as
  required. From a clean state (no sams.db, no output/): 
  `python sams.py sample_signin-sheets/1.jpeg sample_signin-sheets/1.xml` →
  exit 0, DB + output/ auto-created, 6 records saved;
  `python infovis.py 001` → exit 0, records + timeline;
  `python investigate.py 001` → exit 0, match verdict 58/100 vs threshold 40.
- Test suite in the SAME web-free venv: **189 passed, 7 skipped** — the 7 skips
  are exactly the Streamlit AppTest tests (importorskip), proving the grader
  path never needs the web install. With requirements-web.txt added: **196
  passed, 0 skipped**.
- Absolute-path scan clean; config.py fully PROJECT_ROOT-relative (env seams
  keep relative defaults). README documents install, the three brief commands
  verbatim (with the 10.07.2019.png filename-date note per AR-11), tests,
  optional Web UI, and the submission ZIP structure.

### File List

- README.md (rewritten — was a bare title)
- requirements-dev.txt (new — pytest pin for the reproducible test protocol)
- tests/test_packaging.py (new — 6 packaging guards)
- _bmad-output/implementation-artifacts/1-7-run-everything-on-a-fresh-machine.md (this file)
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-07-18: Story 1.7 implemented — packaging guards, README, dev
  requirements, fresh-venv verification (107 s install; 3/3 commands clean;
  189 passed + 7 web skips). No production code changes required.

### Review Findings (code review 2026-07-18, Sprint-8)

- [x] [Review][Patch] README.md was listed in .gitignore (only prior tracking saved it) — rule removed + a guard test now asserts the README exists, is tracked, and is not ignore-matched [.gitignore:25]
- [x] [Review][Patch] The AC's literal command could not run from a fresh unzip (no 10.07.2019.png / info.xml shipped) — both now committed (dateless Info File, so the filename date becomes the Sheet Identifier per AR-11) and verified end-to-end; README leads with the verbatim command [10.07.2019.png, info.xml]
- [x] [Review][Patch] Import-graph probe never reached lazily-imported engine modules, inherited PYTHONPATH/PYTHONSAFEPATH, and only blocked a hardcoded trio — now imports every sams_core submodule via pkgutil in a scrubbed env and blocks streamlit/tornado/pydeck/altair/webui [tests/test_packaging.py]
- [x] [Review][Patch] Grep guard missed comma-form imports and engine→webui layering violations; sams_core scan was non-recursive — regex extended, rglob everywhere [tests/test_packaging.py]
- [x] [Review][Patch] Pin parsing broke on BOM/inline comments, accepted non-numeric versions and conflicting duplicates, skipped PEP 503 normalization; -r check matched comments — strict shared parser with loud failures [tests/test_packaging.py]
- [x] [Review][Patch] requirements-dev.txt was the one unguarded door into the "web-free" proof venv — guarded (must extend core, pin pytest, contain no web package) [tests/test_packaging.py]
- [x] [Review][Patch] Absolute-path guard missed /var,/etc,/opt,/mnt,/srv, UNC, "C:" join-style literals, and skipped webui/ — broadened + webui/ scanned [tests/test_packaging.py]
- [x] [Review][Patch] cli_display honored only the literal SAMS_HEADLESS=1 while visualization/conftest accept any truthy value (SAMS_HEADLESS=true → Agg charts but popping cv2 windows) — unified truthy rule [cli_display.py:23]
- [x] [Review][Patch] README claims corrected: Linux libGL note; 3.12-unverified caveat; timeline-window headless qualifier; flags scoped to sams.py + PowerShell env syntax; references/ relabeled as a COMMITTED input never to exclude; submission ZIP exclusion list made explicit (.git/, _bmad*, internal notes, the coursework docx) [README.md]
- [x] [Review][Dismissed] Entry-script budget counts raw lines — AD-1 defines the budget as literal file lines; not gameability worth a parser
- [x] [Review][Dismissed] pytest transitive deps unpinned — consistent with the repo's top-level-pin style; full lock is out of coursework scope

