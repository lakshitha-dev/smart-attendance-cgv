"""Table localization: detect student table and signature cells on a deskewed signing sheet.

Story 1.3: Locate the student table and signature cells.
- Identify the 4-column Metadata Row (Date | Time | Lecturer's Name | Lecturer Signature)
- Identify the 5-column Student Table (No | Student No | Title | Student Name | Signature)
- Detect horizontal grid lines to infer dynamic row count
- Mask out grid lines from cell ROIs (AD-8, required by Story 1.4)
- Report row-count mismatches as warnings, never exceptions (AD-6)
- Produce an RGB overlay showing the detected table structure (stage 6, AD-3)
"""

from dataclasses import dataclass

import cv2
import numpy as np

from sams_core import config
from sams_core.models import SheetResult


@dataclass
class _GridStructure:
    """Detected grid lines: sorted horizontal and vertical line positions."""

    horizontal_lines: list[int]  # y-coordinates of horizontal lines (top to bottom)
    vertical_lines: list[int]  # x-coordinates of vertical lines (left to right)


def _detect_grid_lines(binary_image: np.ndarray) -> _GridStructure:
    """Detect horizontal and vertical grid lines via Hough transform.

    Returns a _GridStructure with sorted lists of line positions (y and x coords).
    Lines are filtered to exclude near-horizontal and near-vertical noise.
    """
    height, width = binary_image.shape
    ink = 255 - binary_image  # black table lines appear as white in inverted binary

    # Hough transform to detect all lines
    lines = cv2.HoughLinesP(
        ink,
        1,
        np.pi / 180,
        threshold=config.LOCATE_HOUGH_THRESHOLD,
        minLineLength=int(max(height, width) * config.LOCATE_MIN_LINE_LENGTH_FRACTION),
        maxLineGap=config.LOCATE_MAX_LINE_GAP,
    )

    h_lines = []
    v_lines = []

    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)

            if dy > dx:  # more vertical than horizontal
                # Vertical line: use x coordinate
                if dx < max(height, width) * config.LOCATE_MIN_VERTICAL_LINE_WIDTH:
                    v_lines.append((x1 + x2) // 2)
            else:  # more horizontal than vertical
                # Horizontal line: use y coordinate
                h_lines.append((y1 + y2) // 2)

    # Remove duplicates and sort
    h_lines = sorted(set(h_lines))
    v_lines = sorted(set(v_lines))

    # Cluster nearby horizontal lines together (tolerance: 5 pixels)
    # This filters out fragmented detections of the same line
    if h_lines:
        clustered_h = []
        current_cluster = [h_lines[0]]
        for line in h_lines[1:]:
            if line - current_cluster[-1] <= 5:  # within tolerance
                current_cluster.append(line)
            else:
                # Finalize current cluster
                clustered_h.append(int(np.mean(current_cluster)))
                current_cluster = [line]
        clustered_h.append(int(np.mean(current_cluster)))
        h_lines = sorted(clustered_h)

    # Similarly cluster vertical lines
    if v_lines:
        clustered_v = []
        current_cluster = [v_lines[0]]
        for line in v_lines[1:]:
            if line - current_cluster[-1] <= 5:
                current_cluster.append(line)
            else:
                clustered_v.append(int(np.mean(current_cluster)))
                current_cluster = [line]
        clustered_v.append(int(np.mean(current_cluster)))
        v_lines = sorted(clustered_v)

    return _GridStructure(h_lines, v_lines)


def _find_table_bands(grid: _GridStructure, info_file_row_count: int) -> tuple[
    tuple[int, int] | None,
    tuple[int, int] | None,
    int,
    list[str],
]:
    """Identify the metadata row and student table row ranges.

    The metadata row is a single 4-column band at the top.
    The student table is a multi-row 5-column band below it.

    Returns:
        (metadata_y_range, student_table_y_range, detected_row_count, warnings)
    """
    warnings = []

    if len(grid.horizontal_lines) < 3:
        # Not enough lines to form a table structure
        warnings.append("Insufficient horizontal grid lines detected for table structure")
        return None, None, 0, warnings

    # The first two horizontal lines bound the metadata row
    metadata_y0 = grid.horizontal_lines[0]
    metadata_y1 = grid.horizontal_lines[1]

    # The student table starts after the metadata row
    if len(grid.horizontal_lines) < 3:
        warnings.append("No student table rows detected")
        return (metadata_y0, metadata_y1), None, 0, warnings

    student_table_y0 = grid.horizontal_lines[1]
    student_table_y1 = grid.horizontal_lines[-1]

    # Infer row count from horizontal lines
    # Expected: metadata row (2 lines) + student rows (n+1 lines for n rows)
    # So if we have k horizontal lines total, we expect k-2 student rows
    detected_row_count = max(0, len(grid.horizontal_lines) - 2)

    # Check for row-count mismatch
    if detected_row_count != info_file_row_count:
        warnings.append(
            f"Detected {detected_row_count} student rows, Info File has {info_file_row_count} students"
        )

    return (
        (metadata_y0, metadata_y1),
        (student_table_y0, student_table_y1),
        detected_row_count,
        warnings,
    )


def _create_grid_mask(binary_image: np.ndarray, grid: _GridStructure) -> np.ndarray:
    """Create a binary mask of grid lines, for masking out from cell ROIs.

    Returns a binary image (same shape as input) where grid lines are white (255)
    and non-grid areas are black (0). This mask is used to exclude grid ink
    from cell-level inspection (Story 1.4).
    """
    height, width = binary_image.shape
    grid_mask = np.zeros((height, width), dtype=np.uint8)
    thickness = config.LOCATE_GRID_MASK_THICKNESS

    # Draw horizontal lines
    for y in grid.horizontal_lines:
        y0 = max(0, y - thickness)
        y1 = min(height, y + thickness + 1)
        grid_mask[y0:y1, :] = 255

    # Draw vertical lines
    for x in grid.vertical_lines:
        x0 = max(0, x - thickness)
        x1 = min(width, x + thickness + 1)
        grid_mask[:, x0:x1] = 255

    return grid_mask


def _create_overlay_image(binary_image: np.ndarray, grid: _GridStructure) -> np.ndarray:
    """Create an RGB overlay showing the detected table structure.

    Converts the binary image to RGB and draws the detected grid lines in color.
    This is the output for stage 6 ("table-grid") in the artifact registry.
    """
    # Convert binary to RGB (white background)
    overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2RGB)

    # Draw horizontal lines in blue
    for y in grid.horizontal_lines:
        cv2.line(overlay, (0, y), (overlay.shape[1], y), (0, 0, 255), 2)

    # Draw vertical lines in green
    for x in grid.vertical_lines:
        cv2.line(overlay, (x, 0), (x, overlay.shape[0]), (0, 255, 0), 2)

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
        - sheet_result: SheetResult with table structure and warnings
        - overlay_image: RGB overlay for stage 6 artifact, showing detected grid
    """
    # Detect grid lines
    grid = _detect_grid_lines(deskewed_image)

    # Find table bands (metadata row and student table)
    metadata_y_range, student_table_y_range, detected_row_count, warnings = _find_table_bands(
        grid, info_file_row_count
    )

    # Create grid mask for cell ROI masking (Story 1.4)
    grid_mask = _create_grid_mask(deskewed_image, grid)

    # Create overlay image for artifact display
    overlay_image = _create_overlay_image(deskewed_image, grid)

    # Construct result
    sheet_result = SheetResult(
        warnings=warnings,
        detected_row_count=detected_row_count,
        metadata_row_y_range=metadata_y_range,
        student_table_y_range=student_table_y_range,
        detected_grid_lines={"mask": grid_mask, "h_lines": grid.horizontal_lines, "v_lines": grid.vertical_lines},
    )

    return sheet_result, overlay_image
