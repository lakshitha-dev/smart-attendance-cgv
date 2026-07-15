import numpy as np
import pytest

import sams_core.artifacts as artifacts
import sams_core.config as config
import sams_core.detect as detect
from sams_core.models import AttendanceStatus, SheetResult, StageArtifact

WIDTH, HEIGHT = 300, 300
COLUMN_X0 = 200  # last vertical grid line -> Signature column starts here
ROW_HEIGHT = 50
H_LINES = [100, 150, 200, 250, 300]  # 4 student rows: [100-150), [150-200), [200-250), [250-300)


def _blank_binary_image() -> np.ndarray:
    """An all-white (paper, no ink) binarized image, per pipeline's WHITE=paper/BLACK=ink contract."""
    return np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)


def _sheet_result(h_lines=None, v_lines=None, grid_mask=None) -> SheetResult:
    return SheetResult(
        warnings=[],
        detected_row_count=len(H_LINES) - 1,
        metadata_row_y_range=(0, 100),
        student_table_y_range=(100, 300),
        detected_grid_lines={
            "h_lines": H_LINES if h_lines is None else h_lines,
            "v_lines": [COLUMN_X0] if v_lines is None else v_lines,
            "mask": np.zeros((HEIGHT, WIDTH), dtype=np.uint8) if grid_mask is None else grid_mask,
        },
    )


def _draw_ink(image: np.ndarray, y0: int, y1: int, x0: int, x1: int) -> np.ndarray:
    """Paint a black (ink) rectangle onto a copy of `image`."""
    out = image.copy()
    out[y0:y1, x0:x1] = 0
    return out


# --- Attribution (majority-area rule + straddling signatures) --------------------


def test_signature_fully_inside_one_row_is_attributed_to_that_row_only():
    image = _blank_binary_image()
    image = _draw_ink(image, y0=160, y1=190, x0=210, x1=260)  # entirely inside row 1 [150,200)

    results, _ = detect.detect_signatures(image, _sheet_result())

    covered_rows = [r.row_index for r in results if r.ink_coverage > 0]
    assert covered_rows == [1]


def test_straddling_signature_counts_for_exactly_one_row_not_two():
    """A signature overrunning the printed line between two rows (dev note: samples 1 and 5)
    must be evidence for exactly one cell, never both."""
    image = _blank_binary_image()
    # One connected ink blob straddling the row0/row1 boundary at y=150, with most of its
    # area in row0 [100,150).
    image = _draw_ink(image, y0=120, y1=155, x0=210, x1=260)
    blob_area = (155 - 120) * (260 - 210)

    results, _ = detect.detect_signatures(image, _sheet_result())
    by_row = {r.row_index: r for r in results}

    rows_with_ink = [r.row_index for r in results if r.ink_coverage > 0]
    assert rows_with_ink == [0], "the straddling component must be wholly attributed to one row"

    attributed_pixels = round(by_row[0].ink_coverage * (WIDTH - COLUMN_X0) * ROW_HEIGHT)
    assert attributed_pixels == blob_area  # no pixels lost, none double-counted


def test_two_separate_signatures_attribute_independently():
    image = _blank_binary_image()
    image = _draw_ink(image, y0=110, y1=140, x0=210, x1=260)  # row 0
    image = _draw_ink(image, y0=210, y1=240, x0=210, x1=260)  # row 2

    results, _ = detect.detect_signatures(image, _sheet_result())
    covered_rows = sorted(r.row_index for r in results if r.ink_coverage > 0)

    assert covered_rows == [0, 2]


def test_ink_outside_signature_column_is_ignored():
    image = _blank_binary_image()
    image = _draw_ink(image, y0=110, y1=140, x0=0, x1=100)  # left of the Signature column

    results, _ = detect.detect_signatures(image, _sheet_result())

    assert all(r.ink_coverage == 0 for r in results)


def test_grid_mask_ink_is_never_counted():
    image = _blank_binary_image()
    grid_mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    grid_mask[148:152, :] = 255  # the printed row-boundary line at y=150

    image = _draw_ink(image, y0=148, y1=152, x0=210, x1=260)  # ink lies exactly on the grid line

    results, _ = detect.detect_signatures(image, _sheet_result(grid_mask=grid_mask))

    assert all(r.ink_coverage == 0 for r in results)


