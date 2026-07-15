"""Canonical stage registry (AD-3).

Stage order/slug/label are defined exactly ONCE here and shared verbatim by
CLI window titles, saved filenames (`artifacts.py`), and (later) the Web
strip (UX-DR16). The full registry has 7 stages; this story wires the first
five (original, greyscale, denoised, binarized, deskewed) as pure
ndarray-in/ndarray-out functions. Slots 6-7 (table grid, per-cell inspection)
are reserved for Stories 1.3/1.4.
"""

import logging
from collections.abc import Callable, Iterator

import cv2
import numpy as np

from sams_core import config
from sams_core.errors import InputError, ProcessingError
from sams_core.models import SheetResult, StageArtifact

logger = logging.getLogger(__name__)

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

    height, width = rgb_image.shape[:2]
    biggest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(biggest) < height * width * config.CROP_MIN_AREA_FRACTION:
        return None

    bbox = cv2.boundingRect(biggest)
    # Sanity: a Signing Sheet is large in BOTH dimensions. A big-area but
    # degenerate blob (e.g. Otsu splitting noise on an edge-to-edge photo)
    # must not slice real table rows away.
    _, _, box_w, box_h = bbox
    if box_w < width * config.CROP_MIN_BBOX_DIM_FRACTION or box_h < height * config.CROP_MIN_BBOX_DIM_FRACTION:
        return None

    return bbox


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
    if image.ndim != 3 or image.shape[2] != 3:
        raise InputError(
            "Expected a 3-channel colour image; got shape "
            f"{image.shape} (library callers must supply what image_io.load_image returns)"
        )
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _stage_greyscale(rgb_image: np.ndarray) -> np.ndarray:
    """Crop out the desk background, then convert to greyscale (photo -> Signing Sheet only)."""
    bbox = _find_sheet_bbox(rgb_image)
    if bbox is None:
        logger.warning(
            "Sheet boundary not detected; processing the full frame "
            "(desk background may leak into later stages)"
        )
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
        config.DESKEW_HOUGH_RHO,
        config.DESKEW_HOUGH_THETA_RAD,
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

    if not angles:
        # Lines exist but ALL exceed the candidate cap: heavy skew or a
        # sideways photo. Returning 0.0 is the only safe correction, but it
        # must not masquerade as "measured straight".
        logger.warning(
            "Deskew found %d line(s) but none within +/-%d deg; "
            "sheet may be heavily skewed or rotated 90 degrees",
            len(lines),
            config.DESKEW_MAX_CANDIDATE_ANGLE_DEG,
        )
        return 0.0

    return float(np.median(angles))


