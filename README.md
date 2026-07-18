# SAMS — Smart Attendance Management System

Computer Graphics and Visualization (CS402.3) group assignment: an image-processing
prototype that reads a photographed Signing Sheet, marks attendance per student,
visualizes attendance history, and verifies signatures against references.

## Requirements

- Python 3.12 or 3.13 (fresh-machine protocol verified on 3.13)
- Windows/macOS: no other system dependencies — everything installs from
  `requirements.txt`. Minimal Linux servers additionally need OpenCV's system
  libraries (`sudo apt install libgl1 libglib2.0-0`).

## Install (one step)

```
pip install -r requirements.txt
```

This installs the pinned engine + CLI dependencies only (OpenCV, NumPy, Matplotlib).
No web framework is required to run or grade the prototype.

## Run (the three commands)

All three commands run from the project root. Sample inputs live in
`sample_signin-sheets/` (five real Signing Sheet photos `1.jpeg`–`5.jpeg`, each
with its Info File `1.xml`–`5.xml`).

**1. Process a Signing Sheet** — detects each student's signature cell and saves
Attendance Records to the Local DB (`sams.db`, auto-created on first run). The
brief's exact invocation works out of the box (`10.07.2019.png` and `info.xml`
ship in the project root; the filename's date becomes the Sheet Identifier
because this Info File carries no session date):

```
python sams.py 10.07.2019.png info.xml
```

The seven pipeline stages (Original → Greyscale → Denoised → Binarized →
Deskewed → Table Grid → Per-Cell Inspection) display live and are saved under
`output/<sheet-date>/`. The per-student summary prints Present / Absent /
Ambiguous, and signature crops are saved for verification. The five sample
sheets process the same way:

```
python sams.py sample_signin-sheets/1.jpeg sample_signin-sheets/1.xml
```

**2. Query a student's attendance + timeline graph** — either index form works
(short `No` ordinal or 8-digit Student Index return identical records):

```
python infovis.py 001
python infovis.py 10000409
```

Prints every saved Attendance Record for the student and opens the per-session
timeline chart with the attendance rate (when a display is available — the
chart window is suppressed under `SAMS_HEADLESS`/headless sessions).

**3. Verify a signature** — compares the student's probe signature (cropped by
step 1) against their Reference Signatures and reports a match verdict:

```
python investigate.py 001
```

Reference Signatures live under `references/<student-index>/`.

Process all five sample sheets first for the full experience:

```
python sams.py sample_signin-sheets/1.jpeg sample_signin-sheets/1.xml
python sams.py sample_signin-sheets/2.jpeg sample_signin-sheets/2.xml
python sams.py sample_signin-sheets/3.jpeg sample_signin-sheets/3.xml
python sams.py sample_signin-sheets/4.jpeg sample_signin-sheets/4.xml
python sams.py sample_signin-sheets/5.jpeg sample_signin-sheets/5.xml
```

Useful flags (`sams.py` only): `--no-display` suppresses the stage windows;
`--overwrite` replaces operator-resolved rows on re-processing; `--date`
overrides the Sheet Identifier. To run everything fully windowless (CI/
servers): `set SAMS_HEADLESS=1` (cmd), `$env:SAMS_HEADLESS="1"` (PowerShell),
or `SAMS_HEADLESS=1 ...` (bash).

## Tests

```
pip install -r requirements-dev.txt
pytest
```

The suite is headless (no windows) and self-contained: it includes the PRD §6.3
accuracy gate proving 100% classification accuracy on all five sample sheets
against the committed ground truth (`tests/data/ground_truth.csv`).

## Optional: Web UI

The browser front-end is a separate, optional install — the graded CLI path
never needs it:

```
pip install -r requirements-web.txt
streamlit run webui/app.py
```

## Project layout

```
sams.py / infovis.py / investigate.py   thin CLI entry scripts (<50 lines each)
cli_display.py                          CLI rendering (windows, stdout, figures)
sams_core/                              the engine: pipeline, detection, DB, charts
webui/                                  optional Streamlit front-end
sample_signin-sheets/                   five sample sheets + Info Files
10.07.2019.png + info.xml               the brief's verbatim-command inputs
references/                             COMMITTED Reference Signatures (investigate.py input — keep!)
tests/                                  pytest suite incl. the accuracy gate
output/  sams.db                        created/managed at runtime (safe to delete)
```

## Submission packaging

The prototype ZIP contains the code, the samples, `10.07.2019.png` + `info.xml`,
and `references/` (a required input — never exclude it). Exclude the dev-only
material: `.git/`, `.venv*/`, `__pycache__/`, `.pytest_cache/`, `output/`,
`sams.db`, `.claude/`, `_bmad/`, `_bmad-output/`, `docs/`, internal notes
(`TUNING_LOG.md`, `STORY_*.md`, `IMPLEMENTATION_*.md`, `FINAL_DELIVERY_*.md`),
and the coursework brief documents. The prototype ZIP plus the MS Word report
go into the outer ZIP for LMS. A fresh unzip of the prototype ZIP satisfies
the Install/Run steps above with no further setup.