def test_no_vertical_lines_falls_back_to_documented_fraction():
    image = _blank_binary_image()
    fallback_x0 = int(WIDTH * config.DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION)
    image = _draw_ink(image, y0=110, y1=140, x0=fallback_x0 + 5, x1=fallback_x0 + 40)

    results, _ = detect.detect_signatures(image, _sheet_result(v_lines=[]))

    assert any(r.ink_coverage > 0 for r in results)


# --- Classification bands (Ambiguous is first-class, never coerced) --------------


def test_classify_present_at_or_above_threshold():
    assert detect._classify(config.INK_COVERAGE_PRESENT_THRESHOLD) == AttendanceStatus.PRESENT
    assert detect._classify(config.INK_COVERAGE_PRESENT_THRESHOLD + 0.5) == AttendanceStatus.PRESENT


def test_classify_absent_at_or_below_threshold():
    assert detect._classify(config.INK_COVERAGE_ABSENT_THRESHOLD) == AttendanceStatus.ABSENT
    assert detect._classify(0.0) == AttendanceStatus.ABSENT


def test_classify_between_thresholds_is_ambiguous():
    midpoint = (config.INK_COVERAGE_PRESENT_THRESHOLD + config.INK_COVERAGE_ABSENT_THRESHOLD) / 2
    assert detect._classify(midpoint) == AttendanceStatus.AMBIGUOUS


def test_empty_cell_is_classified_absent():
    image = _blank_binary_image()  # no ink anywhere

    results, _ = detect.detect_signatures(image, _sheet_result())

    assert all(r.status == AttendanceStatus.ABSENT for r in results)


# --- 7th registry stage: one composite "per-cell inspection" overlay ------------


def test_detect_signatures_emits_the_7th_stage_artifact():
    image = _blank_binary_image()

    _, inspection_stage = detect.detect_signatures(image, _sheet_result())

    assert isinstance(inspection_stage, StageArtifact)
    assert (inspection_stage.order, inspection_stage.slug, inspection_stage.label) == (
        7,
        "per-cell-inspection",
        "Per-Cell Inspection",
    )
    assert inspection_stage.image.ndim == 3  # RGB composite, never greyscale


def test_one_cell_result_per_detected_row():
    image = _blank_binary_image()

    results, _ = detect.detect_signatures(image, _sheet_result())

    assert [r.row_index for r in results] == list(range(len(H_LINES) - 1))


def test_expected_row_count_trims_leading_metadata_and_header_bands():
    """FALLBACK PATH ONLY (no cell_rois supplied): when a caller provides raw
    h_lines, leading bands are header/metadata lines rather than student rows,
    so when the Info File's student count is smaller than the band count only
    the trailing bands (the genuine student rows) are kept. The production
    path receives header-excluded rows via cell_rois and ignores this trim."""
    h_lines = [0, 60, 95, 145, 195, 245]  # 5 bands: 2 leading (irregular) + 3 real rows
    image = _blank_binary_image()
    image = _draw_ink(image, y0=100, y1=140, x0=210, x1=260)  # ink in the first "real" row

    sheet_result = _sheet_result(h_lines=h_lines)
    sheet_result.student_table_y_range = (0, 245)

    results, _ = detect.detect_signatures(image, sheet_result, expected_row_count=3)

    assert len(results) == 3
    assert results[0].ink_coverage > 0  # re-indexed to 0, not its original band index of 2


def test_expected_row_count_no_op_when_band_count_already_matches():
    image = _blank_binary_image()

    results, _ = detect.detect_signatures(image, _sheet_result(), expected_row_count=len(H_LINES) - 1)

    assert len(results) == len(H_LINES) - 1


# --- Production path: cell_rois supplied by locate (Story 1.3) -------------------


