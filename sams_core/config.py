import os
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# SAMS_DB_PATH / SAMS_OUTPUT_DIR env overrides exist so test suites and scripted
# runs can redirect ALL persistence away from the real working data (AD-9) —
# defaults stay relative to the project root (FR-15).
DB_PATH = Path(os.environ.get("SAMS_DB_PATH", PROJECT_ROOT / "sams.db"))
OUTPUT_DIR = Path(os.environ.get("SAMS_OUTPUT_DIR", PROJECT_ROOT / "output"))
REFERENCES_DIR = PROJECT_ROOT / "references"

# Wait this long for a concurrent writer before failing a DB operation (AD-4).
DB_BUSY_TIMEOUT_S = 10.0

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpeg", ".jpg")

# Reject degenerate inputs before the pipeline: below this, the fixed-size
# kernels (median 5px, threshold block 35px) have no meaningful signal to work
# with and cv2 failures would surface as cryptic asserts mid-run.
MIN_IMAGE_DIMENSION_PX = 200

# --- Pipeline stage tunables (AD-5): no numeric literals in sams_core/pipeline.py ---

# Denoising: median blur, chosen for speed at phone-photo resolutions (AD-5).
DENOISE_MEDIAN_KERNEL = 5  # must be odd

# Binarization: adaptive Gaussian threshold, chosen over global Otsu because the
# sample sheets show uneven desk lighting across a single photo.
THRESHOLD_BLOCK_SIZE = 35  # must be odd
THRESHOLD_C = 11

# Sheet-boundary detection (background exclusion, folded into the greyscale stage):
# segment the paper from the desk background via HSV saturation, then crop to its
# bounding box, padded outward so ink touching the table boundary is retained.
CROP_BLUR_KERNEL = (25, 25)
CROP_MORPH_KERNEL = np.ones((25, 25), dtype=np.uint8)
CROP_MIN_AREA_FRACTION = 0.5  # ignore a detected region smaller than this fraction of the photo
CROP_MIN_BBOX_DIM_FRACTION = 0.4  # a real sheet is large in BOTH dimensions; reject degenerate blobs
CROP_PADDING_PX = 30  # expand the detected bounding box outward by this many pixels

# Deskew: rotate to correct residual tilt, measured from long near-horizontal ink
# lines (the table grid) via Hough transform - robust against scattered text/marks
# that would otherwise dominate a whole-page minAreaRect fit.
DESKEW_HOUGH_RHO = 1  # Hough distance resolution (px)
DESKEW_HOUGH_THETA_RAD = np.pi / 360  # Hough angular resolution (0.5 deg)
DESKEW_HOUGH_THRESHOLD = 200
DESKEW_MIN_LINE_LENGTH_FRACTION = 0.25  # fraction of image width
DESKEW_MAX_LINE_GAP = 20
DESKEW_MAX_CANDIDATE_ANGLE_DEG = 20  # ignore near-vertical lines (table's side borders)
DESKEW_MIN_ANGLE_DEG = 0.5  # skip rotation below this angle (noise, not real skew)

# Table/Grid localization (Story 1.3): morphological line extraction + table grouping.
# Grid lines are found by opening the ink with long thin kernels (handwriting vanishes,
# printed rules survive), grouped into table regions, and the 5-column student table is
# selected below the 4-column Metadata Row band (FR-3). No pixel coordinates (SM-C1).
LOCATE_HLINE_KERNEL_DIVISOR = 15  # horizontal kernel length = image width // this
LOCATE_VLINE_KERNEL_DIVISOR = 40  # vertical kernel length = image height // this
LOCATE_MIN_LINE_KERNEL_PX = 20  # lower bound on either kernel, for small test images
LOCATE_LINE_COVERAGE_FRACTION = 0.5  # a row/col of a region is a grid line if line pixels span this fraction
LOCATE_CLUSTER_TOLERANCE_PX = 10  # merge line positions closer than this into one line
LOCATE_LINE_DRIFT_TOLERANCE_PX = 15  # residual tilt drift a line may show across its length
LOCATE_GRID_JOIN_KERNEL_PX = 11  # dilation used to connect one table's lines into one component
LOCATE_MIN_TABLE_WIDTH_FRACTION = 0.35  # a component narrower than this fraction of the image is not a table
LOCATE_STUDENT_TABLE_COLUMNS = 5  # No | Student No | Title | Student Name | Signature
LOCATE_METADATA_TABLE_COLUMNS = 4  # Date | Time | Lecturer's Name | Lecturer Signature
LOCATE_GRID_MASK_DILATION_PX = 5  # dilate detected line pixels by this to build the grid mask

