"""Stage image writer (AD-7): persists StageArtifact frames to disk."""

from pathlib import Path

import cv2

from sams_core.config import OUTPUT_DIR
from sams_core.models import StageArtifact


def save_stage(sheet_id: str, stage: StageArtifact) -> Path:
    """Save one StageArtifact to `output/<Sheet Identifier>/NN-slug.png`."""
    sheet_dir = OUTPUT_DIR / sheet_id
    sheet_dir.mkdir(parents=True, exist_ok=True)
    out_path = sheet_dir / f"{stage.order:02d}-{stage.slug}.png"

    to_write = stage.image if stage.image.ndim == 2 else cv2.cvtColor(stage.image, cv2.COLOR_RGB2BGR)
    # cv2.imwrite fails silently on non-ASCII paths on Windows; encode + write bytes ourselves.
    encoded = cv2.imencode(".png", to_write)[1]
    encoded.tofile(str(out_path))

    return out_path


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
    out_path = crops_dir / f"{identifier}.png"

    to_write = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    encoded = cv2.imencode(".png", to_write)[1]
    encoded.tofile(str(out_path))

    return out_path
