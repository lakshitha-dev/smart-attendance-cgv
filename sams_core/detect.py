"""Signature detection and classification on a localized Signing Sheet.

Story 1.4: Classify each Signature Cell - Present, Absent, or Ambiguous.

- Segment handwritten ink (any pen colour, measured post-binarization - AD-5)
  in the Signature column into connected components, AFTER Story 1.3's
  grid-line mask has been applied so printed table lines are never counted
  as ink.
- Attribute each component to exactly ONE Signature Cell (majority-area
  rule over the component's own pixels, centroid tie-break) using dilated
  row ROIs so spillover - including a signature that straddles two printed
  rows - is captured. A single component is never evidence for two cells.
- Classify each cell's ink coverage against the named thresholds in
  `config.py`: Ambiguous is a first-class result, never coerced.
- Emit the 7th and final registry stage ("per-cell inspection") as ONE
  composite overlay image.
- Save one signature-cell crop per row via `artifacts.save_crop` - these
  become Epic 3's verification probes (AD-10).
"""

from dataclasses import dataclass

import cv2
import numpy as np

from sams_core import artifacts, config
from sams_core.models import AttendanceStatus, SheetResult, StageArtifact

_STATUS_COLOR = {
    # BGR-independent: these are RGB tuples, matching StageArtifact's RGB contract.
    AttendanceStatus.PRESENT: (34, 177, 76),
    AttendanceStatus.ABSENT: (220, 40, 40),
    AttendanceStatus.AMBIGUOUS: (255, 165, 0),
}


@dataclass(frozen=True)
class CellResult:
    """Detection + classification outcome for one Signature Cell (one row).

    `row_index` is the 0-based position of the row within the rows Story 1.3
    detected (top to bottom) - Story 1.5 maps this to a Student Record by row
    order, exactly as the Info File's `no` ordinals do.
    """

    row_index: int
    roi: tuple[int, int, int, int]  # (x0, y0, x1, y1) - the cell's own, un-dilated ROI
    ink_coverage: float  # attributed ink pixels / roi area
    status: AttendanceStatus
    crop: np.ndarray  # the cell's dilated ROI, cropped from the input image


@dataclass(frozen=True)
class _RowBand:
    row_index: int
    y0: int
    y1: int
    dilated_y0: int
    dilated_y1: int


def _signature_column_bounds(sheet_result: SheetResult, width: int) -> tuple[int, int]:
    """Return (x0, x1) of the Signature column, dilated into the right margin.

    Prefers the last detected vertical grid line (Story 1.3) as the column's
    left edge; falls back to a documented fraction of the image width when no
    vertical lines were detected (SM-C1: no per-sheet pixel coordinates).
    """
    v_lines = sheet_result.detected_grid_lines.get("v_lines") or []
    if v_lines:
        x0 = v_lines[-1]
    else:
        x0 = int(width * config.DETECT_SIGNATURE_COLUMN_FALLBACK_FRACTION)

    x1 = min(width, width + config.DETECT_RIGHT_MARGIN_PADDING_PX)  # margin already = image edge
    return max(0, x0), x1


def _row_bands(sheet_result: SheetResult, height: int, expected_row_count: int | None = None) -> list[_RowBand]:
    """Return the student-table row bands, each dilated vertically for spillover.

    Story 1.3's `student_table_y_range` starts right after the Metadata Row's
    header line, so it also captures the Metadata Row's own DATA line (date/
    time/lecturer + Lecturer's Signature) and the Student Table's column-header
    line ("No | Student No | ... | Signature") as if they were student rows -
    both always appear first, with irregular heights, ahead of the genuine,
    uniformly-sized student rows (observed on all five sample sheets).

    When `expected_row_count` (the Info File's student count) is smaller than
    the number of detected bands, only the LAST `expected_row_count` bands are
    kept - those are consistently the real per-student Signature Cells - and
    re-indexed from 0 so `row_index` still lines up with Story 1.5's row-order
    mapping. This does not touch Story 1.3's row-count-mismatch warning; that
    still surfaces via `SheetResult.warnings` unchanged.
    """
    if sheet_result.student_table_y_range is None:
        return []

    y0, y1 = sheet_result.student_table_y_range
    h_lines = sorted(
        y for y in (sheet_result.detected_grid_lines.get("h_lines") or []) if y0 <= y <= y1
    )
    if len(h_lines) < 2:
        return []

    row_edges = list(zip(h_lines, h_lines[1:]))
    if expected_row_count is not None and len(row_edges) > expected_row_count > 0:
        row_edges = row_edges[-expected_row_count:]

    dilation = config.DETECT_CELL_ROW_DILATION_PX
    bands = []
    for row_index, (top, bottom) in enumerate(row_edges):
        bands.append(
            _RowBand(
                row_index=row_index,
                y0=top,
                y1=bottom,
                dilated_y0=max(0, top - dilation),
                dilated_y1=min(height, bottom + dilation),
            )
        )
    return bands


