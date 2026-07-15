from pathlib import Path

from sams_core.image_io import load_image
from sams_core.models import StageArtifact
from sams_core.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_signin-sheets"

EXPECTED_STAGES = (
    (1, "original"),
    (2, "greyscale"),
    (3, "denoised"),
    (4, "binarized"),
    (5, "deskewed"),
)


def test_run_pipeline_yields_stages_in_canonical_order():
    image = load_image(str(SAMPLES / "1.jpeg"))
    stages = list(run_pipeline(image))

    assert [(s.order, s.slug) for s in stages] == list(EXPECTED_STAGES)
    assert all(isinstance(s, StageArtifact) for s in stages)


def test_run_pipeline_labels_are_glossary_verbatim():
    image = load_image(str(SAMPLES / "1.jpeg"))
    stages = {s.slug: s.label for s in run_pipeline(image)}

    assert stages == {
        "original": "Original",
        "greyscale": "Greyscale",
        "denoised": "Denoised",
        "binarized": "Binarized",
        "deskewed": "Deskewed",
    }


def test_original_stage_is_rgb_and_later_stages_are_greyscale():
    image = load_image(str(SAMPLES / "1.jpeg"))
    stages = {s.slug: s.image for s in run_pipeline(image)}

    assert stages["original"].ndim == 3 and stages["original"].shape[2] == 3
    for slug in ("greyscale", "denoised", "binarized", "deskewed"):
        assert stages[slug].ndim == 2


def test_stage_functions_are_pure_same_input_same_output():
    image = load_image(str(SAMPLES / "1.jpeg"))
    first_run = [s.image.copy() for s in run_pipeline(image)]
    second_run = [s.image.copy() for s in run_pipeline(image)]

    for first, second in zip(first_run, second_run, strict=True):
        assert (first == second).all()


def test_run_pipeline_completes_on_all_five_sample_sheets():
    for i in range(1, 6):
        image = load_image(str(SAMPLES / f"{i}.jpeg"))
        stages = list(run_pipeline(image))
        assert [s.slug for s in stages] == [slug for _, slug in EXPECTED_STAGES]
        for stage in stages:
            assert stage.image.size > 0


def test_greyscale_stage_crops_out_desk_background_on_all_five_sheets():
    """AC2: background outside the sheet is excluded (the greyscale stage crops
    to the detected sheet) — on every sample. The deskew stage may legitimately
    re-grow the frame slightly: its canvas expands so rotation clips no corners."""
    for i in range(1, 6):
        image = load_image(str(SAMPLES / f"{i}.jpeg"))
        stages = {s.slug: s.image for s in run_pipeline(image)}

        original_pixels = stages["original"].shape[0] * stages["original"].shape[1]
        cropped_pixels = stages["greyscale"].shape[0] * stages["greyscale"].shape[1]
        deskewed_pixels = stages["deskewed"].shape[0] * stages["deskewed"].shape[1]
        assert cropped_pixels < original_pixels, f"sheet {i}: desk background not excluded"
        assert deskewed_pixels <= cropped_pixels * 1.2, f"sheet {i}: deskew canvas grew abnormally"


def test_deskew_preserves_binary_invariant():
    """Rotation must keep the {0, 255} value set: grey interpolation halos
    would later be counted as ink by `> 0` tests (regression: INTER_CUBIC)."""
    import numpy as np

    from sams_core.pipeline import _stage_deskewed

    image = np.full((600, 800), 255, dtype=np.uint8)
    for y in (100, 200, 300, 400, 500):  # long table-like lines at ~2 degrees
        import cv2

        cv2.line(image, (20, y), (780, y + 27), 0, 3)

    deskewed = _stage_deskewed(image)

    assert set(np.unique(deskewed)) <= {0, 255}, "deskew produced non-binary grey values"


def test_stage_identity_rejects_out_of_range_orders():
    import pytest

    from sams_core.pipeline import stage_identity

    with pytest.raises(ValueError):
        stage_identity(0)
    with pytest.raises(ValueError):
        stage_identity(8)
    assert stage_identity(5)[1] == "deskewed"


def test_full_pipeline_streams_lazily_and_populates_run_holder():
    """FR-11: stages must be produced (and thus displayable) one at a time,
    not materialized up front; results land on the holder by exhaustion."""
    from sams_core.pipeline import run_pipeline_with_detection

    image = load_image(str(SAMPLES / "1.jpeg"))
    stages, run = run_pipeline_with_detection(image, 6)

    first = next(stages)
    assert first.slug == "original"
    assert run.sheet_result is None, "pipeline ran eagerly — stages must stream lazily"

    remaining = list(stages)
    assert [s.order for s in [first, *remaining]] == [1, 2, 3, 4, 5, 6, 7]
    assert run.sheet_result is not None
    assert run.cell_results is not None and len(run.cell_results) == 6


def test_no_cv2_imshow_in_sams_core():
    """AC3: cv2.imshow never appears inside sams_core (display is a CLI/adapter concern)."""
    sams_core_dir = ROOT / "sams_core"
    offenders = [
        path
        for path in sams_core_dir.glob("*.py")
        if "imshow" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
