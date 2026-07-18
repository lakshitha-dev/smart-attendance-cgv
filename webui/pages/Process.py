"""Process page — the landing (Story 4.1, FR-12/UX-DR3/UX-DR4): two labelled
file slots and one Process button. This story ships the shell + empty state
only; Story 4.2 wires the actual processing run. ZERO engine logic here
(AD-1/AD-8) — the page never parses, detects, or persists anything."""

import streamlit as st

st.title("Mark today's attendance")

# UX-DR12 verbatim upload hint.
st.markdown("Add the sheet photo and the info file, then tap Process. That's all you need to do.")


def _slot_ready(uploaded) -> bool:
    return uploaded is not None and uploaded.size > 0


def _ready_note(uploaded) -> None:
    """Quiet slate "Ready" (UX-DR3: primary slate, never Present green). The
    filename renders as a code span so markdown metacharacters in real-world
    names (scan[2].png, my_photo_*.jpg) cannot break the directive."""
    if uploaded is None:
        return
    if uploaded.size == 0:
        st.markdown("That file looks empty — please pick it again.")
        return
    safe_name = uploaded.name.replace("`", "'")
    st.markdown(f":primary[✓ Ready] — `{safe_name}`")


# UX-DR3: two labelled slots.
sheet_photo = st.file_uploader("Signing Sheet", type=["jpeg", "jpg", "png"])
st.caption("JPEG or PNG. On iPhone, choose 'Most Compatible' or export the photo as JPEG.")
_ready_note(sheet_photo)

info_file = st.file_uploader("Info File", type=["xml"])
_ready_note(info_file)

# UX-DR4: one full-width primary Process button, disabled until both inputs
# are ready. Story 4.2 fences the run in session state and calls the engine.
clicked = st.button(
    "Process",
    type="primary",
    width="stretch",
    disabled=not (_slot_ready(sheet_photo) and _slot_ready(info_file)),
)
if clicked:
    # Interim honesty until 4.2 lands: a tap must never silently do nothing.
    st.markdown("Processing arrives in the next update — nothing was saved. Your files are still here.")