def _sheet_result_with_cell_rois(rows=None, signature_column=(200, 260), grid_mask=None) -> SheetResult:
    """SheetResult as the real pipeline builds it: geometry via cell_rois."""
    default_rows = [(100, 150), (150, 200), (200, 250), (250, 300)]
    result = _sheet_result(grid_mask=grid_mask)
    result.cell_rois = {
        "rows": default_rows if rows is None else rows,
        "signature_column": signature_column,
        "table_bbox": (0, 100, 260, 300),
    }
    return result


def test_cell_rois_rows_are_used_verbatim_and_straddle_attributes_to_one_row():
    image = _blank_binary_image()
    image = _draw_ink(image, y0=120, y1=155, x0=210, x1=250)  # straddles rows 0/1, majority row 0

    results, _ = detect.detect_signatures(image, _sheet_result_with_cell_rois())

    rows_with_ink = [r.row_index for r in results if r.ink_coverage > 0]
    assert rows_with_ink == [0]
    assert len(results) == 4


def test_empty_cell_rois_rows_yields_zero_results_not_fallback():
    """Regression: `rows: []` (header-only table) must NOT fall back to raw
    h_lines and resurrect the header band as a phantom student row."""
    image = _blank_binary_image()
    image = _draw_ink(image, y0=110, y1=140, x0=210, x1=260)  # ink that a fallback would count

    results, _ = detect.detect_signatures(image, _sheet_result_with_cell_rois(rows=[]))

    assert results == []


def test_margin_spillover_is_captured_but_denominator_stays_unpadded():
    """Ink past the printed column border (within the +margin padding) counts
    toward the cell, while coverage divides by the UN-padded cell area."""
    image = _blank_binary_image()
    image = _draw_ink(image, y0=110, y1=140, x0=265, x1=290)  # right of column x1=260, inside padding

    results, _ = detect.detect_signatures(image, _sheet_result_with_cell_rois())
    by_row = {r.row_index: r for r in results}

    ink_area = (140 - 110) * (290 - 265)
    unpadded_area = (260 - 200) * (150 - 100)
    assert by_row[0].ink_coverage == pytest.approx(ink_area / unpadded_area)
    assert by_row[0].roi == (200, 100, 260, 150)  # un-dilated ROI, documented contract


def test_crops_have_grid_lines_whited_out():
    """Crops are Epic 3's probes: printed border pixels must not appear in them."""
    image = _blank_binary_image()
    grid_mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    grid_mask[148:152, :] = 255
    image = _draw_ink(image, y0=148, y1=152, x0=200, x1=260)  # ink exactly on the printed line

    results, _ = detect.detect_signatures(image, _sheet_result_with_cell_rois(grid_mask=grid_mask))

    for result in results:
        assert result.crop.min() == 255, "printed grid ink leaked into a saved crop"


# --- Crops (Story 1.4 AD-10 / Epic 3 probes) -------------------------------------


@pytest.fixture(autouse=True)
def _redirect_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", tmp_path)
    return tmp_path


def test_save_crops_without_student_indices_uses_row_ordinal(tmp_path):
    image = _blank_binary_image()
    results, _ = detect.detect_signatures(image, _sheet_result())

    paths = detect.save_crops("2019-05-31", results)

    assert paths[0] == tmp_path / "2019-05-31" / "crops" / "001.png"
    assert all(path.is_file() for path in paths)


def test_save_crops_with_student_indices_names_by_index(tmp_path):
    image = _blank_binary_image()
    results, _ = detect.detect_signatures(image, _sheet_result())
    indices = [f"1000930{i}" for i in range(len(results))]

    paths = detect.save_crops("2019-05-31", results, student_indices=indices)

    assert paths[0].name == f"{indices[0]}.png"
    assert all(path.is_file() for path in paths)


def test_save_crops_short_index_list_falls_back_to_ordinal_without_error(tmp_path):
    image = _blank_binary_image()
    results, _ = detect.detect_signatures(image, _sheet_result())

    paths = detect.save_crops("2019-05-31", results, student_indices=["10009301"])  # shorter than rows

    assert paths[0].name == "10009301.png"
    assert all(p.name == f"{i + 2:03d}.png" for i, p in enumerate(paths[1:]))
    assert all(path.is_file() for path in paths)
