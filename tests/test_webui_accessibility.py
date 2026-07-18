"""Story 4.7 (UX-DR13/DR14/DR15): the accessibility-floor guarantees that CAN
be asserted without a browser. The visual audits the DoD also requires —
phone/desktop/projector walkthrough screenshots, greyscale desaturation, and a
keyboard Tab/Enter pass — need a real browser and are recorded in the story's
Dev Agent Record as a manual hand-off, not faked here.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEBUI = ROOT / "webui"
PAGES = sorted((WEBUI / "pages").glob("*.py")) + [WEBUI / "app.py"]

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

# UX-DR14 banned interaction primitives — none may appear in webui source.
BANNED_CALLS = ("st.balloons", "st.snow", "st.toast", "st.camera_input")


def test_no_banned_interaction_primitives_in_webui():
    """UX-DR14: no auto-play/celebration/info-bearing-toast primitives, and no
    carousel/wizard constructs. (Confirm dialogs for reversible actions are
    banned too — resolve/undo use a direct st.button, verified in 4.4.)"""
    for source in sorted(WEBUI.rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        text = source.read_text(encoding="utf-8")
        for call in BANNED_CALLS:
            assert call not in text, f"{source.name} uses banned primitive {call} (UX-DR14)"


def test_status_chips_are_never_colour_only():
    """UX-DR15 accessibility floor: every status chip carries icon + label, so
    it survives greyscale — colour is never the sole signal."""
    from sams_core.models import AttendanceStatus
    from webui.process_logic import STATUS_CHIP

    for status in AttendanceStatus:
        icon, label, colour = STATUS_CHIP[status]
        assert icon and label, f"{status} chip must carry both an icon and a text label"
        assert label == status.value


@pytest.mark.parametrize(
    ("page", "expected_labels"),
    [
        ("pages/Process.py", ["Signing Sheet", "Info File"]),
        ("pages/Lookup.py", ["Student number"]),
        ("pages/Investigate.py", ["Student number"]),
    ],
)
def test_every_input_has_a_visible_label(page, expected_labels):
    """UX-DR15: all inputs have visible labels (no placeholder-only fields)."""
    at = AppTest.from_file(str(WEBUI / page), default_timeout=30).run()
    assert not at.exception
    labels = [w.label for w in at.get("file_uploader")] + [w.label for w in at.text_input]
    for expected in expected_labels:
        assert any(expected in (lbl or "") for lbl in labels), f"{page} missing label {expected!r}"


def test_actions_use_real_buttons_not_html_onclick():
    """UX-DR14/keyboard: actions are real st.button widgets (keyboard-operable,
    in reading order) — never HTML onclick handlers smuggled through markdown."""
    for source in PAGES:
        text = source.read_text(encoding="utf-8")
        assert "onclick" not in text.lower(), f"{source.name} has an HTML onclick handler"


def test_stage_images_carry_a_textual_description():
    """UX-DR15 alt text 'Stage N of 7 — <Label>'. st.image exposes no HTML alt
    attribute (a Streamlit platform limit), so the required text is carried as
    the image caption — the visible, screen-reader-available description. This
    pins the caption wording so it can't silently drop."""
    source = (WEBUI / "pages" / "Process.py").read_text(encoding="utf-8")
    assert re.search(r"Stage \{[^}]*\} of \{[^}]*\}", source), (
        "stage images must caption 'Stage N of <count> — <Label>' (UX-DR15)"
    )
