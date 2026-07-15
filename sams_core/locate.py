"""Table localization: detect student table and signature cells on a deskewed signing sheet.

Story 1.3: Locate the student table and signature cells.
- Extract printed grid lines morphologically (long horizontal / vertical ink runs)
- Group them into table regions and select, per FR-3, the 5-column Student Table
  (No | Student No | Title | Student Name | Signature) that sits BELOW the
  4-column Metadata Row band (Date | Time | Lecturer's Name | Signature)
- Exclude the Student Table's own printed header row from the student rows
- Detect a dynamic row count; report mismatches vs the Info File as warnings,
  never exceptions (AD-6)
- Produce a pixel-accurate grid mask from the detected TABLE line positions only
  (Story 1.4 must never count printed borders as ink - and a long handwriting
  stroke elsewhere on the page must never be mistaken for a printed border)
- Produce an RGB overlay showing the detected structure (stage 6, AD-3)

No OCR of printed header text (the template contains typos) and no hard-coded
pixel coordinates (SM-C1): everything below is derived from line geometry.
"""

from dataclasses import dataclass

import cv2
import numpy as np

from sams_core import config
from sams_core.models import SheetResult


@dataclass(frozen=True)
class _Table:
    """One detected grid region: its component bbox and internal line positions."""

    x0: int
    y0: int
    x1: int
    y1: int
    h_lines: list[int]  # y-coordinates of horizontal lines, top to bottom
    v_lines: list[int]  # x-coordinates of vertical lines, left to right

    @property
    def column_count(self) -> int:
        return max(0, len(self.v_lines) - 1)

    @property
    def row_count(self) -> int:
        return max(0, len(self.h_lines) - 1)

    @property
    def line_bbox(self) -> tuple[int, int, int, int]:
        """Bbox spanned by the detected lines themselves - unlike the component
        bbox, this is not inflated by the join dilation."""
        return (min(self.v_lines), min(self.h_lines), max(self.v_lines), max(self.h_lines))


def _extract_line_masks(binary_image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Extract printed grid lines as two binary masks (horizontal, vertical).

    Morphological opening with long thin kernels keeps only ink runs at least
    as long as the kernel - handwriting and text vanish, table rules survive.
    """
    height, width = binary_image.shape
    ink = cv2.bitwise_not(binary_image)  # printed lines are dark -> white in `ink`

    h_kernel_len = max(config.LOCATE_MIN_LINE_KERNEL_PX, width // config.LOCATE_HLINE_KERNEL_DIVISOR)
    v_kernel_len = max(config.LOCATE_MIN_LINE_KERNEL_PX, height // config.LOCATE_VLINE_KERNEL_DIVISOR)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_len, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_len))

    h_mask = cv2.morphologyEx(ink, cv2.MORPH_OPEN, h_kernel)
    v_mask = cv2.morphologyEx(ink, cv2.MORPH_OPEN, v_kernel)
    return h_mask, v_mask


def _dilate_for_projection(h_mask: np.ndarray, v_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Dilate each mask along its perpendicular axis, ONCE, on the full image.

    Residual tilt/perspective makes a long line drift a few pixels across its
    perpendicular axis, smearing its projection below the coverage threshold.
    Dilating globally (rather than per region) also keeps border lines
    symmetric - a region-cropped dilation clips edge lines on one side and
    biases their clustered position inward.
    """
    drift = 2 * config.LOCATE_LINE_DRIFT_TOLERANCE_PX + 1
    h_proj = cv2.dilate(h_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (1, drift)))
    v_proj = cv2.dilate(v_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (drift, 1)))
    return h_proj, v_proj


def _cluster_positions(positions: np.ndarray, tolerance: int) -> list[int]:
    """Collapse consecutive pixel positions into one representative per line."""
    if positions.size == 0:
        return []
    clusters: list[list[int]] = [[int(positions[0])]]
    for pos in positions[1:]:
        if int(pos) - clusters[-1][-1] <= tolerance:
            clusters[-1].append(int(pos))
        else:
            clusters.append([int(pos)])
    return [int(np.mean(cluster)) for cluster in clusters]