# Signature detection & classification (Story 1.4): measure ink per Signature Cell.
# The classification bands at the bottom of this section were tuned during the
# 2026-07-13 review against the 30-row adjudication now committed as
# tests/data/ground_truth.csv. Provenance note: the adjudication was performed in
# the working tree BEFORE the tuning and both landed on 2026-07-16 as adjacent
# commits (ground truth first, 069f99d -> 0436aee) — the ordering is attested by
# the review record, not independently provable from timestamps. Story 1.6 owns
# the executable accuracy gate that keeps these values honest from here on.
# All values are GLOBAL across sheets (SM-C1) - never per-sheet.

# Signature column: the Signature Cell is the rightmost column of the 5-column
# Student Table. When Story 1.3's vertical-line detection succeeds, the last
# detected vertical line is used as the column's left edge. When it does not
# (no vertical lines detected), fall back to a fixed fraction of the sheet's
# width, since the Signature column is consistently the last ~1/5th to 1/4th
# of a 5-column row on the sample sheets.
# Story 1.6 tuning (see TUNING_LOG.md): visual inspection of all five sample
# sheets places the true Signature column's left edge at roughly 0.72-0.85 of
# the width; 0.72 is the honest left edge of that observed range. NOTE: the
# tuning log's diagnosis ("localization returns zero v_lines") described the
# ORIGINAL Hough-based locate.py; since the 2026-07-13 morphological rework,
# all five sample sheets localize a full 6-v-line grid and detection uses
# cell_rois - this fallback now fires only when localization genuinely fails.
DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION = 0.72  # left edge as a fraction of image width

# Spillover margin (PRD FR-4): the Signature Cell ROI is dilated outward so ink
# that overruns the printed grid line - including into the blank right margin
# of the page - is still attributed to a cell instead of being lost.
DETECT_CELL_ROW_DILATION_PX = 12  # vertical dilation applied to each row band
DETECT_RIGHT_MARGIN_PADDING_PX = 60  # extend the signature column past the last vertical line

# Connected-component noise floor: ignore specks (stray dots, paper texture,
# residual grid-mask fragments) below this pixel area before attribution runs.
DETECT_MIN_COMPONENT_AREA_PX = 25

# Per-cell inspection overlay (stage 7) rendering.
DETECT_OVERLAY_FONT_SCALE = 1.1
DETECT_OVERLAY_TEXT_THICKNESS = 3
DETECT_OVERLAY_PADDING_PX = 10

# CLI stage-window display: shrink the on-screen copy to fit a screen; saved
# artifacts keep full resolution (adapter-side tunable, used by cli_display.py).
CLI_MAX_DISPLAY_DIM = 1000

# --- Import-time validation: fail loudly HERE, not as a cryptic cv2 assert mid-run ---
for _odd_constant in ("DENOISE_MEDIAN_KERNEL", "THRESHOLD_BLOCK_SIZE"):
    if globals()[_odd_constant] % 2 == 0:
        raise ValueError(f"config.{_odd_constant} must be odd (cv2 requirement)")

# Classification bands (AD-5): coverage = attributed ink pixels / the cell's own
# (un-dilated) ROI area. coverage >= PRESENT -> Present, <= ABSENT -> Absent,
# otherwise Ambiguous (a first-class result, never coerced either way).
#
# Tuned against the 30-row adjudication committed as tests/data/ground_truth.csv
# (adjudicated before the tuning — see the provenance note at the top of this
# section and TUNING_LOG.md's 2026-07-16 addendum): across all five sample
# sheets, genuine signatures measure >= 5.1% coverage while empty cells
# (including stray fragments of a neighbouring row's stroke at the printed
# boundary) measure <= 1.0%. The bands below keep a >= 1.5x margin on each side
# of that separation; values are GLOBAL (SM-C1).
INK_COVERAGE_PRESENT_THRESHOLD = 0.030
INK_COVERAGE_ABSENT_THRESHOLD = 0.015
