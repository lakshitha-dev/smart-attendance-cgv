"""Process page — the landing (Story 4.1, FR-12/UX-DR3/UX-DR4): two labelled
file slots and one Process button. This story ships the shell + empty state
only; Story 4.2 wires the actual processing run. ZERO engine logic here
(AD-1/AD-8) — the page never parses, detects, or persists anything."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

st.title("Mark today's attendance")

# UX-DR12 verbatim upload hint.
st.markdown("Add the sheet photo and the info file, then tap Process. That's all you need to do.")

# UX-DR3: two labelled slots. Filename + quiet "Ready" in slate on accept —
# slate, never Present green (status colours are for Attendance Records only).
sheet_photo = st.file_uploader("Signing Sheet", type=["jpeg", "jpg", "png"])
if sheet_photo is not None:
    st.markdown(f":gray[✓ Ready — {sheet_photo.name}]")

info_file = st.file_uploader("Info File", type=["xml"])
if info_file is not None:
    st.markdown(f":gray[✓ Ready — {info_file.name}]")

# UX-DR4: one full-width primary Process button, disabled until both inputs
# are ready. Story 4.2 fences the run in session state and calls the engine;
# until then the button arms but performs no action.
st.button(
    "Process",
    type="primary",
    use_container_width=True,
    disabled=sheet_photo is None or info_file is None,
)