def _attribute_components(
    ink_mask: np.ndarray, bands: list[_RowBand]
) -> dict[int, np.ndarray]:
    """Assign each connected ink component to exactly one row band.

    Majority-area rule: a component's pixels are counted per band (using the
    band's dilated y-range, since the column's x-range is identical for every
    row); the component is assigned wholly to the band holding the most of
    its pixels. Ties are broken by centroid proximity to the band's own
    (un-dilated) vertical centre - never split between two cells.

    Returns {row_index: boolean mask of attributed ink pixels}, same shape as
    `ink_mask`.
    """
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        ink_mask, connectivity=8
    )

    per_row_mask = {band.row_index: np.zeros_like(ink_mask, dtype=bool) for band in bands}
    if num_labels <= 1 or not bands:  # label 0 is background
        return per_row_mask

    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] < config.DETECT_MIN_COMPONENT_AREA_PX:
            continue

        component_mask = labels == label
        ys = np.nonzero(component_mask)[0]

        counts = {band.row_index: int(np.count_nonzero((ys >= band.dilated_y0) & (ys < band.dilated_y1))) for band in bands}
        best_count = max(counts.values())
        if best_count == 0:
            continue  # component falls entirely outside every row band (e.g. above/below table)

        candidates = [row_index for row_index, count in counts.items() if count == best_count]
        if len(candidates) == 1:
            winner = candidates[0]
        else:
            centroid_y = centroids[label][1]
            band_by_index = {band.row_index: band for band in bands}
            winner = min(
                candidates,
                key=lambda row_index: abs(centroid_y - (band_by_index[row_index].y0 + band_by_index[row_index].y1) / 2),
            )

        per_row_mask[winner] |= component_mask

    return per_row_mask


def _classify(coverage: float) -> AttendanceStatus:
    if coverage >= config.INK_COVERAGE_PRESENT_THRESHOLD:
        return AttendanceStatus.PRESENT
    if coverage <= config.INK_COVERAGE_ABSENT_THRESHOLD:
        return AttendanceStatus.ABSENT
    return AttendanceStatus.AMBIGUOUS