def _lines_in_region(
    h_proj: np.ndarray, v_proj: np.ndarray, x0: int, y0: int, x1: int, y1: int
) -> tuple[list[int], list[int]]:
    """Find line positions inside a bbox by projecting each (pre-dilated) mask.

    A horizontal line is a row of the region where horizontal-mask pixels span
    a large fraction of the region's width (and vice versa for vertical).
    """
    width = max(1, x1 - x0)
    height = max(1, y1 - y0)

    row_coverage = (h_proj[y0:y1, x0:x1] > 0).sum(axis=1) / width
    col_coverage = (v_proj[y0:y1, x0:x1] > 0).sum(axis=0) / height

    h_positions = np.nonzero(row_coverage >= config.LOCATE_LINE_COVERAGE_FRACTION)[0] + y0
    v_positions = np.nonzero(col_coverage >= config.LOCATE_LINE_COVERAGE_FRACTION)[0] + x0

    tolerance = config.LOCATE_CLUSTER_TOLERANCE_PX
    return _cluster_positions(h_positions, tolerance), _cluster_positions(v_positions, tolerance)


def _find_tables(
    binary_image: np.ndarray,
    h_mask: np.ndarray,
    v_mask: np.ndarray,
    h_proj: np.ndarray,
    v_proj: np.ndarray,
) -> list[_Table]:
    """Group grid-line pixels into table regions, top to bottom.

    Component grouping runs on the RAW line masks (+ the small join kernel):
    joining the drift-dilated projections would bridge the Metadata Row band
    into the Student Table and produce phantom leading "student rows". The
    dilated projections are used only to read line positions inside a region.
    """
    height, width = binary_image.shape
    grid = cv2.bitwise_or(h_mask, v_mask)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (config.LOCATE_GRID_JOIN_KERNEL_PX, config.LOCATE_GRID_JOIN_KERNEL_PX)
    )
    joined = cv2.dilate(grid, kernel)

    n_labels, _, stats, _ = cv2.connectedComponentsWithStats(joined, connectivity=8)
    tables = []
    for label in range(1, n_labels):
        x, y, w, h = (
            stats[label, cv2.CC_STAT_LEFT],
            stats[label, cv2.CC_STAT_TOP],
            stats[label, cv2.CC_STAT_WIDTH],
            stats[label, cv2.CC_STAT_HEIGHT],
        )
        if w < width * config.LOCATE_MIN_TABLE_WIDTH_FRACTION:
            continue  # not a table - short rule, underline, or noise
        h_lines, v_lines = _lines_in_region(h_proj, v_proj, x, y, x + w, y + h)
        if len(h_lines) < 2 or len(v_lines) < 2:
            continue  # no cell structure
        tables.append(_Table(x0=x, y0=y, x1=x + w, y1=y + h, h_lines=h_lines, v_lines=v_lines))

    tables.sort(key=lambda t: t.y0)
    return tables


def _select_student_table(tables: list[_Table]) -> tuple[_Table | None, _Table | None, list[str]]:
    """Pick (metadata_table, student_table) per FR-3's explicit mechanism.

    The student table is the 5-column grid below the 4-column Metadata Row
    band. Preference order keeps this robust when one band is missed:
    a 5-column table below a 4-column one; else the last 5-column table;
    else the lowest multi-row table (with a warning).
    """
    warnings: list[str] = []
    five_col = [t for t in tables if t.column_count == config.LOCATE_STUDENT_TABLE_COLUMNS]
    four_col = [t for t in tables if t.column_count == config.LOCATE_METADATA_TABLE_COLUMNS]

    if five_col:
        metadata = None
        for candidate in four_col:
            if candidate.y0 < five_col[-1].y0:
                metadata = candidate
        if metadata is None:
            warnings.append(
                "Metadata Row band not separately detected; student table selected by "
                "column count alone - if the two tables merged, leading rows may not be students"
            )
        return metadata, five_col[-1], warnings

    multi_row = [t for t in tables if t.row_count >= 2]
    if multi_row:
        warnings.append(
            f"Student table matched by fallback: expected {config.LOCATE_STUDENT_TABLE_COLUMNS} "
            f"columns, found tables with {[t.column_count for t in tables]} columns"
        )
        return None, multi_row[-1], warnings

    warnings.append("No student table structure detected")
    return None, None, warnings


