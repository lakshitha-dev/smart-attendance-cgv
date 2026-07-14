from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "sams.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REFERENCES_DIR = PROJECT_ROOT / "references"

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpeg", ".jpg")

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
CROP_PADDING_PX = 30  # expand the detected bounding box outward by this many pixels

# Deskew: rotate to correct residual tilt, measured from long near-horizontal ink
# lines (the table grid) via Hough transform - robust against scattered text/marks
# that would otherwise dominate a whole-page minAreaRect fit.
DESKEW_HOUGH_THRESHOLD = 200
DESKEW_MIN_LINE_LENGTH_FRACTION = 0.25  # fraction of image width
DESKEW_MAX_LINE_GAP = 20
DESKEW_MAX_CANDIDATE_ANGLE_DEG = 20  # ignore near-vertical lines (table's side borders)
DESKEW_MIN_ANGLE_DEG = 0.5  # skip rotation below this angle (noise, not real skew)

# Table/Grid localization (Story 1.3): detect the metadata row and student table structure.
# Parameters tune Hough-based line detection to find the table's horizontal and vertical grid.
LOCATE_HOUGH_THRESHOLD = 150  # threshold for Hough line detection (higher = fewer, stronger lines)
LOCATE_MIN_LINE_LENGTH_FRACTION = 0.4  # fraction of image width/height for min line length
LOCATE_MAX_LINE_GAP = 20  # max gap between line segments before they're broken
LOCATE_MIN_VERTICAL_LINE_WIDTH = 0.05  # fraction of image width; lines shorter than this ignored
LOCATE_GRID_MASK_THICKNESS = 2  # pixels to mask out around detected grid lines (no hardcoded coords; SM-C1)

