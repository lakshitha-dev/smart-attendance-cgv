from pathlib import Path

import cv2
import numpy as np

from sams_core.config import SUPPORTED_IMAGE_EXTENSIONS
from sams_core.errors import InputError


def load_image(path: str) -> np.ndarray:
    """Load a Signing Sheet image (.png/.jpeg/.jpg), raising InputError on failure."""
    image_path = Path(path)
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise InputError(
            f"Unsupported image type '{image_path.suffix}': expected "
            f"{', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )
    if not image_path.is_file():
        raise InputError(f"Image not found: {path}")

    # cv2.imread fails silently on non-ASCII paths on Windows; read bytes ourselves instead.
    file_bytes = np.fromfile(str(image_path), dtype=np.uint8)
    return _decode(file_bytes, source=path)


def load_image_bytes(data: bytes) -> np.ndarray:
    """Decode raw image bytes to a BGR array (AD-12: the Web UI has no path).

    Reuses the same validation/`InputError` path as `load_image` so both
    frontends surface identical decode-level errors (EXPERIENCE.md "Bad image").
    """
    if not data:
        raise InputError("Image could not be read (unreadable or corrupt): empty upload")
    file_bytes = np.frombuffer(data, dtype=np.uint8)
    return _decode(file_bytes, source="uploaded image")


def _decode(file_bytes: np.ndarray, source: str) -> np.ndarray:
    """Shared decode step for path- and bytes-based loading."""
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise InputError(f"Image could not be read (unreadable or corrupt): {source}")
    return image
