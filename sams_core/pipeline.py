"""Canonical stage registry (AD-3).

Stage order/slug/label are defined exactly ONCE here and shared verbatim by
CLI window titles, saved filenames (`artifacts.py`), and (later) the Web
strip (UX-DR16). The full registry has 7 stages; this story wires the first
five (original, greyscale, denoised, binarized, deskewed) as pure
ndarray-in/ndarray-out functions. Slots 6-7 (table grid, per-cell inspection)
are reserved for Stories 1.3/1.4.
"""

from collections.abc import Callable, Iterator

import cv2
import numpy as np

from sams_core import config
from sams_core.models import StageArtifact

StageFunction = Callable[[np.ndarray], np.ndarray]


def _find_sheet_bbox(rgb_image: np.ndarray) -> tuple[int, int, int, int] | None:
    """Find the Signing Sheet's bounding box within the photo, or None if not found.

    The paper is near-neutral (low HSV saturation) while the desk background carries
    more colour, even under uneven lighting - Otsu-threshold the saturation channel
    to isolate the paper's silhouette (more reliable here than an edge-based quad
    search, which fragments on shadows and the punched holes/margin notes).
    """
    saturation = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)[:, :, 1]
    blurred = cv2.GaussianBlur(saturation, config.CROP_BLUR_KERNEL, 0)
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, config.CROP_MORPH_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, config.CROP_MORPH_KERNEL)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    image_area = rgb_image.shape[0] * rgb_image.shape[1]
    biggest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(biggest) < image_area * config.CROP_MIN_AREA_FRACTION:
        return None

    return cv2.boundingRect(biggest)


def _crop_with_padding(image: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Crop `image` to `bbox`, expanded by a pixel margin so boundary-touching ink survives."""
    height, width = image.shape[:2]
    x, y, box_w, box_h = bbox
    pad = config.CROP_PADDING_PX
    x0, y0 = max(x - pad, 0), max(y - pad, 0)
    x1, y1 = min(x + box_w + pad, width), min(y + box_h + pad, height)
    return image[y0:y1, x0:x1]


def _stage_original(image: np.ndarray) -> np.ndarray:
    """The raw photo, converted from cv2's BGR to display-ready RGB (AD-2)."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _stage_greyscale(rgb_image: np.ndarray) -> np.ndarray:
    """Crop out the desk background, then convert to greyscale (photo -> Signing Sheet only)."""
    bbox = _find_sheet_bbox(rgb_image)
    cropped = _crop_with_padding(rgb_image, bbox) if bbox is not None else rgb_image
    return cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY)


def _stage_denoised(gray_image: np.ndarray) -> np.ndarray:
    """Remove photo/scan sensor noise ahead of thresholding.

    Median blur, not fastNlMeansDenoising: at these phone-photo resolutions
    (~4000x3000) NLM takes ~20s/image, which is unusable for a "live" CLI
    display; median blur is near-instant and adequate for shot noise.
    """
    return cv2.medianBlur(gray_image, config.DENOISE_MEDIAN_KERNEL)


def _stage_binarized(denoised_image: np.ndarray) -> np.ndarray:
    """Adaptive Gaussian threshold, chosen over global Otsu for uneven desk lighting (NFR-1)."""
    return cv2.adaptiveThreshold(
        denoised_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.THRESHOLD_BLOCK_SIZE,
        config.THRESHOLD_C,
    )


def _measure_skew_angle(binary_image: np.ndarray) -> float:
    """Median angle of long near-horizontal ink lines (table borders/rows).

    Robust to scattered text/annotations that would otherwise dominate a
    whole-page minAreaRect fit: only long straight segments (the table grid)
    vote on the angle.
    """
    width = binary_image.shape[1]
    ink = 255 - binary_image
    lines = cv2.HoughLinesP(
        ink,
        1,
        np.pi / 360,
        threshold=config.DESKEW_HOUGH_THRESHOLD,
        minLineLength=width * config.DESKEW_MIN_LINE_LENGTH_FRACTION,
        maxLineGap=config.DESKEW_MAX_LINE_GAP,
    )
    if lines is None:
        return 0.0

    angles = []
    for x1, y1, x2, y2 in lines[:, 0]:
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        angle = (angle + 90) % 180 - 90  # normalize to (-90, 90]
        if abs(angle) <= config.DESKEW_MAX_CANDIDATE_ANGLE_DEG:
            angles.append(angle)

    return float(np.median(angles)) if angles else 0.0


def _stage_deskewed(binary_image: np.ndarray) -> np.ndarray:
    """Rotate to correct residual tilt measured from the table grid's line angle."""
    angle = _measure_skew_angle(binary_image)
    if abs(angle) < config.DESKEW_MIN_ANGLE_DEG:
        return binary_image

    height, width = binary_image.shape
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        binary_image, matrix, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


# Single ordered stage registry (AD-3): (order, slug, label, stage_function).
# `None` marks a stage not yet implemented — reserved for a later story.
_REGISTRY: tuple[tuple[int, str, str, StageFunction | None], ...] = (
    (1, "original", "Original", _stage_original),
    (2, "greyscale", "Greyscale", _stage_greyscale),
    (3, "denoised", "Denoised", _stage_denoised),
    (4, "binarized", "Binarized", _stage_binarized),
    (5, "deskewed", "Deskewed", _stage_deskewed),
    (6, "table-grid", "Table Grid", None),  # Story 1.3
    (7, "per-cell-inspection", "Per-Cell Inspection", None),  # Story 1.4
)


def run_pipeline(image: np.ndarray) -> Iterator[StageArtifact]:
    """Yield a StageArtifact per implemented registry stage, in canonical order."""
    current = image
    for order, slug, label, stage_fn in _REGISTRY:
        if stage_fn is None:
            return
        current = stage_fn(current)
        yield StageArtifact(order=order, slug=slug, label=label, image=current)
