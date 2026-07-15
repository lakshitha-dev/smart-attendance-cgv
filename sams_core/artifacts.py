"""Stage image writer (AD-7): persists StageArtifact frames to disk."""

import shutil
from pathlib import Path

import cv2

from sams_core.config import OUTPUT_DIR
from sams_core.errors import ProcessingError
from sams_core.models import StageArtifact


def _write_png(image, out_path: Path) -> Path:
    """Encode + write one image, validating both steps.

    cv2.imwrite fails silently on non-ASCII paths on Windows, so we encode and
    write the bytes ourselves — and unlike the bare `imencode(...)[1]` pattern,
    the success flag is checked so a corrupt/empty PNG can never be left behind
    silently (Epic 3 reads crops back as verification probes).
    """
    if image is None or image.size == 0:
        raise ProcessingError(f"Refusing to write an empty image to {out_path.name}")

    to_write = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".png", to_write)
    if not ok:
        raise ProcessingError(f"PNG encoding failed for {out_path.name}")
    encoded.tofile(str(out_path))
    return out_path


def reset_sheet_output(sheet_id: str) -> Path:
    """Clear this sheet's output folder at the start of a run.

    Re-processing must never leave stale files (e.g. crops for rows that no
    longer exist) mixed indistinguishably with fresh output.
    """
    sheet_dir = OUTPUT_DIR / sheet_id
    if sheet_dir.exists():
        shutil.rmtree(sheet_dir)
    sheet_dir.mkdir(parents=True, exist_ok=True)
    return sheet_dir


def save_stage(sheet_id: str, stage: StageArtifact) -> Path:
    """Save one StageArtifact to `output/<Sheet Identifier>/NN-slug.png`."""
    sheet_dir = OUTPUT_DIR / sheet_id
    sheet_dir.mkdir(parents=True, exist_ok=True)
    return _write_png(stage.image, sheet_dir / f"{stage.order:02d}-{stage.slug}.png")


def save_crop(sheet_id: str, identifier: str, image) -> Path:
    """Save one per-student signature-cell crop (Story 1.4, AD-10).

    Written to `output/<Sheet Identifier>/crops/<identifier>.png` — NOT a
    StageArtifact (crops are per-student, not per-pipeline-stage). `identifier`
    is normally the canonical 8-digit Student Index once it is known (Epic 3
    reads these back as verification probes); callers without a resolved
    index yet may pass a row ordinal instead.
    """
    crops_dir = OUTPUT_DIR / sheet_id / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    return _write_png(image, crops_dir / f"{identifier}.png")
