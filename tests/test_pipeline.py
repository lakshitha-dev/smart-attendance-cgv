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


def test_deskewed_stage_crops_out_desk_background():
    """AC2: background outside the sheet is excluded (shrinks the frame)."""
    image = load_image(str(SAMPLES / "1.jpeg"))
    stages = {s.slug: s.image for s in run_pipeline(image)}

    original_pixels = stages["original"].shape[0] * stages["original"].shape[1]
    deskewed_pixels = stages["deskewed"].shape[0] * stages["deskewed"].shape[1]
    assert deskewed_pixels < original_pixels


def test_no_cv2_imshow_in_sams_core():
    """AC3: cv2.imshow never appears inside sams_core (display is a CLI/adapter concern)."""
    sams_core_dir = ROOT / "sams_core"
    offenders = [
        path
        for path in sams_core_dir.glob("*.py")
        if "imshow" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
