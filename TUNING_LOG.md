> **ADDENDUM (2026-07-16, post-merge review) — READ THIS FIRST.**
> The diagnosis below was written against the ORIGINAL Hough-based `locate.py` and is
> superseded on every material point by the 2026-07-13 morphological localization rework
> merged from `fix-localization-detection`:
>
> - **Gate status: GREEN — 30/30 (100%) on all five sheets** (`pytest tests/test_accuracy.py`).
>   The "RED / 76.7%" status below predates the rework; do NOT activate the descope ladder from it.
> - Localization now detects the full 6-v-line grid on all five sheets; detection uses
>   `cell_rois`, so `DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION` (tuned below) is a
>   rarely-exercised fallback, untested on current geometry — re-validate it if
>   localization ever fails on a real sheet.
> - The `LOCATE_HOUGH_*` constants recommended below NO LONGER EXIST; the current
>   tunables are the `LOCATE_*` morphological family in `sams_core/config.py`.
> - The classification bands were retuned 0.020/0.006 → **0.030/0.015** during the
>   2026-07-13 review (commit 0436aee), against the same 30-row adjudication this log's
>   protocol demands: measured separation was genuine ink >= 5.1% vs empty-cell
>   noise <= 1.0%, and the chosen bands keep >= 1.5x margin on each side. The
>   statement below that the bands were "left unchanged" described the pre-rework state.

# Story 1.6 Tuning Log — accuracy gate (SM-1..SM-3)

**Status: gate is RED.** `pytest tests/test_accuracy.py::test_sm1_classification_accuracy_on_non_disputed_rows`
fails: **76.7% (23/30)** non-Disputed rows correctly classified, against the
100% required by SM-1. SM-2 (CLI smoke) and SM-3 (7-stage contract) pass.

This is reported honestly rather than forced green. Per SM-C1 and the
instructions for this story, only global constants in `config.py` may move —
no per-sheet coordinates, no per-image thresholds. That constraint is
respected below, and it is not enough to close the gap. **The remaining
failure is a Story 1.3 defect, not a tuning problem.**

## Root cause

`sams_core/locate.py`'s `_detect_grid_lines` returns `v_lines: []` (zero
vertical grid lines) on **all five** real sample sheets. Confirmed by
inspection on this branch:

```
sheet 1: v_lines=[]   sheet 2: v_lines=[]   sheet 3: v_lines=[]
sheet 4: v_lines=[]   sheet 5: v_lines=[]
```

Because no vertical line is ever found, `detect.py`'s
`_signature_column_bounds` always falls back to
`DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION` for the Signature column's left
edge, instead of using the real detected column boundary. Visual inspection
of all five sheets at full resolution places the true column's left edge at
roughly **0.72–0.85** of the image width — the fallback constant was `0.78`,
which sits *inside* the real column and truncates the left half of every
signature (where pen strokes start), while the ROI's right edge still runs to
the image margin, inflating the coverage denominator with blank space.

Measured on sheet 3 before this fix (fallback = 0.78):

| row | truth | ink coverage |
| --- | --- | --- |
| 0 | Present (signed) | 0.82% |
| 1 | Absent (empty) | 0.92% |
| 2 | Absent (empty) | 0.95% |

**A signed row measured less ink than an empty one.** The ordering between
Present and Absent is inverted for at least some rows on some sheets, and no
single global coverage threshold can separate an inverted distribution.

## What was tried (global constants only, SM-C1)

`DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION` was swept across the full 0–1
range against all five sheets (30 scored rows) using the existing
classification thresholds:

| fraction | accuracy |
| --- | --- |
| 0.40 | inflated — see caveat below |
| 0.60 | 86.7% — inflated, see caveat below |
| 0.70 | 83.3% |
| **0.72 (adopted)** | **76.7%** |
| 0.75 | 66.7% |
| 0.78 (previous default) | 60.0% |
| 0.80 | 46.7% |
| 0.85 | 13.3% |

Fractions below ~0.70 drift the ROI out of the Signature column entirely and
into the **Student Name** column. Accuracy rises there, but only because that
column's ink coincidentally correlates with attendance in this five-sheet
sample — the ROI is no longer measuring signatures at all. Adopting that
value would be curve-fitting the test, not fixing detection, so it was
**deliberately rejected** even though it scores higher.

Within the diagnosed true column range (0.72–0.85), coverage distributions
for Present vs. Absent rows were dumped and a threshold search was run at
`fraction=0.72`:

- Present coverages ranged 1.56%–16.9%
- Absent coverages ranged 1.33%–3.80%

These ranges **overlap** (e.g., a Present row at 1.56% vs. an Absent row at
3.80%) — no threshold pair separates them cleanly. The best-scoring threshold
pair found by brute-force search was a near-zero-width band
(`absent≈1.4%`, `present≈1.5%`), which would leave almost no room for the
Ambiguous status to ever fire. That is itself a form of overfitting to this
exact five-sheet sample (SM-C1: Ambiguous must stay first-class, not be
squeezed out to chase a number), so it was **not adopted** either.

## Change actually applied

`sams_core/config.py`:

```
DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION: 0.78 -> 0.72
```

0.72 is the left edge of the visually-diagnosed true column range — the most
defensible honest value, not a value chosen to maximize the test score.
`INK_COVERAGE_PRESENT_THRESHOLD` (0.020) and `INK_COVERAGE_ABSENT_THRESHOLD`
(0.006) were left unchanged; tightening them further only improves the score
by memorizing this sample's specific coverage distribution, not by fixing the
underlying signal.

**Result: 60.0% → 76.7% (18/30 → 23/30).** A genuine, defensible improvement.
The remaining 7 misclassifications are the direct consequence of the
row/column ROI still being wrong on some sheets (both the column's left edge
in this fallback path, and in a couple of cases the fallback-derived ROI
crossing into a neighbouring row's ink because `locate.py` also mis-detects
`h_lines`, producing extra spurious bands — see `SheetResult.warnings`
below).

## For the Story 1.3 owner

On every one of the five sample sheets, `SheetResult.warnings` reports a
row-count mismatch (e.g. `"Detected 8 student rows, Info File has 6
students"`). `detect.py`'s `expected_row_count` trimming keeps only the
*trailing* N bands, which works when the extra bands are always leading
(the Metadata Row + Student Table header, per its own dev note) — but the
persistent `v_lines: []` result means the Signature column position used for
*every* row is the same crude fallback fraction, not the real per-sheet
column. Fixing `locate._detect_grid_lines` so it actually returns non-empty
`v_lines` on these five sheets (the Hough parameters in `config.py` —
`LOCATE_HOUGH_THRESHOLD`, `LOCATE_MIN_LINE_LENGTH_FRACTION`,
`LOCATE_MIN_VERTICAL_LINE_WIDTH` — are all global-constant candidates worth
revisiting) is very likely what closes this gate the rest of the way; this
tuning pass could not go further without violating SM-C1 or the Story 1.3/1.4
ownership boundary.

## Sprint impact

Per the sprint plan, a red gate at Day 5 activates the descope ladder. This
is a Story 1.3 blocker, not a Story 1.5/1.6 scope gap: Story 1.5's persistence
chain (mapping, repository, `process_sheet`) is fully implemented and unit
tested independent of this gate.
