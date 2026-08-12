# SAMS — Technical Notes

The detail behind the [README](../README.md): how the pipeline works, what the numbers are, how to
configure it, and how it ships.

- [The seven-stage pipeline](#the-seven-stage-pipeline)
- [Detection accuracy](#detection-accuracy)
- [Visualization encoding](#visualization-encoding)
- [Signature verification](#signature-verification)
- [CLI reference](#cli-reference)
- [Web UI pages](#web-ui-pages)
- [Configuration](#configuration)
- [Tests](#tests)
- [Project structure](#project-structure)
- [Deployment](#deployment)
- [Submission packaging](#submission-packaging)

---

## The seven-stage pipeline

Each stage is displayed live (unless suppressed) and written to
`output/<sheet-date>/01-original.png` … `07-per-cell-inspection.png`.

| # | Stage | What it does | Technique |
|---|-------|--------------|-----------|
| 1 | **Original** | The photo as loaded, after the sheet boundary is cropped out of the background | Largest-contour sheet detection with padding |
| 2 | **Greyscale** | Drops colour — signature ink is a shape problem, not a colour one | `cv2.cvtColor` |
| 3 | **Denoised** | Removes camera speckle that would otherwise read as ink | Median blur, kernel 5 |
| 4 | **Binarized** | Separates ink from paper under uneven desk lighting | Adaptive Gaussian threshold, block 35, C 11 |
| 5 | **Deskewed** | Rotates the crooked photo back level | Hough lines over long near-horizontal rules; corrects above 0.5°, ignores beyond 20° |
| 6 | **Table Grid** | Finds the Student Table and every cell in it | Directional morphology → line clustering → pick the 5-column table below the 4-column metadata row |
| 7 | **Per-Cell Inspection** | Measures ink per signature cell and classifies each student | Connected components, majority-area attribution, coverage thresholds |

Adaptive thresholding is used in stage 4 rather than a global Otsu threshold because a phone photo
of a sheet on a desk is lit unevenly — one side of the page is often noticeably darker than the
other.

Stage 6 uses **no OCR and no hard-coded pixel coordinates**. Horizontal and vertical rules are
pulled out with directional morphology, clustered into tables, and the five-column Student Table
(`No | Student No | Title | Student Name | Signature`) is picked out from below the four-column
metadata row — so the sheet can move around in frame between photos.

In stage 7, each signature cell's ink is measured by connected component, and a signature that
spills over a row line is attributed to whichever cell holds most of its area. Coverage at or above
3.0% is Present, at or below 1.5% is Absent, and anything between is **Ambiguous** — handed to the
operator with the actual crop shown, never quietly guessed.

Thresholds and kernels all live in one place — `sams_core/config.py` — with the reasoning for each
value written next to it. No pipeline module contains a bare numeric literal.

---

## Detection accuracy

<div align="center">
  <img src="report/m1-detection-eval.png" alt="Bar chart showing six of six rows correct on each of the five sample sheets, thirty of thirty overall" width="700"/>
</div>

Detection is checked against a hand-adjudicated answer key (`tests/data/ground_truth.csv`, 30 rows
across the five sample sheets, adjudicated *before* the thresholds were tuned and then independently
re-adjudicated). Current result: **30/30 — 100%**, enforced as a test so it cannot silently regress.

```bash
python evaluate_detection.py        # per-sheet table + output/detection_results.csv
python evaluate_verification.py     # signature score distribution figure
```

---

## Visualization encoding

<div align="center">
  <img src="report/m1-session-rates.png" alt="Bar chart of per-session attendance rates with the green and ochre threshold lines marked" width="700"/>
</div>

Attendance rates use one hue encoding everywhere — green at or above 80%, ochre at or above 50%, red
below — shared by the dashboard, the history page, and the report figures.

The per-student timeline shows sessions along the x-axis with Present / Ambiguous / Absent as
labelled bands and ✓ / ? / ✕ glyph markers, so the chart still reads correctly in greyscale or with
colour-vision deficiency. **Colour is never the only signal.**

The chart builders return a Matplotlib `Figure` and never call `plt.show()`, so the CLI window and
the web page render the identical figure object. `tests/test_parity.py` asserts the CLI and the web
app produce the same data for the same inputs.

---

## Signature verification

<div align="center">
  <img src="report/m1-verification-evidence.png" alt="A student's best-matching reference signature above the probe signature from a later sheet, which scored 39 against the threshold of 40" width="620"/>
</div>

Each detected signature is normalized (binarize → despeckle → crop to the ink bounding box → fit to a
fixed size preserving aspect ratio), described with a **HOG descriptor**, and compared to the
student's reference signatures by **cosine similarity**. The best-scoring reference wins, and the
score is reported on a 0–100 scale with the decision threshold drawn in, so a borderline call is
visibly borderline.

Threshold `0.40` sits at the measured equal-error operating point. Measured **AUC ≈ 0.74** — good
enough to raise a flag for a human, and deliberately *not* presented as proof of forgery.

The figure above is what a signature alert actually looks like: the probe scored **39** against a
threshold of **40**. A near-miss like this is exactly why the verdict goes to a person rather than
straight into the record.

Reference signatures live under `references/<student-index>/`.

---

## CLI reference

All three commands run from the project root. Sample inputs live in `sample_signin-sheets/` — five
real Signing Sheet photos `1.jpeg`–`5.jpeg`, each with its Info File `1.xml`–`5.xml`.

### 1. Process a Signing Sheet

Detects each student's signature cell and saves the Attendance Records to the local database
(`sams.db`, created automatically on first run). The brief's exact invocation works out of the box —
`10.07.2019.png` and `info.xml` ship in the project root, and the filename's date becomes the Sheet
Identifier because this Info File carries no session date:

```bash
python sams.py 10.07.2019.png info.xml
```

Process all five samples for the full experience:

```bash
python sams.py sample_signin-sheets/1.jpeg sample_signin-sheets/1.xml
python sams.py sample_signin-sheets/2.jpeg sample_signin-sheets/2.xml
python sams.py sample_signin-sheets/3.jpeg sample_signin-sheets/3.xml
python sams.py sample_signin-sheets/4.jpeg sample_signin-sheets/4.xml
python sams.py sample_signin-sheets/5.jpeg sample_signin-sheets/5.xml
```

Flags (`sams.py` only):

| Flag | Effect |
|------|--------|
| `--no-display` | Suppresses the live stage windows |
| `--overwrite` | Replaces operator-resolved rows when reprocessing a sheet |
| `--date` | Overrides the Sheet Identifier |

Records are upserted on `(student_index, sheet_id)`, so reprocessing a sheet updates it instead of
duplicating it — and an operator's manual resolution is preserved unless `--overwrite` is passed.
Signature images are stored as **paths, never blobs**.

### 2. Query a student

Either index form works — the short roster ordinal and the full 8-digit student index return
identical records:

```bash
python infovis.py 001
python infovis.py 10000409
```

Prints every saved Attendance Record for that student and opens the per-session timeline chart with
the attendance rate. The chart window is suppressed on headless sessions.

### 3. Verify a signature

```bash
python investigate.py 001
```

Compares the student's probe signature (cropped by step 1) against their reference signatures and
reports a match verdict.

### Running fully windowless

For CI or a server with no display:

```bash
SAMS_HEADLESS=1 python sams.py 10.07.2019.png info.xml   # bash
```

```powershell
$env:SAMS_HEADLESS="1"                                    # PowerShell
```

```
set SAMS_HEADLESS=1                                       :: cmd
```

---

## Web UI pages

```bash
pip install -r requirements-web.txt
streamlit run webui/app.py
```

Run it **from the project root**, otherwise Streamlit won't find the theme in `.streamlit/` and
silently falls back to its defaults.

| Page | What it does |
|------|--------------|
| **Dashboard** | Quick actions, a date-range window, four stat tiles, the latest session's rate, and a "needs attention" panel combining low attendance with signature alerts |
| **Mark today's attendance** | Upload the sheet photo and Info File, watch the seven stages stream, review per-student results, export CSV. Ambiguous rows show the actual crop |
| **Session history** | Sessions grouped by Sheet Identifier, an attendance-trend chart, per-session rate bars, and a per-session student list |
| **Look up a student** | Student number in, the same Matplotlib timeline `infovis.py` renders out |
| **Check a signature** | Reference crop beside the sheet crop, the similarity score on a scale with the threshold marked, a plain-English verdict, and the other reference scores |

Each Streamlit page is paired with a Streamlit-free `*_logic.py` twin, so the page logic is
unit-testable without a browser.

---

## Configuration

`sams_core/config.py` is the single source for every tunable. The ones you're most likely to touch:

| Setting | Default | What it controls |
|---------|---------|------------------|
| `SAMS_DB_PATH` (env) | `sams.db` | Where the attendance database lives |
| `SAMS_OUTPUT_DIR` (env) | `output/` | Where stage images and crops are written |
| `SAMS_HEADLESS` (env) | unset | Set to `1` to suppress all windows and force the Agg backend |
| `INK_COVERAGE_PRESENT_THRESHOLD` | `0.030` | Ink coverage at or above which a cell is Present |
| `INK_COVERAGE_ABSENT_THRESHOLD` | `0.015` | Ink coverage at or below which a cell is Absent |
| `SIMILARITY_THRESHOLD` | `0.40` | Signature match cut-off (measured equal-error point) |
| `LOW_ATTENDANCE_THRESHOLD` | `75` | Dashboard "needs attention" cut-off (in `webui/dashboard_logic.py`) |

The two ink thresholds have a comfortable margin around real data: genuine signatures measured at
5.1% coverage or more, empty cells at 1.0% or less — at least 1.5× clear of the boundary on both
sides.

Roster XML is parsed with `ElementTree` and hardened against DOCTYPE and entity-expansion attacks,
since the web UI accepts uploaded files.

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

**269 tests across 25 files.** The suite is fully headless — no windows open — and self-contained.
It includes the PRD §6.3 accuracy gate proving 100% classification accuracy on all five sample
sheets against the committed ground truth, plus CLI↔web parity, accessibility, and packaging checks.

Accessibility is asserted, not eyeballed: `tests/test_webui_accessibility.py` checks that every page
works at 360 px with no horizontal scrolling and that every control is at least 44 px tall.

---

## Project structure

```
sams.py / infovis.py / investigate.py   thin CLI entry scripts (<50 lines each)
cli_display.py                          CLI rendering (windows, stdout, figures)
evaluate_detection.py                   detection accuracy harness
evaluate_verification.py                signature score-distribution harness
sams_core/                              the engine: pipeline, locate, detect,
                                        verification, repository, visualization, config
webui/                                  optional Streamlit front-end
  app.py                                page config + 5-page router
  pages/                                the five screens
  *_logic.py                            Streamlit-free logic twin per screen
sample_signin-sheets/                   five sample sheets + Info Files
10.07.2019.png + info.xml               the brief's verbatim-command inputs
references/                             COMMITTED Reference Signatures
                                        (investigate.py input — keep!)
tests/                                  pytest suite incl. the accuracy gate
docs/walkthrough/                       Playwright walkthrough + UI screenshots
docs/report/                            report figures and generator
.streamlit/config.toml                  the app theme
.github/workflows/deploy.yml            Azure deployment
output/  sams.db                        created at runtime (safe to delete)
```

---

## Deployment

Pushing to `main` (or running the workflow manually) triggers `.github/workflows/deploy.yml`, which
prepares a server-safe build and deploys it to Azure App Service (`sams-cgv`):

1. Swaps `opencv-python` for `opencv-python-headless` — no display libraries on the server.
2. Folds the web dependencies into `requirements.txt`.
3. Zips the app, excluding `.git`, `.github`, `tests`, `docs`, and the sample sheets.
4. Deploys with `azure/webapps-deploy@v3` using the `AZUREAPPSERVICE_PUBLISHPROFILE` secret.

Branch flow: `Sprint-*` → `develop` → `UAT` → `main`.

---

## Submission packaging

The prototype ZIP contains the code, the samples, `10.07.2019.png` + `info.xml`, and `references/`
(a required input — **never exclude it**). Exclude the dev-only material: `.git/`, `.venv*/`,
`__pycache__/`, `.pytest_cache/`, `output/`, `sams.db`, `.claude/`, `_bmad/`, `_bmad-output/`,
`docs/`, internal notes (`TUNING_LOG.md`, `STORY_*.md`, `IMPLEMENTATION_*.md`,
`FINAL_DELIVERY_*.md`), and the coursework brief documents. The prototype ZIP plus the MS Word
report go into the outer ZIP for LMS. A fresh unzip of the prototype ZIP satisfies the README's
Quick start with no further setup.
