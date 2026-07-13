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
