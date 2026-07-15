"""Story 1.3 unit tests: synthetic-sheet table localization.

Synthetic sheets are drawn (white paper, black 3px grid lines) so every
geometric expectation is exact and no sample-photo variance leaks in:
a 4-column Metadata Row band on top, a 5-column Student Table below it
(header row + N student rows), per the FR-3 layout.
"""

import numpy as np
import pytest

import sams_core.config as config
from sams_core import locate

WIDTH, HEIGHT = 700, 900
LINE_THICKNESS = 3

# Metadata table: 4 columns (5 v-lines), one data row (2 h-lines).
META_H = [50, 130]
META_V = [50, 200, 300, 500, 650]

# Student table: 5 columns (6 v-lines); header row + 3 student rows (5 h-lines).
STUD_H = [180, 250, 320, 390, 460]
STUD_V = [50, 130, 260, 340, 500, 650]
STUDENT_ROWS = len(STUD_H) - 2  # minus header row
SIGNATURE_COLUMN = (STUD_V[-2], STUD_V[-1])


def _draw_table(image: np.ndarray, h_lines: list[int], v_lines: list[int]) -> None:
    x0, x1 = v_lines[0], v_lines[-1]
    y0, y1 = h_lines[0], h_lines[-1]
    for y in h_lines:
        image[y : y + LINE_THICKNESS, x0:x1] = 0
    for x in v_lines:
        image[y0:y1, x : x + LINE_THICKNESS] = 0


def _synthetic_sheet(with_metadata: bool = True) -> np.ndarray:
    image = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
    if with_metadata:
        _draw_table(image, META_H, META_V)
    _draw_table(image, STUD_H, STUD_V)
    return image


# --- FR-3 selection mechanism -----------------------------------------------------


def test_selects_five_column_table_below_metadata_band():
    result, overlay = locate.locate_table(_synthetic_sheet(), STUDENT_ROWS)

    assert result.metadata_row_y_range is not None
    assert result.student_table_y_range is not None
    assert result.metadata_row_y_range[0] < result.student_table_y_range[0]
    assert result.detected_row_count == STUDENT_ROWS
    assert overlay.ndim == 3  # RGB stage-6 artifact


def test_header_row_is_excluded_from_student_rows():
    result, _ = locate.locate_table(_synthetic_sheet(), STUDENT_ROWS)

    rows = result.cell_rois["rows"]
    assert len(rows) == STUDENT_ROWS
    # First student row starts at the SECOND horizontal line (below the header).
    assert rows[0][0] == pytest.approx(STUD_H[1], abs=10)
    assert rows[0][0] > STUD_H[0] + 20


def test_signature_column_is_span_of_last_two_vertical_lines():
    result, _ = locate.locate_table(_synthetic_sheet(), STUDENT_ROWS)

    x0, x1 = result.cell_rois["signature_column"]
    assert x0 == pytest.approx(SIGNATURE_COLUMN[0], abs=10)
    assert x1 == pytest.approx(SIGNATURE_COLUMN[1], abs=10)


def test_row_count_mismatch_lands_in_warnings_not_exceptions():
    result, _ = locate.locate_table(_synthetic_sheet(), STUDENT_ROWS + 3)

    assert any(
        f"Detected {STUDENT_ROWS} student rows, Info File has {STUDENT_ROWS + 3}" in w
        for w in result.warnings
    )


def test_matching_row_count_produces_no_mismatch_warning():
    result, _ = locate.locate_table(_synthetic_sheet(), STUDENT_ROWS)

    assert not any("student rows, Info File has" in w for w in result.warnings)


# --- Degraded inputs ---------------------------------------------------------------


def test_blank_sheet_warns_and_reports_zero_rows():
    blank = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)

    result, _ = locate.locate_table(blank, STUDENT_ROWS)

    assert result.detected_row_count == 0
    assert result.cell_rois is None
    assert any("No student table structure detected" in w for w in result.warnings)
    assert any(f"Info File has {STUDENT_ROWS}" in w for w in result.warnings)


def test_missing_metadata_band_still_selects_student_table_with_warning():
    result, _ = locate.locate_table(_synthetic_sheet(with_metadata=False), STUDENT_ROWS)

    assert result.detected_row_count == STUDENT_ROWS
    assert result.metadata_row_y_range is None
    assert any("Metadata Row band not separately detected" in w for w in result.warnings)


def test_fallback_selected_table_does_not_publish_cell_rois():
    """A table that is not genuinely 5-column must not offer cell geometry —
    its 'last column' could be a stray stroke."""
    image = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
    _draw_table(image, STUD_H, [50, 300, 650])  # 2 columns, multi-row

    result, _ = locate.locate_table(image, STUDENT_ROWS)

    assert result.cell_rois is None
    assert any("fallback" in w for w in result.warnings)


# --- Grid mask correctness (regression: signature strokes must survive) -----------


def test_grid_mask_covers_printed_table_lines():
    result, _ = locate.locate_table(_synthetic_sheet(), STUDENT_ROWS)

    mask = result.detected_grid_lines["mask"]
    assert mask[STUD_H[2] + 1, 400] == 255  # a printed row line
    assert mask[300, STUD_V[-1] + 1] == 255  # a printed column line


def test_long_signature_stroke_inside_a_cell_is_not_masked_as_grid():
    """A straight signature underline long enough to survive the morphological
    opening must NOT be treated as a printed border (it is ink, and it must
    stay in the crops)."""
    image = _synthetic_sheet()
    stroke_y = (STUD_H[1] + STUD_H[2]) // 2  # mid-cell, far from any printed line
    image[stroke_y : stroke_y + LINE_THICKNESS, 510:640] = 0  # 130px underline

    result, _ = locate.locate_table(image, STUDENT_ROWS)

    mask = result.detected_grid_lines["mask"]
    assert mask[stroke_y + 1, 570] == 0, "signature stroke wrongly absorbed into the grid mask"
