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
    """UX-DR15: all inputs have visible labels (no placeholder-only fields).
    Checks both that the label text is present AND that no input hides it via
    label_visibility (a hidden label still populates the widget's .label)."""
    source = (WEBUI / page).read_text(encoding="utf-8")
    assert 'label_visibility="collapsed"' not in source, f"{page} collapses an input label"
    assert 'label_visibility="hidden"' not in source, f"{page} hides an input label"

    at = AppTest.from_file(str(WEBUI / page), default_timeout=60).run()
    assert not at.exception
    labels = [w.label for w in at.get("file_uploader")] + [w.label for w in at.text_input]
    for expected in expected_labels:
        assert any(expected in (lbl or "") for lbl in labels), f"{page} missing label {expected!r}"


def test_actions_use_no_html_event_handlers():
    """UX-DR14/keyboard: actions are real st.button widgets (keyboard-operable,
    in reading order) — never DOM event handlers or javascript: links smuggled
    through markdown/unsafe_allow_html anywhere under webui/."""
    # HTML event handler (onclick="/onmouseover = '), or a javascript: URL. The
    # \b + quote anchor keeps it from matching Python words like "done =" or the
    # `on_stage=` keyword argument.
    handler = re.compile(r"""\bon[a-z]+\s*=\s*['"]|javascript:""", re.IGNORECASE)
    for source in sorted(WEBUI.rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        match = handler.search(source.read_text(encoding="utf-8"))
        assert not match, f"{source.name} has an HTML event handler / js: link ({match.group()!r})"


def test_stage_and_evidence_images_carry_a_full_textual_description():
    """UX-DR15 alt text 'Stage N of 7 — <Label>'. st.image exposes no HTML alt
    attribute (a Streamlit platform limit), so the required text rides as the
    image caption — the visible, screen-reader-available description. Pin the
    FULL caption (count AND the '— <Label>' the AC names) so neither half drops,
    and require every st.image under webui/ to pass a caption at all."""
    process_src = (WEBUI / "pages" / "Process.py").read_text(encoding="utf-8")
    # Must include the "— {label}" suffix, not just the "Stage N of C" prefix.
    assert re.search(r"Stage \{[^}]*\} of \{[^}]*\} — \{", process_src), (
        "stage-image caption must be 'Stage N of <count> — <Label>' (UX-DR15)"
    )
    # Every st.image call under webui/ must carry a caption (evidence images on
    # the Investigate page rely on it as their accessible description too). Use a
    # line window rather than a paren regex — some calls nest parens, e.g.
    # st.image(str(png), caption=...).
    for source in sorted(WEBUI.rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        lines = source.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if "st.image(" in line:
                window = " ".join(lines[i : i + 5])
                assert "caption=" in window, f"{source.name}:{i + 1} st.image without a caption"
