---
status: ready-for-dev
epic: 1
story: '1.7'
title: Run everything on a fresh machine
frs: [FR-15]
owner: M1 + M2 (packaging pair)
sprint: Week 2, Day 9
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

## Dependencies

- **Requires:** 1.1–1.6 minimum; by Day 9 also 2.x and 3.x for the three-command check.
- **Enables:** submission; Story 4.7's parity verification.

## Definition of Done

Fresh-machine (or fresh-venv) run of all three CLI commands + tests documented with output; README merged; no web imports reachable from engine/CLI path.
