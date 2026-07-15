from pathlib import Path

import pytest

from sams_core.errors import InputError
from sams_core.image_io import load_image

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"
FIXTURES = ROOT / "tests" / "data"


def test_load_valid_jpeg():
    image = load_image(str(SAMPLES / "1.jpeg"))
    assert image is not None
    assert image.ndim == 3


def test_load_missing_image():
    with pytest.raises(InputError, match="not found"):
        load_image(str(SAMPLES / "does_not_exist.jpeg"))


def test_load_unsupported_extension():
    with pytest.raises(InputError, match="Unsupported image type"):
        load_image(str(FIXTURES / "info_no_date.xml"))


def test_load_corrupt_image():
    with pytest.raises(InputError, match="could not be read"):
        load_image(str(FIXTURES / "corrupt.png"))


def test_load_valid_image_non_ascii_path(tmp_path):
    non_ascii_path = tmp_path / "café.jpeg"
    non_ascii_path.write_bytes((SAMPLES / "1.jpeg").read_bytes())

    image = load_image(str(non_ascii_path))
    assert image is not None
    assert image.ndim == 3