def _grid_mask(h_mask: np.ndarray, v_mask: np.ndarray, tables: list[_Table]) -> np.ndarray:
    """Pixel-accurate mask of the printed grid, restricted to detected tables.

    Only line pixels within a drift band around a detected table line enter the
    mask - a long handwriting stroke elsewhere (a signature underline that
    survives the morphological opening) is NOT masked, so Story 1.4 still
    counts it as ink and crops keep it. The mask is dilated to cover the full
    printed stroke width plus binarization halo.
    """
    mask = np.zeros_like(h_mask)
    band = config.LOCATE_LINE_DRIFT_TOLERANCE_PX
    height, width = mask.shape

    for table in tables:
        for y in table.h_lines:
            y0, y1 = max(0, y - band), min(height, y + band + 1)
            mask[y0:y1, table.x0:table.x1] |= h_mask[y0:y1, table.x0:table.x1]
        for x in table.v_lines:
            x0, x1 = max(0, x - band), min(width, x + band + 1)
            mask[table.y0:table.y1, x0:x1] |= v_mask[table.y0:table.y1, x0:x1]

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (config.LOCATE_GRID_MASK_DILATION_PX, config.LOCATE_GRID_MASK_DILATION_PX)
    )
    return cv2.dilate(mask, kernel)


def _overlay(
    binary_image: np.ndarray, metadata: _Table | None, student: _Table | None
) -> np.ndarray:
    """Stage-6 RGB overlay: detected table bounds, grid, and Signature column."""
    overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2RGB)

    if metadata is not None:
        mx0, my0, mx1, my1 = metadata.line_bbox
        cv2.rectangle(overlay, (mx0, my0), (mx1, my1), (255, 165, 0), 6)

    if student is not None:
        sx0, sy0, sx1, sy1 = student.line_bbox
        cv2.rectangle(overlay, (sx0, sy0), (sx1, sy1), (30, 90, 220), 8)
        for y in student.h_lines:
            cv2.line(overlay, (sx0, y), (sx1, y), (30, 90, 220), 3)
        for x in student.v_lines:
            cv2.line(overlay, (x, sy0), (x, sy1), (0, 150, 60), 3)
        if len(student.v_lines) >= 2:
            cv2.rectangle(
                overlay, (student.v_lines[-2], sy0), (student.v_lines[-1], sy1), (200, 40, 160), 6
            )

    return overlay


def locate_table(
    deskewed_image: np.ndarray,
    info_file_row_count: int,
) -> tuple[SheetResult, np.ndarray]:
    """Locate the student table and signature cells on a deskewed sheet.

    Args:
        deskewed_image: binary uint8 image, output from pipeline stage 5 (deskewed)
        info_file_row_count: number of students from the Info File

    Returns:
        (sheet_result, overlay_image)
        - sheet_result: SheetResult with table structure and warnings.
          `cell_rois` (only published when a genuine 5-column student table was
          found) carries what Story 1.4 consumes: `rows` (per student row,
          header excluded, top to bottom) and `signature_column` (x0, x1).
        - overlay_image: RGB overlay for stage 6 ("table-grid")
    """
    h_mask, v_mask = _extract_line_masks(deskewed_image)
    h_proj, v_proj = _dilate_for_projection(h_mask, v_mask)
    tables = _find_tables(deskewed_image, h_mask, v_mask, h_proj, v_proj)
    metadata, student, warnings = _select_student_table(tables)

    detected_row_count = 0
    cell_rois = None
    if student is not None:
        # First band between the table's first two horizontal lines is the
        # printed header row ("No | Student No | ..."), not a student row.
        row_bands = list(zip(student.h_lines, student.h_lines[1:]))[1:]
        detected_row_count = len(row_bands)
        if student.column_count == config.LOCATE_STUDENT_TABLE_COLUMNS:
            # Publish cell geometry only for a trusted 5-column table; a
            # fallback-selected table's "last column" may be a stray stroke.
            cell_rois = {
                "rows": row_bands,
                "signature_column": (student.v_lines[-2], student.v_lines[-1]),
                "table_bbox": student.line_bbox,
            }
    if detected_row_count != info_file_row_count:
        warnings.append(
            f"Detected {detected_row_count} student rows, Info File has {info_file_row_count} students"
        )

    sheet_result = SheetResult(
        warnings=warnings,
        detected_row_count=detected_row_count,
        metadata_row_y_range=(metadata.y0, metadata.y1) if metadata is not None else None,
        student_table_y_range=(student.y0, student.y1) if student is not None else None,
        detected_grid_lines={
            "mask": _grid_mask(h_mask, v_mask, tables),
            "h_lines": student.h_lines if student is not None else [],
            "v_lines": student.v_lines if student is not None else [],
        },
        cell_rois=cell_rois,
    )

    return sheet_result, _overlay(deskewed_image, metadata, student)