def _stage_deskewed(binary_image: np.ndarray) -> np.ndarray:
    """Rotate to correct residual tilt measured from the table grid's line angle.

    INTER_NEAREST + white constant border keep the {0, 255} binary invariant:
    smooth interpolation would create grey halos that downstream `ink > 0`
    tests count as ink, and replicated borders would smear edge pixels into
    fake grid lines. The canvas is expanded so no table corner is rotated
    out of frame.
    """
    angle = _measure_skew_angle(binary_image)
    if abs(angle) < config.DESKEW_MIN_ANGLE_DEG:
        return binary_image

    height, width = binary_image.shape
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_width = int(height * sin + width * cos)
    new_height = int(height * cos + width * sin)
    matrix[0, 2] += new_width / 2 - width / 2
    matrix[1, 2] += new_height / 2 - height / 2
    return cv2.warpAffine(
        binary_image,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


# Single ordered stage registry (AD-3): (order, slug, label, stage_function).
# Order/slug/label for ALL seven stages are defined here and nowhere else;
# stages 6-7 carry no pure stage function (they need table context beyond a
# bare ndarray) and are produced by locate.py / detect.py, which read their
# identity from this registry via `stage_identity()`.
_REGISTRY: tuple[tuple[int, str, str, StageFunction | None], ...] = (
    (1, "original", "Original", _stage_original),
    (2, "greyscale", "Greyscale", _stage_greyscale),
    (3, "denoised", "Denoised", _stage_denoised),
    (4, "binarized", "Binarized", _stage_binarized),
    (5, "deskewed", "Deskewed", _stage_deskewed),
    (6, "table-grid", "Table Grid", None),  # produced by locate.locate_table
    (7, "per-cell-inspection", "Per-Cell Inspection", None),  # produced by detect.detect_signatures
)


def stage_identity(order: int) -> tuple[int, str, str]:
    """Return (order, slug, label) for a registry stage — the single source (AD-3)."""
    if not 1 <= order <= len(_REGISTRY):
        raise ValueError(f"No pipeline stage with order {order} (valid: 1..{len(_REGISTRY)})")
    entry = _REGISTRY[order - 1]
    if entry[0] != order:
        raise ProcessingError(f"Stage registry out of order at slot {order}")
    return entry[0], entry[1], entry[2]


class PipelineRun:
    """Results that accumulate while the stage generator is consumed.

    The stage stream is lazy so the CLI/Web UI can display each stage LIVE as
    it is produced (FR-11); `sheet_result`/`cell_results` are populated by the
    time the generator is exhausted.
    """

    def __init__(self) -> None:
        self.sheet_result: SheetResult | None = None
        self.cell_results: list | None = None


def run_pipeline(image: np.ndarray) -> Iterator[StageArtifact]:
    """Yield a StageArtifact per pure-function registry stage, in canonical order."""
    current = image
    for order, slug, label, stage_fn in _REGISTRY:
        if stage_fn is None:
            return
        current = stage_fn(current)
        yield StageArtifact(order=order, slug=slug, label=label, image=current)


def run_pipeline_with_localization(
    image: np.ndarray, info_file_row_count: int
) -> tuple[Iterator[StageArtifact], PipelineRun]:
    """Stream the pipeline through table localization (stages 1-6).

    Returns (stage_generator, run). Stages are computed lazily as the
    generator is consumed — display them as they arrive (FR-11). After the
    generator is exhausted, `run.sheet_result` holds the table structure.
    """
    from sams_core import locate  # deferred: locate imports models/config only

    run = PipelineRun()

    def _stages() -> Iterator[StageArtifact]:
        current = image
        for stage in run_pipeline(image):  # yields every pure-function stage, stops before slot 6
            current = stage.image
            yield stage

        run.sheet_result, overlay_image = locate.locate_table(current, info_file_row_count)
        order, slug, label = stage_identity(6)
        yield StageArtifact(order=order, slug=slug, label=label, image=overlay_image)

    return _stages(), run


def run_pipeline_with_detection(
    image: np.ndarray, info_file_row_count: int
) -> tuple[Iterator[StageArtifact], PipelineRun]:
    """Stream the full pipeline through signature detection (stages 1-7).

    Returns (stage_generator, run). Stages are computed lazily as the
    generator is consumed — display them as they arrive (FR-11). After the
    generator is exhausted, `run.sheet_result` and `run.cell_results` are set.
    """
    from sams_core import detect  # deferred so the engine imports stay acyclic

    run = PipelineRun()

    def _stages() -> Iterator[StageArtifact]:
        inner_stages, inner_run = run_pipeline_with_localization(image, info_file_row_count)
        deskewed_slug = stage_identity(5)[1]  # registry-sourced, not a magic string
        deskewed_image: np.ndarray | None = None
        for stage in inner_stages:
            if stage.slug == deskewed_slug:
                deskewed_image = stage.image
            yield stage
        run.sheet_result = inner_run.sheet_result

        if deskewed_image is None:
            raise ProcessingError("Pipeline produced no deskewed stage; cannot run detection")
        run.cell_results, inspection_stage = detect.detect_signatures(
            deskewed_image, run.sheet_result, expected_row_count=info_file_row_count
        )
        yield inspection_stage

    return _stages(), run
