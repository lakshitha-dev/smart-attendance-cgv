import cv2
import numpy as np
import pytest

import sams_core.artifacts as artifacts
from sams_core.models import StageArtifact


@pytest.fixture(autouse=True)
def _redirect_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", tmp_path)
    return tmp_path


def test_save_stage_writes_expected_path(tmp_path):
    stage = StageArtifact(order=2, slug="greyscale", label="Greyscale", image=np.zeros((10, 10), dtype=np.uint8))

    out_path = artifacts.save_stage("2019-05-31", stage)

    assert out_path == tmp_path / "2019-05-31" / "02-greyscale.png"
    assert out_path.is_file()


def test_save_stage_five_sheets_do_not_overwrite_each_other(tmp_path):
    stage = StageArtifact(order=1, slug="original", label="Original", image=np.zeros((5, 5, 3), dtype=np.uint8))

    paths = {artifacts.save_stage(f"sheet-{i}", stage) for i in range(1, 6)}

    assert len(paths) == 5
    assert all(path.is_file() for path in paths)


def test_save_stage_converts_rgb_to_bgr_for_cv2(tmp_path):
    rgb_image = np.zeros((4, 4, 3), dtype=np.uint8)
    rgb_image[:, :] = (255, 0, 0)  # pure red in RGB
    stage = StageArtifact(order=1, slug="original", label="Original", image=rgb_image)

    out_path = artifacts.save_stage("sheet-1", stage)

    reloaded_bgr = cv2.imread(str(out_path))
    assert tuple(reloaded_bgr[0, 0]) == (0, 0, 255)  # red is (0, 0, 255) in BGR


def test_save_stage_greyscale_image_passes_through_unconverted(tmp_path):
    gray_image = np.full((4, 4), 128, dtype=np.uint8)
    stage = StageArtifact(order=4, slug="binarized", label="Binarized", image=gray_image)

    out_path = artifacts.save_stage("sheet-1", stage)

    reloaded = cv2.imread(str(out_path), cv2.IMREAD_UNCHANGED)
    assert reloaded.ndim == 2
    assert (reloaded == 128).all()