def _draw_inspection_overlay(
    base_image: np.ndarray, column_bounds: tuple[int, int], results: list[CellResult]
) -> np.ndarray:
    """Build the 7th registry stage: one composite "per-cell inspection" overlay.

    Each Signature Cell gets a colour-coded border (green/red/orange = Present/
    Absent/Ambiguous) plus a status chip. The chip is drawn vertically centred
    inside the cell's own ROI - not above it - with a solid background behind
    the text, so it never overlaps the row above and stays readable over ink.
    """
    overlay = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB) if base_image.ndim == 2 else base_image.copy()
    x0, x1 = column_bounds
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.1
    thickness = 3
    padding = 10

    for result in results:
        _, roi_y0, _, roi_y1 = result.roi
        color = _STATUS_COLOR[result.status]
        box_x1 = min(x1, overlay.shape[1] - 1)
        cv2.rectangle(overlay, (x0, roi_y0), (box_x1, roi_y1), color, 4)

        label = f"Row {result.row_index + 1}: {result.status.value} ({result.ink_coverage * 100:.1f}%)"
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        chip_x0 = x0 + padding
        chip_y_center = (roi_y0 + roi_y1) // 2
        chip_y0 = chip_y_center - text_h // 2 - padding
        chip_y1 = chip_y_center + text_h // 2 + baseline + padding
        chip_x1 = min(box_x1 - 2, chip_x0 + text_w + 2 * padding)

        cv2.rectangle(overlay, (chip_x0, chip_y0), (chip_x1, chip_y1), color, -1)
        text_color = (255, 255, 255)
        cv2.putText(
            overlay,
            label,
            (chip_x0 + padding, chip_y_center + text_h // 2),
            font,
            font_scale,
            text_color,
            thickness,
            cv2.LINE_AA,
        )

    return overlay


def detect_signatures(
    binary_image: np.ndarray, sheet_result: SheetResult, expected_row_count: int | None = None
) -> tuple[list[CellResult], StageArtifact]:
    """Detect and classify one Signature Cell per detected student-table row.

    Args:
        binary_image: binarized/deskewed image, post grid-line masking is
            applied internally via `sheet_result.detected_grid_lines["mask"]`
            (Story 1.3, AD-8).
        sheet_result: table structure detected in Story 1.3.
        expected_row_count: the Info File's student count. When given and
            smaller than the number of bands Story 1.3 detected, only the
            trailing `expected_row_count` bands are treated as real Signature
            Cells (see `_row_bands`) - without this, the Metadata Row's
            signature line and the Student Table's own header line get
            misdetected as student rows 1 and 2.

    Returns:
        (cell_results, inspection_stage)
        - cell_results: one `CellResult` per detected row, in row order
          (Story 1.5 maps these to Student Records by that same order).
        - inspection_stage: the 7th `StageArtifact` ("per-cell-inspection").
    """
    height, width = binary_image.shape
    grid_mask = sheet_result.detected_grid_lines.get("mask")

    # Ink = binarized foreground (dark pen strokes on light paper), with the
    # printed grid mask removed (Story 1.3, AD-8) so table lines are never ink.
    ink = cv2.bitwise_not(binary_image)
    if grid_mask is not None:
        ink = cv2.bitwise_and(ink, cv2.bitwise_not(grid_mask))
    ink_mask = (ink > 0).astype(np.uint8) * 255

    column_x0, column_x1 = _signature_column_bounds(sheet_result, width)
    bands = _row_bands(sheet_result, height, expected_row_count)

    # Only the Signature column is in scope for this story; blank out ink
    # anywhere else so it can never be attributed to a Signature Cell.
    column_ink_mask = np.zeros_like(ink_mask)
    column_ink_mask[:, column_x0:column_x1] = ink_mask[:, column_x0:column_x1]

    per_row_ink = _attribute_components(column_ink_mask, bands)

    results: list[CellResult] = []
    for band in bands:
        roi = (column_x0, band.y0, column_x1, band.y1)
        cell_area = max(1, (column_x1 - column_x0) * (band.y1 - band.y0))
        attributed_pixels = int(np.count_nonzero(per_row_ink[band.row_index]))
        coverage = attributed_pixels / cell_area
        status = _classify(coverage)

        crop = binary_image[band.dilated_y0:band.dilated_y1, column_x0:column_x1]

        results.append(
            CellResult(
                row_index=band.row_index,
                roi=roi,
                ink_coverage=coverage,
                status=status,
                crop=crop,
            )
        )

    inspection_image = _draw_inspection_overlay(binary_image, (column_x0, column_x1), results)
    inspection_stage = StageArtifact(
        order=7, slug="per-cell-inspection", label="Per-Cell Inspection", image=inspection_image
    )

    return results, inspection_stage


def save_crops(sheet_id: str, cell_results: list[CellResult], student_indices: list[str] | None = None):
    """Save one crop per `CellResult` via `artifacts.save_crop` (Story 1.4, AD-10).

    `student_indices`, when given, must be parallel to Story 1.3's detected
    rows and supplies the canonical 8-digit Student Index used to name each
    file (`output/<Sheet Identifier>/crops/<student_index>.png`) - this is how
    Epic 3 finds its verification probes. Before Student Records are mapped
    (Story 1.5), callers may omit it; crops then fall back to a zero-padded
    row ordinal so nothing is lost.

    Returns the list of paths written, in row order.
    """
    paths = []
    for result in cell_results:
        if student_indices is not None:
            identifier = student_indices[result.row_index]
        else:
            identifier = f"{result.row_index + 1:03d}"
        paths.append(artifacts.save_crop(sheet_id, identifier, result.crop))
    return paths
